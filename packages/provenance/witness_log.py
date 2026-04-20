
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
from packages.provenance.manifest import build_artifact_bindings, build_manifest
from packages.provenance.sigstore_signer import verify_attestation
from packages.provenance.transparency_log import verify_bundle_transparency

WITNESS_LOG_FILE = 'witness_log.jsonl'
WITNESS_CHECKPOINT_FILE = 'witness_checkpoint.json'
PUBLISHED_WITNESS_CHECKPOINT_FILE = 'published_checkpoint.json'
WITNESS_RECORD_FILE = 'witness_record.json'
WITNESS_CHECKPOINT_SNAPSHOT_FILE = 'witness_checkpoint_snapshot.json'
PUBLISHED_CHECKPOINT_REFERENCE_FILE = 'published_checkpoint_reference.json'
VERIFICATION_RECEIPTS_FILE = 'verification_receipts.json'


def _canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _witness_secret() -> tuple[str, str]:
    secret = os.getenv('AUDIT_PROOF_WITNESS_SECRET') or os.getenv('AUDIT_PROOF_TRANSPARENCY_SECRET') or os.getenv('AUDIT_PROOF_SIGNING_SECRET', 'audit-proof-dev-secret')
    key_id = os.getenv('AUDIT_PROOF_WITNESS_KEY_ID') or 'local-witness-key'
    return secret, key_id


def _sign_payload(payload: dict[str, Any]) -> str:
    secret, _ = _witness_secret()
    return hmac.new(secret.encode('utf-8'), _canonical_json(payload).encode('utf-8'), hashlib.sha256).hexdigest()


def witness_dir_from_bundle(bundle_dir: str | Path) -> Path:
    bundle_path = Path(bundle_dir)
    return bundle_path.parent.parent / 'witness'


def witness_log_path(bundle_dir: str | Path) -> Path:
    return witness_dir_from_bundle(bundle_dir) / WITNESS_LOG_FILE


def witness_checkpoint_path(bundle_dir: str | Path) -> Path:
    return witness_dir_from_bundle(bundle_dir) / WITNESS_CHECKPOINT_FILE


def published_checkpoint_path(bundle_dir: str | Path) -> Path:
    return witness_dir_from_bundle(bundle_dir) / PUBLISHED_WITNESS_CHECKPOINT_FILE


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


def verify_witness_chain(entries: list[dict[str, Any]]) -> dict[str, Any]:
    notes: list[str] = []
    previous_hash = None
    seen_bundle_ids: set[str] = set()
    duplicate_bundle_ids: set[str] = set()
    for index, entry in enumerate(entries, start=1):
        if entry.get('previous_entry_hash') != previous_hash:
            notes.append(f'Witness entry {index} previous_entry_hash does not match the prior witness entry hash.')
        expected_hash = _entry_hash(entry)
        if entry.get('entry_hash') != expected_hash:
            notes.append(f'Witness entry {index} entry_hash does not match canonical content.')
        bundle_id = str(entry.get('bundle_id'))
        if bundle_id in seen_bundle_ids:
            duplicate_bundle_ids.add(bundle_id)
        seen_bundle_ids.add(bundle_id)
        previous_hash = entry.get('entry_hash')
    if duplicate_bundle_ids:
        notes.append('Duplicate bundle IDs present in witness log: ' + ', '.join(sorted(duplicate_bundle_ids)))
    return {
        'verified': len(notes) == 0,
        'entry_count': len(entries),
        'head_entry_hash': previous_hash,
        'verification_notes': notes,
    }


