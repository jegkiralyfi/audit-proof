# Provider contract

Provider-agnostic does not mean provider-identical. Every backend needs an explicit operational profile.

## Required contract

Each provider profile must declare:
- provider name
- transport type
- authentication mode
- base URL expectations
- model identifier semantics
- JSON / structured-output behavior
- timeout guidance
- evidence-extraction caveats
- known incompatibilities

## Audit-Proof expectation

Every provider used by Audit-Proof must be able to return a structured evidence payload with:
- status
- confidence
- notes
- evidence spans

## Security note

Sandbox only. Not Red Team certified. Manual prompt-injection guardrails only.
