from __future__ import annotations

from typing import Iterable

from packages.checks.common.references import DOI_RE, _find_reference_section, _split_reference_candidates
from packages.core.models import Certificate, ParsedDocument, ReferenceResolutionArtifact, ReferenceResolutionEntry
from packages.ingest.doi import DoiLookupError, fetch_crossref_metadata, normalize_doi


def _unique_doi_candidates(reference_entries: Iterable[str], limit: int = 10) -> list[tuple[str, str]]:
    seen: set[str] = set()
    out: list[tuple[str, str]] = []
    for entry in reference_entries:
        for match in DOI_RE.findall(entry):
            normalized = normalize_doi(match)
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            out.append((match, entry.strip()))
            if len(out) >= limit:
                return out
    return out


def build_reference_resolution_artifact(
    certificate: Certificate,
    document: ParsedDocument,
    *,
    bundle_id: str | None = None,
    fetch_enabled: bool = False,
    timeout_seconds: int = 5,
) -> ReferenceResolutionArtifact | None:
    source_checks = [check for check in certificate.checks_run if check.runner_metadata and check.runner_metadata.runner_type == 'reference_integrity_check']
    if not source_checks:
        return None

    section_name, reference_text = _find_reference_section(document)
    entries = _split_reference_candidates(reference_text) if reference_text else []
    doi_candidates = _unique_doi_candidates(entries)

    artifact_entries: list[ReferenceResolutionEntry] = []
    if not doi_candidates:
        for check in source_checks:
            artifact_entries.append(
                ReferenceResolutionEntry(
                    source_check_id=check.check_id,
                    doi_original='',
                    doi_normalized='',
                    resolution_status='no_doi_detected',
                    reference_snippet=(entries[0][:280] if entries else None),
                    notes=['No DOI-like signals were detected in the references section.'],
                )
            )
        return ReferenceResolutionArtifact(bundle_id=bundle_id, doc_hash=certificate.doc_hash, domain=certificate.domain, entries=artifact_entries)

    # assign discovered DOI candidates to the first source check; duplicateing across checks would be noisy.
    source_check_id = source_checks[0].check_id
    for doi_original, snippet in doi_candidates:
        normalized = normalize_doi(doi_original)
        entry = ReferenceResolutionEntry(
            source_check_id=source_check_id,
            doi_original=doi_original,
            doi_normalized=normalized,
            resolution_status='normalized_only',
            reference_snippet=snippet[:320],
            notes=['DOI normalized from reference trail.'],
        )
        if fetch_enabled:
            try:
                resolved = fetch_crossref_metadata(normalized, timeout=timeout_seconds)
                entry.resolution_status = 'resolved'
                entry.crossref_title = resolved.get('title')
                entry.crossref_journal = resolved.get('journal')
                entry.crossref_published_year = resolved.get('published_year')
                entry.crossref_publisher = resolved.get('publisher')
                entry.notes.append('Crossref resolution succeeded.')
            except DoiLookupError as exc:
                entry.resolution_status = 'resolution_failed'
                entry.notes.append(str(exc))
        else:
            entry.resolution_status = 'fetch_disabled'
            entry.notes.append('Reference DOI resolution fetch is disabled in runtime configuration.')
        artifact_entries.append(entry)

    return ReferenceResolutionArtifact(bundle_id=bundle_id, doc_hash=certificate.doc_hash, domain=certificate.domain, entries=artifact_entries)
