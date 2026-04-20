from __future__ import annotations

import hashlib
import hmac
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from packages.core.hashing import sha256_file, sha256_text
from packages.core.security import PROTOTYPE_SECURITY_FLAGS, PROTOTYPE_SECURITY_NOTICE


TRANSPARENCY_LOG_FILE = 'transparency_log.jsonl'
TRANSPARENCY_CHECKPOINT_FILE = 'transparency_checkpoint.json'
TRANSPARENCY_RECORD_FILE = 'transparency_record.json'
TRANSPARENCY_CHECKPOINT_SNAPSHOT_FILE = 'transparency_checkpoint_snapshot.json'


def _canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _transparency_secret() -> tuple[str, str]:
    secret = os.getenv('AUDIT_PROOF_TRANSPARENCY_SECRET') or os.getenv('AUDIT_PROOF_SIGNING_SECRET', 'audit-proof-dev-secret')
    key_id = os.getenv('AUDIT_PROOF_TRANSPARENCY_KEY_ID') or os.getenv('AUDIT_PROOF_SIGNING_KEY_ID', 'local-dev-key')
    return secret, key_id


def _sign_payload(payload: dict[str, Any]) -> str:
    secret, _ = _transparency_secret()
    return hmac.new(secret.encode('utf-8'), _canonical_json(payload).encode('utf-8'), hashlib.sha256).hexdigest()


def transparency_dir_from_bundle(bundle_dir: str | Path) -> Path:
    bundle_path = Path(bundle_dir)
    return bundle_path.parent.parent / 'transparency'


def transparency_log_path(bundle_dir: str | Path) -> Path:
    return transparency_dir_from_bundle(bundle_dir) / TRANSPARENCY_LOG_FILE


def transparency_checkpoint_path(bundle_dir: str | Path) -> Path:
    return transparency_dir_from_bundle(bundle_dir) / TRANSPARENCY_CHECKPOINT_FILE


def _load_entries(log_path: Path) -> list[dict[str, Any]]:
    if not log_path.exists():
        return []
    entries: list[dict[str, Any]] = []
    for line in log_path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line:
            continue
        entries.append(json.loads(line))
    return entries


def _entry_hash(entry: dict[str, Any]) -> str:
    payload = {k: v for k, v in entry.items() if k != 'entry_hash'}
    return sha256_text(_canonical_json(payload))


def verify_transparency_chain(entries: list[dict[str, Any]]) -> dict[str, Any]:
    notes: list[str] = []
    previous_hash = None
    duplicate_bundle_ids: set[str] = set()
    seen_bundle_ids: set[str] = set()
    for index, entry in enumerate(entries, start=1):
        expected_prev = previous_hash
        actual_prev = entry.get('previous_entry_hash')
        if actual_prev != expected_prev:
            notes.append(f'Entry {index} previous_entry_hash does not match the prior entry hash.')
        expected_hash = _entry_hash(entry)
        if entry.get('entry_hash') != expected_hash:
            notes.append(f'Entry {index} entry_hash does not match its canonical content.')
        bundle_id = entry.get('bundle_id')
        if bundle_id in seen_bundle_ids:
            duplicate_bundle_ids.add(str(bundle_id))
        seen_bundle_ids.add(str(bundle_id))
        previous_hash = entry.get('entry_hash')
    if duplicate_bundle_ids:
        notes.append('Duplicate bundle IDs present in transparency log: ' + ', '.join(sorted(duplicate_bundle_ids)))
    return {
        'verified': len(notes) == 0,
        'entry_count': len(entries),
        'head_entry_hash': previous_hash,
        'verification_notes': notes,
    }


def build_transparency_entry(
    *,
    bundle_id: str,
    certificate_path: str | Path,
    manifest_path: str | Path,
    artifact_bindings_path: str | Path,
    attestation_path: str | Path,
    trust_tier: str | None,
    previous_entry_hash: str | None,
    sequence_number: int,
) -> dict[str, Any]:
    entry = {
        'entry_version': '0.1.0',
        'security_notice': PROTOTYPE_SECURITY_NOTICE,
        **PROTOTYPE_SECURITY_FLAGS,
        'sequence_number': sequence_number,
        'logged_at': datetime.now(timezone.utc).isoformat(),
        'bundle_id': bundle_id,
        'certificate_sha256': sha256_file(Path(certificate_path)),
        'manifest_sha256': sha256_file(Path(manifest_path)),
        'artifact_bindings_sha256': sha256_file(Path(artifact_bindings_path)),
        'attestation_sha256': sha256_file(Path(attestation_path)),
        'bundle_fingerprint_sha256': json.loads(Path(artifact_bindings_path).read_text(encoding='utf-8')).get('bundle_fingerprint_sha256'),
        'trust_tier': trust_tier,
        'previous_entry_hash': previous_entry_hash,
    }
    entry['entry_hash'] = _entry_hash(entry)
    return entry


