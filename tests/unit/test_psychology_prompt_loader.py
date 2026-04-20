from packages.checks.domains.quant_experimental.prompts import available_prompt_templates, load_prompt_template


def test_prompt_templates_exist():
    names = available_prompt_templates()
    assert "sample_size.md" in names
    assert "overclaiming.md" in names


def test_load_prompt_template_returns_real_text():
    text = load_prompt_template("sample_size")
    assert "sample-size signal" in text.lower()
    assert len(text) > 80
