from __future__ import annotations

from pathlib import Path
import json

import gradio as gr

from packages.certificates.builder import build_certificate
from packages.core.security import PROTOTYPE_SECURITY_NOTICE, PROTOTYPE_SECURITY_SHORT
from packages.ingest.doi import enrich_metadata_with_doi
from packages.ingest.parser import parse_path_to_document, parse_text_to_document
from packages.routing.domain_registry import get_domain_policy, list_domains
from packages.routing.domain_router import get_workflow
from packages.storage.registry import list_bundles, persist_bundle
from packages.provenance.verify_bundle import verify_bundle
from packages.checks.registry import get_default_registry

LLM_PROVIDER_CHOICES = [
    "heuristic",
    "openai-compatible",
    "anthropic",
    "gemini",
    "custom",
]


def _llm_runtime_override(provider: str, model: str, base_url: str, api_key_env: str) -> dict:
    provider_value = (provider or "heuristic").strip()
    if provider_value == "custom" and model and ":" in model:
        provider_value = model.strip()
    return {
        "llm_provider": provider_value,
        "llm_model": model.strip() or None,
        "llm_base_url": base_url.strip() or None,
        "llm_api_key_env": api_key_env.strip() or None,
    }


def _run_document(document, domain: str, notes: str = '', llm_runtime_override: dict | None = None):
    policy = get_domain_policy(domain)
    workflow = get_workflow(domain)
    checks = workflow.run(document, context={"llm_runtime_override": llm_runtime_override or {}})
    certificate, html_report = build_certificate(
        document=document,
        domain=domain,
        checks_run=checks,
        policy=policy,
        notes=notes,
    )
    return certificate, html_report


def _artifact_summary(artifacts, certificate):
    return (
        f"WARNING: {PROTOTYPE_SECURITY_SHORT}\n"
        f"Notice: {PROTOTYPE_SECURITY_NOTICE}\n\n"
        f"Bundle: {artifacts.bundle_id}\n"
        f"Issuance: {certificate.issuance.status}\n"
        f"Dir: {artifacts.bundle_dir}\n"
        f"Certificate: {artifacts.certificate_path}\n"
        f"RO-Crate: {artifacts.rocrate_path}\n"
        f"Execution plan: {artifacts.execution_plan_path or 'n/a'}\n"
        f"Execution attempts: {artifacts.execution_attempts_path or 'n/a'}\n"
        f"Execution receipts: {artifacts.execution_receipts_path or 'n/a'}\n"
        f"Execution stub outputs: {artifacts.execution_stub_outputs_path or 'n/a'}\n"
        f"Artifact bindings: {artifacts.artifact_bindings_path or 'n/a'}\n"
        f"Repository metadata: {artifacts.repository_metadata_path or 'n/a'}\n"
        f"Reference audit: {artifacts.reference_audit_path or 'n/a'}\n"
        f"Reference resolution: {artifacts.reference_resolution_path or 'n/a'}\n"
        f"Transparency record: {artifacts.transparency_record_path or 'n/a'}\n"
        f"Transparency checkpoint: {artifacts.transparency_checkpoint_path or 'n/a'}\n"
        f"Verification receipts: {artifacts.verification_receipts_path or 'n/a'}\n"
        f"Witness record: {artifacts.witness_record_path or 'n/a'}\n"
        f"Witness checkpoint: {artifacts.witness_checkpoint_path or 'n/a'}\n"
        f"Published checkpoint reference: {artifacts.published_checkpoint_reference_path or 'n/a'}\n"
        f"Formal semantic audit: {getattr(artifacts, 'formal_semantic_audit_path', None) or 'n/a'}"
    )


def issue_certificate_from_text(text: str, domain: str, doi: str, title: str, llm_provider: str, llm_model: str, llm_base_url: str, llm_api_key_env: str):
    metadata, notes = enrich_metadata_with_doi({'doi': doi or None, 'title': title or None})
    document = parse_text_to_document(text=text, source_name='gradio-text', metadata=metadata)
    certificate, html_report = _run_document(
        document,
        domain,
        notes=' '.join(notes),
        llm_runtime_override=_llm_runtime_override(llm_provider, llm_model, llm_base_url, llm_api_key_env),
    )
    artifacts = persist_bundle(document=document, certificate=certificate, html_report=html_report)
    final_html_report = Path(artifacts.report_path).read_text(encoding='utf-8')
    return certificate.model_dump_json(indent=2), final_html_report, _artifact_summary(artifacts, certificate)