def build_transparency_checkpoint(*, bundle_dir: str | Path, entries: list[dict[str, Any]]) -> dict[str, Any]:
    log_path = transparency_log_path(bundle_dir)
    _, key_id = _transparency_secret()
    payload = {
        'checkpoint_version': '0.1.0',
        'security_notice': PROTOTYPE_SECURITY_NOTICE,
        **PROTOTYPE_SECURITY_FLAGS,
        'mode': 'local-hmac-v1',
        'key_id': key_id,
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'log_file': TRANSPARENCY_LOG_FILE,
        'log_sha256': sha256_file(log_path) if log_path.exists() else None,
        'entry_count': len(entries),
        'head_entry_hash': entries[-1].get('entry_hash') if entries else None,
        'note': 'PoC local transparency checkpoint. Replace with external witness/transparency service in a later phase.',
    }
    payload['signature'] = _sign_payload(payload)
    payload['algorithm'] = 'hmac-sha256'
    return payload


def verify_transparency_checkpoint(checkpoint_doc: dict[str, Any], *, log_path: str | Path) -> dict[str, Any]:
    log_file = Path(log_path)
    notes: list[str] = []
    payload = {k: v for k, v in checkpoint_doc.items() if k not in {'signature', 'algorithm'}}
    expected_signature = _sign_payload(payload)
    signature_matches = hmac.compare_digest(checkpoint_doc.get('signature', ''), expected_signature)
    if not signature_matches:
        notes.append('Transparency checkpoint signature mismatch.')
    log_sha_matches = True
    if log_file.exists():
        expected_log_sha = sha256_file(log_file)
        log_sha_matches = checkpoint_doc.get('log_sha256') == expected_log_sha
        if not log_sha_matches:
            notes.append('Transparency checkpoint log_sha256 does not match the current transparency log file.')
    else:
        log_sha_matches = False
        notes.append('Transparency log file is missing.')
    verified = signature_matches and log_sha_matches
    return {
        'verified': verified,
        'signature_matches': signature_matches,
        'log_sha256_matches': log_sha_matches,
        'verification_notes': notes,
    }


