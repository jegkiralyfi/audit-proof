from __future__ import annotations

import hashlib
import hmac
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from packages.core.hashing import sha256_file
from packages.core.security import PROTOTYPE_SECURITY_FLAGS, PROTOTYPE_SECURITY_NOTICE


def _canonical_json(payload: dict) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _local_secret() -> tuple[str, str]:
    secret = os.getenv("AUDIT_PROOF_SIGNING_SECRET", "audit-proof-dev-secret")
    key_id = os.getenv("AUDIT_PROOF_SIGNING_KEY_ID", "local-dev-key")
    return secret, key_id


def _sign_payload(payload: dict[str, Any]) -> str:
    secret, _ = _local_secret()
    return hmac.new(secret.encode('utf-8'), _canonical_json(payload).encode('utf-8'), hashlib.sha256).hexdigest()


def build_attestation(
    bundle_dir: str | Path,
    subject_path: str | Path,
    manifest_path: str | Path | None = None,
    artifact_bindings_path: str | Path | None = None,
    issuer: str = 'audit-proof-local-signer',
    trust_tier: str | None = None,
) -> dict:
    bundle_path = Path(bundle_dir)
    subject = Path(subject_path)
    manifest = Path(manifest_path) if manifest_path else None
    artifact_bindings = Path(artifact_bindings_path) if artifact_bindings_path else None

    _, key_id = _local_secret()
    payload = {
        'attestation_version': '0.3.0',
        'security_notice': PROTOTYPE_SECURITY_NOTICE,
        **PROTOTYPE_SECURITY_FLAGS,
        'mode': 'local-hmac-v1',
        'issuer': issuer,
        'key_id': key_id,
        'bundle_dir': str(bundle_path),
        'subject': subject.name,
        'subject_sha256': sha256_file(subject),
        'manifest': manifest.name if manifest and manifest.exists() else None,
        'manifest_sha256': sha256_file(manifest) if manifest and manifest.exists() else None,
        'artifact_bindings': artifact_bindings.name if artifact_bindings and artifact_bindings.exists() else None,
        'artifact_bindings_sha256': sha256_file(artifact_bindings) if artifact_bindings and artifact_bindings.exists() else None,
        'bundle_fingerprint_sha256': None,
        'trust_tier': trust_tier,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'note': 'PoC local attestation. Replace with real Sigstore integration in a later phase.',
    }
    if artifact_bindings and artifact_bindings.exists():
        try:
            bindings_payload = json.loads(artifact_bindings.read_text(encoding='utf-8'))
            payload['bundle_fingerprint_sha256'] = bindings_payload.get('bundle_fingerprint_sha256')
        except Exception:
            payload['bundle_fingerprint_sha256'] = None
    signature = _sign_payload(payload)
    payload['signature'] = signature
    payload['algorithm'] = 'hmac-sha256'
    return payload


def verify_attestation(
    attestation_doc: dict[str, Any],
    *,
    bundle_dir: str | Path,
    subject_path: str | Path,
    manifest_path: str | Path | None = None,
    artifact_bindings_path: str | Path | None = None,
) -> dict[str, Any]:
    subject = Path(subject_path)
    manifest = Path(manifest_path) if manifest_path else None
    artifact_bindings = Path(artifact_bindings_path) if artifact_bindings_path else None

    notes: list[str] = []
    payload = {k: v for k, v in attestation_doc.items() if k not in {'signature', 'algorithm'}}
    expected_signature = _sign_payload(payload)
    signature_matches = hmac.compare_digest(attestation_doc.get('signature', ''), expected_signature)
    if not signature_matches:
        notes.append('Attestation signature mismatch.')

    subject_sha_matches = True
    if subject.exists():
        expected = sha256_file(subject)
        subject_sha_matches = attestation_doc.get('subject_sha256') == expected
        if not subject_sha_matches:
            notes.append('Attestation subject_sha256 does not match the current certificate.json.')
    else:
        subject_sha_matches = False
        notes.append('Attestation subject path is missing.')

    manifest_sha_matches = True
    if manifest is not None and manifest.exists():
        expected = sha256_file(manifest)
        manifest_sha_matches = attestation_doc.get('manifest_sha256') == expected
        if not manifest_sha_matches:
            notes.append('Attestation manifest_sha256 does not match the current manifest.json.')

    bindings_sha_matches = True
    bundle_fingerprint_matches = True
    if artifact_bindings is not None and artifact_bindings.exists():
        expected = sha256_file(artifact_bindings)
        bindings_sha_matches = attestation_doc.get('artifact_bindings_sha256') == expected
        if not bindings_sha_matches:
            notes.append('Attestation artifact_bindings_sha256 does not match the current artifact_bindings.json.')
        try:
            bindings_payload = json.loads(artifact_bindings.read_text(encoding='utf-8'))
            bundle_fingerprint_matches = attestation_doc.get('bundle_fingerprint_sha256') == bindings_payload.get('bundle_fingerprint_sha256')
            if not bundle_fingerprint_matches:
                notes.append('Attestation bundle fingerprint does not match the current artifact_bindings.json.')
        except Exception:
            bundle_fingerprint_matches = False
            notes.append('Current artifact_bindings.json could not be parsed during attestation verification.')

    verified = all([signature_matches, subject_sha_matches, manifest_sha_matches, bindings_sha_matches, bundle_fingerprint_matches])
    return {
        'verified': verified,
        'signature_matches': signature_matches,
        'subject_sha256_matches': subject_sha_matches,
        'manifest_sha256_matches': manifest_sha_matches,
        'artifact_bindings_sha256_matches': bindings_sha_matches,
        'bundle_fingerprint_matches': bundle_fingerprint_matches,
        'verification_notes': notes,
    }
