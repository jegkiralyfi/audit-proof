from pathlib import Path

from packages.evaluation.goldset import load_gold_manifest


def test_load_quant_experimental_gold_manifest():
    manifest = Path('tests/fixtures/gold_sets/quant_experimental/manifest.json')
    cases = load_gold_manifest(manifest)
    assert len(cases) >= 5
    assert cases[0].domain == 'quant_experimental'
    assert 'sample_size_present' in cases[0].expected
