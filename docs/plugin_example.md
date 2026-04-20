# Third-party Plugin Example

Audit-Proof supports lightweight third-party plugin registration via the `plugins/` namespace.

The included example plugin is `plugins.wordcount_plugin`. It registers a `word_count_check` runner without modifying the core registry code.

## Contract

A plugin module exposes:

```python
def register(registry):
    registry.register(...)
```

The plugin runner can then be referenced from a policy YAML by `type`.

## Why this matters

This keeps the core system OS-like: domains, methods, and checker families can be added as plugins while the certificate layer stays stable.
