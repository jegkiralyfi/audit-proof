from pathlib import Path

from fastapi.testclient import TestClient

from apps.api.main import app


def _patch_bundle_root(tmp_path, monkeypatch):
    from packages.storage import local_store, registry

    bundle_root = tmp_path / '.artifacts' / 'bundles'
    monkeypatch.setattr(local_store, 'DEFAULT_BUNDLE_ROOT', bundle_root)
    monkeypatch.setattr(registry, 'DEFAULT_BUNDLE_ROOT', bundle_root)
    return bundle_root


def test_verify_bundle_endpoint_end_to_end(tmp_path, monkeypatch):
    _patch_bundle_root(tmp_path, monkeypatch)
    client = TestClient(app)

    response = client.post(
        '/intake/text',
        json={
            'domain': 'quant_experimental',
            'title': 'Verify API E2E',
            'text': 'Methods: We enrolled 150 participants. Results: The treatment effect was statistically significant.',
            'llm_provider': 'heuristic',
        },
    )
    assert response.status_code == 200
    bundle_id = response.json()['artifacts']['bundle_id']

    verify_response = client.get(f'/verify/bundles/{bundle_id}')
    assert verify_response.status_code == 200
    payload = verify_response.json()
    assert payload['bundle_id'] == bundle_id
    assert payload['verified'] is True
    assert payload['trust_tier_matches'] is True
    assert payload['transparency_verified'] is True

    transparency_response = client.get(f'/verify/bundles/{bundle_id}/transparency')
    assert transparency_response.status_code == 200
    assert transparency_response.json()['verified'] is True
