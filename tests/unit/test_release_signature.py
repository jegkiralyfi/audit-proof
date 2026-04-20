from __future__ import annotations

import json
from pathlib import Path

from packages.provenance.release_signing import build_release_signature, generate_keypair, verify_release_signature
from packages.provenance.trust import build_release_manifest, build_build_provenance, build_issuer_trust_profile


def test_release_signature_and_trust_upgrade(tmp_path: Path) -> None:
    (tmp_path / 'README.md').write_text('demo', encoding='utf-8')
    (tmp_path / 'app.py').write_text('print("hi")\n', encoding='utf-8')
    keys_dir = tmp_path / 'keys'
    private_key = keys_dir / 'release_signing_private_key.pem'
    public_key = keys_dir / 'release_signing_public_key.pem'
    generate_keypair(private_path=private_key, public_path=public_key)

    manifest = build_release_manifest(tmp_path, repo_url='https://example.test/repo', release_channel='stable', release_tag='v-test', release_commit='abc123')
    manifest_path = tmp_path / 'release_manifest.json'
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding='utf-8')

    signature = build_release_signature(
        manifest=manifest,
        manifest_path=manifest_path,
        private_key_path=private_key,
        public_key_path=public_key,
        issuer='test-signer',
    )
    signature_path = tmp_path / 'release_manifest.signature.json'
    signature_path.write_text(json.dumps(signature, indent=2), encoding='utf-8')

    verification = verify_release_signature(
        manifest=manifest,
        manifest_path=manifest_path,
        signature_doc=signature,
        public_key_path=public_key,
    )
    assert verification['verified'] is True

    provenance = build_build_provenance(tmp_path)
    trust = build_issuer_trust_profile(provenance)

    assert provenance.repo_matches_release is True
    assert provenance.release_signature_verified is True
    assert trust.trust_tier == 'self_hosted_release_matched_with_provenance'
