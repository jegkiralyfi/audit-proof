from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from packages.core.hashing import sha256_bytes, sha256_file, sha256_text
from packages.core.models import BuildProvenanceArtifact, IssuerTrustProfile
from packages.provenance.release_signing import release_signature_path as release_signature_path_for, signing_public_key_path, verify_release_signature

IGNORE_DIRS = {
    '.git',
    '.artifacts',
    '__pycache__',
    '.pytest_cache',
    '.mypy_cache',
    '.ruff_cache',
    '.venv',
    'venv',
    'build',
    'dist',
}
IGNORE_FILES = {
    'release_manifest.json',
    'release_manifest.signature.json',
    'release_verification.json',
}
IGNORE_SUFFIXES = {'.pyc', '.pyo', '.zip'}
IGNORE_PATH_PREFIXES = {'examples/example_certificates', 'keys/release_signing_public_key.pem', 'keys/release_signing_private_key.pem'}


def project_root_from_any(path: str | Path) -> Path:
    p = Path(path).resolve()
    if p.is_file():
        p = p.parent
    for candidate in [p, *p.parents]:
        if (candidate / 'pyproject.toml').exists() or (candidate / 'README.md').exists():
            return candidate
    return p


def should_include_path(path: Path, root: Path) -> bool:
    rel_parts = path.relative_to(root).parts
    if any(part in IGNORE_DIRS for part in rel_parts[:-1]):
        return False
    rel = path.relative_to(root).as_posix()
    if any(rel == prefix or rel.startswith(prefix + '/') for prefix in IGNORE_PATH_PREFIXES):
        return False
    if path.name in IGNORE_FILES:
        return False
    if path.suffix in IGNORE_SUFFIXES:
        return False
    return True


def iter_source_files(root: str | Path) -> list[Path]:
    root_path = Path(root).resolve()
    return sorted(
        path
        for path in root_path.rglob('*')
        if path.is_file() and should_include_path(path, root_path)
    )


def compute_source_tree_hash(root: str | Path) -> tuple[str, list[dict[str, Any]]]:
    root_path = Path(root).resolve()
    file_rows: list[dict[str, Any]] = []
    digest_lines: list[str] = []
    for path in iter_source_files(root_path):
        rel = path.relative_to(root_path).as_posix()
        file_hash = sha256_file(path)
        size_bytes = path.stat().st_size
        file_rows.append({'path': rel, 'sha256': file_hash, 'size_bytes': size_bytes})
        digest_lines.append(f'{rel}\t{file_hash}\t{size_bytes}')
    tree_hash = sha256_text('\n'.join(digest_lines))
    return tree_hash, file_rows


def load_release_manifest(root: str | Path) -> dict[str, Any] | None:
    root_path = project_root_from_any(root)
    path = root_path / 'release_manifest.json'
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return None



def load_release_signature(root: str | Path) -> dict[str, Any] | None:
    root_path = project_root_from_any(root)
    path = release_signature_path_for(root_path)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return None


def build_release_verification(root: str | Path) -> dict[str, Any]:
    root_path = project_root_from_any(root)
    manifest = load_release_manifest(root_path)
    signature = load_release_signature(root_path)
    if manifest is None:
        return {
            'artifact_version': '0.1.0',
            'verified': False,
            'verifier_chain_present': False,
            'verification_notes': ['No release_manifest.json present at runtime.'],
        }
    public_key_path = signing_public_key_path(root_path)
    verification = verify_release_signature(
        manifest=manifest,
        manifest_path=root_path / 'release_manifest.json',
        signature_doc=signature or {},
        public_key_path=public_key_path,
    )
    verification['verifier_chain_present'] = bool(signature is not None and public_key_path.exists())
    return verification


def get_git_info(root: str | Path) -> dict[str, Any]:
    root_path = project_root_from_any(root)
    info = {
        'repo_present': False,
        'runtime_commit': None,
        'working_tree_clean': None,
        'branch': None,
    }
    if not (root_path / '.git').exists():
        return info
    info['repo_present'] = True
    try:
        commit = subprocess.check_output(['git', '-C', str(root_path), 'rev-parse', 'HEAD'], text=True).strip()
        info['runtime_commit'] = commit or None
    except Exception:
        pass
    try:
        branch = subprocess.check_output(['git', '-C', str(root_path), 'rev-parse', '--abbrev-ref', 'HEAD'], text=True).strip()
        info['branch'] = branch or None
    except Exception:
        pass
    try:
        status = subprocess.check_output(['git', '-C', str(root_path), 'status', '--porcelain'], text=True)
        info['working_tree_clean'] = not bool(status.strip())
    except Exception:
        pass
    return info


def build_release_manifest(
    root: str | Path,
    *,
    repo_url: str | None = None,
    release_channel: str = 'stable',
    release_tag: str | None = None,
    release_commit: str | None = None,
) -> dict[str, Any]:
    root_path = project_root_from_any(root)
    tree_hash, files = compute_source_tree_hash(root_path)
    return {
        'manifest_version': '0.1.0',
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'project_root': str(root_path),
        'repo_url': repo_url,
        'release_channel': release_channel,
        'release_tag': release_tag,
        'release_commit': release_commit,
        'source_tree_hash': tree_hash,
        'file_count': len(files),
        'files': files,
    }


