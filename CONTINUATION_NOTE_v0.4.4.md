# Audit-Proof PoC v0.4.4 — continuation note

This continuation build closes the next OS-level step after the earlier bundle/integrity work.

## What was added

### 1. First-class bundle verification
- `packages/provenance/verify_bundle.py`
- `scripts/verify_bundle.py`
- `GET /verify/`
- `GET /verify/bundles/{bundle_id}`
- Gradio UI tab: **Verify bundle**

The verify flow now recomputes canonical bundle hashes and checks:
- `manifest.json` against recomputed canonical bundle artifacts
- `artifact_bindings.json` against recomputed bindings
- `bundle_fingerprint_sha256`
- `certificate.json` hash vs stored bindings
- local attestation integrity
- stored trust tier vs trust tier recomputed from `build_provenance.json`

### 2. Canonical artifact-binding discipline
The bundle hash discipline was tightened to avoid cyclic dependency issues.

`manifest.json` and `artifact_bindings.json` now cover only **canonical bundle artifacts** and explicitly exclude derived/rendered files:
- `manifest.json`
- `artifact_bindings.json`
- `attestation.json`
- `report.html`

This keeps the verify path stable and avoids binding the rendered report or attestation back into their own hash chain.

### 3. Stronger local attestation
`attestation.json` was strengthened to include:
- manifest hash
- artifact-bindings hash
- canonical bundle fingerprint
- trust tier snapshot

The local attestation verifier now checks:
- HMAC signature
- certificate hash
- manifest hash
- artifact-bindings hash
- bundle fingerprint

### 4. Research note skeleton added to docs
Added:
- `docs/manuals/core/external-calibration-note.md`

This keeps the retrospective citation-calibration memo in the docs tree while remaining clearly outside certificate issuance.

## Validation run
- `pytest -q tests/unit tests/integration tests/e2e`
- Result: **30 passed**
- `python -m compileall apps packages plugins scripts`

## Why this matters
This build moves the PoC closer to a real certification operating system by making verification a first-class feature rather than a narrative claim.
