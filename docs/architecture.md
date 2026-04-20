# Audit-Proof Architecture

## 1. Purpose

Audit-Proof is a modular certification operating system for scientific artifacts.

The architecture is designed around one central constraint:

> the certification layer must remain flexible, domain-extensible, and reducible without collapsing the whole system.

We are not encoding one universal methodology.
We are building a runtime that can host multiple methodologies as separate policy-driven workflows.

## 2. Architectural principles

### Overlay architecture
The system sits above existing repositories and publishing infrastructure.
It does not replace arXiv, Zenodo, OSF, journals, DOI registries, or software repositories.

### Policy-driven execution
A certificate is not a generic AI opinion.
It is the output of a declared policy:

- domain
- tier
- selected checks
- issuance rules
- evidence requirements
- confidence semantics

### Modular check runners
Each domain workflow is built from small check runners.
A runner may be:

- rule-based
- parser-based
- external-tool-based
- LLM-assisted
- execution-based
- human-review-assisted later

### Artifact-first design
The final unit of value is not only a web response.
It is an auditable artifact bundle containing:

- source document identity
- metadata snapshot
- normalized parse output
- executed checks
- certificate output
- report output
- provenance manifest
- signature or signing-ready payload

## 3. High-level system diagram

```text
User
  |
  v
Web UI / API
  |
  v
Intake Layer
  |- upload or DOI
  |- doc hash
  |- metadata fetch
  |
  v
Parsing Layer
  |- GROBID
  |- normalized sections and spans
  |
  v
Domain Router
  |- select policy bundle
  |
  +-------------------------------+
  |                               |
  v                               v
Domain Workflow A            Domain Workflow B
  |- check runners              |- check runners
  |- evidence extraction        |- execution traces
  |- scoring                    |- scoring
  |                               |
  +---------------+---------------+
                  |
                  v
Evidence Binder
  |
  v
Certificate Builder
  |- JSON certificate
  |- report output
  |- certificate hash
  |
  v
Provenance Packager
  |- manifest
  |- RO-Crate
  |- signing payload
  |
  v
Registry / Storage
```

## 4. Component boundaries

### `apps/web`
User-facing interface.
Responsibilities:
- file upload
- DOI entry
- domain selection
- job submission
- report viewing

This layer should remain thin.

### `apps/api`
Public system interface.
Responsibilities:
- intake requests
- job orchestration
- retrieval of certificates and reports
- health and admin endpoints later

### `apps/worker`
Long-running background execution.
Responsibilities:
- parse documents
- fetch metadata
- invoke workflow runners
- build certificates
- package artifacts

### `packages/core`
Shared primitives.
Responsibilities:
- config
- shared models
- hashing
- typed errors
- logging

### `packages/ingest`
Document acquisition and normalization.
Responsibilities:
- DOI lookup
- PDF parsing
- document normalization
- parse abstraction

### `packages/routing`
Policy and workflow selection.
Responsibilities:
- domain registry
- domain policy loading
- issuance policy selection

### `packages/checks`
Execution of domain-specific checks.
Responsibilities:
- workflow assembly
- check interfaces
- evidence binding
- common scoring support

### Check-runner registry
The registry resolves policy-declared runner `type`s into executable runner families.
This is the core plugin seam of the OS.

A policy should be able to switch a check from a regex runner to an LLM evidence runner or a later execution runner without changing the certificate layer.

### `packages/certificates`
Certificate and report generation.
Responsibilities:
- certificate schema binding
- summary logic
- report rendering
- hash generation

### `packages/provenance`
Artifact trust layer.
Responsibilities:
- RO-Crate packaging
- manifest generation
- signing integration
- attestations

### `packages/storage`
Persistence abstraction.
Responsibilities:
- local storage
- S3/MinIO abstraction
- registry pathing

### `packages/llm`
Optional structured LLM support.
Responsibilities:
- provider abstraction
- prompt versioning
- typed extraction contracts
- guardrails

## 5. Domain extensibility model

A domain is not hard-coded into the system core.
A domain is a package of:

1. policy metadata
2. required and optional checks
3. issuance rules
4. evidence requirements
5. reporting semantics

