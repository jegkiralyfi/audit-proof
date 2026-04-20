from pathlib import Path

from packages.evaluation.real_papers import (
    evaluate_real_paper_case,
    load_real_paper_manifest,
    summarize_real_paper_results,
)


def test_real_paper_harness_runs_on_local_text_fixture(tmp_path):
    src = Path('tests/fixtures/gold_sets/quant_experimental/qe_01_good_controlled.txt')
    local_file = tmp_path / 'real-paper.txt'
    local_file.write_text(src.read_text(encoding='utf-8'), encoding='utf-8')
    manifest = tmp_path / 'manifest.json'
    manifest.write_text(
        '{"cases": [{"case_id": "rp1", "title": "Local paper", "file": "real-paper.txt", "domain": "quant_experimental", "expected": {"sample_size_present": "pass", "control_group_present": "pass"}}]}',
        encoding='utf-8',
    )
    cases = load_real_paper_manifest(manifest)
    results = [evaluate_real_paper_case(case, llm_provider='heuristic') for case in cases]
    summary = summarize_real_paper_results(results)
    assert summary['n_cases'] == 1
    assert summary['n_labeled_cases'] == 1
    assert 'sample_size_present' in summary['labeled_summary']['per_check']
