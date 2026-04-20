from pathlib import Path

from packages.evaluation.real_papers import load_real_paper_manifest


def test_real_paper_manifest_template_loads():
    manifest = Path('examples/real_papers/manifest.template.json')
    cases = load_real_paper_manifest(manifest)
    assert len(cases) == 1
    assert cases[0].domain == 'quant_experimental'
