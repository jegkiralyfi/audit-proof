from __future__ import annotations

import json
from pathlib import Path

from packages.checks.common.attempts import build_execution_attempts_artifact, build_execution_plan_artifact
from packages.checks.common.execution_stub import materialize_controlled_execution_stub
from packages.checks.common.formal_semantic_artifact import extract_formal_semantic_audit
from packages.checks.common.reference_resolution import build_reference_resolution_artifact
from packages.checks.common.references import build_reference_audit_artifact
from packages.checks.common.repository_metadata import build_repository_metadata_artifact
from packages.certificates.hashes import compute_certificate_hash
from packages.certificates.report_html import render_html_report
from packages.core.config import load_runtime_config
from packages.core.models import ArtifactBundleRef, ArtifactReference, BundleDetail, BundleSummary, Certificate, ParsedDocument
from packages.provenance.manifest import build_artifact_bindings, build_manifest
from packages.provenance.rocrate_builder import build_rocrate_metadata, write_rocrate
from packages.provenance.sigstore_signer import build_attestation
from packages.provenance.transparency_log import append_transparency_log, TRANSPARENCY_CHECKPOINT_SNAPSHOT_FILE, TRANSPARENCY_RECORD_FILE
from packages.provenance.witness_log import (
    PUBLISHED_CHECKPOINT_REFERENCE_FILE,
    VERIFICATION_RECEIPTS_FILE,
    WITNESS_CHECKPOINT_SNAPSHOT_FILE,
    WITNESS_RECORD_FILE,
    append_witness_log,
    build_verification_receipts,
)
from packages.provenance.trust import build_build_provenance, build_issuer_trust_profile, build_release_verification, load_release_manifest, load_release_signature, project_root_from_any
from packages.provenance.release_signing import signing_public_key_path
from packages.storage.local_store import DEFAULT_BUNDLE_ROOT, ensure_bundle_dir


