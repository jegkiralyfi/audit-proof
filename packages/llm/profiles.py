from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from packages.core.config import RuntimeConfig


@dataclass(slots=True)
class ProviderProfile:
    provider_id: str
    display_name: str
    transport: str
    source_kind: str
    supports_system_prompt: bool
    supports_json_mode: bool
    supports_response_schema: bool
    self_hostable: bool
    recommended_lanes: list[str]
    api_style: str
    auth_mode: str
    env_requirements: list[str]
    known_caveats: list[str]
    notes: str = ''

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


PROVIDER_PROFILES: dict[str, ProviderProfile] = {
    'heuristic': ProviderProfile(
        provider_id='heuristic',
        display_name='Heuristic offline baseline',
        transport='in-process',
        source_kind='builtin',
        supports_system_prompt=False,
        supports_json_mode=True,
        supports_response_schema=True,
        self_hostable=True,
        recommended_lanes=['quant_experimental'],
        api_style='none',
        auth_mode='none',
        env_requirements=[],
        known_caveats=['Pattern-based and conservative; not a semantic model.'],
        notes='Good pinned baseline and fallback for CI/evaluation.',
    ),
    'openai-compatible': ProviderProfile(
        provider_id='openai-compatible',
        display_name='OpenAI-compatible chat completions',
        transport='http',
        source_kind='builtin',
        supports_system_prompt=True,
        supports_json_mode=True,
        supports_response_schema=False,
        self_hostable=True,
        recommended_lanes=['quant_experimental', 'reference_integrity'],
        api_style='openai-chat-completions',
        auth_mode='bearer-token',
        env_requirements=['AUDIT_PROOF_LLM_BASE_URL', 'AUDIT_PROOF_LLM_API_KEY_ENV'],
        known_caveats=['Compatibility varies by backend implementation.', 'JSON mode behavior is backend-dependent.'],
        notes='Use for self-hosted vLLM/TGI/llama.cpp server deployments when they expose an OpenAI-style API.',
    ),
    'anthropic': ProviderProfile(
        provider_id='anthropic',
        display_name='Anthropic Messages API',
        transport='http',
        source_kind='builtin',
        supports_system_prompt=False,
        supports_json_mode=False,
        supports_response_schema=False,
        self_hostable=False,
        recommended_lanes=['quant_experimental'],
        api_style='anthropic-messages',
        auth_mode='x-api-key',
        env_requirements=['ANTHROPIC_API_KEY'],
        known_caveats=['Requires manual JSON discipline in prompts.', 'Response parsing depends on text block extraction.'],
        notes='Useful as a hosted comparative provider in the matrix.',
    ),
    'gemini': ProviderProfile(
        provider_id='gemini',
        display_name='Google Gemini generateContent',
        transport='http',
        source_kind='builtin',
        supports_system_prompt=True,
        supports_json_mode=True,
        supports_response_schema=True,
        self_hostable=False,
        recommended_lanes=['quant_experimental', 'reference_integrity'],
        api_style='google-generativelanguage',
        auth_mode='api-key-query-param',
        env_requirements=['GEMINI_API_KEY'],
        known_caveats=['Structured output support depends on model/version.', 'Rate limits and quotas are external to Audit-Proof.'],
        notes='Good candidate when schema-constrained JSON output matters.',
    ),
    'custom': ProviderProfile(
        provider_id='custom',
        display_name='Custom Python provider',
        transport='in-process-or-http',
        source_kind='plugin-or-local',
        supports_system_prompt=True,
        supports_json_mode=True,
        supports_response_schema=True,
        self_hostable=True,
        recommended_lanes=['quant_experimental', 'reference_integrity', 'computational_reproducibility_preflight'],
        api_style='custom',
        auth_mode='custom',
        env_requirements=['depends on deployment'],
        known_caveats=['Behavior is entirely implementation-dependent.', 'Must satisfy the provider contract manually.'],
        notes='Preferred path for organization-specific or self-hosted deployments.',
    ),
}

ALIASES = {
    'openai': 'openai-compatible',
    'openai_compatible': 'openai-compatible',
    'claude': 'anthropic',
    'gemini-direct': 'gemini',
    'google-genai': 'gemini',
    'mock': 'heuristic',
    'offline': 'heuristic',
}


def canonical_provider_id(provider_name: str) -> str:
    raw = (provider_name or '').strip().lower()
    if raw.startswith('custom:') or (':' in raw and raw not in ALIASES):
        return 'custom'
    return ALIASES.get(raw, raw or 'heuristic')


def get_provider_profile(provider_name: str) -> ProviderProfile:
    return PROVIDER_PROFILES.get(canonical_provider_id(provider_name), PROVIDER_PROFILES['heuristic'])


def export_provider_profiles() -> dict[str, Any]:
    return {
        'profiles': [profile.to_dict() for profile in PROVIDER_PROFILES.values()],
        'aliases': ALIASES,
    }


def recommended_provider_for_lane(lane: str, matrix_payload: dict[str, Any] | None = None) -> dict[str, Any] | None:
    lane = (lane or '').strip()
    if matrix_payload:
        ranking = matrix_payload.get('ranking') or []
        for row in ranking:
            profile = get_provider_profile(row['provider'])
            if lane in profile.recommended_lanes:
                return {
                    'lane': lane,
                    'provider': row['provider'],
                    'reason': 'top-ranked available provider compatible with lane',
                    'profile': profile.to_dict(),
                    'metrics': row,
                }
        if ranking:
            row = ranking[0]
            return {
                'lane': lane,
                'provider': row['provider'],
                'reason': 'top-ranked available provider on current matrix',
                'profile': get_provider_profile(row['provider']).to_dict(),
                'metrics': row,
            }
    for profile in PROVIDER_PROFILES.values():
        if lane in profile.recommended_lanes:
            return {
                'lane': lane,
                'provider': profile.provider_id,
                'reason': 'static profile recommendation',
                'profile': profile.to_dict(),
            }
    return None


def runtime_provider_summary(config: RuntimeConfig) -> dict[str, Any]:
    profile = get_provider_profile(config.llm_provider)
    return {
        'active_provider': canonical_provider_id(config.llm_provider),
        'profile': profile.to_dict(),
    }
