from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packages.llm.profiles import export_provider_profiles


def main() -> None:
    payload = export_provider_profiles()
    out = ROOT / 'schemas' / 'provider_profiles.json'
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f'Wrote {out}')


if __name__ == '__main__':
    main()
