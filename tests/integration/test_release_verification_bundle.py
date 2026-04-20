from __future__ import annotations

import json
from pathlib import Path

from packages.certificates.builder import build_certificate
from packages.ingest.parser import parse_text_to_document
from packages.routing.domain_registry import get_domain_policy
from packages.routing.domain_router import get_workflow
from packages.storage.registry import persist_bundle


def test_bundle_contains_release_verification_artifacts(tmp_path: Path) -> None:
    text = (
        'Methods\nSample size N = 40. Participants were randomly assigned to a control group and a treatment group.\n'
        'Results\nCohen\'s d = 0.40, p = .03, 95% CI [0.10, 0.70].\n'
        'References\n[1] Example, A. (2020). https://doi.org/10.1000/example\n'
    )
    document = parse_text_to_document(text=text, source_name='test.txt', metadata={})
    policy = get_domain_policy('quant_experimental')
    workflow = get_workflow('quant_experimental')
    checks = workflow.run(document)
    cert, report = build_certificate(document=document, domain='quant_experimental', checks_run=checks, policy=policy, notes='')
    artifacts = persist_bundle(document=document, certificate=cert, html_report=report)
    assert artifacts.release_manifest_path is not None
    assert artifacts.release_signature_path is not None
    assert artifacts.release_verification_path is not None
    payload = json.loads(Path(artifacts.release_verification_path).read_text(encoding='utf-8'))
    assert 'verified' in payload
