from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from packages.provenance.release_signing import generate_keypair
from packages.provenance.trust import project_root_from_any


def main() -> None:
    parser = argparse.ArgumentParser(description='Generate an Ed25519 release signing keypair for self-hosted release manifests.')
    parser.add_argument('--root', type=str, default='.')
    parser.add_argument('--private', type=str, default=None)
    parser.add_argument('--public', type=str, default=None)
    args = parser.parse_args()

    root = project_root_from_any(args.root)
    private_path = Path(args.private) if args.private else root / 'keys' / 'release_signing_private_key.pem'
    public_path = Path(args.public) if args.public else root / 'keys' / 'release_signing_public_key.pem'
    generate_keypair(private_path=private_path, public_path=public_path)
    print(public_path)


if __name__ == '__main__':
    main()
