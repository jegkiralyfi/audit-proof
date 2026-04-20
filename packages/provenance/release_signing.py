from __future__ import annotations

import base64
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

from packages.core.hashing import sha256_bytes, sha256_file
from packages.core.security import PROTOTYPE_SECURITY_FLAGS, PROTOTYPE_SECURITY_NOTICE


def _canonical_json(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def signing_public_key_path(root: str | Path) -> Path:
    return Path(root).resolve() / 'keys' / 'release_signing_public_key.pem'


def signing_private_key_path(root: str | Path) -> Path:
    override = os.getenv('AUDIT_PROOF_RELEASE_SIGNING_PRIVATE_KEY_PATH')
    if override:
        return Path(override).resolve()
    return Path(root).resolve() / 'keys' / 'release_signing_private_key.pem'


def release_signature_path(root: str | Path) -> Path:
    return Path(root).resolve() / 'release_manifest.signature.json'


def release_verification_path(root: str | Path) -> Path:
    return Path(root).resolve() / 'release_verification.json'


def generate_keypair(*, private_path: str | Path, public_path: str | Path) -> tuple[Path, Path]:
    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    private_path = Path(private_path)
    public_path = Path(public_path)
    private_path.parent.mkdir(parents=True, exist_ok=True)
    public_path.parent.mkdir(parents=True, exist_ok=True)
    private_path.write_bytes(private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ))
    public_path.write_bytes(public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ))
    return private_path, public_path


def load_private_key(path: str | Path):
    return serialization.load_pem_private_key(Path(path).read_bytes(), password=None)


def load_public_key(path: str | Path):
    return serialization.load_pem_public_key(Path(path).read_bytes())


def public_key_fingerprint(public_key) -> str:
    public_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return sha256_bytes(public_bytes)


def build_release_signature(*, manifest: dict[str, Any], manifest_path: str | Path, private_key_path: str | Path, public_key_path: str | Path, issuer: str = 'audit-proof-release-signer') -> dict[str, Any]:
    private_key = load_private_key(private_key_path)
    public_key = load_public_key(public_key_path)
    manifest_bytes = _canonical_json(manifest)
    signature = private_key.sign(manifest_bytes)
    return {
        'artifact_version': '0.1.0',
        'security_notice': PROTOTYPE_SECURITY_NOTICE,
        **PROTOTYPE_SECURITY_FLAGS,
        'signature_type': 'ed25519',
        'issuer': issuer,
        'key_id': os.getenv('AUDIT_PROOF_RELEASE_SIGNING_KEY_ID', 'local-release-signing-key'),
        'manifest_path': Path(manifest_path).name,
        'manifest_sha256': sha256_file(manifest_path),
        'public_key_path': Path(public_key_path).name,
        'public_key_fingerprint': public_key_fingerprint(public_key),
        'signature_b64': base64.b64encode(signature).decode('ascii'),
        'signed_at': datetime.now(timezone.utc).isoformat(),
        'note': 'Self-hosted release signature for stable manifest verification. Not an external audit guarantee.',
    }


def verify_release_signature(*, manifest: dict[str, Any], manifest_path: str | Path, signature_doc: dict[str, Any], public_key_path: str | Path) -> dict[str, Any]:
    verification: dict[str, Any] = {
        'artifact_version': '0.1.0',
        'security_notice': PROTOTYPE_SECURITY_NOTICE,
        **PROTOTYPE_SECURITY_FLAGS,
        'verification_type': 'release_manifest_signature',
        'manifest_path': Path(manifest_path).name,
        'manifest_sha256': sha256_file(manifest_path) if Path(manifest_path).exists() else None,
        'signature_path': 'release_manifest.signature.json',
        'public_key_path': Path(public_key_path).name if Path(public_key_path).exists() else None,
        'verified': False,
        'verification_notes': [],
        'verified_at': datetime.now(timezone.utc).isoformat(),
        'key_id': signature_doc.get('key_id'),
        'public_key_fingerprint': signature_doc.get('public_key_fingerprint'),
    }
    if not Path(public_key_path).exists():
        verification['verification_notes'].append('Public key missing.')
        return verification
    if not signature_doc:
        verification['verification_notes'].append('Signature document missing.')
        return verification
    if signature_doc.get('manifest_sha256') != verification['manifest_sha256']:
        verification['verification_notes'].append('Manifest SHA-256 does not match signature document.')
        return verification
    try:
        public_key = load_public_key(public_key_path)
        signature = base64.b64decode(signature_doc['signature_b64'])
        public_key.verify(signature, _canonical_json(manifest))
        verification['verified'] = True
        verification['verification_notes'].append('Ed25519 signature verified successfully.')
    except (InvalidSignature, ValueError, TypeError, KeyError) as exc:
        verification['verification_notes'].append(f'Signature verification failed: {exc}')
    return verification
