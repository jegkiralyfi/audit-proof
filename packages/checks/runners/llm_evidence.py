from __future__ import annotations

import importlib
from typing import Any

from packages.checks.base import CheckRunner
from packages.checks.common.scoring import build_result
from packages.core.models import ParsedDocument, PolicyCheck
from packages.llm.client import LLMClient
from packages.llm.extraction import select_excerpt
from packages.llm.guardrails import clamp_response
from packages.llm.schemas import EvidenceRequest


def _load_domain_hook(domain: str):
    module_name = f"packages.checks.domains.{domain}.llm_checks"
    try:
        return importlib.import_module(module_name)
    except ModuleNotFoundError:
        return None


class LLMEvidenceCheckRunner(CheckRunner):
    def __init__(self) -> None:
        self.default_client = LLMClient()

    def _build_request(
        self,
        document: ParsedDocument,
        configured_check: PolicyCheck,
        *,
        domain: str,
        excerpt: str,
        preferred_sections: list[str],
        match_scope: str,
    ) -> tuple[EvidenceRequest, dict[str, Any]]:
        hook = _load_domain_hook(domain)
        if hook and hasattr(hook, "build_evidence_request"):
            request = hook.build_evidence_request(
                configured_check=configured_check,
                domain=domain,
                document_title=document.title,
                excerpt=excerpt,
                preferred_sections=preferred_sections,
            )
            metadata = getattr(hook, "runner_context_metadata", lambda *_args, **_kwargs: {})(configured_check)
            return request, metadata or {}

        params = configured_check.params or {}
        instruction = str(
            params.get(
                "instruction",
                f"Check whether the document contains evidence relevant to {configured_check.id}.",
            )
        )
        request = EvidenceRequest(
            domain=domain,
            check_id=f"{domain}.{configured_check.id}",
            instruction=instruction,
            document_title=document.title,
            document_excerpt=excerpt,
            preferred_sections=preferred_sections,
            pass_patterns=list(params.get("pass_patterns", [])),
            fail_patterns=list(params.get("fail_patterns", [])),
            evidence_limit=int(params.get("evidence_limit", 2)),
            match_scope=match_scope,
        )
        return request, {}

    def run(
        self,
        document: ParsedDocument,
        configured_check: PolicyCheck,
        *,
        domain: str,
        context: dict[str, Any] | None = None,
    ):
        params = configured_check.params or {}
        preferred_sections = list(params.get("preferred_sections", []))
        match_scope = str(params.get("search_scope", "preferred"))
        section_label, excerpt = select_excerpt(document, preferred_sections, match_scope=match_scope)
        request, metadata = self._build_request(
            document,
            configured_check,
            domain=domain,
            excerpt=excerpt,
            preferred_sections=preferred_sections,
            match_scope=match_scope,
        )
        client = LLMClient.from_context(context) if context and context.get("llm_runtime_override") else self.default_client
        response = clamp_response(client.analyze_evidence(request))
        notes = response.notes
        if section_label:
            notes = f"{notes} Checked section scope: {section_label}.".strip()
        details: dict[str, Any] = {}
        if metadata:
            details.update(metadata)
        details.update({
            "llm_provider": response.provider,
            "match_scope": match_scope,
        })
        return build_result(
            check_id=f"{domain}.{configured_check.id}",
            status=response.status,
            confidence=response.confidence,
            evidence=response.evidence,
            notes=notes,
            details=details or None,
        )
