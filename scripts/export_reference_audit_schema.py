from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packages.core.models import ReferenceAuditArtifact

OUTPUT = ROOT / 'schemas' / 'reference_audit.schema.json'

if __name__ == '__main__':
    OUTPUT.write_text(json.dumps(ReferenceAuditArtifact.model_json_schema(), indent=2), encoding='utf-8')
    print(OUTPUT)
