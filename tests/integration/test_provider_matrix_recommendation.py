from pathlib import Path

from packages.evaluation.goldset import load_gold_manifest
from packages.evaluation.matrix import evaluate_provider_matrix, matrix_markdown_report


def test_matrix_payload_contains_lane_recommendation_and_profiles():
    manifest = Path('tests/fixtures/gold_sets/quant_experimental/manifest.json')
    cases = load_gold_manifest(manifest)
    payload = evaluate_provider_matrix(['heuristic'], cases[:3], lane='quant_experimental')
    assert payload['recommended_by_lane']['quant_experimental']['provider'] == 'heuristic'
    markdown = matrix_markdown_report(payload)
    assert 'Recommended provider by lane' in markdown
    assert 'heuristic' in markdown