def build_verification_receipts(bundle_dir: str | Path) -> dict[str, Any]:
    bundle_path = Path(bundle_dir)
    notes: list[str] = []

    manifest = json.loads((bundle_path / 'manifest.json').read_text(encoding='utf-8')) if (bundle_path / 'manifest.json').exists() else {}
    recomputed_manifest = build_manifest(bundle_path)
    manifest_matches = manifest.get('artifacts') == recomputed_manifest.get('artifacts') and manifest.get('artifact_scope') == recomputed_manifest.get('artifact_scope')
    if not manifest_matches:
        notes.append('Stored manifest does not match recomputed canonical artifact manifest.')

    bindings = json.loads((bundle_path / 'artifact_bindings.json').read_text(encoding='utf-8')) if (bundle_path / 'artifact_bindings.json').exists() else {}
    recomputed_bindings = build_artifact_bindings(recomputed_manifest, bundle_id=bundle_path.name)
    bindings_match = bindings.get('bindings') == recomputed_bindings.get('bindings')
    bundle_fingerprint_matches = bindings.get('bundle_fingerprint_sha256') == recomputed_bindings.get('bundle_fingerprint_sha256')
    if not bindings_match:
        notes.append('Stored artifact bindings do not match recomputed canonical bindings.')
    if not bundle_fingerprint_matches:
        notes.append('Stored bundle fingerprint does not match recomputed bundle fingerprint.')

    cert_binding_ok = True
    cert_sha = sha256_file(bundle_path / 'certificate.json') if (bundle_path / 'certificate.json').exists() else None
    cert_binding = (bindings.get('bindings') or {}).get('certificate.json')
    if cert_binding and cert_sha:
        cert_binding_ok = cert_binding.get('sha256') == cert_sha
        if not cert_binding_ok:
            notes.append('certificate.json hash does not match artifact bindings.')

    attestation = json.loads((bundle_path / 'attestation.json').read_text(encoding='utf-8')) if (bundle_path / 'attestation.json').exists() else {}
    attestation_verification = verify_attestation(
        attestation,
        bundle_dir=bundle_path,
        subject_path=bundle_path / 'certificate.json',
        manifest_path=bundle_path / 'manifest.json',
        artifact_bindings_path=bundle_path / 'artifact_bindings.json',
    ) if attestation else {
        'verified': False,
        'verification_notes': ['attestation.json is missing or unreadable.'],
    }

    transparency_verification = verify_bundle_transparency(bundle_path)

    receipts = [
        {
            'verifier_id': 'canonical_bundle_verifier_v1',
            'scope': 'canonical-artifacts',
            'verified': bool(manifest_matches and bindings_match and bundle_fingerprint_matches and cert_binding_ok),
            'checks': {
                'manifest_matches': manifest_matches,
                'artifact_bindings_match': bindings_match,
                'bundle_fingerprint_matches': bundle_fingerprint_matches,
                'certificate_hash_matches_binding': cert_binding_ok,
            },
            'notes': notes,
        },
        {
            'verifier_id': 'attestation_verifier_v1',
            'scope': 'attestation',
            'verified': bool(attestation_verification.get('verified')),
            'checks': {
                'signature_matches': bool(attestation_verification.get('signature_matches')),
                'subject_sha256_matches': bool(attestation_verification.get('subject_sha256_matches')),
                'manifest_sha256_matches': bool(attestation_verification.get('manifest_sha256_matches')),
                'artifact_bindings_sha256_matches': bool(attestation_verification.get('artifact_bindings_sha256_matches')),
                'bundle_fingerprint_matches': bool(attestation_verification.get('bundle_fingerprint_matches')),
            },
            'notes': list(attestation_verification.get('verification_notes') or []),
        },
        {
            'verifier_id': 'transparency_inclusion_verifier_v1',
            'scope': 'transparency-log',
            'verified': bool(transparency_verification.get('verified')),
            'checks': {
                'log_present': bool(transparency_verification.get('log_present')),
                'checkpoint_present': bool(transparency_verification.get('checkpoint_present')),
                'chain_verified': bool(transparency_verification.get('chain_verified')),
                'checkpoint_verified': bool(transparency_verification.get('checkpoint_verified')),
                'bundle_included': bool(transparency_verification.get('bundle_included')),
                'entry_matches_current_bundle': bool(transparency_verification.get('entry_matches_current_bundle')),
                'bundle_snapshot_matches': bool(transparency_verification.get('bundle_snapshot_matches')),
            },
            'notes': list(transparency_verification.get('verification_notes') or []),
        },
    ]
    return {
        'receipt_version': '0.1.0',
        'security_notice': PROTOTYPE_SECURITY_NOTICE,
        **PROTOTYPE_SECURITY_FLAGS,
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'bundle_id': bundle_path.name,
        'all_verifiers_passed': all(bool(r.get('verified')) for r in receipts),
        'verifier_count': len(receipts),
        'receipts': receipts,
    }


