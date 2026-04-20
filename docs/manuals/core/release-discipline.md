# Release Discipline

## Purpose

This document defines how Audit-Proof releases are named, structured, described, and verified.

Its goal is not bureaucracy. Its goal is epistemic discipline.

A certification system must not only generate claims; it must also control how those claims are packaged, frozen, described, and re-verified over time. Release discipline is the mechanism that prevents architectural drift, overclaiming, and silent mutation of trust-bearing artifacts.

## Core principle

A release is not merely a zip file or a tag.

A release is a **declared, frozen, and interpretable state** of the system, together with enough metadata and verification structure that a third party can understand:

- what the system could do at that moment
- what it could not yet do
- which artifacts were canonical
- which claims were legitimate
- how the release can be checked later

## Release classes

Audit-Proof uses the following release classes.

### 1. Internal build

Used for active development.  
May be incomplete, unstable, or exploratory.  
Not suitable for external citation.

Example:
- `v0.4.6-witness-layer`

### 2. PoC milestone release

Used when a coherent capability boundary has been reached and frozen.  
This class is appropriate for internal demonstration, design review, partner conversation, and research planning.

Example:
- `v0.5.0-poc-freeze`

### 3. Public alpha release

Used when the system is externally presentable and the scope is stable enough for broader scrutiny, but significant limitations remain.

Example:
- `v0.6.0-alpha`

### 4. Production release

Reserved for materially hardened releases with explicit operational guarantees, public checkpointing, and disciplined external verification.

This class must not be used prematurely.

## Version naming

Version names should reflect both semantic progression and release role.

Recommended pattern:

`vMAJOR.MINOR.PATCH[-qualifier]`

Examples:
- `v0.4.7-readme-pot`
- `v0.5.0-poc-freeze`
- `v0.6.0-alpha`

### Naming rules

- Increase **PATCH** for bounded implementation increments.
- Increase **MINOR** for meaningful new capability layers.
- Increase **MAJOR** only when the public conceptual contract changes materially.
- Use qualifiers sparingly and only when they communicate a real release state.

## Required release artifacts

Every serious release must contain, at minimum:

- source state or release archive
- release note
- continuation note or changelog
- canonical bundle semantics
- verification path
- provenance artifacts sufficient to re-check the release claims

Where applicable, the release should also include:
- test status summary
- known limitations
- explicit scope statement
- status declaration such as “PoC freeze” or “not production”

## Canonical vs rendered artifacts

A release must explicitly distinguish between:

### Canonical artifacts
Machine-readable artifacts that carry the authoritative certification state.

Examples:
- `certificate.json`
- stable provenance-linked records
- bindings
- manifest
- attestation
- verification receipts

### Rendered views
Human-readable outputs that summarize or display canonical content, but are not themselves the authority.

Examples:
- HTML report
- Markdown narrative summary
- UI rendering

A release must never blur this boundary.

## Required claims discipline

Every release must state:

1. what the system does
2. what the system does not do
3. what is stable
4. what remains provisional
5. what is future work

A release must not imply stronger guarantees than the system actually provides.

### Forbidden overclaims

A release must not claim, unless explicitly and independently supported:

- truth-certification
- authorship-certification
- AI-origin detection
- external audit completion
- production readiness
- public witness equivalence when only local witnessing exists
- real-paper validation completeness when only synthetic or scaffolded evaluation exists

## Freeze criteria for a PoC milestone

A release qualifies as a PoC milestone only if:

- the core workflow is end-to-end coherent
- the canonical artifacts are well defined
- verification is a first-class function
- provenance structure exists and is testable
- scope is explicit and non-misleading
- known limitations are declared
- the architecture is stable enough that further work can move to validation rather than redesign

## Release checklist

Before freezing a serious release, verify the following:

### A. Functionality
- intake works
- certification runs
- bundle generation works
- provenance artifacts are emitted
- verification succeeds on fresh outputs

### B. Canonical integrity
- no cyclic hash dependencies
- canonical artifacts are clearly defined
- rendered views are non-authoritative
- trust-tier recomputation is stable

### C. Logging and witnessing
- transparency inclusion is verifiable
- checkpoints exist where promised
- witness receipts are internally consistent

### D. Documentation
- README is up to date
- release note exists
- known limitations are listed
- philosophy and scope are explicit
- AI / Proof of Thought position is clear

### E. Test discipline
- relevant unit tests pass
- integration tests pass
- end-to-end tests pass
- compilation / import sanity passes

## Required release note structure

Every milestone release note should include:

1. release status
2. purpose of the release
3. core capabilities added or frozen
4. canonical artifact interpretation
5. explicit non-claims
6. known limitations
7. recommended next phase

This prevents future readers from mistaking an architectural freeze for a finished product.

## Published checkpoints

A published checkpoint is an externally placed reference snapshot of a release or log state.

Its purpose is not to certify truth.  
Its purpose is to make silent retroactive mutation harder.

Examples of acceptable published checkpoints:
- GitHub release asset
- static hosted checkpoint file
- immutable object-store reference
- signed public manifest

Until such a mechanism is genuinely external and publicly comparable, it must be described as a planned or local witness feature — not as completed public transparency infrastructure.

## Changelog and continuation discipline

Every non-trivial release should include either:

- a `CHANGELOG.md` entry, or
- a release-specific continuation note

The continuation note should describe:

- what changed
- what was fixed
- what architectural decision was made
- what remains intentionally unfinished

This is essential for epistemic continuity.

## Deprecation discipline

When a previous interpretation, artifact role, or trust statement becomes obsolete, the release should not silently overwrite history.

Instead:
- mark the old interpretation as deprecated
- state what replaces it
- explain why the change was necessary

## Final rule

A release is only trustworthy if it is easier to verify than to misunderstand.

Release discipline exists to make that true.
