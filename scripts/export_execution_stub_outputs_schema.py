from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packages.core.models import ExecutionStubOutputsArtifact


def main() -> None:
    out = ROOT / "schemas" / "execution_stub_outputs.schema.json"
    out.write_text(json.dumps(ExecutionStubOutputsArtifact.model_json_schema(), indent=2), encoding="utf-8")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