def build_witness_entry(
    *,
    bundle_dir: str | Path,
    verification_receipts_path: str | Path,
    previous_entry_hash: str | None,
    sequence_number: int,
) -> dict[str, Any]:
    bundle_path = Path(bundle_dir)
    bindings = json.loads((bundle_path / 'artifact_bindings.json').read_text(encoding='utf-8')) if (bundle_path / 'artifact_bindings.json').exists() else {}
    transparency_record = json.loads((bundle_path / 'transparency_record.json').read_text(encoding='utf-8')) if (bundle_path / 'transparency_record.json').exists() else {}
    entry = {
        'entry_version': '0.1.0',
        'security_notice': PROTOTYPE_SECURITY_NOTICE,
        **PROTOTYPE_SECURITY_FLAGS,
        'witness_mode': 'local-hmac-v1',
        'logged_at': datetime.now(timezone.utc).isoformat(),
        'bundle_id': bundle_path.name,
        'sequence_number': sequence_number,
        'bundle_fingerprint_sha256': bindings.get('bundle_fingerprint_sha256'),
        'artifact_bindings_sha256': sha256_file(bundle_path / 'artifact_bindings.json') if (bundle_path / 'artifact_bindings.json').exists() else None,
        'manifest_sha256': sha256_file(bundle_path / 'manifest.json') if (bundle_path / 'manifest.json').exists() else None,
        'attestation_sha256': sha256_file(bundle_path / 'attestation.json') if (bundle_path / 'attestation.json').exists() else None,
        'verification_receipts_sha256': sha256_file(Path(verification_receipts_path)),
        'transparency_entry_hash': transparency_record.get('entry_hash'),
        'transparency_sequence_number': transparency_record.get('sequence_number'),
        'witnessed_all_verifiers_passed': json.loads(Path(verification_receipts_path).read_text(encoding='utf-8')).get('all_verifiers_passed'),
        'previous_entry_hash': previous_entry_hash,
    }
    entry['entry_hash'] = _entry_hash(entry)
    return entry


def build_witness_checkpoint(*, bundle_dir: str | Path, entries: list[dict[str, Any]]) -> dict[str, Any]:
    log_path = witness_log_path(bundle_dir)
    _, key_id = _witness_secret()
    payload = {
        'checkpoint_version': '0.1.0',
        'security_notice': PROTOTYPE_SECURITY_NOTICE,
        **PROTOTYPE_SECURITY_FLAGS,
        'mode': 'local-hmac-v1',
        'key_id': key_id,
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'log_file': WITNESS_LOG_FILE,
        'log_sha256': sha256_file(log_path) if log_path.exists() else None,
        'entry_count': len(entries),
        'head_entry_hash': entries[-1].get('entry_hash') if entries else None,
        'note': 'PoC local witness checkpoint. Replace with external witness publication in a later phase.',
    }
    payload['signature'] = _sign_payload(payload)
    payload['algorithm'] = 'hmac-sha256'
    return payload


def verify_witness_checkpoint(checkpoint_doc: dict[str, Any], *, log_path: str | Path) -> dict[str, Any]:
    log_file = Path(log_path)
    notes: list[str] = []
    payload = {k: v for k, v in checkpoint_doc.items() if k not in {'signature', 'algorithm'}}
    expected_signature = _sign_payload(payload)
    signature_matches = hmac.compare_digest(checkpoint_doc.get('signature', ''), expected_signature)
    if not signature_matches:
        notes.append('Witness checkpoint signature mismatch.')
    log_sha_matches = True
    if log_file.exists():
        expected_log_sha = sha256_file(log_file)
        log_sha_matches = checkpoint_doc.get('log_sha256') == expected_log_sha
        if not log_sha_matches:
            notes.append('Witness checkpoint log_sha256 does not match the current witness log file.')
    else:
        log_sha_matches = False
        notes.append('Witness log file is missing.')
    return {
        'verified': bool(signature_matches and log_sha_matches),
        'signature_matches': signature_matches,
        'log_sha256_matches': log_sha_matches,
        'verification_notes': notes,
    }


def build_published_checkpoint_reference(*, bundle_dir: str | Path, checkpoint_doc: dict[str, Any]) -> dict[str, Any]:
    checkpoint_id = sha256_text(_canonical_json(checkpoint_doc))
    published_payload = {
        'published_checkpoint_version': '0.1.0',
        'security_notice': PROTOTYPE_SECURITY_NOTICE,
        **PROTOTYPE_SECURITY_FLAGS,
        'published_at': datetime.now(timezone.utc).isoformat(),
        'publication_channel': 'local-static-file-placeholder',
        'checkpoint_id': checkpoint_id,
        'checkpoint_entry_count': checkpoint_doc.get('entry_count'),
        'checkpoint_head_entry_hash': checkpoint_doc.get('head_entry_hash'),
        'note': 'PoC local published checkpoint reference. Replace with an external static or transparency publication channel in a later phase.',
    }
    published_payload['reference_sha256'] = sha256_text(_canonical_json(published_payload))
    return published_payload


