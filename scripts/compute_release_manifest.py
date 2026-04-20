from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from packages.provenance.trust import export_release_manifest, project_root_from_any


def main() -> int:
    parser = argparse.ArgumentParser(description='Compute release_manifest.json for the current source tree.')
    parser.add_argument('--root', type=str, default='.', help='Project root (defaults to current directory).')
    args = parser.parse_args()
    root = project_root_from_any(Path(args.root))
    out_path = export_release_manifest(root)
    print(f'Wrote release manifest: {out_path}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
