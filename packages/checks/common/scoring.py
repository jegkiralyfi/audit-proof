from __future__ import annotations

from typing import Any

from packages.core.models import CheckResult, EvidenceSpan

VALID_STATUSES = {"pass", "warning", "fail", "not_applicable", "error"}


def normalize_status(value: Any, default: str = "error") -> str:
    status = str(value or default).strip().lower()
    return status if status in VALID_STATUSES else default


def normalize_confidence(value: Any, default: float = 0.5) -> float:
    try:
        confidence = float(value)
    except Exception:
        confidence = float(default)
    return min(1.0, max(0.0, confidence))


def normalize_notes(value: Any) -> str:
    return " ".join(str(value or "").split()).strip()


def normalize_details(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {}


def build_result(
    *,
    check_id: str,
    status: Any,
    confidence: Any,
    evidence: list[EvidenceSpan] | None = None,
    notes: Any = "",
    details: dict[str, Any] | None = None,
) -> CheckResult:
    return CheckResult(
        check_id=check_id,
        status=normalize_status(status),
        confidence=normalize_confidence(confidence),
        evidence=evidence or [],
        notes=normalize_notes(notes),
        details=normalize_details(details),
    )


def summarize_statuses(results: list[CheckResult]) -> dict[str, int]:
    summary = {key: 0 for key in sorted(VALID_STATUSES)}
    for result in results:
        summary[result.status] = summary.get(result.status, 0) + 1
    return summary