def issue_certificate_from_file(file_obj, domain: str, doi: str, title: str, llm_provider: str, llm_model: str, llm_base_url: str, llm_api_key_env: str):
    if not file_obj:
        return '{"error": "No file provided"}', '<p>No file provided.</p>', ''

    file_path = Path(file_obj)
    metadata, notes = enrich_metadata_with_doi({'doi': doi or None, 'title': title or None})
    document = parse_path_to_document(file_path, metadata=metadata)
    document.source_name = file_path.name
    certificate, html_report = _run_document(
        document,
        domain,
        notes=' '.join(notes),
        llm_runtime_override=_llm_runtime_override(llm_provider, llm_model, llm_base_url, llm_api_key_env),
    )
    artifacts = persist_bundle(
        document=document,
        certificate=certificate,
        html_report=html_report,
        original_bytes=file_path.read_bytes(),
        original_name=file_path.name,
    )
    final_html_report = Path(artifacts.report_path).read_text(encoding='utf-8')
    return certificate.model_dump_json(indent=2), final_html_report, _artifact_summary(artifacts, certificate)




def verify_bundle_from_ui(bundle_id: str):
    bundle_value = (bundle_id or '').strip()
    if not bundle_value:
        return '{"error": "No bundle id provided"}', ''
    artifacts_root = Path('.artifacts/bundles') / bundle_value
    if not artifacts_root.exists():
        return '{"error": "Bundle not found"}', ''
    payload = verify_bundle(artifacts_root)
    badge = '✅ VERIFIED' if payload.get('verified') else '⚠️ VERIFY FAILED'
    lines = [
        f"{badge}",
        f"Bundle: {payload.get('bundle_id')}",
        f"Trust tier matches: {payload.get('trust_tier_matches')}",
        f"Stored trust tier: {payload.get('stored_trust_tier')}",
        f"Recomputed trust tier: {payload.get('recomputed_trust_tier')}",
        f"Attestation verified: {payload.get('attestation_verified')}",
        f"Transparency verified: {payload.get('transparency_verified')}",
        f"Witness verified: {payload.get('witness_verified')}",
        f"Published checkpoint matches: {(payload.get('witness') or {}).get('published_checkpoint_matches')}",
        f"Independent verifiers passed: {(payload.get('witness') or {}).get('passed_verifiers')}/{(payload.get('witness') or {}).get('total_verifiers')}",
        f"Artifact bindings match: {payload.get('artifact_bindings_match')}",
        f"Manifest matches: {payload.get('manifest_matches')}",
    ]
    notes = payload.get('verification_notes') or []
    if notes:
        lines.append('Notes:')
        lines.extend(f"- {note}" for note in notes)
    return json.dumps(payload, indent=2), '\n'.join(lines)

def registry_table():
    bundles = list_bundles(limit=20)
    rows = []
    for b in bundles:
        rows.append([
            b.bundle_id,
            b.created_at,
            b.domain or '',
            b.issuance_status or '',
            b.title or '',
            ", ".join(b.runner_families),
            ", ".join(b.capability_classes),
            ', '.join(b.source_kinds),
            b.execution_attempts,
            b.summary.get('passed', 0),
            b.summary.get('failed', 0),
        ])
    return rows


def runners_table():
    registry = get_default_registry()
    rows = []
    for descriptor in registry.list_descriptors():
        rows.append([
            descriptor.get('runner_type', ''),
            descriptor.get('runner_family', ''),
            descriptor.get('execution_mode', ''),
            ", ".join(descriptor.get('capabilities', [])),
            descriptor.get('source_kind', ''),
            descriptor.get('source_module', ''),
            descriptor.get('description', ''),
        ])
    return rows


