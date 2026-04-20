from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BUNDLE_ROOT = ROOT / '.artifacts' / 'bundles'


def ensure_bundle_dir(doc_hash: str) -> tuple[str, Path]:
    short_hash = doc_hash.split(':')[-1][:12]
    bundle_id = f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{short_hash}"
    bundle_dir = DEFAULT_BUNDLE_ROOT / bundle_id
    bundle_dir.mkdir(parents=True, exist_ok=True)
    return bundle_id, bundle_dir
