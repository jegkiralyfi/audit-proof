from pathlib import Path

from packages.evaluation.goldset import load_gold_manifest
from packages.evaluation.matrix import matrix_markdown_report, evaluate_provider_matrix


def test_quant_experimental_provider_matrix_markdown_contains_sandbox_note():
    manifest = Path("tests/fixtures/gold_sets/quant_experimental/manifest.json")
    cases = load_gold_manifest(manifest)
    payload = evaluate_provider_matrix(["heuristic"], cases[:2])
    markdown = matrix_markdown_report(payload)
    assert "SANDBOX ONLY" in markdown
    assert "heuristic" in markdown
