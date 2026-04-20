from __future__ import annotations

import json
from datetime import datetime, timezone
from urllib.request import Request, urlopen

from packages.checks.common.repo_identity import normalize_repository_identity
from packages.core.models import ExecutionPlanArtifact, RepositoryMetadataArtifact, RepositoryMetadataEntry


def _fetch_json(url: str, timeout_seconds: int) -> dict:
    req = Request(url, headers={'User-Agent': 'audit-proof-poc/0.3.0 (+https://example.invalid)'})
    with urlopen(req, timeout=timeout_seconds) as resp:  # noqa: S310 - controlled GET to provider API
        return json.loads(resp.read().decode('utf-8'))


def _fetch_provider_metadata(entry: RepositoryMetadataEntry, timeout_seconds: int) -> RepositoryMetadataEntry:
    if not entry.api_url:
        entry.fetch_status = 'unsupported_provider'
        entry.notes.append('No provider API URL could be derived from the repository URL.')
        return entry
    try:
        payload = _fetch_json(entry.api_url, timeout_seconds=timeout_seconds)
    except Exception as exc:  # best-effort external enrichment
        entry.fetch_status = 'fetch_failed'
        entry.notes.append(f'Provider metadata fetch failed: {type(exc).__name__}')
        return entry

    provider = (entry.repository_provider or '').lower()
    if provider == 'github':
        entry.fetch_status = 'fetched'
        entry.default_branch = payload.get('default_branch')
        entry.stars = payload.get('stargazers_count')
        entry.archived = payload.get('archived')
        entry.visibility = payload.get('visibility')
        entry.license_name = (payload.get('license') or {}).get('spdx_id') or (payload.get('license') or {}).get('name')
        entry.description = payload.get('description')
        entry.homepage = payload.get('homepage')
        entry.topics = list(payload.get('topics') or [])
        entry.fetched_at = datetime.now(timezone.utc)
        return entry
    if provider == 'gitlab':
        entry.fetch_status = 'fetched'
        entry.default_branch = payload.get('default_branch')
        entry.stars = payload.get('star_count')
        entry.archived = payload.get('archived')
        entry.visibility = payload.get('visibility')
        entry.license_name = (payload.get('license') or {}).get('key') or (payload.get('license') or {}).get('name')
        entry.description = payload.get('description')
        entry.homepage = payload.get('web_url')
        entry.topics = list(payload.get('topics') or payload.get('tag_list') or [])
        entry.fetched_at = datetime.now(timezone.utc)
        return entry

    entry.fetch_status = 'unsupported_provider'
    entry.notes.append('Provider API enrichment is not yet implemented for this provider.')
    return entry


def build_repository_metadata_artifact(
    execution_plan: ExecutionPlanArtifact | None,
    *,
    bundle_id: str | None = None,
    fetch_enabled: bool = False,
    timeout_seconds: int = 5,
) -> RepositoryMetadataArtifact | None:
    if execution_plan is None:
        return None

    seen: set[tuple[str, str]] = set()
    repositories: list[RepositoryMetadataEntry] = []
    for entry in execution_plan.entries:
        if not entry.repository_url:
            continue
        key = (entry.repository_url, entry.check_id)
        if key in seen:
            continue
        seen.add(key)
        normalized = normalize_repository_identity(entry.repository_url, entry.repository_provider)
        record = RepositoryMetadataEntry(
            source_check_id=entry.check_id,
            repository_url=entry.repository_url,
            repository_provider=entry.repository_provider,
            fetch_status='normalized_only',
            **normalized,
        )
        if not normalized:
            record.fetch_status = 'unsupported_provider'
            record.notes.append('Repository URL was detected, but normalization is not implemented for this provider.')
        elif fetch_enabled:
            record = _fetch_provider_metadata(record, timeout_seconds=timeout_seconds)
        else:
            record.fetch_status = 'fetch_disabled'
            record.notes.append('Repository metadata fetching is disabled in runtime configuration.')
        repositories.append(record)

    if not repositories:
        return None

    return RepositoryMetadataArtifact(
        bundle_id=bundle_id or execution_plan.bundle_id,
        doc_hash=execution_plan.doc_hash,
        domain=execution_plan.domain,
        repositories=repositories,
    )
