from __future__ import annotations

from typing import Any

from packages.core.config import RuntimeConfig, apply_runtime_overrides, load_runtime_config
from packages.llm.providers import build_provider
from packages.llm.schemas import EvidenceRequest, EvidenceResponse


class LLMClient:
    def __init__(self, config: RuntimeConfig | None = None) -> None:
        self.config = config or load_runtime_config()
        self.provider = build_provider(self.config)

    @classmethod
    def from_context(cls, context: dict[str, Any] | None = None) -> "LLMClient":
        config = load_runtime_config()
        overrides = (context or {}).get("llm_runtime_override") or {}
        config = apply_runtime_overrides(config, overrides)
        return cls(config=config)

    def analyze_evidence(self, request: EvidenceRequest) -> EvidenceResponse:
        return self.provider.analyze(request)