def append_transparency_log(
    *,
    bundle_dir: str | Path,
    certificate_path: str | Path,
    manifest_path: str | Path,
    artifact_bindings_path: str | Path,
    attestation_path: str | Path,
    trust_tier: str | None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    bundle_path = Path(bundle_dir)
    log_dir = transparency_dir_from_bundle(bundle_path)
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = transparency_log_path(bundle_path)
    entries = _load_entries(log_path)
    chain_status = verify_transparency_chain(entries)
    if entries and not chain_status.get('verified'):
        raise ValueError('Transparency log chain is already broken; refusing to append a new bundle entry.')

    entry = build_transparency_entry(
        bundle_id=bundle_path.name,
        certificate_path=certificate_path,
        manifest_path=manifest_path,
        artifact_bindings_path=artifact_bindings_path,
        attestation_path=attestation_path,
        trust_tier=trust_tier,
        previous_entry_hash=entries[-1].get('entry_hash') if entries else None,
        sequence_number=len(entries) + 1,
    )
    with log_path.open('a', encoding='utf-8') as fh:
        fh.write(json.dumps(entry, sort_keys=True) + '\n')
    entries.append(entry)
    checkpoint = build_transparency_checkpoint(bundle_dir=bundle_path, entries=entries)
    transparency_checkpoint_path(bundle_path).write_text(json.dumps(checkpoint, indent=2), encoding='utf-8')
    return entry, checkpoint


def verify_bundle_transparency(bundle_dir: str | Path) -> dict[str, Any]:
    bundle_path = Path(bundle_dir)
    log_path = transparency_log_path(bundle_path)
    checkpoint_path = transparency_checkpoint_path(bundle_path)
    notes: list[str] = []

    log_present = log_path.exists()
    checkpoint_present = checkpoint_path.exists()
    entries = _load_entries(log_path) if log_present else []
    chain_status = verify_transparency_chain(entries) if log_present else {
        'verified': False,
        'entry_count': 0,
        'head_entry_hash': None,
        'verification_notes': ['Transparency log file is missing.'],
    }
    notes.extend([n for n in chain_status.get('verification_notes', []) if n not in notes])

    checkpoint_doc = json.loads(checkpoint_path.read_text(encoding='utf-8')) if checkpoint_present else {}
    checkpoint_status = verify_transparency_checkpoint(checkpoint_doc, log_path=log_path) if checkpoint_present else {
        'verified': False,
        'signature_matches': False,
        'log_sha256_matches': False,
        'verification_notes': ['Transparency checkpoint file is missing.'],
    }
    notes.extend([n for n in checkpoint_status.get('verification_notes', []) if n not in notes])

    matching_entries = [entry for entry in entries if entry.get('bundle_id') == bundle_path.name]
    bundle_included = len(matching_entries) > 0
    if not bundle_included:
        notes.append('Bundle ID is not present in the transparency log.')
    elif len(matching_entries) > 1:
        notes.append('Multiple transparency log entries found for the same bundle ID.')
    matching_entry = matching_entries[-1] if matching_entries else {}

    entry_matches_current_bundle = True
    if matching_entry:
        current_certificate_sha = sha256_file(bundle_path / 'certificate.json') if (bundle_path / 'certificate.json').exists() else None
        current_manifest_sha = sha256_file(bundle_path / 'manifest.json') if (bundle_path / 'manifest.json').exists() else None
        current_bindings_sha = sha256_file(bundle_path / 'artifact_bindings.json') if (bundle_path / 'artifact_bindings.json').exists() else None
        current_attestation_sha = sha256_file(bundle_path / 'attestation.json') if (bundle_path / 'attestation.json').exists() else None
        current_bundle_fingerprint = None
        if (bundle_path / 'artifact_bindings.json').exists():
            current_bundle_fingerprint = json.loads((bundle_path / 'artifact_bindings.json').read_text(encoding='utf-8')).get('bundle_fingerprint_sha256')
        current_trust_tier = None
        if (bundle_path / 'certificate.json').exists():
            current_trust_tier = json.loads((bundle_path / 'certificate.json').read_text(encoding='utf-8')).get('issuer_trust_profile', {}).get('trust_tier')
        comparisons = [
            ('certificate_sha256', current_certificate_sha),
            ('manifest_sha256', current_manifest_sha),
            ('artifact_bindings_sha256', current_bindings_sha),
            ('attestation_sha256', current_attestation_sha),
            ('bundle_fingerprint_sha256', current_bundle_fingerprint),
            ('trust_tier', current_trust_tier),
        ]
        for key, expected_value in comparisons:
            if matching_entry.get(key) != expected_value:
                entry_matches_current_bundle = False
                notes.append(f'Transparency log entry field {key} does not match the current bundle state.')

    snapshot_entry_path = bundle_path / TRANSPARENCY_RECORD_FILE
    snapshot_checkpoint_path = bundle_path / TRANSPARENCY_CHECKPOINT_SNAPSHOT_FILE
    bundle_snapshot_matches = True
    if snapshot_entry_path.exists() and matching_entry:
        try:
            snapshot_entry = json.loads(snapshot_entry_path.read_text(encoding='utf-8'))
            if snapshot_entry != matching_entry:
                bundle_snapshot_matches = False
                notes.append('Bundle transparency_record.json does not match the active transparency log entry.')
        except Exception:
            bundle_snapshot_matches = False
            notes.append('Bundle transparency_record.json could not be parsed.')
    if snapshot_checkpoint_path.exists() and checkpoint_doc:
        try:
            snapshot_checkpoint = json.loads(snapshot_checkpoint_path.read_text(encoding='utf-8'))
            if snapshot_checkpoint != checkpoint_doc:
                bundle_snapshot_matches = False
                notes.append('Bundle transparency_checkpoint_snapshot.json does not match the active transparency checkpoint.')
        except Exception:
            bundle_snapshot_matches = False
            notes.append('Bundle transparency_checkpoint_snapshot.json could not be parsed.')

    verified = bool(log_present and checkpoint_present and chain_status.get('verified') and checkpoint_status.get('verified') and bundle_included and entry_matches_current_bundle and bundle_snapshot_matches)
    return {
        'log_present': log_present,
        'checkpoint_present': checkpoint_present,
        'chain_verified': bool(chain_status.get('verified')),
        'checkpoint_verified': bool(checkpoint_status.get('verified')),
        'bundle_included': bundle_included,
        'entry_matches_current_bundle': entry_matches_current_bundle,
        'bundle_snapshot_matches': bundle_snapshot_matches,
        'entry_count': chain_status.get('entry_count', 0),
        'head_entry_hash': chain_status.get('head_entry_hash'),
        'included_sequence_number': matching_entry.get('sequence_number') if matching_entry else None,
        'included_entry_hash': matching_entry.get('entry_hash') if matching_entry else None,
        'checkpoint': checkpoint_status,
        'verification_notes': notes,
        'verified': verified,
    }
