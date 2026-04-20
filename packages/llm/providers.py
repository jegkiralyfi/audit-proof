from __future__ import annotations

import importlib
import json
import os
import re
import urllib.parse
import urllib.request
from abc import ABC, abstractmethod
from typing import Any

from packages.core.config import RuntimeConfig
from packages.core.models import EvidenceSpan
from packages.llm.schemas import EvidenceRequest, EvidenceResponse


def _compile_patterns(values: list[str]) -> list[re.Pattern[str]]:
    return [re.compile(value, flags=re.IGNORECASE | re.MULTILINE) for value in values]


def _spans_from_patterns(text: str, patterns: list[str], evidence_limit: int, section_name: str = "excerpt") -> list[EvidenceSpan]:
    spans: list[EvidenceSpan] = []
    for pattern in _compile_patterns(patterns):
        for match in pattern.finditer(text):
            start, end = match.span()
            quote_start = max(0, start - 60)
            quote_end = min(len(text), end + 120)
            quote = text[quote_start:quote_end].strip().replace("\n", " ")
            spans.append(EvidenceSpan(section=section_name, quote=quote, offset_start=start, offset_end=end))
            if len(spans) >= evidence_limit:
                return spans
    return spans


def _json_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "status": {"type": "string", "enum": ["pass", "warning", "fail", "not_applicable", "error"]},
            "confidence": {"type": "number"},
            "notes": {"type": "string"},
            "evidence": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "section": {"type": "string"},
                        "quote": {"type": "string"},
                        "offset_start": {"type": "integer"},
                        "offset_end": {"type": "integer"},
                    },
                    "required": ["section", "quote", "offset_start", "offset_end"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["status", "confidence", "notes", "evidence"],
    }


def _fallback_text_prompt(request: EvidenceRequest) -> str:
    payload = {
        "check_id": request.check_id,
        "domain": request.domain,
        "instruction": request.instruction,
        "preferred_sections": request.preferred_sections,
        "document_title": request.document_title,
        "document_excerpt": request.document_excerpt,
        "pass_patterns": request.pass_patterns,
        "fail_patterns": request.fail_patterns,
        "evidence_limit": request.evidence_limit,
    }
    return (
        "Return JSON only with keys status, confidence, notes, evidence. "
        "Use only pass, warning, fail, not_applicable, error. "
        "Evidence must be a list of objects with section, quote, offset_start, offset_end.\n\n"
        + json.dumps(payload, ensure_ascii=False)
    )


def _extract_json_object(text: str) -> dict[str, Any]:
    text = text.strip()
    if not text:
        raise ValueError("Empty model response")
    try:
        return json.loads(text)
    except Exception:
        pass
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        raise ValueError("No JSON object found in model response")
    return json.loads(match.group(0))


def _http_json(url: str, *, payload: dict[str, Any], headers: dict[str, str], timeout: int) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


class EvidenceProvider(ABC):
    @abstractmethod
    def analyze(self, request: EvidenceRequest) -> EvidenceResponse:
        raise NotImplementedError


class HeuristicEvidenceProvider(EvidenceProvider):
    def analyze(self, request: EvidenceRequest) -> EvidenceResponse:
        text = request.document_excerpt
        fail_spans = _spans_from_patterns(text, request.fail_patterns, request.evidence_limit)
        if fail_spans:
            return EvidenceResponse(
                status="warning",
                confidence=0.76,
                notes="Heuristic evidence provider detected language requiring human review.",
                evidence=fail_spans,
                provider="heuristic",
                raw_response={"matched": "fail_patterns"},
            )
        pass_spans = _spans_from_patterns(text, request.pass_patterns, request.evidence_limit)
        if pass_spans:
            return EvidenceResponse(
                status="pass",
                confidence=0.82,
                notes="Heuristic evidence provider found supporting evidence for the configured check.",
                evidence=pass_spans,
                provider="heuristic",
                raw_response={"matched": "pass_patterns"},
            )
        return EvidenceResponse(
            status="warning",
            confidence=0.55,
            notes="Heuristic evidence provider found no decisive evidence in the available excerpt.",
            provider="heuristic",
            raw_response={"matched": "none"},
        )


class OpenAICompatibleEvidenceProvider(EvidenceProvider):
    def __init__(self, config: RuntimeConfig):
        self.config = config

    def analyze(self, request: EvidenceRequest) -> EvidenceResponse:
        if not self.config.llm_base_url:
            raise RuntimeError("AUDIT_PROOF_LLM_BASE_URL is required for openai-compatible provider")
        api_key = os.getenv(self.config.llm_api_key_env, "")
        if not api_key:
            raise RuntimeError(f"API key env var {self.config.llm_api_key_env} is not set")
        payload = {
            "model": self.config.llm_model,
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are an evidence extraction engine for scientific audit checks. "
                        "Return strict JSON only. Never invent evidence."
                    ),
                },
                {"role": "user", "content": _fallback_text_prompt(request)},
            ],
            "temperature": 0,
            "max_tokens": self.config.llm_max_output_tokens,
        }
        data = _http_json(
            self.config.llm_base_url.rstrip("/") + "/v1/chat/completions",
            payload=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            timeout=self.config.llm_timeout_seconds,
        )
        content = data["choices"][0]["message"]["content"]
        parsed = _extract_json_object(content)
        parsed.setdefault("provider", "openai-compatible")
        parsed.setdefault("raw_response", data)
        return EvidenceResponse.model_validate(parsed)


