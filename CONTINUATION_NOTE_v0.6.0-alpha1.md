# Continuation note — v0.6.0-alpha1

## Purpose

This build upgrades the v0.5 PoC freeze line to v0.6 by baking a formal-proof semantic audit directly into the Proof of Thought engine.

## Main changes

1. Added a new `formal_proof` certification type in `configs/policies/formal_proof.yaml`.
2. Added a new built-in runner: `formal_semantic_audit_check`.
3. Added a new formal-proof bundle artifact: `formal_semantic_audit.json`.
4. Added documentation for formal validity vs semantic closure.
5. Updated README framing to include theorem-prover semantic-load auditing as a first-class lane.
6. Bumped package and API version metadata to `0.6.0a1`.

## Methodological change

The key v0.6 lesson is that theorem-prover acceptance must not be conflated with mathematical closure.
A build can be `sorry`-free and still be semantically hollow if real obligations have been replaced by vacuous propositions or surface-only packaging.

The engine now treats that as an auditable issue rather than only a philosophical warning.

## Scope note

This is still an alpha build.
The new formal-proof lane is a first-tier semantic audit, not a claim of full theorem verification.