def append_witness_log(*, bundle_dir: str | Path, verification_receipts_path: str | Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    bundle_path = Path(bundle_dir)
    log_dir = witness_dir_from_bundle(bundle_path)
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = witness_log_path(bundle_path)
    entries = _load_entries(log_path)
    chain_status = verify_witness_chain(entries)
    if entries and not chain_status.get('verified'):
        raise ValueError('Witness log chain is already broken; refusing to append a new bundle entry.')

    entry = build_witness_entry(
        bundle_dir=bundle_path,
        verification_receipts_path=verification_receipts_path,
        previous_entry_hash=entries[-1].get('entry_hash') if entries else None,
        sequence_number=len(entries) + 1,
    )
    with log_path.open('a', encoding='utf-8') as fh:
        fh.write(json.dumps(entry, sort_keys=True) + '\n')
    entries.append(entry)
    checkpoint = build_witness_checkpoint(bundle_dir=bundle_path, entries=entries)
    witness_checkpoint_path(bundle_path).write_text(json.dumps(checkpoint, indent=2), encoding='utf-8')
    published_reference = build_published_checkpoint_reference(bundle_dir=bundle_path, checkpoint_doc=checkpoint)
    published_checkpoint_path(bundle_path).write_text(json.dumps(published_reference, indent=2), encoding='utf-8')
    return entry, checkpoint, published_reference


def verify_bundle_witness(bundle_dir: str | Path) -> dict[str, Any]:
    bundle_path = Path(bundle_dir)
    log_path = witness_log_path(bundle_path)
    checkpoint_path = witness_checkpoint_path(bundle_path)
    published_path = published_checkpoint_path(bundle_path)
    notes: list[str] = []

    log_present = log_path.exists()
    checkpoint_present = checkpoint_path.exists()
    published_checkpoint_present = published_path.exists()
    entries = _load_entries(log_path) if log_present else []
    chain_status = verify_witness_chain(entries) if log_present else {
        'verified': False,
        'entry_count': 0,
        'head_entry_hash': None,
        'verification_notes': ['Witness log file is missing.'],
    }
    notes.extend([n for n in chain_status.get('verification_notes', []) if n not in notes])

    checkpoint_doc = json.loads(checkpoint_path.read_text(encoding='utf-8')) if checkpoint_present else {}
    checkpoint_status = verify_witness_checkpoint(checkpoint_doc, log_path=log_path) if checkpoint_present else {
        'verified': False,
        'signature_matches': False,
        'log_sha256_matches': False,
        'verification_notes': ['Witness checkpoint file is missing.'],
    }
    notes.extend([n for n in checkpoint_status.get('verification_notes', []) if n not in notes])

    published_doc = json.loads(published_path.read_text(encoding='utf-8')) if published_checkpoint_present else {}
    published_checkpoint_matches = True
    if published_doc:
        expected_checkpoint_id = sha256_text(_canonical_json(checkpoint_doc)) if checkpoint_doc else None
        published_checkpoint_matches = published_doc.get('checkpoint_id') == expected_checkpoint_id
        if not published_checkpoint_matches:
            notes.append('Published checkpoint reference does not match the active witness checkpoint.')
    else:
        published_checkpoint_matches = False
        notes.append('Published checkpoint reference file is missing.')

    matching_entries = [entry for entry in entries if entry.get('bundle_id') == bundle_path.name]
    bundle_included = len(matching_entries) > 0
    if not bundle_included:
        notes.append('Bundle ID is not present in the witness log.')
    elif len(matching_entries) > 1:
        notes.append('Multiple witness log entries found for the same bundle ID.')
    matching_entry = matching_entries[-1] if matching_entries else {}

    entry_matches_current_bundle = True
    if matching_entry:
        current_bundle_fingerprint = None
        if (bundle_path / 'artifact_bindings.json').exists():
            current_bundle_fingerprint = json.loads((bundle_path / 'artifact_bindings.json').read_text(encoding='utf-8')).get('bundle_fingerprint_sha256')
        comparisons = [
            ('bundle_fingerprint_sha256', current_bundle_fingerprint),
            ('artifact_bindings_sha256', sha256_file(bundle_path / 'artifact_bindings.json') if (bundle_path / 'artifact_bindings.json').exists() else None),
            ('manifest_sha256', sha256_file(bundle_path / 'manifest.json') if (bundle_path / 'manifest.json').exists() else None),
            ('attestation_sha256', sha256_file(bundle_path / 'attestation.json') if (bundle_path / 'attestation.json').exists() else None),
            ('verification_receipts_sha256', sha256_file(bundle_path / VERIFICATION_RECEIPTS_FILE) if (bundle_path / VERIFICATION_RECEIPTS_FILE).exists() else None),
        ]
        transparency_record = json.loads((bundle_path / 'transparency_record.json').read_text(encoding='utf-8')) if (bundle_path / 'transparency_record.json').exists() else {}
        if matching_entry.get('transparency_entry_hash') != transparency_record.get('entry_hash'):
            entry_matches_current_bundle = False
            notes.append('Witness entry transparency_entry_hash does not match the current transparency record.')
        for key, expected_value in comparisons:
            if matching_entry.get(key) != expected_value:
                entry_matches_current_bundle = False
                notes.append(f'Witness log entry field {key} does not match the current bundle state.')

    verification_receipts_path = bundle_path / VERIFICATION_RECEIPTS_FILE
    receipts_snapshot_matches = True
    verifier_receipts_match = True
    if verification_receipts_path.exists():
        try:
            stored_receipts = json.loads(verification_receipts_path.read_text(encoding='utf-8'))
            recomputed_receipts = build_verification_receipts(bundle_path)
            verifier_receipts_match = stored_receipts.get('receipts') == recomputed_receipts.get('receipts') and stored_receipts.get('all_verifiers_passed') == recomputed_receipts.get('all_verifiers_passed')
            if not verifier_receipts_match:
                notes.append('verification_receipts.json does not match the current multi-verifier recomputation.')
        except Exception:
            verifier_receipts_match = False
            notes.append('verification_receipts.json could not be parsed.')
    else:
        verifier_receipts_match = False
        notes.append('verification_receipts.json is missing.')

    snapshot_entry_path = bundle_path / WITNESS_RECORD_FILE
    snapshot_checkpoint_path = bundle_path / WITNESS_CHECKPOINT_SNAPSHOT_FILE
    snapshot_published_path = bundle_path / PUBLISHED_CHECKPOINT_REFERENCE_FILE
    if snapshot_entry_path.exists() and matching_entry:
        try:
            snapshot_entry = json.loads(snapshot_entry_path.read_text(encoding='utf-8'))
            if snapshot_entry != matching_entry:
                receipts_snapshot_matches = False
                notes.append('Bundle witness_record.json does not match the active witness log entry.')
        except Exception:
            receipts_snapshot_matches = False
            notes.append('Bundle witness_record.json could not be parsed.')
    if snapshot_checkpoint_path.exists() and checkpoint_doc:
        try:
            snapshot_checkpoint = json.loads(snapshot_checkpoint_path.read_text(encoding='utf-8'))
            if snapshot_checkpoint != checkpoint_doc:
                receipts_snapshot_matches = False
                notes.append('Bundle witness_checkpoint_snapshot.json does not match the active witness checkpoint.')
        except Exception:
            receipts_snapshot_matches = False
            notes.append('Bundle witness_checkpoint_snapshot.json could not be parsed.')
    if snapshot_published_path.exists() and published_doc:
        try:
            snapshot_published = json.loads(snapshot_published_path.read_text(encoding='utf-8'))
            if snapshot_published != published_doc:
                receipts_snapshot_matches = False
                notes.append('Bundle published_checkpoint_reference.json does not match the active published checkpoint reference.')
        except Exception:
            receipts_snapshot_matches = False
            notes.append('Bundle published_checkpoint_reference.json could not be parsed.')

    verified = bool(
        log_present and checkpoint_present and published_checkpoint_present and
        chain_status.get('verified') and checkpoint_status.get('verified') and
        bundle_included and entry_matches_current_bundle and verifier_receipts_match and
        receipts_snapshot_matches and published_checkpoint_matches
    )

    stored_receipts = json.loads(verification_receipts_path.read_text(encoding='utf-8')) if verification_receipts_path.exists() else {}
    passed = sum(1 for r in stored_receipts.get('receipts', []) if r.get('verified'))
    total = len(stored_receipts.get('receipts', []))
    return {
        'log_present': log_present,
        'checkpoint_present': checkpoint_present,
        'published_checkpoint_present': published_checkpoint_present,
        'chain_verified': bool(chain_status.get('verified')),
        'checkpoint_verified': bool(checkpoint_status.get('verified')),
        'published_checkpoint_matches': published_checkpoint_matches,
        'bundle_included': bundle_included,
        'entry_matches_current_bundle': entry_matches_current_bundle,
        'verifier_receipts_match': verifier_receipts_match,
        'bundle_snapshot_matches': receipts_snapshot_matches,
        'entry_count': chain_status.get('entry_count', 0),
        'head_entry_hash': chain_status.get('head_entry_hash'),
        'included_sequence_number': matching_entry.get('sequence_number') if matching_entry else None,
        'included_entry_hash': matching_entry.get('entry_hash') if matching_entry else None,
        'checkpoint': checkpoint_status,
        'passed_verifiers': passed,
        'total_verifiers': total,
        'verification_notes': notes,
        'verified': verified,
    }
