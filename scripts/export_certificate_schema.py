from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packages.certificates.schema import export_certificate_json_schema


if __name__ == '__main__':
    output = ROOT / 'schemas' / 'certificate.schema.json'
    export_certificate_json_schema(output)
    print(output)
