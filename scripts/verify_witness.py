from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from packages.provenance.witness_log import verify_bundle_witness


def main() -> int:
    parser = argparse.ArgumentParser(description='Verify witness-log and published-checkpoint inclusion for an Audit-Proof bundle.')
    parser.add_argument('bundle_dir', type=Path)
    args = parser.parse_args()
    payload = verify_bundle_witness(args.bundle_dir)
    print(json.dumps(payload, indent=2))
    return 0 if payload.get('verified') else 1


if __name__ == '__main__':
    raise SystemExit(main())
