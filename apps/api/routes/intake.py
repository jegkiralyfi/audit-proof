from __future__ import annotations

from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from packages.certificates.builder import build_certificate
from packages.core.models import IntakeRequest, IntakeResponse
from packages.ingest.doi import enrich_metadata_with_doi
from packages.ingest.parser import parse_path_to_document, parse_text_to_document
from packages.routing.domain_registry import get_domain_policy
from packages.routing.domain_router import get_workflow
from packages.storage.registry import persist_bundle

router = APIRouter(prefix='/intake', tags=['intake'])


def _llm_runtime_override(payload: IntakeRequest | None = None, **kwargs) -> dict:
    values = {}
    if payload is not None:
        values.update({
            "llm_provider": payload.llm_provider,
            "llm_model": payload.llm_model,
            "llm_base_url": payload.llm_base_url,
            "llm_api_key_env": payload.llm_api_key_env,
        })
    values.update(kwargs)
    cleaned = {k: v for k, v in values.items() if v not in (None, "")}
    return cleaned


@router.post('/text', response_model=IntakeResponse)
def intake_text(payload: IntakeRequest) -> IntakeResponse:
    text = (payload.text or '').strip()
    if not text:
        raise HTTPException(status_code=400, detail='No text provided')

    base_metadata = {'doi': payload.doi, 'title': payload.title, 'abstract': payload.abstract}
    metadata, enrichment_notes = enrich_metadata_with_doi(base_metadata)
    document = parse_text_to_document(text=text, source_name=payload.source_name, metadata=metadata)
    policy = get_domain_policy(payload.domain)
    workflow = get_workflow(payload.domain)
    checks = workflow.run(document, context={"llm_runtime_override": _llm_runtime_override(payload)})
    notes = ' '.join(enrichment_notes)
    certificate, html_report = build_certificate(document=document, domain=payload.domain, checks_run=checks, policy=policy, notes=notes)
    artifacts = persist_bundle(document=document, certificate=certificate, html_report=html_report)
    final_html_report = Path(artifacts.report_path).read_text(encoding='utf-8')
    return IntakeResponse(
        message='SANDBOX ONLY · NOT RED TEAM CERTIFIED · MANUAL PROMPT-INJECTION GUARDRAILS. Certificate issued from inline text.',
        certificate=certificate.model_dump(mode='json'),
        html_report=final_html_report,
        artifacts=artifacts,
    )


@router.post('/file', response_model=IntakeResponse)
async def intake_file(
    file: UploadFile = File(...),
    domain: str = Form('quant_experimental'),
    doi: str | None = Form(None),
    title: str | None = Form(None),
    abstract: str | None = Form(None),
    llm_provider: str | None = Form(None),
    llm_model: str | None = Form(None),
    llm_base_url: str | None = Form(None),
    llm_api_key_env: str | None = Form(None),
) -> IntakeResponse:
    file_bytes = await file.read()
    suffix = Path(file.filename or 'upload.txt').suffix or '.txt'
    with NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(file_bytes)
        temp_path = Path(tmp.name)

    try:
        base_metadata = {'doi': doi, 'title': title, 'abstract': abstract}
        metadata, enrichment_notes = enrich_metadata_with_doi(base_metadata)
        document = parse_path_to_document(temp_path, metadata=metadata)
        document.source_name = file.filename or temp_path.name
        policy = get_domain_policy(domain)
        workflow = get_workflow(domain)
        checks = workflow.run(document, context={"llm_runtime_override": _llm_runtime_override(None, llm_provider=llm_provider, llm_model=llm_model, llm_base_url=llm_base_url, llm_api_key_env=llm_api_key_env)})
        notes = ' '.join(enrichment_notes)
        certificate, html_report = build_certificate(document=document, domain=domain, checks_run=checks, policy=policy, notes=notes)
        artifacts = persist_bundle(
            document=document,
            certificate=certificate,
            html_report=html_report,
            original_bytes=file_bytes,
            original_name=file.filename or 'upload.bin',
        )
        final_html_report = Path(artifacts.report_path).read_text(encoding='utf-8')
        return IntakeResponse(
            message='SANDBOX ONLY · NOT RED TEAM CERTIFIED · MANUAL PROMPT-INJECTION GUARDRAILS. Certificate issued from uploaded file.',
            certificate=certificate.model_dump(mode='json'),
            html_report=final_html_report,
            artifacts=artifacts,
        )
    finally:
        temp_path.unlink(missing_ok=True)