def _build_artifact_references(
    *,
    original_name: str | None,
    has_build_provenance: bool,
    has_execution_plan: bool,
    has_execution_attempts: bool,
    has_execution_receipts: bool,
    has_execution_stub_outputs: bool,
    has_release_manifest: bool,
    has_release_signature: bool,
    has_release_verification: bool,
    has_release_public_key: bool,
    has_repository_metadata: bool,
    has_reference_audit: bool,
    has_reference_resolution: bool,
    has_transparency_record: bool,
    has_transparency_checkpoint: bool,
    has_verification_receipts: bool,
    has_witness_record: bool,
    has_witness_checkpoint: bool,
    has_published_checkpoint_reference: bool,
    has_formal_semantic_audit: bool,
) -> list[ArtifactReference]:
    refs = [
        ArtifactReference(artifact_name='certificate', path='certificate.json', role='certificate', media_type='application/json'),
        ArtifactReference(artifact_name='report', path='report.html', role='human-readable-report', media_type='text/html'),
        ArtifactReference(artifact_name='document', path='document.txt', role='normalized-document', media_type='text/plain'),
        ArtifactReference(artifact_name='rocrate', path='ro-crate-metadata.json', role='provenance-package', media_type='application/json'),
        ArtifactReference(artifact_name='manifest', path='manifest.json', role='bundle-manifest', media_type='application/json'),
        ArtifactReference(artifact_name='attestation', path='attestation.json', role='bundle-attestation', media_type='application/json'),
        ArtifactReference(artifact_name='artifact_bindings', path='artifact_bindings.json', role='artifact-hash-bindings', media_type='application/json'),
    ]
    if has_build_provenance:
        refs.append(ArtifactReference(artifact_name='build_provenance', path='build_provenance.json', role='build-provenance', media_type='application/json'))
    if has_execution_plan:
        refs.append(ArtifactReference(artifact_name='execution_plan', path='execution_plan.json', role='execution-plan', media_type='application/json'))
    if has_execution_attempts:
        refs.append(ArtifactReference(artifact_name='execution_attempts', path='execution_attempts.json', role='execution-attempt-log', media_type='application/json'))
    if has_execution_receipts:
        refs.append(ArtifactReference(artifact_name='execution_receipts', path='execution_receipts.json', role='execution-receipt-log', media_type='application/json'))
    if has_execution_stub_outputs:
        refs.append(ArtifactReference(artifact_name='execution_stub_outputs', path='execution_stub_outputs.json', role='execution-stub-output-log', media_type='application/json'))
    if has_release_manifest:
        refs.append(ArtifactReference(artifact_name='release_manifest', path='release_manifest.json', role='source-release-manifest', media_type='application/json'))
    if has_release_signature:
        refs.append(ArtifactReference(artifact_name='release_manifest_signature', path='release_manifest.signature.json', role='release-manifest-signature', media_type='application/json'))
    if has_release_verification:
        refs.append(ArtifactReference(artifact_name='release_verification', path='release_verification.json', role='release-verification-record', media_type='application/json'))
    if has_release_public_key:
        refs.append(ArtifactReference(artifact_name='release_public_key', path='keys/release_signing_public_key.pem', role='release-signing-public-key', media_type='application/x-pem-file'))
    if has_repository_metadata:
        refs.append(ArtifactReference(artifact_name='repository_metadata', path='repository_metadata.json', role='repository-metadata-log', media_type='application/json'))
    if has_reference_audit:
        refs.append(ArtifactReference(artifact_name='reference_audit', path='reference_audit.json', role='literature-reference-audit', media_type='application/json'))
    if has_reference_resolution:
        refs.append(ArtifactReference(artifact_name='reference_resolution', path='reference_resolution.json', role='reference-doi-resolution', media_type='application/json'))
    if has_transparency_record:
        refs.append(ArtifactReference(artifact_name='transparency_record', path='transparency_record.json', role='transparency-log-entry-snapshot', media_type='application/json'))
    if has_transparency_checkpoint:
        refs.append(ArtifactReference(artifact_name='transparency_checkpoint', path='transparency_checkpoint_snapshot.json', role='transparency-log-checkpoint-snapshot', media_type='application/json'))
    if has_verification_receipts:
        refs.append(ArtifactReference(artifact_name='verification_receipts', path='verification_receipts.json', role='multi-verifier-receipts', media_type='application/json'))
    if has_witness_record:
        refs.append(ArtifactReference(artifact_name='witness_record', path='witness_record.json', role='witness-log-entry-snapshot', media_type='application/json'))
    if has_witness_checkpoint:
        refs.append(ArtifactReference(artifact_name='witness_checkpoint', path='witness_checkpoint_snapshot.json', role='witness-log-checkpoint-snapshot', media_type='application/json'))
    if has_published_checkpoint_reference:
        refs.append(ArtifactReference(artifact_name='published_checkpoint_reference', path='published_checkpoint_reference.json', role='published-checkpoint-reference', media_type='application/json'))
    if has_formal_semantic_audit:
        refs.append(ArtifactReference(artifact_name='formal_semantic_audit', path='formal_semantic_audit.json', role='formal-proof-semantic-audit', media_type='application/json'))
    if original_name:
        refs.append(ArtifactReference(artifact_name='original_upload', path=original_name, role='original-upload', media_type='application/octet-stream', optional=True))
    return refs


