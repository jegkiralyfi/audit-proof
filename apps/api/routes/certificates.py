from __future__ import annotations

from fastapi import APIRouter, HTTPException

from packages.core.security import PROTOTYPE_SECURITY_NOTICE, PROTOTYPE_SECURITY_SHORT
from packages.storage.registry import get_bundle_detail, list_bundles

router = APIRouter(prefix='/certificates', tags=['certificates'])


@router.get('/')
def certificates_root(limit: int = 100):
    return {'warning': PROTOTYPE_SECURITY_SHORT, 'security_notice': PROTOTYPE_SECURITY_NOTICE, 'bundles': [b.model_dump(mode='json') for b in list_bundles(limit=limit)]}


@router.get('/{bundle_id}')
def certificate_detail(bundle_id: str):
    detail = get_bundle_detail(bundle_id)
    if detail is None:
        raise HTTPException(status_code=404, detail='Bundle not found')
    return detail.certificate
