from __future__ import annotations

from typing import Any

from packages.core.models import PolicyCheck
from packages.llm.schemas import EvidenceRequest
from packages.checks.domains.psychology.prompts import load_prompt_template

PROMPT_TEMPLATE_MAP = {
    "sample_size_present": "sample_size",
    "control_group_present": "control_group",
    "raw_data_availability": "raw_data",
    "overclaiming_detected": "overclaiming",
}


def resolve_prompt_name(configured_check: PolicyCheck) -> str | None:
    params = configured_check.params or {}
    explicit = params.get("prompt_template")
    if isinstance(explicit, str) and explicit.strip():
        return explicit.strip()
    return PROMPT_TEMPLATE_MAP.get(configured_check.id)


def build_instruction(configured_check: PolicyCheck) -> str:
    params = configured_check.params or {}
    prompt_name = resolve_prompt_name(configured_check)
    base = load_prompt_template(prompt_name) if prompt_name else ""
    extra = str(params.get("instruction", "")).strip()
    if base and extra:
        return f"{base}\n\nTask-specific note: {extra}"
    if base:
        return base
    if extra:
        return extra
    return f"Assess evidence relevant to psychology methodological check {configured_check.id}."


def build_evidence_request(
    *,
    configured_check: PolicyCheck,
    domain: str,
    document_title: str | None,
    excerpt: str,
    preferred_sections: list[str],
) -> EvidenceRequest:
    params = configured_check.params or {}
    return EvidenceRequest(
        domain=domain,
        check_id=f"{domain}.{configured_check.id}",
        instruction=build_instruction(configured_check),
        document_title=document_title,
        document_excerpt=excerpt,
        preferred_sections=preferred_sections,
        pass_patterns=list(params.get("pass_patterns", [])),
        fail_patterns=list(params.get("fail_patterns", [])),
        evidence_limit=int(params.get("evidence_limit", 2)),
        match_scope=str(params.get("search_scope", "preferred")),
    )


def runner_context_metadata(configured_check: PolicyCheck) -> dict[str, Any]:
    prompt_name = resolve_prompt_name(configured_check)
    return {
        "prompt_template": f"psychology/{prompt_name}.md" if prompt_name else None,
        "llm_domain": "psychology",
    }
