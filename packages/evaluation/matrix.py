from __future__ import annotations

from typing import Any

from packages.evaluation.goldset import GoldCase, evaluate_case, summarize_results
from packages.llm.profiles import export_provider_profiles, get_provider_profile, recommended_provider_for_lane


def evaluate_provider(provider: str, cases: list[GoldCase]) -> dict[str, Any]:
    results = [evaluate_case(case, llm_provider=provider) for case in cases]
    summary = summarize_results(results)
    profile = get_provider_profile(provider).to_dict()
    return {
        'provider': provider,
        'status': 'ok',
        'summary': summary,
        'cases': results,
        'profile': profile,
    }


def evaluate_provider_matrix(providers: list[str], cases: list[GoldCase], *, lane: str = 'quant_experimental') -> dict[str, Any]:
    matrix: list[dict[str, Any]] = []
    for provider in providers:
        try:
            matrix.append(evaluate_provider(provider, cases))
        except Exception as exc:  # pragma: no cover - operational fallback
            matrix.append({
                'provider': provider,
                'status': 'error',
                'error': f'{type(exc).__name__}: {exc}',
                'summary': None,
                'cases': [],
                'profile': get_provider_profile(provider).to_dict(),
            })
    ranking = [
        {
            'provider': item['provider'],
            'exact_accuracy': item['summary']['exact_accuracy'],
            'micro_false_positive_rate': item['summary']['micro_false_positive_rate'],
            'micro_false_negative_rate': item['summary']['micro_false_negative_rate'],
        }
        for item in matrix if item.get('status') == 'ok' and item.get('summary')
    ]
    ranking.sort(
        key=lambda row: (
            -row['exact_accuracy'],
            row['micro_false_positive_rate'],
            row['micro_false_negative_rate'],
            row['provider'],
        )
    )
    recommended = recommended_provider_for_lane(lane, {'ranking': ranking})
    return {
        'lane': lane,
        'providers': providers,
        'matrix': matrix,
        'ranking': ranking,
        'recommended_by_lane': {lane: recommended} if recommended else {},
        'provider_profiles': export_provider_profiles(),
    }


def matrix_markdown_report(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    lane = payload.get('lane', 'quant_experimental')
    lines.append('# Quant Experimental Evaluation Matrix')
    lines.append('')
    lines.append(
        f'This report compares available providers against the pinned gold set for the `{lane}` certification type.'
    )
    lines.append('')
    lines.append('| Provider | Status | Exact accuracy | FP rate | FN rate | Self-hostable | JSON/schema |')
    lines.append('|---|---:|---:|---:|---:|---:|---:|')
    for item in payload.get('matrix', []):
        profile = item.get('profile') or {}
        if item.get('status') != 'ok' or not item.get('summary'):
            lines.append(
                f"| {item['provider']} | error | – | – | – | {str(profile.get('self_hostable', '–'))} | {str(profile.get('supports_response_schema', '–'))} |"
            )
            continue
        s = item['summary']
        lines.append(
            f"| {item['provider']} | ok | {s['exact_accuracy']:.3f} | {s['micro_false_positive_rate']:.3f} | {s['micro_false_negative_rate']:.3f} | {str(profile.get('self_hostable', False))} | {str(profile.get('supports_response_schema', False))} |"
        )
    lines.append('')
    lines.append('## Ranking')
    lines.append('')
    if not payload.get('ranking'):
        lines.append('No successful provider runs were recorded.')
    else:
        for idx, row in enumerate(payload['ranking'], start=1):
            lines.append(
                f"{idx}. **{row['provider']}** — exact accuracy {row['exact_accuracy']:.3f}, FP {row['micro_false_positive_rate']:.3f}, FN {row['micro_false_negative_rate']:.3f}"
            )
    rec = (payload.get('recommended_by_lane') or {}).get(lane)
    lines.append('')
    lines.append('## Recommended provider by lane')
    lines.append('')
    if rec:
        prof = rec.get('profile') or {}
        metrics = rec.get('metrics') or {}
        lines.append(f"For **{lane}**, the current recommendation is **{rec['provider']}**.")
        lines.append('')
        lines.append(f"- Reason: {rec.get('reason', 'n/a')}")
        if metrics:
            lines.append(f"- Exact accuracy: {metrics.get('exact_accuracy', 0):.3f}")
            lines.append(f"- FP rate: {metrics.get('micro_false_positive_rate', 0):.3f}")
            lines.append(f"- FN rate: {metrics.get('micro_false_negative_rate', 0):.3f}")
        lines.append(f"- Self-hostable: {prof.get('self_hostable')}")
        lines.append(f"- Response-schema support: {prof.get('supports_response_schema')}")
        lines.append(f"- Recommended lanes: {', '.join(prof.get('recommended_lanes', [])) or 'n/a'}")
    else:
        lines.append('No recommendation available.')
    lines.append('')
    lines.append('## Provider profile summary')
    lines.append('')
    lines.append('| Provider | Transport | API style | Auth | Self-hostable | Recommended lanes |')
    lines.append('|---|---|---|---|---:|---|')
    profiles = (payload.get('provider_profiles') or {}).get('profiles') or []
    for profile in profiles:
        lines.append(
            f"| {profile['provider_id']} | {profile['transport']} | {profile['api_style']} | {profile['auth_mode']} | {str(profile['self_hostable'])} | {', '.join(profile.get('recommended_lanes', []))} |"
        )
    lines.append('')
    lines.append('## Notes')
    lines.append('')
    lines.append('- This matrix is only as strong as the pinned gold set.')
    lines.append('- Providers marked `error` were unavailable or not configured in the current runtime.')
    lines.append('- Provider-agnostic does not mean provider-identical. Every backend needs an explicit operational profile.')
    lines.append('- SANDBOX ONLY — NOT RED TEAM CERTIFIED — MANUAL PROMPT-INJECTION GUARDRAILS.')
    return '\n'.join(lines) + '\n'
