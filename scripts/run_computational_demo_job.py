from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from packages.certificates.builder import build_certificate
from packages.certificates.serializer import certificate_to_json
from packages.ingest.parser import parse_path_to_document
from packages.routing.domain_registry import get_domain_policy
from packages.routing.domain_router import get_workflow
from packages.storage.registry import persist_bundle

EXAMPLE = ROOT / "examples" / "computational_paper_01.txt"
OUTPUT_DIR = ROOT / "examples" / "example_certificates"


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    metadata = {"title": "Example computational paper", "metadata_source": "example-fixture"}
    document = parse_path_to_document(EXAMPLE, metadata=metadata)
    policy = get_domain_policy("computational")
    workflow = get_workflow("computational")
    checks = workflow.run(document)
    certificate, html_report = build_certificate(
        document=document,
        domain="computational",
        checks_run=checks,
        policy=policy,
        notes="Computational demo artifact generated from example fixture.",
    )
    persist_bundle(document=document, certificate=certificate, html_report=html_report)

    (OUTPUT_DIR / "computational_example_certificate.json").write_text(certificate_to_json(certificate), encoding="utf-8")
    (OUTPUT_DIR / "computational_example_report.html").write_text(html_report, encoding="utf-8")
    print("Wrote computational example certificate artifacts to", OUTPUT_DIR)


if __name__ == "__main__":
    main()
