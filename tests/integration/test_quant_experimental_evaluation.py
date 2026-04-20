from pathlib import Path

from packages.evaluation.goldset import load_gold_manifest, evaluate_case, summarize_results


def test_quant_experimental_goldset_evaluation_runs():
    manifest = Path('tests/fixtures/gold_sets/quant_experimental/manifest.json')
    cases = load_gold_manifest(manifest)
    results = [evaluate_case(case, llm_provider='heuristic') for case in cases[:2]]
    summary = summarize_results(results)
    assert summary['n_cases'] == 2
    assert summary['n_check_evaluations'] > 0
    assert 'sample_size_present' in summary['per_check']
