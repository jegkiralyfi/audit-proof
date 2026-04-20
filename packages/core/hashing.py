from __future__ import annotations

import hashlib
from pathlib import Path


def sha256_bytes(data: bytes) -> str:
    return f"sha256:{hashlib.sha256(data).hexdigest()}"



def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))



def sha256_file(path: str | Path) -> str:
    p = Path(path)
    return sha256_bytes(p.read_bytes())
