# formal_proof certification type

The `formal_proof` certification type audits theorem-prover artifacts under a semantic-load standard.

Its first-tier question is not simply whether the artifact compiles.
Its question is whether the artifact appears to carry genuine mathematical load rather than only theorem-surface closure.

This certification type is intentionally narrow. It is not a complete verification of a large formalization project. It is a bounded methodological audit for Proof of Thought.

## Core ideas

- formal validity is not semantic closure
- build-clean is not content-complete
- theorem-surface closure is not kernel closure
- only genuine dependency elimination counts as proof progress

## First-tier checks

The current PoC checks for:

- explicit holes such as `sorry`, `admit`, or uncited axioms
- vacuous markers such as `Prop := True`, `: True`, `True.intro`, `trivial`, and empty `Prop` fields
- low visible semantic load
- elevated wrapper / surface naming pressure

## Intended use

Use this lane for Lean or other theorem-prover artifacts when you want a machine-readable statement that the artifact was screened for semantic emptiness and surface-only closure risks.
