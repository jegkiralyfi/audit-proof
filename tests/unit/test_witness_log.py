from __future__ import annotations

from pathlib import Path

from packages.certificates.builder import build_certificate
from packages.ingest.parser import parse_text_to_document
from packages.provenance.verify_bundle import verify_bundle
from packages.provenance.witness_log import verify_bundle_witness
from packages.routing.domain_registry import get_domain_policy
from packages.routing.domain_router import get_workflow
from packages.storage.registry import persist_bundle


def _issue_demo_bundle() -> Path:
    document = parse_text_to_document(
        text='Methods: randomized control group, effect size, and sample size are reported. Results: p < 0.05.',
        source_name='witness-test',
        metadata={'title': 'Witness demo'},
    )
    domain = 'quant_experimental'
    policy = get_domain_policy(domain)
    workflow = get_workflow(domain)
    checks = workflow.run(document, context={})
    certificate, html_report = build_certificate(document=document, domain=domain, checks_run=checks, policy=policy)
    artifacts = persist_bundle(document=document, certificate=certificate, html_report=html_report)
    return Path(artifacts.bundle_dir)


def test_witness_log_and_receipts_are_verified(tmp_path: Path, monkeypatch) -> None:
    from packages.storage import local_store, registry

    bundle_root = tmp_path / '.artifacts' / 'bundles'
    monkeypatch.setattr(local_store, 'DEFAULT_BUNDLE_ROOT', bundle_root)
    monkeypatch.setattr(registry, 'DEFAULT_BUNDLE_ROOT', bundle_root)

    bundle_dir = _issue_demo_bundle()

    assert (bundle_dir / 'verification_receipts.json').exists()
    assert (bundle_dir / 'witness_record.json').exists()
    assert (bundle_dir / 'witness_checkpoint_snapshot.json').exists()
    assert (bundle_dir / 'published_checkpoint_reference.json').exists()

    witness = verify_bundle_witness(bundle_dir)
    assert witness['verified'] is True
    assert witness['passed_verifiers'] == witness['total_verifiers']

    full = verify_bundle(bundle_dir)
    assert full['witness_verified'] is True
