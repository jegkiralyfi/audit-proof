# Threat Model

## Core risks
- fabricated evidence spans
- parser failures on malformed PDFs
- prompt injection within uploaded documents
- false confidence from incomplete checks
- silent checker drift after dependency updates
- storage mismatch between document and certificate

## Mitigations (initial)
- fixed typed output schemas
- prompt version pinning
- hash binding for source and certificate
- explicit `not_run` / `uncertain` statuses
- checker version tracking
- local fixtures for regression testing
