from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from packages.core.hashing import sha256_file, sha256_text
from packages.core.security import PROTOTYPE_SECURITY_FLAGS, PROTOTYPE_SECURITY_NOTICE

DERIVED_BUNDLE_ARTIFACTS = {
    'artifact_bindings.json',
    'attestation.json',
    'manifest.json',
    'report.html',
    'transparency_record.json',
    'transparency_checkpoint_snapshot.json',
    'verification_receipts.json',
    'witness_record.json',
    'witness_checkpoint_snapshot.json',
    'published_checkpoint_reference.json',
}


def iter_canonical_bundle_artifacts(bundle_dir: str | Path) -> list[Path]:
    bundle_path = Path(bundle_dir)
    return sorted(
        path
        for path in bundle_path.rglob('*')
        if path.is_file() and path.relative_to(bundle_path).as_posix() not in DERIVED_BUNDLE_ARTIFACTS
    )


def _manifest_rows(bundle_path: Path, artifacts: Iterable[Path]) -> list[dict]:
    rows = []
    for path in artifacts:
        rel = path.relative_to(bundle_path).as_posix()
        rows.append({
            'path': rel,
            'sha256': sha256_file(path),
            'size_bytes': path.stat().st_size,
        })
    return rows


def build_manifest(bundle_dir: str | Path) -> dict:
    bundle_path = Path(bundle_dir)
    artifacts = _manifest_rows(bundle_path, iter_canonical_bundle_artifacts(bundle_path))
    return {
        'manifest_version': '0.2.0',
        'artifact_scope': 'canonical-bundle-artifacts',
        'excluded_paths': sorted(DERIVED_BUNDLE_ARTIFACTS),
        'security_notice': PROTOTYPE_SECURITY_NOTICE,
        **PROTOTYPE_SECURITY_FLAGS,
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'bundle_dir': str(bundle_path),
        'artifacts': artifacts,
    }


def build_artifact_bindings(manifest: dict, *, bundle_id: str) -> dict:
    by_name = {}
    for entry in manifest.get('artifacts', []):
        path = entry.get('path', '')
        key = Path(path).name
        by_name[key] = {
            'path': path,
            'sha256': entry.get('sha256', ''),
            'size_bytes': int(entry.get('size_bytes', 0) or 0),
        }
    return {
        'artifact_version': '0.2.0',
        'artifact_scope': manifest.get('artifact_scope', 'canonical-bundle-artifacts'),
        'excluded_paths': list(manifest.get('excluded_paths', [])),
        'security_notice': PROTOTYPE_SECURITY_NOTICE,
        **PROTOTYPE_SECURITY_FLAGS,
        'bundle_id': bundle_id,
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'bundle_fingerprint_sha256': bundle_fingerprint(by_name),
        'bindings': by_name,
    }


def bundle_fingerprint(bindings: dict[str, dict] | None) -> str:
    rows = []
    for key, value in sorted((bindings or {}).items()):
        rows.append(f"{key}	{value.get('path','')}	{value.get('sha256','')}	{int(value.get('size_bytes', 0) or 0)}")
    return sha256_text('\n'.join(rows))
