from __future__ import annotations

from fastapi import APIRouter, HTTPException

from packages.ingest.doi import DoiLookupError, fetch_crossref_metadata

router = APIRouter(prefix='/metadata', tags=['metadata'])


@router.get('/doi/{doi:path}')
def metadata_from_doi(doi: str):
    try:
        return fetch_crossref_metadata(doi)
    except DoiLookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
