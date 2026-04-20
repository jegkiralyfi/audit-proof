from __future__ import annotations

import json
from pathlib import Path

from packages.certificates.builder import build_certificate
from packages.ingest.parser import parse_text_to_document
from packages.provenance.transparency_log import transparency_log_path, verify_bundle_transparency
from packages.routing.domain_registry import get_domain_policy
from packages.routing.domain_router import get_workflow
from packages.storage.registry import persist_bundle


def _issue_demo_bundle() -> Path:
    document = parse_text_to_document(
        text='Methods: We enrolled 120 participants and report a statistically significant treatment effect. Results: p < 0.05.',
        source_name='unit-test',
        metadata={'title': 'Transparency demo'},
    )
    domain = 'quant_experimental'
    policy = get_domain_policy(domain)
    workflow = get_workflow(domain)
    checks = workflow.run(document, context={})
    certificate, html_report = build_certificate(document=document, domain=domain, checks_run=checks, policy=policy)
    artifacts = persist_bundle(document=document, certificate=certificate, html_report=html_report)
    return Path(artifacts.bundle_dir)


def test_transparency_log_inclusion_passes_for_fresh_bundle(tmp_path: Path, monkeypatch) -> None:
    from packages.storage import local_store, registry

    bundle_root = tmp_path / '.artifacts' / 'bundles'
    monkeypatch.setattr(local_store, 'DEFAULT_BUNDLE_ROOT', bundle_root)
    monkeypatch.setattr(registry, 'DEFAULT_BUNDLE_ROOT', bundle_root)

    bundle_dir = _issue_demo_bundle()
    payload = verify_bundle_transparency(bundle_dir)

    assert payload['verified'] is True
    assert payload['bundle_included'] is True
    assert payload['entry_matches_current_bundle'] is True
    assert payload['checkpoint_verified'] is True


def test_transparency_log_detects_log_tamper(tmp_path: Path, monkeypatch) -> None:
    from packages.storage import local_store, registry

    bundle_root = tmp_path / '.artifacts' / 'bundles'
    monkeypatch.setattr(local_store, 'DEFAULT_BUNDLE_ROOT', bundle_root)
    monkeypatch.setattr(registry, 'DEFAULT_BUNDLE_ROOT', bundle_root)

    bundle_dir = _issue_demo_bundle()
    log_path = transparency_log_path(bundle_dir)
    entries = [json.loads(line) for line in log_path.read_text(encoding='utf-8').splitlines() if line.strip()]
    entries[0]['trust_tier'] = 'tampered-tier'
    log_path.write_text('\n'.join(json.dumps(entry) for entry in entries) + '\n', encoding='utf-8')

    payload = verify_bundle_transparency(bundle_dir)
    assert payload['verified'] is False
    assert payload['chain_verified'] is False or payload['entry_matches_current_bundle'] is False
