# Check-Runner Registry

The registry is the plugin seam of Audit-Proof.

A policy declares **what kind of runner** should execute a check.
The registry resolves that declared type into an executable component.
The workflow itself stays thin.

## Mental model

- **policy** declares
- **registry** resolves
- **runner** executes
- **certificate layer** records the outcome

This is how we keep Audit-Proof as an OS layer rather than a hard-coded methodology.

## Built-in runner families

- `pattern_check`
- `rule_check`
- `llm_evidence_check`
- `llm_interpretation_check`
- `computational_signal_check`
- `repo2docker_check`

## Adding a new runner

1. Create a class implementing `CheckRunner`
2. Register it in `packages/checks/registry.py`
3. Reference its `type` from a domain policy YAML

## Minimal example

```python
from packages.checks.base import CheckRunner
from packages.checks.common.scoring import build_result

class MyCustomRunner(CheckRunner):
    def run(self, document, configured_check, *, domain: str, context=None):
        return build_result(
            check_id=f"{domain}.{configured_check.id}",
            status="warning",
            confidence=0.6,
            notes="Custom runner executed in PoC mode.",
        )
```

Then register it:

```python
registry.register("my_custom_check", MyCustomRunner)
```

Then use it from policy:

```yaml
- id: my_custom_signal
  type: my_custom_check
  required: false
  params: {}
```

## Why this matters

The registry is what lets us:

- add new domains without rewriting the core
- swap one checker family for another
- reduce or expand a policy without collapsing the system
- keep the certificate layer stable while runners evolve


## Registry metadata

Each registered runner declares public metadata in addition to its factory:
- runner family
- execution mode
- capability classes
- implementation path
- description

This makes the registry part of the certification surface, not just an internal wiring table.


## Plugin autodiscovery

Audit-Proof can auto-discover third-party plugin modules from the top-level `plugins/` package.
A plugin module simply exposes a `register(registry)` function.

Example built-in demo plugin:
- `plugins.wordcount_plugin`

Environment/config controls:
- `plugin_autodiscovery: true|false`
- `plugin_modules: []`
- `AUDIT_PROOF_PLUGIN_MODULES=plugins.my_plugin,plugins.other_plugin`
