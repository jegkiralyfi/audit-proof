from pathlib import Path

from packages.evaluation.goldset import load_gold_manifest
from packages.evaluation.matrix import evaluate_provider_matrix


def test_provider_matrix_runs_with_heuristic():
    manifest = Path("tests/fixtures/gold_sets/quant_experimental/manifest.json")
    cases = load_gold_manifest(manifest)
    payload = evaluate_provider_matrix(["heuristic"], cases[:2])
    assert payload["matrix"][0]["status"] == "ok"
    assert payload["matrix"][0]["summary"]["n_cases"] == 2
    assert payload["ranking"][0]["provider"] == "heuristic"
