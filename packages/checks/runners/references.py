from __future__ import annotations

import re
from typing import Any

from packages.checks.base import CheckRunner
from packages.checks.common.scoring import build_result, normalize_confidence, normalize_status
from packages.checks.common.references import _find_reference_section, _split_reference_candidates, _count_body_citations, DOI_RE, URL_RE, YEAR_RE, _style_guess
from packages.core.models import EvidenceSpan, ParsedDocument, PolicyCheck


class ReferenceIntegrityCheckRunner(CheckRunner):
    """First-tier literature-reference audit runner.

    This runner does not verify every citation against external databases yet.
    It checks whether the document advertises a plausible literature trail:
    a references section, reference-like entries, in-text citation signals, and
    basic DOI/URL richness.
    """

    def run(self, document: ParsedDocument, configured_check: PolicyCheck, *, domain: str, context: dict[str, Any] | None = None):
        params = configured_check.params or {}
        section_name, reference_text = _find_reference_section(document)
        entries = _split_reference_candidates(reference_text) if reference_text else []
        in_text_count = _count_body_citations(document, section_name)
        doi_count = sum(len(DOI_RE.findall(entry)) for entry in entries)
        url_count = sum(len(URL_RE.findall(entry)) for entry in entries)
        year_count = sum(len(YEAR_RE.findall(entry)) for entry in entries)
        style = _style_guess(entries)

        evidence: list[EvidenceSpan] = []
        if section_name and reference_text:
            sample = entries[0] if entries else reference_text[:240]
            evidence.append(EvidenceSpan(section=section_name, quote=sample[:280], offset_start=0, offset_end=min(len(reference_text), 280)))

        details = {
            'reference_count': len(entries),
            'in_text_citation_count': in_text_count,
            'doi_count': doi_count,
            'url_count': url_count,
            'year_count': year_count,
            'references_section_name': section_name,
            'style_guess': style,
            'representative_references': entries[:5],
        }

        min_refs_pass = int(params.get('min_references_for_pass', 3))
        min_body_citations = int(params.get('min_in_text_citations_for_pass', 1))

        on_pass_status = normalize_status(params.get('on_pass_status', 'pass'), 'pass')
        on_warning_status = normalize_status(params.get('on_warning_status', 'warning'), 'warning')
        on_fail_status = normalize_status(params.get('on_fail_status', 'fail'), 'fail')

        pass_conf = normalize_confidence(params.get('on_pass_confidence', 0.84), 0.84)
        warn_conf = normalize_confidence(params.get('on_warning_confidence', 0.68), 0.68)
        fail_conf = normalize_confidence(params.get('on_fail_confidence', 0.8), 0.8)

        note_on_pass = str(params.get('note_on_pass', 'A plausible literature trail was detected.'))
        note_on_warning = str(params.get('note_on_warning', 'Some literature-reference structure was detected, but the trail looks incomplete.'))
        note_on_fail = str(params.get('note_on_fail', 'No strong literature-reference structure was detected.'))

        if len(entries) >= min_refs_pass and in_text_count >= min_body_citations:
            notes = f"{note_on_pass} References: {len(entries)}; in-text citations: {in_text_count}; DOI/URL signals: {doi_count + url_count}."
            return build_result(check_id=f'{domain}.{configured_check.id}', status=on_pass_status, confidence=pass_conf, evidence=evidence, notes=notes, details=details)

        if entries:
            notes = f"{note_on_warning} References: {len(entries)}; in-text citations: {in_text_count}."
            return build_result(check_id=f'{domain}.{configured_check.id}', status=on_warning_status, confidence=warn_conf, evidence=evidence, notes=notes, details=details)

        return build_result(check_id=f'{domain}.{configured_check.id}', status=on_fail_status, confidence=fail_conf, evidence=evidence, notes=note_on_fail, details=details)