class AnthropicEvidenceProvider(EvidenceProvider):
    def __init__(self, config: RuntimeConfig):
        self.config = config

    def analyze(self, request: EvidenceRequest) -> EvidenceResponse:
        base_url = (self.config.llm_base_url or "https://api.anthropic.com").rstrip("/")
        api_key = os.getenv(self.config.llm_api_key_env, "")
        if not api_key:
            raise RuntimeError(f"API key env var {self.config.llm_api_key_env} is not set")
        payload = {
            "model": self.config.llm_model,
            "max_tokens": self.config.llm_max_output_tokens,
            "messages": [{"role": "user", "content": _fallback_text_prompt(request)}],
        }
        data = _http_json(
            base_url + "/v1/messages",
            payload=payload,
            headers={
                "content-type": "application/json",
                "x-api-key": api_key,
                "anthropic-version": self.config.llm_anthropic_version,
            },
            timeout=self.config.llm_timeout_seconds,
        )
        text_blocks = []
        for block in data.get("content", []):
            if isinstance(block, dict) and block.get("type") == "text":
                text_blocks.append(block.get("text", ""))
        parsed = _extract_json_object("\n".join(text_blocks))
        parsed.setdefault("provider", "anthropic")
        parsed.setdefault("raw_response", data)
        return EvidenceResponse.model_validate(parsed)


class GeminiEvidenceProvider(EvidenceProvider):
    def __init__(self, config: RuntimeConfig):
        self.config = config

    def analyze(self, request: EvidenceRequest) -> EvidenceResponse:
        api_key = os.getenv(self.config.llm_api_key_env, "")
        if not api_key:
            raise RuntimeError(f"API key env var {self.config.llm_api_key_env} is not set")
        base_url = (self.config.llm_base_url or "https://generativelanguage.googleapis.com/v1beta").rstrip("/")
        model_name = self.config.llm_model
        if not model_name.startswith("models/"):
            model_name = f"models/{model_name}"
        url = f"{base_url}/{model_name}:generateContent?key={urllib.parse.quote(api_key)}"
        payload = {
            "systemInstruction": {
                "parts": [{"text": "You are an evidence extraction engine for scientific audit checks. Return JSON only and never invent evidence."}]
            },
            "contents": [{"role": "user", "parts": [{"text": _fallback_text_prompt(request)}]}],
            "generationConfig": {
                "temperature": 0,
                "maxOutputTokens": self.config.llm_max_output_tokens,
                "responseMimeType": "application/json",
                "responseJsonSchema": _json_schema(),
            },
        }
        data = _http_json(
            url,
            payload=payload,
            headers={"Content-Type": "application/json"},
            timeout=self.config.llm_timeout_seconds,
        )
        candidate = (data.get("candidates") or [{}])[0]
        parts = ((candidate.get("content") or {}).get("parts") or [])
        text = "\n".join(part.get("text", "") for part in parts if isinstance(part, dict))
        parsed = _extract_json_object(text)
        parsed.setdefault("provider", "gemini")
        parsed.setdefault("raw_response", data)
        return EvidenceResponse.model_validate(parsed)


def _load_provider_class(path: str) -> type[EvidenceProvider]:
    if ":" not in path:
        raise RuntimeError("Custom provider path must use module:Class syntax")
    module_name, class_name = path.split(":", 1)
    module = importlib.import_module(module_name)
    provider_cls = getattr(module, class_name)
    if not issubclass(provider_cls, EvidenceProvider):
        raise RuntimeError(f"Custom provider {path} must inherit from EvidenceProvider")
    return provider_cls


def build_provider(config: RuntimeConfig) -> EvidenceProvider:
    provider = config.llm_provider.strip().lower()
    if provider in {"heuristic", "mock", "offline"}:
        return HeuristicEvidenceProvider()
    if provider in {"openai", "openai-compatible", "openai_compatible"}:
        return OpenAICompatibleEvidenceProvider(config)
    if provider in {"anthropic", "claude"}:
        return AnthropicEvidenceProvider(config)
    if provider in {"gemini", "gemini-direct", "google-genai"}:
        return GeminiEvidenceProvider(config)
    if provider.startswith("custom:"):
        provider_cls = _load_provider_class(config.llm_provider.split("custom:", 1)[1])
        return provider_cls(config)
    if ":" in config.llm_provider:
        provider_cls = _load_provider_class(config.llm_provider)
        return provider_cls(config)
    return HeuristicEvidenceProvider()
