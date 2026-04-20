from pathlib import Path

from fastapi.testclient import TestClient

from apps.api.main import app


def _patch_bundle_root(tmp_path, monkeypatch):
    from packages.storage import local_store, registry

    bundle_root = tmp_path / ".artifacts" / "bundles"
    monkeypatch.setattr(local_store, "DEFAULT_BUNDLE_ROOT", bundle_root)
    monkeypatch.setattr(registry, "DEFAULT_BUNDLE_ROOT", bundle_root)
    return bundle_root


def test_file_intake_end_to_end_registry_roundtrip(tmp_path, monkeypatch):
    bundle_root = _patch_bundle_root(tmp_path, monkeypatch)
    client = TestClient(app)
    file_path = Path('examples/computational_paper_01.txt')

    with file_path.open('rb') as handle:
        response = client.post(
            '/intake/file',
            data={'domain': 'computational', 'title': 'Computational E2E', 'llm_provider': 'heuristic'},
            files={'file': (file_path.name, handle, 'text/plain')},
        )
    assert response.status_code == 200
    payload = response.json()
    bundle_id = payload['artifacts']['bundle_id']
    assert (bundle_root / bundle_id / 'execution_plan.json').exists()

    detail = client.get(f'/registry/bundles/{bundle_id}')
    assert detail.status_code == 200
    detail_payload = detail.json()
    assert detail_payload['bundle_id'] == bundle_id
    assert detail_payload['certificate']['domain'] == 'computational'
