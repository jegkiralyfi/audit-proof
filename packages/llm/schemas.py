from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from packages.core.models import EvidenceSpan


class EvidenceRequest(BaseModel):
    domain: str
    check_id: str
    instruction: str
    document_title: str | None = None
    document_excerpt: str
    preferred_sections: list[str] = Field(default_factory=list)
    pass_patterns: list[str] = Field(default_factory=list)
    fail_patterns: list[str] = Field(default_factory=list)
    evidence_limit: int = 2
    match_scope: str = "preferred"


class EvidenceResponse(BaseModel):
    status: Literal["pass", "warning", "fail", "not_applicable", "error"]
    confidence: float = Field(ge=0.0, le=1.0)
    notes: str = ""
    evidence: list[EvidenceSpan] = Field(default_factory=list)
    provider: str = "heuristic"
    raw_response: dict | None = None