with gr.Blocks(title='Audit-Proof') as demo:
    gr.Markdown('# Audit-Proof v0.6.0 Alpha 1\nIssue a machine-readable audit certificate, persist a canonical artifact bundle, verify it, witness it in a local transparency log, and audit formal-proof artifacts for semantic load-bearingness rather than treating theorem-prover acceptance as enough by itself.')
    gr.Markdown(f"**Warning:** {PROTOTYPE_SECURITY_SHORT}\n\n{PROTOTYPE_SECURITY_NOTICE}")

    with gr.Accordion('LLM provider profile', open=False):
        gr.Markdown('Choose the evidence provider profile for LLM-backed checks. Provider-agnostic does not mean provider-identical.')
        provider_text = gr.Dropdown(choices=LLM_PROVIDER_CHOICES, value='heuristic', label='LLM provider')
        model_text = gr.Textbox(label='LLM model / custom provider path', value='heuristic-evidence-v1')
        base_url_text = gr.Textbox(label='Base URL (OpenAI-compatible / Anthropic / Gemini direct)', value='')
        api_key_env_text = gr.Textbox(label='API key environment variable', value='OPENAI_API_KEY')

    with gr.Tab('Text intake'):
        with gr.Row():
            with gr.Column():
                title_text = gr.Textbox(label='Title')
                doi_text = gr.Textbox(label='DOI (optional)')
                domain_text = gr.Dropdown(choices=list_domains(), value='quant_experimental', label='Certification type')
                text = gr.Textbox(label='Paper text', lines=20)
                run_button_text = gr.Button('Issue certificate from text')
            with gr.Column():
                cert_json_text = gr.Code(label='Certificate JSON', language='json')
                report_html_text = gr.HTML(label='HTML report')
                artifacts_box_text = gr.Textbox(label='Artifacts', lines=10)
        run_button_text.click(
            issue_certificate_from_text,
            inputs=[text, domain_text, doi_text, title_text, provider_text, model_text, base_url_text, api_key_env_text],
            outputs=[cert_json_text, report_html_text, artifacts_box_text],
        )

    with gr.Tab('File intake'):
        with gr.Row():
            with gr.Column():
                title_file = gr.Textbox(label='Title override')
                doi_file = gr.Textbox(label='DOI (optional)')
                domain_file = gr.Dropdown(choices=list_domains(), value='quant_experimental', label='Certification type')
                file_input = gr.File(label='Upload PDF or text file', type='filepath')
                run_button_file = gr.Button('Issue certificate from file')
            with gr.Column():
                cert_json_file = gr.Code(label='Certificate JSON', language='json')
                report_html_file = gr.HTML(label='HTML report')
                artifacts_box_file = gr.Textbox(label='Artifacts', lines=10)
        run_button_file.click(
            issue_certificate_from_file,
            inputs=[file_input, domain_file, doi_file, title_file, provider_text, model_text, base_url_text, api_key_env_text],
            outputs=[cert_json_file, report_html_file, artifacts_box_file],
        )


    with gr.Tab('Verify bundle'):
        with gr.Row():
            with gr.Column():
                verify_bundle_id = gr.Textbox(label='Bundle ID')
                verify_button = gr.Button('Verify bundle')
            with gr.Column():
                verify_json = gr.Code(label='Verification JSON', language='json')
                verify_summary = gr.Textbox(label='Verification summary', lines=10)
        verify_button.click(
            verify_bundle_from_ui,
            inputs=[verify_bundle_id],
            outputs=[verify_json, verify_summary],
        )

    with gr.Tab('Recent bundles'):
        refresh = gr.Button('Refresh registry')
        table = gr.Dataframe(
            headers=['bundle_id', 'created_at', 'domain', 'issuance', 'title', 'runner_families', 'capability_classes', 'source_kinds', 'execution_attempts', 'passed', 'failed'],
            datatype=['str', 'str', 'str', 'str', 'str', 'str', 'str', 'str', 'number', 'number', 'number'],
            value=registry_table,
            interactive=False,
        )
        refresh.click(registry_table, outputs=[table])

    with gr.Tab('Runner registry'):
        refresh_runners = gr.Button('Refresh runners')
        runners = gr.Dataframe(
            headers=['runner_type', 'runner_family', 'execution_mode', 'capabilities', 'source_kind', 'source_module', 'description'],
            datatype=['str', 'str', 'str', 'str', 'str', 'str', 'str'],
            value=runners_table,
            interactive=False,
        )
        refresh_runners.click(runners_table, outputs=[runners])


if __name__ == '__main__':
    demo.launch()
