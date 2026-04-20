from __future__ import annotations

import importlib
import pkgutil
from types import ModuleType
from typing import Iterable

from packages.core.config import load_runtime_config


class PluginRegistryProxy:
    def __init__(self, registry, module_name: str) -> None:
        self._registry = registry
        self._module_name = module_name

    def register(self, runner_type, factory, **kwargs):
        kwargs.setdefault('source_kind', 'plugin')
        kwargs.setdefault('source_module', self._module_name)
        return self._registry.register(runner_type, factory, **kwargs)


def _iter_autodiscovery_modules() -> list[str]:
    names: list[str] = []
    try:
        pkg = importlib.import_module("plugins")
    except Exception:
        return names

    for info in pkgutil.iter_modules(getattr(pkg, "__path__", []), prefix="plugins."):
        if info.name.endswith(".__pycache__"):
            continue
        names.append(info.name)
    return sorted(set(names))


def _maybe_register_module(module: ModuleType, registry) -> bool:
    register = getattr(module, "register", None)
    if callable(register):
        register(PluginRegistryProxy(registry, module.__name__))
        return True
    return False


def load_plugin_modules(registry, module_names: Iterable[str]) -> list[str]:
    loaded: list[str] = []
    for name in module_names:
        try:
            module = importlib.import_module(name)
        except Exception:
            continue
        if _maybe_register_module(module, registry):
            loaded.append(name)
    return loaded


def load_configured_plugins(registry) -> list[str]:
    cfg = load_runtime_config()
    module_names: list[str] = []
    if cfg.plugin_autodiscovery:
        module_names.extend(_iter_autodiscovery_modules())
    module_names.extend(cfg.plugin_modules or [])
    deduped = []
    seen: set[str] = set()
    for name in module_names:
        if name not in seen:
            deduped.append(name)
            seen.add(name)
    return load_plugin_modules(registry, deduped)