def persist_bundle(document: ParsedDocument, certificate: Certificate, html_report: str, original_bytes: bytes | None = None, original_name: str | None = None) -> ArtifactBundleRef:
    cfg = load_runtime_config()
    bundle_id, bundle_dir = ensure_bundle_dir(document.doc_hash)
    project_root = project_root_from_any(__file__)

    document_path = bundle_dir / 'document.txt'
    if document.raw_text:
        document_path.write_text(document.raw_text, encoding='utf-8')

    if original_bytes is not None:
        raw_name = original_name or 'upload.bin'
        original_path = bundle_dir / raw_name
        original_path.write_bytes(original_bytes)

    build_provenance = build_build_provenance(project_root)
    certificate.issuer_trust_profile = build_issuer_trust_profile(build_provenance)
    release_manifest = load_release_manifest(project_root)
    release_signature = load_release_signature(project_root)
    release_verification = build_release_verification(project_root)
    release_public_key_file = signing_public_key_path(project_root)

    execution_plan = build_execution_plan_artifact(certificate=certificate, bundle_id=bundle_id)
    reference_audit = build_reference_audit_artifact(certificate=certificate, document=document, bundle_id=bundle_id)
    reference_resolution = build_reference_resolution_artifact(
        certificate=certificate,
        document=document,
        bundle_id=bundle_id,
        fetch_enabled=cfg.reference_resolution_fetch_enabled,
        timeout_seconds=cfg.reference_resolution_timeout_seconds,
    )
    repository_metadata = build_repository_metadata_artifact(
        execution_plan,
        bundle_id=bundle_id,
        fetch_enabled=cfg.repository_metadata_fetch_enabled,
        timeout_seconds=cfg.repository_metadata_timeout_seconds,
    )
    execution_attempts = build_execution_attempts_artifact(execution_plan, bundle_id=bundle_id)
    execution_attempts, execution_receipts, execution_stub_outputs = materialize_controlled_execution_stub(
        execution_attempts,
        bundle_dir=bundle_dir,
        enabled=cfg.execution_stub_enabled,
        timeout_seconds=cfg.execution_stub_timeout_seconds,
    )

    certificate.artifact_references = _build_artifact_references(
        original_name=original_name if original_bytes is not None else None,
        has_build_provenance=True,
        has_execution_plan=execution_plan is not None,
        has_execution_attempts=execution_attempts is not None,
        has_execution_receipts=execution_receipts is not None,
        has_execution_stub_outputs=execution_stub_outputs is not None,
        has_release_manifest=release_manifest is not None,
        has_release_signature=release_signature is not None,
        has_release_verification=bool(release_verification),
        has_release_public_key=release_public_key_file.exists(),
        has_repository_metadata=repository_metadata is not None,
        has_reference_audit=reference_audit is not None,
        has_reference_resolution=reference_resolution is not None,
        has_transparency_record=True,
        has_transparency_checkpoint=True,
        has_verification_receipts=True,
        has_witness_record=True,
        has_witness_checkpoint=True,
        has_published_checkpoint_reference=True,
        has_formal_semantic_audit=certificate.domain == 'formal_proof',
    )
    certificate.cert_hash = compute_certificate_hash(certificate)

    certificate_path = bundle_dir / 'certificate.json'
    certificate_path.write_text(certificate.model_dump_json(indent=2), encoding='utf-8')

    build_provenance_path = bundle_dir / 'build_provenance.json'
    build_provenance_path.write_text(build_provenance.model_dump_json(indent=2), encoding='utf-8')

    release_manifest_path = None
    if release_manifest is not None:
        release_manifest_path = bundle_dir / 'release_manifest.json'
        release_manifest_path.write_text(json.dumps(release_manifest, indent=2), encoding='utf-8')

    release_signature_path = None
    if release_signature is not None:
        release_signature_path = bundle_dir / 'release_manifest.signature.json'
        release_signature_path.write_text(json.dumps(release_signature, indent=2), encoding='utf-8')

    release_verification_path = bundle_dir / 'release_verification.json'
    release_verification_path.write_text(json.dumps(release_verification, indent=2), encoding='utf-8')

    release_public_key_path = None
    if release_public_key_file.exists():
        release_public_key_path = bundle_dir / 'keys' / 'release_signing_public_key.pem'
        release_public_key_path.parent.mkdir(parents=True, exist_ok=True)
        release_public_key_path.write_bytes(release_public_key_file.read_bytes())

    execution_plan_path = None
    if execution_plan is not None:
        execution_plan_path = bundle_dir / 'execution_plan.json'
        execution_plan_path.write_text(execution_plan.model_dump_json(indent=2), encoding='utf-8')

    execution_attempts_path = None
    if execution_attempts is not None:
        execution_attempts_path = bundle_dir / 'execution_attempts.json'
        execution_attempts_path.write_text(execution_attempts.model_dump_json(indent=2), encoding='utf-8')

    execution_receipts_path = None
    if execution_receipts is not None:
        execution_receipts_path = bundle_dir / 'execution_receipts.json'
        execution_receipts_path.write_text(execution_receipts.model_dump_json(indent=2), encoding='utf-8')

    execution_stub_outputs_path = None
    if execution_stub_outputs is not None:
        execution_stub_outputs_path = bundle_dir / 'execution_stub_outputs.json'
        execution_stub_outputs_path.write_text(execution_stub_outputs.model_dump_json(indent=2), encoding='utf-8')

    repository_metadata_path = None
    if repository_metadata is not None:
        repository_metadata_path = bundle_dir / 'repository_metadata.json'
        repository_metadata_path.write_text(repository_metadata.model_dump_json(indent=2), encoding='utf-8')

    reference_audit_path = None
    if reference_audit is not None:
        reference_audit_path = bundle_dir / 'reference_audit.json'
        reference_audit_path.write_text(reference_audit.model_dump_json(indent=2), encoding='utf-8')

    reference_resolution_path = None
    if reference_resolution is not None:
        reference_resolution_path = bundle_dir / 'reference_resolution.json'
        reference_resolution_path.write_text(reference_resolution.model_dump_json(indent=2), encoding='utf-8')

    formal_semantic_audit_path = None
    formal_semantic_audit = extract_formal_semantic_audit(certificate)
    if formal_semantic_audit is not None:
        formal_semantic_audit_path = bundle_dir / 'formal_semantic_audit.json'
        formal_semantic_audit_path.write_text(json.dumps(formal_semantic_audit, indent=2), encoding='utf-8')

    report_path = bundle_dir / 'report.html'
    initial_report = render_html_report(
        certificate,
        artifact_bindings=None,
        build_provenance=build_provenance.model_dump(mode='json'),
        execution_plan=execution_plan,
        execution_attempts=execution_attempts,
        execution_receipts=execution_receipts,
        execution_stub_outputs=execution_stub_outputs,
        repository_metadata=repository_metadata,
        reference_audit=reference_audit,
        reference_resolution=reference_resolution,
    )
    report_path.write_text(initial_report, encoding='utf-8')

    artifact_bindings_path = bundle_dir / 'artifact_bindings.json'
    rocrate = build_rocrate_metadata(
        document=document,
        certificate=certificate,
        bundle_id=bundle_id,
        has_build_provenance=True,
        has_execution_plan=execution_plan_path is not None,
        has_execution_attempts=execution_attempts_path is not None,
        has_execution_receipts=execution_receipts_path is not None,
        has_execution_stub_outputs=execution_stub_outputs_path is not None,
        has_release_manifest=release_manifest_path is not None,
        has_release_signature=release_signature_path is not None,
        has_release_verification=release_verification_path is not None,
        has_release_public_key=release_public_key_path is not None,
        has_repository_metadata=repository_metadata_path is not None,
        has_reference_audit=reference_audit_path is not None,
        has_reference_resolution=reference_resolution_path is not None,
        has_artifact_bindings=True,
        has_transparency_record=True,
        has_transparency_checkpoint=True,
        has_verification_receipts=True,
        has_witness_record=True,
        has_witness_checkpoint=True,
        has_published_checkpoint_reference=True,
        original_artifact_name=original_name if original_bytes is not None else None,
    )
    rocrate_path = write_rocrate(bundle_dir=bundle_dir, metadata=rocrate)

    manifest_path = bundle_dir / 'manifest.json'
    manifest = build_manifest(bundle_dir)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding='utf-8')

    artifact_bindings = build_artifact_bindings(manifest, bundle_id=bundle_id)
    artifact_bindings_path.write_text(json.dumps(artifact_bindings, indent=2), encoding='utf-8')

    final_report = render_html_report(
        certificate,
        artifact_bindings=artifact_bindings,
        build_provenance=build_provenance.model_dump(mode='json'),
        execution_plan=execution_plan,
        execution_attempts=execution_attempts,
        execution_receipts=execution_receipts,
        execution_stub_outputs=execution_stub_outputs,
        repository_metadata=repository_metadata,
        reference_audit=reference_audit,
        reference_resolution=reference_resolution,
    )
    report_path.write_text(final_report, encoding='utf-8')

    attestation = build_attestation(
        bundle_dir=bundle_dir,
        subject_path=certificate_path,
        manifest_path=manifest_path,
        artifact_bindings_path=artifact_bindings_path,
        trust_tier=certificate.issuer_trust_profile.trust_tier,
    )
    attestation_path = bundle_dir / 'attestation.json'
    attestation_path.write_text(json.dumps(attestation, indent=2), encoding='utf-8')

    transparency_record, transparency_checkpoint = append_transparency_log(
        bundle_dir=bundle_dir,
        certificate_path=certificate_path,
        manifest_path=manifest_path,
        artifact_bindings_path=artifact_bindings_path,
        attestation_path=attestation_path,
        trust_tier=certificate.issuer_trust_profile.trust_tier,
    )
    transparency_record_path = bundle_dir / TRANSPARENCY_RECORD_FILE
    transparency_record_path.write_text(json.dumps(transparency_record, indent=2), encoding='utf-8')
    transparency_checkpoint_snapshot_path = bundle_dir / TRANSPARENCY_CHECKPOINT_SNAPSHOT_FILE
    transparency_checkpoint_snapshot_path.write_text(json.dumps(transparency_checkpoint, indent=2), encoding='utf-8')

    verification_receipts = build_verification_receipts(bundle_dir)
    verification_receipts_path = bundle_dir / VERIFICATION_RECEIPTS_FILE
    verification_receipts_path.write_text(json.dumps(verification_receipts, indent=2), encoding='utf-8')

    witness_record, witness_checkpoint, published_checkpoint_reference = append_witness_log(
        bundle_dir=bundle_dir,
        verification_receipts_path=verification_receipts_path,
    )
    witness_record_path = bundle_dir / WITNESS_RECORD_FILE
    witness_record_path.write_text(json.dumps(witness_record, indent=2), encoding='utf-8')
    witness_checkpoint_snapshot_path = bundle_dir / WITNESS_CHECKPOINT_SNAPSHOT_FILE
    witness_checkpoint_snapshot_path.write_text(json.dumps(witness_checkpoint, indent=2), encoding='utf-8')
    published_checkpoint_reference_path = bundle_dir / PUBLISHED_CHECKPOINT_REFERENCE_FILE
    published_checkpoint_reference_path.write_text(json.dumps(published_checkpoint_reference, indent=2), encoding='utf-8')

    return ArtifactBundleRef(
        bundle_id=bundle_id,
        bundle_dir=str(bundle_dir),
        certificate_path=str(certificate_path),
        report_path=str(report_path),
        rocrate_path=str(rocrate_path),
        manifest_path=str(manifest_path),
        attestation_path=str(attestation_path),
        execution_plan_path=str(execution_plan_path) if execution_plan_path is not None else None,
        execution_attempts_path=str(execution_attempts_path) if execution_attempts_path is not None else None,
        execution_receipts_path=str(execution_receipts_path) if execution_receipts_path is not None else None,
        artifact_bindings_path=str(artifact_bindings_path),
        build_provenance_path=str(build_provenance_path),
        execution_stub_outputs_path=str(execution_stub_outputs_path) if execution_stub_outputs_path is not None else None,
        release_manifest_path=str(release_manifest_path) if release_manifest_path is not None else None,
        release_signature_path=str(release_signature_path) if release_signature_path is not None else None,
        release_verification_path=str(release_verification_path) if release_verification_path is not None else None,
        release_public_key_path=str(release_public_key_path) if release_public_key_path is not None else None,
        repository_metadata_path=str(repository_metadata_path) if repository_metadata_path is not None else None,
        reference_audit_path=str(reference_audit_path) if reference_audit_path is not None else None,
        reference_resolution_path=str(reference_resolution_path) if reference_resolution_path is not None else None,
        transparency_record_path=str(transparency_record_path),
        transparency_checkpoint_path=str(transparency_checkpoint_snapshot_path),
        verification_receipts_path=str(verification_receipts_path),
        witness_record_path=str(witness_record_path),
        witness_checkpoint_path=str(witness_checkpoint_snapshot_path),
        published_checkpoint_reference_path=str(published_checkpoint_reference_path),
        formal_semantic_audit_path=str(formal_semantic_audit_path) if formal_semantic_audit_path is not None else None,
    )


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return {}


