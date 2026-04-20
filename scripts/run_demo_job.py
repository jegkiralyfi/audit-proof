from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packages.certificates.builder import build_certificate
from packages.certificates.serializer import certificate_to_json
from packages.ingest.doi import enrich_metadata_with_doi
from packages.ingest.parser import parse_path_to_document
from packages.routing.domain_registry import get_domain_policy
from packages.routing.domain_router import get_workflow
from packages.storage.registry import persist_bundle

EXAMPLE = ROOT / "examples" / "psychology_paper_01.txt"
OUTPUT_DIR = ROOT / "examples" / "example_certificates"


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    metadata, notes = enrich_metadata_with_doi({"title": "Example quantitative experimental paper"})
    document = parse_path_to_document(EXAMPLE, metadata=metadata)
    policy = get_domain_policy("quant_experimental")
    workflow = get_workflow("quant_experimental")
    checks = workflow.run(document)
    certificate, html_report = build_certificate(document=document, domain="quant_experimental", checks_run=checks, policy=policy, notes=' '.join(notes))
    persist_bundle(document=document, certificate=certificate, html_report=html_report)

    (OUTPUT_DIR / "example_certificate.json").write_text(certificate_to_json(certificate), encoding="utf-8")
    (OUTPUT_DIR / "example_report.html").write_text(html_report, encoding="utf-8")
    print("Wrote example certificate artifacts to", OUTPUT_DIR)


if __name__ == "__main__":
    main()
