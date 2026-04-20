from __future__ import annotations

import re
from typing import Iterable

from packages.core.models import Certificate, ParsedDocument, ReferenceAuditArtifact, ReferenceAuditEntry

REFERENCE_SECTION_NAMES = (
    'references',
    'bibliography',
    'works cited',
    'literature cited',
)

DOI_RE = re.compile(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", flags=re.IGNORECASE)
URL_RE = re.compile(r"https?://[^\s)\]>\"\']+", flags=re.IGNORECASE)
YEAR_RE = re.compile(r"\b(?:19|20)\d{2}[a-z]?\b")
BODY_CITATION_RE = re.compile(
    r"(?:\[[0-9,;\-\s]{1,20}\])|(?:\([A-Z][A-Za-z'\-]+(?: et al\.)?,\s*(?:19|20)\d{2}[a-z]?\))",
    flags=re.MULTILINE,
)


def _find_reference_section(document: ParsedDocument) -> tuple[str | None, str]:
    for section in document.sections:
        lowered = section.name.strip().lower()
        if lowered in REFERENCE_SECTION_NAMES:
            return section.name, section.text
    for section in document.sections:
        lowered = section.name.strip().lower()
        if 'reference' in lowered or 'bibliograph' in lowered or 'works cited' in lowered:
            return section.name, section.text
    return None, ''


def _split_reference_candidates(text: str) -> list[str]:
    lines = [line.strip() for line in text.splitlines()]
    entries: list[str] = []
    current: list[str] = []
    for line in lines:
        if not line:
            if current:
                entries.append(' '.join(current).strip())
                current = []
            continue
        starts_new = bool(re.match(r"^(?:\[?\d+\]?\.?|•|-)\s+", line))
        if starts_new and current:
            entries.append(' '.join(current).strip())
            current = [line]
            continue
        current.append(line)
    if current:
        entries.append(' '.join(current).strip())
    heuristic = [entry for entry in entries if DOI_RE.search(entry) or YEAR_RE.search(entry) or URL_RE.search(entry)]
    if heuristic:
        return heuristic
    fallback = [line for line in lines if DOI_RE.search(line) or YEAR_RE.search(line)]
    return fallback


def _count_body_citations(document: ParsedDocument, reference_section_name: str | None) -> int:
    chunks: list[str] = []
    for section in document.sections:
        if reference_section_name and section.name == reference_section_name:
            continue
        chunks.append(section.text)
    body = '\n\n'.join(chunks) if chunks else document.raw_text
    return len(BODY_CITATION_RE.findall(body))


def _style_guess(entries: Iterable[str]) -> str | None:
    joined = ' '.join(list(entries)[:5])
    if '[' in joined and ']' in joined:
        return 'numeric'
    if re.search(r"\([A-Z][A-Za-z'\-]+(?: et al\.)?,\s*(?:19|20)\d{2}", joined):
        return 'author-year'
    return None


def build_reference_audit_artifact(certificate: Certificate, document: ParsedDocument, *, bundle_id: str | None = None) -> ReferenceAuditArtifact | None:
    source_checks = [check for check in certificate.checks_run if check.runner_metadata and check.runner_metadata.runner_type == 'reference_integrity_check']
    if not source_checks:
        return None

    section_name, reference_text = _find_reference_section(document)
    entries = _split_reference_candidates(reference_text) if reference_text else []
    in_text_count = _count_body_citations(document, section_name)
    doi_count = sum(len(DOI_RE.findall(entry)) for entry in entries)
    url_count = sum(len(URL_RE.findall(entry)) for entry in entries)
    year_count = sum(len(YEAR_RE.findall(entry)) for entry in entries)
    style = _style_guess(entries)

    if entries and in_text_count and (doi_count or url_count):
        status = 'metadata_rich'
    elif entries and in_text_count:
        status = 'references_and_citations_detected'
    elif entries:
        status = 'references_detected'
    else:
        status = 'no_references_detected'

    notes: list[str] = []
    if not section_name:
        notes.append('No explicit references/bibliography section was detected.')
    if entries and not in_text_count:
        notes.append('Reference-like entries were found, but in-text citation signals were weak or absent.')
    if doi_count == 0 and url_count == 0 and entries:
        notes.append('References were detected, but DOI/URL richness was low.')

    artifact_entries = [
        ReferenceAuditEntry(
            source_check_id=check.check_id,
            status=status,
            references_section_name=section_name,
            reference_count=len(entries),
            in_text_citation_count=in_text_count,
            doi_count=doi_count,
            url_count=url_count,
            year_count=year_count,
            style_guess=style,
            representative_references=entries[:5],
            notes=notes,
        )
        for check in source_checks
    ]

    return ReferenceAuditArtifact(
        bundle_id=bundle_id,
        doc_hash=certificate.doc_hash,
        domain=certificate.domain,
        entries=artifact_entries,
    )
