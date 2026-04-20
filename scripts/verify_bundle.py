from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from packages.provenance.verify_bundle import verify_bundle
from packages.storage.registry import DEFAULT_BUNDLE_ROOT


def main() -> None:
    parser = argparse.ArgumentParser(description='Verify one stored Audit-Proof bundle.')
    parser.add_argument('bundle', help='Bundle ID or bundle directory path')
    args = parser.parse_args()

    candidate = Path(args.bundle)
    bundle_dir = candidate if candidate.exists() else DEFAULT_BUNDLE_ROOT / args.bundle
    payload = verify_bundle(bundle_dir)
    print(json.dumps(payload, indent=2))


if __name__ == '__main__':
    main()
