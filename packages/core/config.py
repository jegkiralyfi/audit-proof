from __future__ import annotations

import os
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RUNTIME_CONFIG = ROOT / "configs" / "runtime" / "default.yaml"


@dataclass(slots=True)
class RuntimeConfig:
    app_name: str = "audit-proof"
    mode: str = "development"
    storage_backend: str = "local"
    llm_provider: str = "heuristic"
    llm_model: str = "heuristic-evidence-v1"
    llm_base_url: str | None = None
    llm_api_key_env: str = "OPENAI_API_KEY"
    llm_timeout_seconds: int = 30
    llm_max_output_tokens: int = 700
    llm_anthropic_version: str = "2023-06-01"
    signing_enabled: bool = False
    plugin_autodiscovery: bool = True
    plugin_modules: list[str] | None = None
    execution_stub_enabled: bool = True
    execution_stub_timeout_seconds: int = 5
    repository_metadata_fetch_enabled: bool = False
    repository_metadata_timeout_seconds: int = 5
    reference_resolution_fetch_enabled: bool = False
    reference_resolution_timeout_seconds: int = 5


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        return {}
    return data


def _coerce_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _apply_env(cfg: RuntimeConfig) -> RuntimeConfig:
    cfg.llm_provider = os.getenv("AUDIT_PROOF_LLM_PROVIDER", cfg.llm_provider)
    cfg.llm_model = os.getenv("AUDIT_PROOF_LLM_MODEL", cfg.llm_model)
    cfg.llm_base_url = os.getenv("AUDIT_PROOF_LLM_BASE_URL", cfg.llm_base_url or "") or None
    cfg.llm_api_key_env = os.getenv("AUDIT_PROOF_LLM_API_KEY_ENV", cfg.llm_api_key_env)
    cfg.llm_timeout_seconds = int(os.getenv("AUDIT_PROOF_LLM_TIMEOUT_SECONDS", str(cfg.llm_timeout_seconds)))
    cfg.llm_max_output_tokens = int(os.getenv("AUDIT_PROOF_LLM_MAX_OUTPUT_TOKENS", str(cfg.llm_max_output_tokens)))
    cfg.llm_anthropic_version = os.getenv("AUDIT_PROOF_LLM_ANTHROPIC_VERSION", cfg.llm_anthropic_version)
    cfg.plugin_autodiscovery = _coerce_bool(os.getenv("AUDIT_PROOF_PLUGIN_AUTODISCOVERY"), cfg.plugin_autodiscovery)
    cfg.plugin_modules = [item.strip() for item in os.getenv("AUDIT_PROOF_PLUGIN_MODULES", ",".join(cfg.plugin_modules or [])).split(",") if item.strip()]
    cfg.execution_stub_enabled = _coerce_bool(os.getenv("AUDIT_PROOF_EXECUTION_STUB_ENABLED"), cfg.execution_stub_enabled)
    cfg.execution_stub_timeout_seconds = int(os.getenv("AUDIT_PROOF_EXECUTION_STUB_TIMEOUT_SECONDS", str(cfg.execution_stub_timeout_seconds)))
    cfg.repository_metadata_fetch_enabled = _coerce_bool(os.getenv("AUDIT_PROOF_REPOSITORY_METADATA_FETCH_ENABLED"), cfg.repository_metadata_fetch_enabled)
    cfg.repository_metadata_timeout_seconds = int(os.getenv("AUDIT_PROOF_REPOSITORY_METADATA_TIMEOUT_SECONDS", str(cfg.repository_metadata_timeout_seconds)))
    cfg.reference_resolution_fetch_enabled = _coerce_bool(os.getenv("AUDIT_PROOF_REFERENCE_RESOLUTION_FETCH_ENABLED"), cfg.reference_resolution_fetch_enabled)
    cfg.reference_resolution_timeout_seconds = int(os.getenv("AUDIT_PROOF_REFERENCE_RESOLUTION_TIMEOUT_SECONDS", str(cfg.reference_resolution_timeout_seconds)))
    return cfg


def load_runtime_config(path: Path | None = None) -> RuntimeConfig:
    data = _load_yaml(path or DEFAULT_RUNTIME_CONFIG)
    cfg = RuntimeConfig(
        app_name=str(data.get("app_name", "audit-proof")),
        mode=str(data.get("mode", "development")),
        storage_backend=str(data.get("storage_backend", "local")),
        llm_provider=str(data.get("llm_provider", "heuristic")),
        llm_model=str(data.get("llm_model", "heuristic-evidence-v1")),
        llm_base_url=data.get("llm_base_url"),
        llm_api_key_env=str(data.get("llm_api_key_env", "OPENAI_API_KEY")),
        llm_timeout_seconds=int(data.get("llm_timeout_seconds", 30)),
        llm_max_output_tokens=int(data.get("llm_max_output_tokens", 700)),
        llm_anthropic_version=str(data.get("llm_anthropic_version", "2023-06-01")),
        signing_enabled=bool(data.get("signing_enabled", False)),
        plugin_autodiscovery=bool(data.get("plugin_autodiscovery", True)),
        plugin_modules=list(data.get("plugin_modules", []) or []),
        execution_stub_enabled=bool(data.get("execution_stub_enabled", True)),
        execution_stub_timeout_seconds=int(data.get("execution_stub_timeout_seconds", 5)),
        repository_metadata_fetch_enabled=bool(data.get("repository_metadata_fetch_enabled", False)),
        repository_metadata_timeout_seconds=int(data.get("repository_metadata_timeout_seconds", 5)),
        reference_resolution_fetch_enabled=bool(data.get("reference_resolution_fetch_enabled", False)),
        reference_resolution_timeout_seconds=int(data.get("reference_resolution_timeout_seconds", 5)),
    )
    return _apply_env(cfg)


def apply_runtime_overrides(config: RuntimeConfig, overrides: dict[str, Any] | None = None) -> RuntimeConfig:
    if not overrides:
        return config
    allowed = set(asdict(config).keys())
    sanitized: dict[str, Any] = {}
    for key, value in overrides.items():
        if key not in allowed:
            continue
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        sanitized[key] = value
    if not sanitized:
        return config
    merged = replace(config, **sanitized)
    if merged.plugin_modules is None:
        merged.plugin_modules = []
    return merged
