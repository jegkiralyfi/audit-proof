from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


CROSSREF_WORKS_API = 'https://api.crossref.org/works/'
USER_AGENT = 'audit-proof/0.1 (+https://example.invalid; mailto:audit-proof@example.invalid)'


class DoiLookupError(RuntimeError):
    pass


def normalize_doi(doi: str) -> str:
    value = (doi or '').strip()
    value = value.removeprefix('https://doi.org/')
    value = value.removeprefix('http://doi.org/')
    value = value.removeprefix('doi:')
    return value.strip()


def _first_text(value: Any) -> str | None:
    if isinstance(value, list) and value:
        first = value[0]
        if isinstance(first, str):
            return first.strip()
    if isinstance(value, str):
        return value.strip()
    return None


def _extract_year(message: dict[str, Any]) -> int | None:
    for key in ('published-print', 'published-online', 'created', 'issued'):
        parts = (((message.get(key) or {}).get('date-parts') or [[None]])[0])
        if parts and parts[0]:
            try:
                return int(parts[0])
            except Exception:
                return None
    return None


def fetch_crossref_metadata(doi: str, timeout: float = 10.0) -> dict[str, Any]:
    normalized = normalize_doi(doi)
    if not normalized:
        raise DoiLookupError('DOI is empty after normalization.')

    url = CROSSREF_WORKS_API + quote(normalized, safe='')
    req = Request(url, headers={'User-Agent': USER_AGENT, 'Accept': 'application/json'})
    try:
        with urlopen(req, timeout=timeout) as response:
            payload = json.loads(response.read().decode('utf-8'))
    except HTTPError as exc:
        raise DoiLookupError(f'Crossref returned HTTP {exc.code} for DOI {normalized}.') from exc
    except URLError as exc:
        raise DoiLookupError(f'Crossref lookup failed for DOI {normalized}: {exc.reason}') from exc
    except Exception as exc:
        raise DoiLookupError(f'Crossref lookup failed for DOI {normalized}.') from exc

    message = payload.get('message') or {}
    authors = []
    for author in message.get('author') or []:
        given = (author.get('given') or '').strip()
        family = (author.get('family') or '').strip()
        full = ' '.join(part for part in [given, family] if part).strip()
        if full:
            authors.append(full)

    return {
        'doi': message.get('DOI') or normalized,
        'title': _first_text(message.get('title')),
        'abstract': message.get('abstract'),
        'journal': _first_text(message.get('container-title')),
        'published_year': _extract_year(message),
        'authors': authors,
        'publisher': message.get('publisher'),
        'source': 'crossref',
        'raw': message,
    }


def enrich_metadata_with_doi(base_metadata: dict[str, Any] | None) -> tuple[dict[str, Any], list[str]]:
    metadata = dict(base_metadata or {})
    notes: list[str] = []
    doi = metadata.get('doi')
    if not doi:
        metadata.setdefault('metadata_source', 'user-input')
        return metadata, notes

    try:
        resolved = fetch_crossref_metadata(str(doi))
    except DoiLookupError as exc:
        metadata['metadata_source'] = 'user-input-doi-unresolved'
        notes.append(str(exc))
        return metadata, notes

    metadata['doi'] = resolved.get('doi') or metadata.get('doi')
    metadata['metadata_source'] = 'crossref+user-input'
    metadata['crossref'] = {
        'journal': resolved.get('journal'),
        'published_year': resolved.get('published_year'),
        'authors': resolved.get('authors'),
        'publisher': resolved.get('publisher'),
    }

    if not metadata.get('title') and resolved.get('title'):
        metadata['title'] = resolved['title']
    if not metadata.get('abstract') and resolved.get('abstract'):
        metadata['abstract'] = resolved['abstract']

    notes.append('Crossref metadata enrichment applied.')
    return metadata, notes
