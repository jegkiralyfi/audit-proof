from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from packages.provenance.trust import build_build_provenance, build_issuer_trust_profile, project_root_from_any


def main() -> int:
    parser = argparse.ArgumentParser(description='Verify whether the current runtime source matches the bundled stable release manifest.')
    parser.add_argument('--root', type=str, default='.', help='Project root (defaults to current directory).')
    args = parser.parse_args()
    root = project_root_from_any(Path(args.root))
    provenance = build_build_provenance(root)
    trust = build_issuer_trust_profile(provenance)
    payload = {
        'build_provenance': provenance.model_dump(mode='json'),
        'issuer_trust_profile': trust.model_dump(mode='json'),
    }
    print(json.dumps(payload, indent=2))
    return 0 if trust.repo_matches_release else 1


if __name__ == '__main__':
    raise SystemExit(main())
