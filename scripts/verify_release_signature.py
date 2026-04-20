from __future__ import annotations

import argparse
import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from packages.provenance.release_signing import signing_public_key_path
from packages.provenance.trust import build_release_verification, project_root_from_any


def main() -> None:
    parser = argparse.ArgumentParser(description='Verify release_manifest.signature.json against the current release_manifest.json and public key.')
    parser.add_argument('--root', type=str, default='.')
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()

    root = project_root_from_any(args.root)
    verification = build_release_verification(root)
    if args.write:
        out = root / 'release_verification.json'
        out.write_text(json.dumps(verification, indent=2), encoding='utf-8')
        print(out)
    else:
        print(json.dumps(verification, indent=2))


if __name__ == '__main__':
    main()
