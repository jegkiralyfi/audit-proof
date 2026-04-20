from packages.checks.domains.quant_experimental.llm_checks import build_evidence_request
from packages.core.models import PolicyCheck


def test_psychology_llm_request_uses_prompt_template_and_patterns():
    check = PolicyCheck(
        id="raw_data_availability",
        required=False,
        type="llm_evidence_check",
        params={
            "prompt_template": "raw_data",
            "pass_patterns": ["osf\\.io", "zenodo"],
            "evidence_limit": 2,
            "search_scope": "full_text",
        },
    )
    req = build_evidence_request(
        configured_check=check,
        domain="quant_experimental",
        document_title="Demo",
        excerpt="Raw data are available on OSF at https://osf.io/abcd1",
        preferred_sections=["methods"],
    )
    assert req.domain == "quant_experimental"
    assert req.check_id == "quant_experimental.raw_data_availability"
    assert "open data" in req.instruction.lower() or "data availability" in req.instruction.lower()
    assert req.pass_patterns == ["osf\\.io", "zenodo"]
