from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packages.core.models import RepositoryMetadataArtifact


if __name__ == '__main__':
    out = ROOT / 'schemas' / 'repository_metadata.schema.json'
    schema = RepositoryMetadataArtifact.model_json_schema()
    out.write_text(json.dumps(schema, indent=2), encoding='utf-8')
    print(out)
