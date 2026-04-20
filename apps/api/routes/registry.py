from __future__ import annotations

from fastapi import APIRouter, HTTPException

from packages.core.security import PROTOTYPE_SECURITY_NOTICE, PROTOTYPE_SECURITY_SHORT
from packages.checks.registry import get_default_registry
from packages.storage.registry import get_bundle_detail, list_bundles

router = APIRouter(prefix='/registry', tags=['registry'])


@router.get('/bundles')
def registry_bundles(limit: int = 100):
    return {'security_notice': PROTOTYPE_SECURITY_NOTICE, 'warning': PROTOTYPE_SECURITY_SHORT, 'bundles': [b.model_dump(mode='json') for b in list_bundles(limit=limit)]}


@router.get('/bundles/{bundle_id}')
def registry_bundle(bundle_id: str):
    detail = get_bundle_detail(bundle_id)
    if detail is None:
        raise HTTPException(status_code=404, detail='Bundle not found')
    return detail.model_dump(mode='json')


@router.get('/runners')
def registry_runners():
    registry = get_default_registry()
    return {'security_notice': PROTOTYPE_SECURITY_NOTICE, 'warning': PROTOTYPE_SECURITY_SHORT, 'runners': registry.list_descriptors()}


@router.get('/runners/{runner_type}')
def registry_runner(runner_type: str):
    registry = get_default_registry()
    descriptor = registry.describe(runner_type)
    if descriptor is None:
        raise HTTPException(status_code=404, detail='Runner not found')
    return {'security_notice': PROTOTYPE_SECURITY_NOTICE, 'warning': PROTOTYPE_SECURITY_SHORT, 'runner': descriptor.to_public_dict()}
