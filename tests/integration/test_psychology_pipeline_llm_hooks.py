from pathlib import Path

from packages.ingest.parser import parse_text_to_document
from packages.routing.domain_router import get_workflow


def test_psychology_pipeline_runs_llm_checks_with_prompt_metadata():
    text = Path("examples/psychology_paper_01.txt").read_text(encoding="utf-8")
    document = parse_text_to_document(text, source_name="example.txt")
    workflow = get_workflow("quant_experimental")
    results = workflow.run(document)
    by_id = {r.check_id: r for r in results}
    assert "quant_experimental.raw_data_availability" in by_id
    assert "quant_experimental.overclaiming_detected" in by_id
    raw = by_id["quant_experimental.raw_data_availability"]
    assert raw.details is not None
    assert raw.details.get("prompt_template") == "quant_experimental/raw_data.md"
    assert raw.details.get("llm_provider") in {"heuristic", "openai-compatible", "dummy"}