def list_bundles(limit: int = 100) -> list[BundleSummary]:
    root = DEFAULT_BUNDLE_ROOT
    if not root.exists():
        return []

    bundles: list[BundleSummary] = []
    for bundle_dir in sorted([p for p in root.iterdir() if p.is_dir()], reverse=True)[:limit]:
        cert = _read_json(bundle_dir / 'certificate.json')
        summary = cert.get('summary') or {}
        issuance = cert.get('issuance') or {}
        operational = cert.get('operational_profile') or {}
        trust = cert.get('issuer_trust_profile') or {}
        execution_attempts = 0
        execution_plan = _read_json(bundle_dir / 'execution_plan.json')
        if execution_plan:
            execution_attempts = len(execution_plan.get('entries') or [])
        bundles.append(
            BundleSummary(
                bundle_id=bundle_dir.name,
                created_at=cert.get('timestamp') or '',
                doc_hash=cert.get('doc_hash'),
                domain=cert.get('domain'),
                title=cert.get('title'),
                doi=cert.get('doi'),
                issuance_status=issuance.get('status'),
                runner_families=list(operational.get('runner_families') or []),
                capability_classes=list(operational.get('capability_classes') or []),
                source_kinds=list(operational.get('source_kinds') or []),
                trust_tier=trust.get('trust_tier'),
                repo_matches_release=trust.get('repo_matches_release'),
                execution_attempts=execution_attempts,
                summary={
                    'passed': int(summary.get('passed', 0) or 0),
                    'warnings': int(summary.get('warnings', 0) or 0),
                    'failed': int(summary.get('failed', 0) or 0),
                    'errors': int(summary.get('errors', 0) or 0),
                },
            )
        )
    return bundles


