from __future__ import annotations

from fastapi import APIRouter, HTTPException

from packages.core.security import PROTOTYPE_SECURITY_NOTICE, PROTOTYPE_SECURITY_SHORT
from packages.storage import registry as storage_registry
from packages.provenance.transparency_log import verify_bundle_transparency
from packages.provenance.witness_log import verify_bundle_witness
from packages.provenance.verify_bundle import verify_bundle

router = APIRouter(prefix='/verify', tags=['verify'])


@router.get('/')
def verify_root():
    return {
        'warning': PROTOTYPE_SECURITY_SHORT,
        'security_notice': PROTOTYPE_SECURITY_NOTICE,
        'message': 'Use /verify/bundles/{bundle_id} to recompute canonical hash bindings, verify the local attestation, compare the stored trust tier to build provenance, check transparency-log inclusion, and verify witness-log / published-checkpoint inclusion.',
    }


@router.get('/bundles/{bundle_id}')
def verify_bundle_endpoint(bundle_id: str):
    bundle_dir = storage_registry.DEFAULT_BUNDLE_ROOT / bundle_id
    if not bundle_dir.exists() or not bundle_dir.is_dir():
        raise HTTPException(status_code=404, detail='Bundle not found')
    payload = verify_bundle(bundle_dir)
    payload['warning'] = PROTOTYPE_SECURITY_SHORT
    payload['security_notice'] = PROTOTYPE_SECURITY_NOTICE
    return payload


@router.get('/bundles/{bundle_id}/transparency')
def verify_bundle_transparency_endpoint(bundle_id: str):
    bundle_dir = storage_registry.DEFAULT_BUNDLE_ROOT / bundle_id
    if not bundle_dir.exists() or not bundle_dir.is_dir():
        raise HTTPException(status_code=404, detail='Bundle not found')
    payload = verify_bundle_transparency(bundle_dir)
    payload['warning'] = PROTOTYPE_SECURITY_SHORT
    payload['security_notice'] = PROTOTYPE_SECURITY_NOTICE
    payload['bundle_id'] = bundle_id
    return payload


@router.get('/bundles/{bundle_id}/witness')
def verify_bundle_witness_endpoint(bundle_id: str):
    bundle_dir = storage_registry.DEFAULT_BUNDLE_ROOT / bundle_id
    if not bundle_dir.exists() or not bundle_dir.is_dir():
        raise HTTPException(status_code=404, detail='Bundle not found')
    payload = verify_bundle_witness(bundle_dir)
    payload['warning'] = PROTOTYPE_SECURITY_SHORT
    payload['security_notice'] = PROTOTYPE_SECURITY_NOTICE
    payload['bundle_id'] = bundle_id
    return payload
