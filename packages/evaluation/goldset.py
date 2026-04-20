from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from packages.ingest.parser import parse_text_to_document
from packages.routing.domain_registry import get_domain_policy
from packages.routing.domain_router import get_workflow


CHECK_POLARITY: dict[str, set[str]] = {
    "sample_size_present": {"pass"},
    "control_group_present": {"pass"},
    "effect_size_reported": {"pass"},
    "ci_or_pvalue_reported": {"pass"},
    "raw_data_availability": {"pass"},
    "overclaiming_detected": {"warning", "fail"},
}


@dataclass
class GoldCase:
    case_id: str
    title: str
    file: Path
    domain: str
    expected: dict[str, str]


def load_gold_manifest(path: str | Path) -> list[GoldCase]:
    manifest_path = Path(path)
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    base = manifest_path.parent
    cases: list[GoldCase] = []
    for item in data.get("cases", []):
        cases.append(GoldCase(
            case_id=str(item["case_id"]),
            title=str(item.get("title", item["case_id"])),
            file=(base / item["file"]).resolve(),
            domain=str(item.get("domain", "quant_experimental")),
            expected={str(k): str(v) for k, v in item.get("expected", {}).items()},
        ))
    return cases


def evaluate_case(case: GoldCase, *, llm_provider: str = "heuristic") -> dict[str, Any]:
    text = case.file.read_text(encoding="utf-8")
    document = parse_text_to_document(text=text, source_name=case.file.name, metadata={"title": case.title})
    workflow = get_workflow(case.domain)
    checks = workflow.run(document, context={"llm_runtime_override": {"llm_provider": llm_provider}})
    predicted = {check.check_id.split(".", 1)[1]: check.status for check in checks}
    per_check: list[dict[str, Any]] = []
    for check_id, expected_status in case.expected.items():
        predicted_status = predicted.get(check_id, "missing")
        positive_statuses = CHECK_POLARITY.get(check_id, {"pass"})
        expected_positive = expected_status in positive_statuses
        predicted_positive = predicted_status in positive_statuses
        per_check.append({
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
        "per_check": per_check,
    }


def summarize_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    per_check_summary: dict[str, dict[str, int]] = {}
    total = exact = fp = fn = 0
    for result in results:
        for row in result["per_check"]:
            total += 1
            if row["exact_match"]:
                exact += 1
            if row["false_positive"]:
                fp += 1
            if row["false_negative"]:
                fn += 1
            bucket = per_check_summary.setdefault(row["check_id"], {
                "n": 0, "exact_matches": 0, "false_positives": 0, "false_negatives": 0
            })
            bucket["n"] += 1
            bucket["exact_matches"] += int(row["exact_match"])
            bucket["false_positives"] += int(row["false_positive"])
            bucket["false_negatives"] += int(row["false_negative"])
    for bucket in per_check_summary.values():
        n = max(bucket["n"], 1)
        bucket["exact_accuracy"] = round(bucket["exact_matches"] / n, 3)
        bucket["false_positive_rate"] = round(bucket["false_positives"] / n, 3)
        bucket["false_negative_rate"] = round(bucket["false_negatives"] / n, 3)
    return {
        "n_cases": len(results),
        "n_check_evaluations": total,
        "exact_matches": exact,
        "exact_accuracy": round(exact / total, 3) if total else 0.0,
        "false_positives": fp,
        "false_negatives": fn,
        "micro_false_positive_rate": round(fp / total, 3) if total else 0.0,
        "micro_false_negative_rate": round(fn / total, 3) if total else 0.0,
        "per_check": per_check_summary,
    }
