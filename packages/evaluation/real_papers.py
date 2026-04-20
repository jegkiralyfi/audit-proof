from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from packages.evaluation.goldset import CHECK_POLARITY, summarize_results
from packages.ingest.parser import parse_path_to_document
from packages.routing.domain_router import get_workflow


@dataclass
class RealPaperCase:
    case_id: str
    title: str
    file: Path
    domain: str
    doi: str | None = None
    notes: str | None = None
    expected: dict[str, str] | None = None


def load_real_paper_manifest(path: str | Path) -> list[RealPaperCase]:
    manifest_path = Path(path)
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    base = manifest_path.parent
    cases: list[RealPaperCase] = []
    for item in data.get("cases", []):
        file_path = Path(item["file"])
        if not file_path.is_absolute():
            file_path = (base / file_path).resolve()
        cases.append(RealPaperCase(
            case_id=str(item["case_id"]),
            title=str(item.get("title", item["case_id"])),
            file=file_path,
            domain=str(item.get("domain", "quant_experimental")),
            doi=item.get("doi"),
            notes=item.get("notes"),
            expected={str(k): str(v) for k, v in (item.get("expected") or {}).items()} or None,
        ))
    return cases


def evaluate_real_paper_case(case: RealPaperCase, *, llm_provider: str = "heuristic") -> dict[str, Any]:
    document = parse_path_to_document(case.file, metadata={"title": case.title, "doi": case.doi})
    workflow = get_workflow(case.domain)
    checks = workflow.run(document, context={"llm_runtime_override": {"llm_provider": llm_provider}})
    predicted = {check.check_id.split(".", 1)[1]: check.status for check in checks}
    rows: list[dict[str, Any]] = []
    if case.expected:
        for check_id, expected_status in case.expected.items():
            predicted_status = predicted.get(check_id, "missing")
            positive_statuses = CHECK_POLARITY.get(check_id, {"pass"})
            expected_positive = expected_status in positive_statuses
            predicted_positive = predicted_status in positive_statuses
            rows.append({
                "check_id": check_id,
                "expected": expected_status,
                "predicted": predicted_status,
                "exact_match": predicted_status == expected_status,
                "expected_positive": expected_positive,
                "predicted_positive": predicted_positive,
                "false_positive": predicted_positive and not expected_positive,
                "false_negative": (not predicted_positive) and expected_positive,
            })
    return {
        "case_id": case.case_id,
        "title": case.title,
        "domain": case.domain,
        "doi": case.doi,
        "notes": case.notes,
        "predicted": predicted,
        "per_check": rows,
        "labeled": bool(case.expected),
        "file": str(case.file),
    }


def summarize_real_paper_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    labeled_results = [r for r in results if r.get("labeled")]
    if labeled_results:
        labeled_summary = summarize_results(labeled_results)
    else:
        labeled_summary = {
            "n_cases": 0,
            "n_check_evaluations": 0,
            "exact_matches": 0,
            "exact_accuracy": None,
            "false_positives": 0,
            "false_negatives": 0,
            "micro_false_positive_rate": None,
            "micro_false_negative_rate": None,
            "per_check": {},
        }
    predicted_checks = sorted({cid for r in results for cid in (r.get("predicted") or {}).keys()})
    return {
        "n_cases": len(results),
        "n_labeled_cases": len(labeled_results),
        "n_unlabeled_cases": len(results) - len(labeled_results),
        "predicted_check_ids": predicted_checks,
        "labeled_summary": labeled_summary,
    }
