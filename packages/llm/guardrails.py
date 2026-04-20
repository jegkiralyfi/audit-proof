from __future__ import annotations

from packages.llm.schemas import EvidenceResponse


def clamp_response(response: EvidenceResponse) -> EvidenceResponse:
    if response.status not in {"pass", "warning", "fail", "not_applicable", "error"}:
        response.status = "error"
    response.confidence = min(1.0, max(0.0, response.confidence))
    return response
