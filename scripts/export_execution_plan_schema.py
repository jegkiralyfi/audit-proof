from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packages.core.models import ExecutionPlanArtifact


def main() -> None:
    out = ROOT / 'schemas' / 'execution_plan.schema.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(ExecutionPlanArtifact.model_json_schema(), indent=2), encoding='utf-8')
    print(f'Wrote {out}')


if __name__ == '__main__':
    main()
