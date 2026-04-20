from __future__ import annotations

import json

from packages.core.hashing import sha256_text
from packages.core.models import Certificate



def compute_certificate_hash(certificate: Certificate) -> str:
    payload = certificate.model_dump(mode="json")
    payload["cert_hash"] = None
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256_text(canonical)
