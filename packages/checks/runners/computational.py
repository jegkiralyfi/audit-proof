from __future__ import annotations

import re
from typing import Any

from packages.checks.base import CheckRunner
from packages.checks.common.scoring import build_result, normalize_confidence, normalize_status
from packages.core.models import EvidenceSpan, ParsedDocument, PolicyCheck


def _compile_patterns(values: list[str]) -> list[re.Pattern[str]]:
    return [re.compile(value, flags=re.IGNORECASE | re.MULTILINE) for value in values]


def _section_text(document: ParsedDocument, preferred_sections: tuple[str, ...], scope: str = "preferred") -> tuple[str, str]:
    if scope == "full_text":
        return "full_text", document.raw_text
    normalized = tuple(section.lower() for section in preferred_sections)
    for section in document.sections:
        if section.name.lower() in normalized:
            return section.name, section.text
    return "full_text", document.raw_text


def _first_match(text: str, patterns: list[str], section_name: str) -> EvidenceSpan | None:
    for pattern in _compile_patterns(patterns):
        match = pattern.search(text)
        if not match:
            continue
        start, end = match.span()
        quote_start = max(0, start - 50)
        quote_end = min(len(text), end + 100)
        quote = text[quote_start:quote_end].strip().replace("\n", " ")
        return EvidenceSpan(section=section_name, quote=quote, offset_start=start, offset_end=end)
    return None


class ComputationalSignalCheckRunner(CheckRunner):
    """Detects first-tier reproducibility signals in a computational paper."""

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

        signal_groups: dict[str, list[str]] = {
            str(group_name): list(patterns)
            for group_name, patterns in dict(params.get("signal_groups", {})).items()
        }
        required_groups = set(str(name) for name in params.get("required_groups", []))
        min_optional_for_pass = int(params.get("min_optional_groups_for_pass", 0))
        min_optional_for_warning = int(params.get("min_optional_groups_for_warning", 0))
        evidence_limit = int(params.get("evidence_limit", 3))

        on_pass_status = normalize_status(params.get("on_pass_status", "pass"), "pass")
        on_warning_status = normalize_status(params.get("on_warning_status", "warning"), "warning")
        on_fail_status = normalize_status(params.get("on_fail_status", "fail"), "fail")

        pass_conf = normalize_confidence(params.get("on_pass_confidence", 0.86), 0.86)
        warn_conf = normalize_confidence(params.get("on_warning_confidence", 0.72), 0.72)
        fail_conf = normalize_confidence(params.get("on_fail_confidence", 0.83), 0.83)

        note_on_pass = str(params.get("note_on_pass", "Computational reproducibility signals look sufficient for a first-tier certificate."))
        note_on_warning = str(params.get("note_on_warning", "Some computational reproducibility signals are present, but the execution trail is incomplete."))
        note_on_fail = str(params.get("note_on_fail", "No credible execution or reproducibility trail was detected for this computational claim."))

        matched: dict[str, EvidenceSpan] = {}
        missing_required: list[str] = []
        optional_hits = 0

        for group_name, patterns in signal_groups.items():
            span = _first_match(text, patterns, section_name)
            if span is not None:
                matched[group_name] = span
                if group_name not in required_groups:
                    optional_hits += 1
            elif group_name in required_groups:
                missing_required.append(group_name)

        evidence = list(matched.values())[:evidence_limit]
        matched_names = sorted(matched.keys())
        check_id = f"{domain}.{configured_check.id}"

        if missing_required:
            notes = f"{note_on_fail} Missing required signal groups: {', '.join(sorted(missing_required))}. Matched groups: {', '.join(matched_names) or 'none'}."
            return build_result(check_id=check_id, status=on_fail_status, confidence=fail_conf, evidence=evidence, notes=notes)

        if optional_hits >= min_optional_for_pass:
            notes = f"{note_on_pass} Matched signal groups: {', '.join(matched_names) or 'none'}."
            return build_result(check_id=check_id, status=on_pass_status, confidence=pass_conf, evidence=evidence, notes=notes)

        if optional_hits >= min_optional_for_warning or matched:
            notes = (
                f"{note_on_warning} Matched signal groups: {', '.join(matched_names) or 'none'}. "
                f"Need at least {min_optional_for_pass} optional group(s) for a clean pass."
            )
            return build_result(check_id=check_id, status=on_warning_status, confidence=warn_conf, evidence=evidence, notes=notes)

        notes = f"{note_on_fail} No signal groups matched in the selected scope."
        return build_result(check_id=check_id, status=on_fail_status, confidence=fail_conf, evidence=evidence, notes=notes)
