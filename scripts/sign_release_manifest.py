from __future__ import annotations

import argparse
import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from packages.provenance.release_signing import build_release_signature, signing_private_key_path, signing_public_key_path
from packages.provenance.trust import load_release_manifest, project_root_from_any


def main() -> None:
    parser = argparse.ArgumentParser(description='Sign release_manifest.json with an Ed25519 key.')
    parser.add_argument('--root', type=str, default='.')
    parser.add_argument('--issuer', type=str, default='audit-proof-release-signer')
    args = parser.parse_args()

    root = project_root_from_any(args.root)
    manifest = load_release_manifest(root)
    if manifest is None:
        raise SystemExit('release_manifest.json not found. Run compute_release_manifest.py first.')

    private_key = signing_private_key_path(root)
    public_key = signing_public_key_path(root)
    if not private_key.exists():
        raise SystemExit(f'Private signing key not found: {private_key}')
    if not public_key.exists():
        raise SystemExit(f'Public signing key not found: {public_key}')

    signature = build_release_signature(
        manifest=manifest,
        manifest_path=root / 'release_manifest.json',
        private_key_path=private_key,
        public_key_path=public_key,
        issuer=args.issuer,
    )
    out = root / 'release_manifest.signature.json'
    out.write_text(json.dumps(signature, indent=2), encoding='utf-8')
    print(out)


if __name__ == '__main__':
    main()
