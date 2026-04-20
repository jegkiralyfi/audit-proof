from pathlib import Path

from fastapi.testclient import TestClient

from apps.api.main import app


def _patch_bundle_root(tmp_path, monkeypatch):
    from packages.storage import local_store, registry

    bundle_root = tmp_path / '.artifacts' / 'bundles'
    monkeypatch.setattr(local_store, 'DEFAULT_BUNDLE_ROOT', bundle_root)
    monkeypatch.setattr(registry, 'DEFAULT_BUNDLE_ROOT', bundle_root)
    return bundle_root


def test_formal_proof_text_intake_creates_semantic_audit_bundle(tmp_path, monkeypatch):
    bundle_root = _patch_bundle_root(tmp_path, monkeypatch)
    client = TestClient(app)
    text = Path('tests/fixtures/formal_proof/lean_with_true_fake.txt').read_text(encoding='utf-8')

    response = client.post('/intake/text', json={
        'domain': 'formal_proof',
        'title': 'Lean artifact with vacuous placeholders',
        'text': text,
    })
    assert response.status_code == 200
    payload = response.json()
    assert payload['certificate']['domain'] == 'formal_proof'
    assert payload['certificate']['issuance']['status'] == 'withheld'
    bundle_id = payload['artifacts']['bundle_id']
    bundle_dir = bundle_root / bundle_id
    assert (bundle_dir / 'formal_semantic_audit.json').exists()
