from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, HTMLResponse

from packages.core.security import PROTOTYPE_SECURITY_NOTICE, PROTOTYPE_SECURITY_SHORT
from packages.storage.registry import get_bundle_detail, get_bundle_file_path

router = APIRouter(prefix='/reports', tags=['reports'])


@router.get('/')
def reports_root():
    return {'warning': PROTOTYPE_SECURITY_SHORT, 'security_notice': PROTOTYPE_SECURITY_NOTICE, 'message': 'Use /reports/{bundle_id} for HTML, /reports/{bundle_id}/manifest for manifest, /reports/{bundle_id}/build-provenance for build provenance, /reports/{bundle_id}/release-manifest for the source release manifest, /reports/{bundle_id}/release-signature for the release signature document, /reports/{bundle_id}/release-verification for the release verification record, /reports/{bundle_id}/repository-metadata for normalized/fetched repository metadata, /reports/{bundle_id}/reference-audit for the literature reference audit, /reports/{bundle_id}/reference-resolution for DOI/Crossref reference resolution, /reports/{bundle_id}/execution-plan for the execution plan artifact, /reports/{bundle_id}/execution-attempts for the execution attempt log, /reports/{bundle_id}/execution-receipts for the execution receipt log, /reports/{bundle_id}/artifact-bindings for hash bindings, or /reports/{bundle_id}/execution-stub-outputs for the local stub output log. Verification is available separately under /verify/bundles/{bundle_id}'}


@router.get('/{bundle_id}', response_class=HTMLResponse)
def report_html(bundle_id: str):
    detail = get_bundle_detail(bundle_id)
    if detail is None or not detail.report_path:
        raise HTTPException(status_code=404, detail='Report not found')
    return FileResponse(detail.report_path, media_type='text/html')


@router.get('/{bundle_id}/manifest')
def report_manifest(bundle_id: str):
    path = get_bundle_file_path(bundle_id, 'manifest.json')
    if path is None:
        raise HTTPException(status_code=404, detail='Manifest not found')
    return FileResponse(str(path), media_type='application/json')




@router.get('/{bundle_id}/build-provenance')
def report_build_provenance(bundle_id: str):
    path = get_bundle_file_path(bundle_id, 'build_provenance.json')
    if path is None:
        raise HTTPException(status_code=404, detail='Build provenance not found')
    return FileResponse(str(path), media_type='application/json')




@router.get('/{bundle_id}/release-manifest')
def report_release_manifest(bundle_id: str):
    path = get_bundle_file_path(bundle_id, 'release_manifest.json')
    if path is None:
        raise HTTPException(status_code=404, detail='Release manifest not found')
    return FileResponse(str(path), media_type='application/json')


@router.get('/{bundle_id}/release-signature')
def report_release_signature(bundle_id: str):
    path = get_bundle_file_path(bundle_id, 'release_manifest.signature.json')
    if path is None:
        raise HTTPException(status_code=404, detail='Release signature not found')
    return FileResponse(str(path), media_type='application/json')


@router.get('/{bundle_id}/release-verification')
def report_release_verification(bundle_id: str):
    path = get_bundle_file_path(bundle_id, 'release_verification.json')
    if path is None:
        raise HTTPException(status_code=404, detail='Release verification not found')
    return FileResponse(str(path), media_type='application/json')

@router.get('/{bundle_id}/repository-metadata')
def report_repository_metadata(bundle_id: str):
    path = get_bundle_file_path(bundle_id, 'repository_metadata.json')
    if path is None:
        raise HTTPException(status_code=404, detail='Repository metadata not found')
    return FileResponse(str(path), media_type='application/json')



@router.get('/{bundle_id}/reference-audit')
def report_reference_audit(bundle_id: str):
    path = get_bundle_file_path(bundle_id, 'reference_audit.json')
    if path is None:
        raise HTTPException(status_code=404, detail='Reference audit not found')
    return FileResponse(str(path), media_type='application/json')


@router.get('/{bundle_id}/reference-resolution')
def report_reference_resolution(bundle_id: str):
    path = get_bundle_file_path(bundle_id, 'reference_resolution.json')
    if path is None:
        raise HTTPException(status_code=404, detail='Reference resolution not found')
    return FileResponse(str(path), media_type='application/json')


@router.get('/{bundle_id}/execution-plan')
def report_execution_plan(bundle_id: str):
    path = get_bundle_file_path(bundle_id, 'execution_plan.json')
    if path is None:
        raise HTTPException(status_code=404, detail='Execution plan not found')
    return FileResponse(str(path), media_type='application/json')


@router.get('/{bundle_id}/execution-attempts')
def report_execution_attempts(bundle_id: str):
    path = get_bundle_file_path(bundle_id, 'execution_attempts.json')
    if path is None:
        raise HTTPException(status_code=404, detail='Execution attempts not found')
    return FileResponse(str(path), media_type='application/json')


@router.get('/{bundle_id}/artifact-bindings')
def report_artifact_bindings(bundle_id: str):
    path = get_bundle_file_path(bundle_id, 'artifact_bindings.json')
    if path is None:
        raise HTTPException(status_code=404, detail='Artifact bindings not found')
    return FileResponse(str(path), media_type='application/json')


@router.get('/{bundle_id}/execution-receipts')
def report_execution_receipts(bundle_id: str):
    path = get_bundle_file_path(bundle_id, 'execution_receipts.json')
    if path is None:
        raise HTTPException(status_code=404, detail='Execution receipts not found')
    return FileResponse(str(path), media_type='application/json')


@router.get('/{bundle_id}/execution-stub-outputs')
def report_execution_stub_outputs(bundle_id: str):
    path = get_bundle_file_path(bundle_id, 'execution_stub_outputs.json')
    if path is None:
        raise HTTPException(status_code=404, detail='Execution stub outputs not found')
    return FileResponse(str(path), media_type='application/json')
