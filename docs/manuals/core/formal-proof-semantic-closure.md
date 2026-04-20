# Formal validity vs semantic closure

## Purpose

This note defines how Audit-Proof treats theorem-prover artifacts under Proof of Thought.

The core distinction is simple: a clean theorem-prover build is evidence of **formal validity** relative to the premises encoded in the repository. It is not, by itself, evidence that those premises carry genuine mathematical substance.

## The hazard

A Lean or theorem-prover project may compile without `sorry`, without visible axioms in its exported theorem surface, and still be semantically empty on the critical path.

This can happen when real dependencies are replaced by devices such as:

- `Prop := True`
- `: True`
- `True.intro`
- `trivial`
- empty `Prop` fields in structures
- theorem-surface wrappers that only repackage lower statements

In that state, the prover has certified internal consequence, not mathematical closure.

## Audit-Proof doctrine

Proof of Thought for formal proof artifacts therefore requires more than build-clean acceptance.

Audit-Proof distinguishes between:

- **build-clean** — the artifact compiles
- **surface-complete** — the exported theorem surface looks closed
- **content-complete** — genuine mathematical dependencies have actually been eliminated

Only the third state is strong evidence of substantive Proof of Thought.

## Non-negotiable rule

A theorem-prover artifact does not count as real proof progress unless it removes a genuine dependency.

This means at least one of the following must be true:

- a previous imported or assumed step becomes internally proved
- a dummy proposition is replaced by a content-bearing proposition
- a kernel lemma is proved in a way that shortens the main proof spine
- a black-box step is reduced to explicit smaller lemmas with real content

## What the formal-proof lane audits

The `formal_proof` certification type performs a first-tier semantic load-bearingness audit.

It explicitly checks for:

- explicit proof holes
- vacuous True-based markers
- empty Prop fields
- low semantic content relative to visible proof structure
- elevated theorem-surface / wrapper pressure signals

## What it does not claim

This lane does **not** certify that a theorem is true in the mathematical sense, that a large proof program is finished, or that a repository is free from every possible semantic shortcut.

It provides a bounded methodological statement:

> the submitted artifact does or does not show evidence of semantic load-bearingness strong enough to support a Proof of Thought style certification claim.

## Practical consequence

A future certificate for a formal proof artifact must never be read as:

> Lean accepted it, therefore the mathematics is complete.

The correct reading is narrower:

> the artifact was audited for semantic placeholders and visible load-bearingness signals, and the certificate records what that audit found.
