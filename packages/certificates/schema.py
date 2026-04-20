from __future__ import annotations

import json
from pathlib import Path

from packages.core.models import Certificate


def validate_certificate(certificate: Certificate) -> Certificate:
    return Certificate.model_validate(certificate.model_dump())


def export_certificate_json_schema(output_path: str | Path) -> Path:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    schema = Certificate.model_json_schema()
    output.write_text(json.dumps(schema, indent=2), encoding='utf-8')
    return output