This means we can:

- add a new domain without rewriting the core
- disable a domain cleanly
- reduce a workflow to a smaller tier
- swap out one check runner without breaking the certificate layer

## 6. Certificate lifecycle

1. intake request created
2. source document identified
3. hash generated
4. metadata attached
5. document parsed
6. domain policy loaded
7. checks executed
8. evidence bound to each result
9. certificate built
10. certificate hash generated
11. artifact package assembled
12. artifact stored
13. optional signature attached

## 7. Why this is an OS architecture

This is an operating system in the narrow infrastructure sense because it provides:

- standard inputs
- standard internal abstractions
- a policy runtime
- pluggable execution units
- standard outputs
- persistence and provenance

Each scientific field can then run its own certification logic on top of the same operating model.

## 8. MVP focus

The MVP should prove four things only:

1. a document can be normalized into a common internal form
2. a declared policy can invoke a domain workflow
3. the workflow can emit evidence-bound results
4. the system can issue an auditable certificate artifact

That is enough for the first serious proof of concept.


## v0.1.2 additions

The system now treats certification-type checks as policy-driven plugins. The quantitative experimental workflow is loaded through a certification-type registry backed by YAML policy files, and every issued certificate is persisted as a local artifact bundle containing the certificate JSON, HTML report, RO-Crate metadata, manifest, and an attestation stub.


## Check-Runner Registry

The policy layer declares runner types (`pattern_check`, future `llm_evidence_check`, `repo2docker_check`, etc.). A central check-runner registry resolves each declared type to a concrete runner implementation. This keeps the OS modular: domains declare what must be checked, the registry decides which executable component runs the check.


## Runner Types

- `pattern_check`: deterministic regex/pattern checks for low-cost signals.
- `llm_evidence_check`: evidence-oriented check that can run in offline heuristic mode or against an OpenAI-compatible API.
- `llm_interpretation_check`: same runner family, tuned for interpretation or overclaiming review.

The registry resolves a policy-declared runner type to a concrete runner implementation. This keeps domain workflows thin and lets us add future runners (for example `repo2docker_check`) without rewriting the workflow layer.


## Computational lane (first stub)

The first computational lane is intentionally modest. We do not execute arbitrary code yet. Instead, the policy can route checks to a `computational_signal_check` runner that inspects the paper for a reproducibility trail: code or archive location, environment specification, and rerun instructions. This keeps the certification OS honest while creating a clean extension point for a later repo2docker-backed execution runner.


## 10. Runner-family roadmap

Near-term runner families:

- deterministic text/pattern checks
- LLM evidence checks
- computational reproducibility signal checks
- repo2docker execution-readiness checks

Later runner families:

- true repo2docker execution
- simulation replay
- formal proof interfaces
- human-review-assisted escalation


## Capability metadata

Each check result now carries runner metadata resolved from the registry: runner type, runner family, execution mode, and capability classes. The certificate builder aggregates these into an operational profile so the issued certificate describes not only what passed, but *how* the audit was performed.


## Preflight execution-attempt lane

The `repo2docker_check` runner currently operates as a preflight execution-attempt stub. It does not execute builds yet; instead it extracts repository URLs, detects execution metadata signals, and emits a structured attempt plan that can later be handed to a true execution runner.


## Execution-plan artifacts

Execution-capable lanes should emit a separate `execution_plan.json` artifact whenever a runner produces attempt-oriented details. The certificate remains the public summary, while the execution plan carries typed attempt semantics such as repository candidate, provider, attempt status, and next step. This keeps the OS honest: preflight and execution metadata are first-class outputs, not ad-hoc notes.


## Execution attempt artifact

The computational lane now emits two execution-facing artifacts:
- `execution_plan.json` for preflight planning
- `execution_attempts.json` for typed, audit-friendly attempt records in stub mode

This keeps execution intent and execution logging separate and makes the OS layer easier to extend toward real execution later.


## Recent additions

- `execution_receipts.json
- `execution_stub_outputs.json` as the local sandbox stub output log` as a controlled dry-run execution receipt artifact
- explicit `artifact_references` embedded in `certificate.json`
- separate API retrieval for execution receipts
