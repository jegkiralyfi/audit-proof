from __future__ import annotations

import json

from packages.core.models import Certificate



def certificate_to_json(certificate: Certificate) -> str:
    return json.dumps(certificate.model_dump(mode="json"), indent=2, sort_keys=True)
