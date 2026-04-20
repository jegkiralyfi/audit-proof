from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from packages.core.models import BuildProvenanceArtifact


def main() -> int:
    out_path = PROJECT_ROOT / 'schemas' / 'build_provenance.schema.json'
    out_path.write_text(json.dumps(BuildProvenanceArtifact.model_json_schema(), indent=2), encoding='utf-8')
    print(f'Wrote {out_path}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