def build_build_provenance(root: str | Path) -> BuildProvenanceArtifact:
    root_path = project_root_from_any(root)
    release_manifest = load_release_manifest(root_path)
    release_signature = load_release_signature(root_path)
    release_verification = build_release_verification(root_path)
    tree_hash, files = compute_source_tree_hash(root_path)
    git_info = get_git_info(root_path)
    release_manifest_hash = sha256_file(root_path / 'release_manifest.json') if (root_path / 'release_manifest.json').exists() else None
    repo_matches_release = bool(release_manifest and release_manifest.get('source_tree_hash') == tree_hash)
    notes: list[str] = []
    if release_manifest is None:
        notes.append('No release_manifest.json present at runtime.')
    elif not repo_matches_release:
        notes.append('Runtime source tree does not match release manifest source_tree_hash.')
    if release_signature is None:
        notes.append('No release_manifest.signature.json present at runtime.')
    if not release_verification.get('verified'):
        notes.extend([n for n in release_verification.get('verification_notes', []) if n not in notes])
    if git_info.get('working_tree_clean') is False:
        notes.append('Git working tree is not clean.')
    if git_info.get('repo_present') is False:
        notes.append('No local .git directory available; git cleanliness/commit checks are unavailable.')
    return BuildProvenanceArtifact(
        project_root=str(root_path),
        repo_url=(release_manifest or {}).get('repo_url'),
        release_channel=(release_manifest or {}).get('release_channel'),
        release_tag=(release_manifest or {}).get('release_tag'),
        release_commit=(release_manifest or {}).get('release_commit'),
        runtime_commit=git_info.get('runtime_commit'),
        source_tree_hash=tree_hash,
        release_manifest_hash=release_manifest_hash,
        release_manifest_signed=release_signature is not None,
        release_signature_verified=bool(release_verification.get('verified')),
        release_signature_key_id=(release_signature or {}).get('key_id'),
        verifier_chain_present=bool(release_verification.get('verifier_chain_present')),
        verifier_chain_verified=bool(release_verification.get('verified')),
        repo_matches_release=repo_matches_release,
        working_tree_clean=git_info.get('working_tree_clean'),
        git_repo_present=bool(git_info.get('repo_present')),
        branch=git_info.get('branch'),
        file_count=len(files),
        notes=notes,
    )


def classify_trust_tier(provenance: BuildProvenanceArtifact) -> str:
    if provenance.external_audit_present or provenance.red_team_certified:
        return 'audited_or_witnessed'
    if provenance.repo_matches_release and provenance.release_signature_verified and provenance.verifier_chain_present:
        return 'self_hosted_release_matched_with_provenance'
    if provenance.repo_matches_release:
        return 'self_hosted_repo_matched'
    return 'self_hosted_non_audited_self_claim'


def build_issuer_trust_profile(provenance: BuildProvenanceArtifact) -> IssuerTrustProfile:
    trust_tier = classify_trust_tier(provenance)
    notes = list(provenance.notes)
    if trust_tier == 'self_hosted_non_audited_self_claim':
        notes.append('Trust tier downgraded because runtime source could not be matched to the current stable release manifest.')
    elif trust_tier == 'self_hosted_repo_matched':
        notes.append('Runtime source matches the bundled stable release manifest. This is still self-hosted and not externally audited.')
    elif trust_tier == 'self_hosted_release_matched_with_provenance':
        notes.append('Runtime source matches the signed stable release manifest and the local verifier chain succeeded. This is stronger than repo-matched but still self-hosted and not externally audited.')
    return IssuerTrustProfile(
        issuer_mode='self_hosted',
        trust_tier=trust_tier,
        repo_url=provenance.repo_url,
        release_channel=provenance.release_channel,
        release_tag=provenance.release_tag,
        release_commit=provenance.release_commit,
        runtime_commit=provenance.runtime_commit,
        source_tree_hash=provenance.source_tree_hash,
        release_manifest_hash=provenance.release_manifest_hash,
        release_manifest_signed=provenance.release_manifest_signed,
        release_signature_verified=provenance.release_signature_verified,
        release_signature_key_id=provenance.release_signature_key_id,
        verifier_chain_present=provenance.verifier_chain_present,
        verifier_chain_verified=provenance.verifier_chain_verified,
        working_tree_clean=provenance.working_tree_clean,
        repo_matches_release=provenance.repo_matches_release,
        build_provenance_present=True,
        container_digest=provenance.container_digest,
        red_team_certified=provenance.red_team_certified,
        external_audit_present=provenance.external_audit_present,
        notes=notes,
    )


def export_release_manifest(path: str | Path | None = None) -> Path:
    root = project_root_from_any(path or Path.cwd())
    manifest = build_release_manifest(
        root,
        repo_url=os.getenv('AUDIT_PROOF_REPO_URL'),
        release_channel=os.getenv('AUDIT_PROOF_RELEASE_CHANNEL', 'stable'),
        release_tag=os.getenv('AUDIT_PROOF_RELEASE_TAG'),
        release_commit=os.getenv('AUDIT_PROOF_RELEASE_COMMIT'),
    )
    out_path = root / 'release_manifest.json'
    out_path.write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    return out_path