def get_bundle_detail(bundle_id: str) -> BundleDetail | None:
    bundle_dir = DEFAULT_BUNDLE_ROOT / bundle_id
    if not bundle_dir.exists() or not bundle_dir.is_dir():
        return None

    cert = _read_json(bundle_dir / 'certificate.json')
    manifest = _read_json(bundle_dir / 'manifest.json')
    artifact_bindings = _read_json(bundle_dir / 'artifact_bindings.json')
    build_provenance = _read_json(bundle_dir / 'build_provenance.json')
    return BundleDetail(
        bundle_id=bundle_id,
        bundle_dir=str(bundle_dir),
        certificate=cert,
        manifest=manifest,
        artifact_bindings=artifact_bindings,
        build_provenance=build_provenance,
        report_path=str(bundle_dir / 'report.html') if (bundle_dir / 'report.html').exists() else None,
        rocrate_path=str(bundle_dir / 'ro-crate-metadata.json') if (bundle_dir / 'ro-crate-metadata.json').exists() else None,
        attestation_path=str(bundle_dir / 'attestation.json') if (bundle_dir / 'attestation.json').exists() else None,
        execution_plan_path=str(bundle_dir / 'execution_plan.json') if (bundle_dir / 'execution_plan.json').exists() else None,
        execution_attempts_path=str(bundle_dir / 'execution_attempts.json') if (bundle_dir / 'execution_attempts.json').exists() else None,
        execution_receipts_path=str(bundle_dir / 'execution_receipts.json') if (bundle_dir / 'execution_receipts.json').exists() else None,
        artifact_bindings_path=str(bundle_dir / 'artifact_bindings.json') if (bundle_dir / 'artifact_bindings.json').exists() else None,
        build_provenance_path=str(bundle_dir / 'build_provenance.json') if (bundle_dir / 'build_provenance.json').exists() else None,
        execution_stub_outputs_path=str(bundle_dir / 'execution_stub_outputs.json') if (bundle_dir / 'execution_stub_outputs.json').exists() else None,
        release_manifest_path=str(bundle_dir / 'release_manifest.json') if (bundle_dir / 'release_manifest.json').exists() else None,
        release_signature_path=str(bundle_dir / 'release_manifest.signature.json') if (bundle_dir / 'release_manifest.signature.json').exists() else None,
        release_verification_path=str(bundle_dir / 'release_verification.json') if (bundle_dir / 'release_verification.json').exists() else None,
        release_public_key_path=str(bundle_dir / 'keys/release_signing_public_key.pem') if (bundle_dir / 'keys/release_signing_public_key.pem').exists() else None,
        repository_metadata_path=str(bundle_dir / 'repository_metadata.json') if (bundle_dir / 'repository_metadata.json').exists() else None,
        reference_audit_path=str(bundle_dir / 'reference_audit.json') if (bundle_dir / 'reference_audit.json').exists() else None,
        reference_resolution_path=str(bundle_dir / 'reference_resolution.json') if (bundle_dir / 'reference_resolution.json').exists() else None,
    )


def get_bundle_file_path(bundle_id: str, filename: str) -> Path | None:
    bundle_dir = DEFAULT_BUNDLE_ROOT / bundle_id
    if not bundle_dir.exists() or not bundle_dir.is_dir():
        return None
    candidate = (bundle_dir / filename).resolve()
    try:
        bundle_resolved = bundle_dir.resolve()
    except FileNotFoundError:
        return None
    if bundle_resolved not in candidate.parents and candidate != bundle_resolved:
        return None
    return candidate if candidate.exists() else None
