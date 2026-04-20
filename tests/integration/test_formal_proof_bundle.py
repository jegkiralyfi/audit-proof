from pathlib import Path

from packages.certificates.builder import build_certificate
from packages.ingest.parser import parse_text_to_document
from packages.routing.domain_registry import get_domain_policy
from packages.routing.domain_router import get_workflow
from packages.storage.registry import persist_bundle


def test_formal_proof_bundle_contains_semantic_audit_artifact(tmp_path: Path, monkeypatch) -> None:
    from packages.storage import local_store, registry

    bundle_root = tmp_path / '.artifacts' / 'bundles'
    monkeypatch.setattr(local_store, 'DEFAULT_BUNDLE_ROOT', bundle_root)
    monkeypatch.setattr(registry, 'DEFAULT_BUNDLE_ROOT', bundle_root)

    text = Path('tests/fixtures/formal_proof/lean_with_true_fake.txt').read_text(encoding='utf-8')
    document = parse_text_to_document(text=text, source_name='fake.lean', metadata={})
    domain = 'formal_proof'
    policy = get_domain_policy(domain)
    workflow = get_workflow(domain)
    checks = workflow.run(document)
    certificate, html_report = build_certificate(document=document, domain=domain, checks_run=checks, policy=policy)
    artifacts = persist_bundle(document=document, certificate=certificate, html_report=html_report)

    assert artifacts.formal_semantic_audit_path is not None
    artifact_path = Path(artifacts.formal_semantic_audit_path)
    assert artifact_path.exists()
    payload = artifact_path.read_text(encoding='utf-8')
    assert 'build_clean_is_not_content_complete' in payload
