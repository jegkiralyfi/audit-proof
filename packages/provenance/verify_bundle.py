from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from packages.core.hashing import sha256_file
from packages.core.models import BuildProvenanceArtifact
from packages.provenance.manifest import build_artifact_bindings, build_manifest
from packages.provenance.sigstore_signer import verify_attestation
from packages.provenance.transparency_log import verify_bundle_transparency
from packages.provenance.witness_log import verify_bundle_witness
from packages.provenance.trust import build_issuer_trust_profile


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return {}


def verify_bundle(bundle_dir: str | Path) -> dict[str, Any]:
    bundle_path = Path(bundle_dir)
    bundle_id = bundle_path.name
    notes: list[str] = []

    certificate = _read_json(bundle_path / 'certificate.json')
    manifest = _read_json(bundle_path / 'manifest.json')
    artifact_bindings = _read_json(bundle_path / 'artifact_bindings.json')
    attestation = _read_json(bundle_path / 'attestation.json')
    build_provenance_doc = _read_json(bundle_path / 'build_provenance.json')

    recomputed_manifest = build_manifest(bundle_path)
    recomputed_bindings = build_artifact_bindings(recomputed_manifest, bundle_id=bundle_id)

    manifest_matches = manifest.get('artifacts') == recomputed_manifest.get('artifacts') and manifest.get('artifact_scope') == recomputed_manifest.get('artifact_scope')
    if not manifest_matches:
        notes.append('Stored manifest.json does not match recomputed canonical artifact manifest.')

    bindings_match = artifact_bindings.get('bindings') == recomputed_bindings.get('bindings')
    if not bindings_match:
        notes.append('Stored artifact_bindings.json does not match recomputed canonical hash bindings.')

    stored_bundle_fingerprint = artifact_bindings.get('bundle_fingerprint_sha256')
    recomputed_bundle_fingerprint = recomputed_bindings.get('bundle_fingerprint_sha256')
    bundle_fingerprint_matches = stored_bundle_fingerprint == recomputed_bundle_fingerprint
    if not bundle_fingerprint_matches:
        notes.append('Stored bundle fingerprint does not match recomputed canonical bundle fingerprint.')

    certificate_sha256 = sha256_file(bundle_path / 'certificate.json') if (bundle_path / 'certificate.json').exists() else None
    certificate_hash_matches_binding = True
    cert_binding = (artifact_bindings.get('bindings') or {}).get('certificate.json')
    if cert_binding is not None and certificate_sha256 is not None:
        certificate_hash_matches_binding = cert_binding.get('sha256') == certificate_sha256
        if not certificate_hash_matches_binding:
            notes.append('certificate.json hash does not match the stored artifact bindings.')

    attestation_verification = verify_attestation(
        attestation,
        bundle_dir=bundle_path,
        subject_path=bundle_path / 'certificate.json',
        manifest_path=bundle_path / 'manifest.json',
        artifact_bindings_path=bundle_path / 'artifact_bindings.json',
    ) if attestation else {
        'verified': False,
        'signature_matches': False,
        'subject_sha256_matches': False,
        'manifest_sha256_matches': False,
        'artifact_bindings_sha256_matches': False,
        'bundle_fingerprint_matches': False,
        'verification_notes': ['attestation.json is missing or unreadable.'],
    }
    notes.extend([n for n in attestation_verification.get('verification_notes', []) if n not in notes])

    transparency_verification = verify_bundle_transparency(bundle_path)
    notes.extend([n for n in transparency_verification.get('verification_notes', []) if n not in notes])

    witness_verification = verify_bundle_witness(bundle_path)
    notes.extend([n for n in witness_verification.get('verification_notes', []) if n not in notes])

    stored_trust_tier = ((certificate.get('issuer_trust_profile') or {}).get('trust_tier'))
    recomputed_trust_tier = None
    trust_tier_matches = False
    if build_provenance_doc:
        provenance = BuildProvenanceArtifact.model_validate(build_provenance_doc)
        recomputed_trust_tier = build_issuer_trust_profile(provenance).trust_tier
        trust_tier_matches = stored_trust_tier == recomputed_trust_tier
        if not trust_tier_matches:
            notes.append('Stored certificate trust tier does not match the trust tier recomputed from build_provenance.json.')
    else:
        notes.append('build_provenance.json is missing or unreadable; trust tier could not be recomputed.')

    verified = all([
        manifest_matches,
        bindings_match,
        bundle_fingerprint_matches,
        certificate_hash_matches_binding,
        attestation_verification.get('verified', False),
        trust_tier_matches,
        (transparency_verification.get('verified', False) if (transparency_verification.get('log_present') or (bundle_path / 'transparency_record.json').exists()) else True),
        (witness_verification.get('verified', False) if (witness_verification.get('log_present') or (bundle_path / 'witness_record.json').exists()) else True),
    ])

    return {
        'bundle_id': bundle_id,
        'verified': verified,
        'manifest_matches': manifest_matches,
        'artifact_bindings_match': bindings_match,
        'bundle_fingerprint_matches': bundle_fingerprint_matches,
        'certificate_hash_matches_binding': certificate_hash_matches_binding,
        'attestation_verified': bool(attestation_verification.get('verified')),
        'attestation': attestation_verification,
        'transparency_verified': bool(transparency_verification.get('verified')),
        'transparency': transparency_verification,
        'witness_verified': bool(witness_verification.get('verified')),
        'witness': witness_verification,
        'stored_trust_tier': stored_trust_tier,
        'recomputed_trust_tier': recomputed_trust_tier,
        'trust_tier_matches': trust_tier_matches,
        'verified_artifact_scope': recomputed_manifest.get('artifact_scope'),
        'verification_notes': notes,
    }
