from pathlib import Path

from fastapi.testclient import TestClient

from apps.api.main import app


def _patch_bundle_root(tmp_path, monkeypatch):
    from packages.storage import local_store, registry

    bundle_root = tmp_path / ".artifacts" / "bundles"
    monkeypatch.setattr(local_store, "DEFAULT_BUNDLE_ROOT", bundle_root)
    monkeypatch.setattr(registry, "DEFAULT_BUNDLE_ROOT", bundle_root)
    return bundle_root


def test_text_intake_end_to_end_creates_bundle(tmp_path, monkeypatch):
    bundle_root = _patch_bundle_root(tmp_path, monkeypatch)
    client = TestClient(app)
    text = Path('tests/fixtures/gold_sets/quant_experimental/qe_01_good_controlled.txt').read_text(encoding='utf-8')

    response = client.post('/intake/text', json={
        'domain': 'quant_experimental',
        'title': 'E2E quant paper',
        'text': text,
        'llm_provider': 'heuristic',
    })
    assert response.status_code == 200
    payload = response.json()
    assert 'SANDBOX ONLY' in payload['message']
    assert payload['certificate']['domain'] == 'quant_experimental'
    bundle_id = payload['artifacts']['bundle_id']
    bundle_dir = bundle_root / bundle_id
    assert bundle_dir.exists()
    assert (bundle_dir / 'certificate.json').exists()
    assert (bundle_dir / 'artifact_bindings.json').exists()
    assert (bundle_dir / 'report.html').exists()
