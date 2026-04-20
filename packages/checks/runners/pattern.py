from __future__ import annotations

import re
from typing import Any

from packages.checks.base import CheckRunner
from packages.checks.common.scoring import build_result, normalize_confidence, normalize_status
from packages.core.models import EvidenceSpan, ParsedDocument, PolicyCheck


def _compile_patterns(values: list[str]) -> list[re.Pattern[str]]:
    return [re.compile(value, flags=re.IGNORECASE | re.MULTILINE) for value in values]


def _find_first_span(text: str, patterns: list[str], section_name: str) -> EvidenceSpan | None:
    for pattern in _compile_patterns(patterns):
        match = pattern.search(text)
        if not match:
            continue
        start, end = match.span()
        quote_start = max(0, start - 40)
        quote_end = min(len(text), end + 80)
        quote = text[quote_start:quote_end].strip().replace("\n", " ")
        return EvidenceSpan(section=section_name, quote=quote, offset_start=start, offset_end=end)
    return None


def _find_all_spans(text: str, patterns: list[str], section_name: str, limit: int = 2) -> list[EvidenceSpan]:
    spans: list[EvidenceSpan] = []
    for pattern in _compile_patterns(patterns):
        for match in pattern.finditer(text):
            start, end = match.span()
            quote_start = max(0, start - 40)
            quote_end = min(len(text), end + 80)
            quote = text[quote_start:quote_end].strip().replace("\n", " ")
            spans.append(EvidenceSpan(section=section_name, quote=quote, offset_start=start, offset_end=end))
            if len(spans) >= limit:
                return spans
    return spans


def _section_text(document: ParsedDocument, preferred_sections: tuple[str, ...], scope: str = "preferred") -> tuple[str, str]:
    if scope == "full_text":
        return "full_text", document.raw_text
    normalized = tuple(section.lower() for section in preferred_sections)
    matched = [section for section in document.sections if section.name.lower() in normalized]
    if matched:
        joined_name = "+".join(section.name for section in matched)
        joined_text = "\n\n".join(section.text for section in matched)
        return joined_name, joined_text
    return "full_text", document.raw_text


class PatternCheckRunner(CheckRunner):
    """Generic regex/pattern based runner driven entirely by policy params."""

    def run(
        self,
        document: ParsedDocument,
        configured_check: PolicyCheck,
        *,
        domain: str,
        context: dict[str, Any] | None = None,
    ):
        params = configured_check.params or {}
        preferred_sections = tuple(params.get("preferred_sections", []))
        search_scope = str(params.get("search_scope", "preferred"))
        section_name, text = _section_text(document, preferred_sections, scope=search_scope)

        pass_patterns = list(params.get("pass_patterns", []))
        fail_patterns = list(params.get("fail_patterns", []))

        on_match_status = normalize_status(params.get("on_match_status", "pass"), "pass")
        on_missing_status = normalize_status(params.get("on_missing_status", "fail"), "fail")
        on_fail_pattern_status = normalize_status(params.get("on_fail_pattern_status", "warning"), "warning")

        on_match_confidence = normalize_confidence(params.get("on_match_confidence", 0.85), 0.85)
        on_missing_confidence = normalize_confidence(params.get("on_missing_confidence", 0.65), 0.65)
        on_fail_pattern_confidence = normalize_confidence(params.get("on_fail_pattern_confidence", 0.7), 0.7)

        note_on_match = str(params.get("note_on_match", "Check evidence found."))
        note_on_missing = str(params.get("note_on_missing", "No evidence found for configured check."))
        note_on_fail_pattern = str(params.get("note_on_fail_pattern", "Potentially problematic language detected; human review recommended."))
        evidence_limit = int(params.get("evidence_limit", 2))
        check_id = f"{domain}.{configured_check.id}"

        if fail_patterns:
            fail_spans = _find_all_spans(text, fail_patterns, section_name, limit=evidence_limit)
            if fail_spans:
                return build_result(
                    check_id=check_id,
                    status=on_fail_pattern_status,
                    confidence=on_fail_pattern_confidence,
                    evidence=fail_spans,
                    notes=note_on_fail_pattern,
                )

        if pass_patterns:
            pass_span = _find_first_span(text, pass_patterns, section_name)
            if pass_span:
                return build_result(
                    check_id=check_id,
                    status=on_match_status,
                    confidence=on_match_confidence,
                    evidence=[pass_span],
                    notes=note_on_match,
                )

        return build_result(
            check_id=check_id,
            status=on_missing_status,
            confidence=on_missing_confidence,
            notes=note_on_missing,
        )
