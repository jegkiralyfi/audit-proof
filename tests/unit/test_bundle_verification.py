from __future__ import annotations

from pathlib import Path

from packages.certificates.builder import build_certificate
from packages.ingest.parser import parse_text_to_document
from packages.provenance.verify_bundle import verify_bundle
from packages.routing.domain_registry import get_domain_policy
from packages.routing.domain_router import get_workflow
from packages.storage.registry import persist_bundle


def _issue_demo_bundle() -> tuple[Path, dict]:
    document = parse_text_to_document(
        text='Methods: We enrolled 120 participants and report a statistically significant treatment effect. Results: p < 0.05.',
        source_name='unit-test',
        metadata={'title': 'Verification demo'},
    )
    domain = 'quant_experimental'
    policy = get_domain_policy(domain)
    workflow = get_workflow(domain)
    checks = workflow.run(document, context={})
    certificate, html_report = build_certificate(document=document, domain=domain, checks_run=checks, policy=policy)
    artifacts = persist_bundle(document=document, certificate=certificate, html_report=html_report)
    return Path(artifacts.bundle_dir), certificate.model_dump(mode='json')


def test_verify_bundle_passes_for_fresh_bundle(tmp_path: Path, monkeypatch) -> None:
    from packages.storage import local_store, registry

    bundle_root = tmp_path / '.artifacts' / 'bundles'
    monkeypatch.setattr(local_store, 'DEFAULT_BUNDLE_ROOT', bundle_root)
    monkeypatch.setattr(registry, 'DEFAULT_BUNDLE_ROOT', bundle_root)

    bundle_dir, cert = _issue_demo_bundle()
    payload = verify_bundle(bundle_dir)

    assert payload['verified'] is True
    assert payload['trust_tier_matches'] is True
    assert payload['transparency_verified'] is True
    assert payload['stored_trust_tier'] == cert['issuer_trust_profile']['trust_tier']


def test_verify_bundle_detects_certificate_tamper(tmp_path: Path, monkeypatch) -> None:
    import json
    from packages.storage import local_store, registry

    bundle_root = tmp_path / '.artifacts' / 'bundles'
    monkeypatch.setattr(local_store, 'DEFAULT_BUNDLE_ROOT', bundle_root)
    monkeypatch.setattr(registry, 'DEFAULT_BUNDLE_ROOT', bundle_root)

    bundle_dir, _ = _issue_demo_bundle()
    certificate_path = bundle_dir / 'certificate.json'
    payload = json.loads(certificate_path.read_text(encoding='utf-8'))
    payload['issuance']['status'] = 'withheld'
    certificate_path.write_text(json.dumps(payload, indent=2), encoding='utf-8')

    verification = verify_bundle(bundle_dir)
    assert verification['verified'] is False
    assert verification['certificate_hash_matches_binding'] is False
