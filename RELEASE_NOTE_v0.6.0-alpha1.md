# Audit-Proof v0.6.0-alpha1

## Release status

This release moves Audit-Proof beyond the PoC freeze baseline and introduces the first built-in formal-proof semantic audit lane inside the Proof of Thought engine.

It is an **alpha release**, not a production release.

## What is new in v0.6

The main addition is a new certification type:

- `formal_proof`

This lane does not treat theorem-prover acceptance as sufficient evidence of substantive proof content.
Instead, it audits theorem-prover artifacts for semantic load-bearingness.

## Core methodological change

Audit-Proof now makes the following distinction explicit inside the engine:

- **build-clean** — the artifact compiles
- **surface-complete** — the exported theorem surface looks closed
- **content-complete** — genuine dependencies have been eliminated

For formal-proof artifacts, only the third state is strong evidence of Proof of Thought.

## New formal-proof checks

The `formal_proof` lane currently includes:

- explicit placeholder-hole detection (`sorry`, `admit`, uncited axioms)
- vacuous marker detection (`Prop := True`, `: True`, `True.intro`, `trivial`, empty `Prop` fields)
- semantic-load floor scoring
- theorem-surface / wrapper-pressure warning signals

## New artifact

Formal-proof bundles now include:

- `formal_semantic_audit.json`

This artifact records the semantic-placeholder audit and the visible semantic-load summary used by the formal-proof lane.

## Why this matters

A theorem prover is a consistency engine, not by itself a semantic honesty engine.
A large repository can be `sorry`-free and still be mathematically hollow on the critical path if its core obligations have been replaced by vacuous propositions or surface-only packaging layers.

v0.6 turns that lesson into a first-class audit rule.

## Included capabilities carried forward

This release retains the v0.5 operating-system base:

- standards-bound certification
- canonical bundle generation
- provenance artifacts
- bundle verification
- transparency logging
- witness-style multi-verifier receipts
- release verification and self-hosted trust tiers

## Not claimed by this release

This release does **not** claim:

- truth-certification of a mathematical theorem
- full semantic understanding of an arbitrary proof repository
- production-grade formal-proof ingestion for entire multi-file Lean repos
- external audit completion
- complete real-paper validation

## Recommended next phase

The strongest next steps after `v0.6.0-alpha1` are:

1. formal-proof repo bundle ingestion beyond single-file text artifacts
2. hand-labeled formal-proof evaluation fixtures
3. external calibration note completion
4. public checkpoint publication and broader release hardening
