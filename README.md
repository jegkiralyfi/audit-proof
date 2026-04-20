# Audit-Proof

**Audit-Proof** is an open certification layer for scientific documents.

We are not building a truth machine.
We are building an auditable certification operating system that sits **above** existing scientific infrastructure.

Audit-Proof does **not** replace journals, repositories, or peer review.
It adds a machine-readable audit certificate on top of existing infrastructure such as arXiv, Zenodo, bioRxiv, OSF, software repositories, and DOI-linked records.

## What we are building

This repository is the **v0.6.0 alpha 1** build of the Audit-Proof certification OS. It extends the PoC freeze line with a first-class formal-proof semantic audit lane inside the Proof of Thought engine.

Our goal is to orchestrate existing open components into one coherent layer:

- intake of a scientific document or DOI
- parsing and normalization of the document
- routing to a domain-specific audit workflow
- generation of a structured certificate
- packaging of the result as an auditable artifact
- extraction of execution-plan artifacts for execution-capable lanes
- optional signing, registry storage, and later publication

The key design decision is modularity:

- domains must be pluggable
- checks must be swappable
- certificate tiers must be configurable
- the system must support both expansion and reduction of scope

We are building an OS, not a fixed research-methodology doctrine.

## Current scope

### Phase target
We are targeting **Phase 2** first.

That means the first meaningful milestone is not only a UI demo, but an **audit-proof artifact pipeline**:

- intake
- parsing
- policy-driven checks
- certificate JSON
- human-readable report
- RO-Crate packaging
- signature stub / signing-ready flow
- storage abstraction

### PoC freeze objective
This release freezes the first internally coherent certification operating system milestone with:

- monorepo layout
- shared models
- certificate schema draft
- architecture specification
- extension points for domain policies
- extension points for check runners
- placeholder services for provenance, signing, and storage

## System philosophy

### 1. Overlay, not replacement
We do not build a new publishing platform.
We build a certification layer above existing infrastructure.

### 2. Open by default
The certification layer is open infrastructure.
The core certificate format, policy interfaces, and artifact packaging should remain open and inspectable.

### 3. Pluggable domains
Psychology, experimental science, computational reproducibility, simulation, and formal-proof semantic auditing should all fit into the same operating model without forcing a single epistemology on every field.

### 4. Evidence-bound outputs
The system should never produce a floating verdict without an audit trail.
Every result should be tied to:

- document hash
- checker identity
- checker version
- prompt version when applicable
- evidence spans or execution traces
- timestamp

### 5. Reduction is a feature
The system should work even when only a minimal subset of checks is active.
A reduced deployment is still useful if it issues a bounded and honest certificate.


## On AI assistance and Proof of Thought

Audit-Proof intentionally does not detect or flag AI-generated text.
Our position is simple: AI is a writing tool, not a category of fraud.
The same logic applies to every tool that has ever accelerated scientific work — statistical packages, spreadsheets, word processors, email, or the car that drove a researcher to the lab.
We do not audit the tools.
We audit the work.

What we certify is not the path.
It is whether the destination was reached.

The certification checks — sample size stated, control condition present, effect size reported, conclusion grounded in the data, raw data available — form a framework for a different question:
does this paper contain evidence of high-agency intellectual contribution?
Did someone actually think about the design, execute a study, interpret results, and take responsibility for a claim?

This is what we call **Proof of Thought**:
not a guarantee of human authorship, but a machine-readable signal that the work meets the methodological commitments its authors declared.

What we do **not** certify:

- the physical reality of a study
- the originality of the prose
- the identity of the tools used to produce it

These questions belong to community judgment, ethics boards, and peer review — not to a methodological audit layer.

What we **do** certify is harder to fake than any of the above:
that a claim is grounded, a method is stated, a conclusion follows from the evidence, and the work is open enough to be challenged.
A paper that cannot pass these checks has not earned the right to ask for trust — regardless of how it was written or by whom.


## On theorem-prover acceptance and semantic closure

Audit-Proof v0.6 adds a formal-proof semantic audit directly to the PoT engine.

A clean Lean or theorem-prover build is **not** treated as sufficient evidence of substantive reasoning. A repository may compile without `sorry`, export a tidy top theorem, and still be semantically hollow if core dependencies have been replaced by devices such as `Prop := True`, `: True`, `True.intro`, `trivial`, empty `Prop` fields, or surface-only wrapper layers.

For formal-proof artifacts, PoT now distinguishes between:

- **build-clean** — the artifact compiles
- **surface-complete** — the exported theorem surface looks closed
- **content-complete** — genuine dependencies have actually been eliminated

The formal-proof lane audits the difference. Lean acceptance is treated as evidence of internal consequence, not as a standalone certificate of mathematical substance.


## Provider matrix evaluation

We ship a pinned gold-set and a provider-matrix harness for the `quant_experimental` certification type.
This lets us compare deterministic and LLM-backed providers on the same fixtures and report exact accuracy,
micro false-positive rate, and micro false-negative rate.

Example:

```bash
python scripts/evaluate_provider_matrix.py --providers heuristic,openai-compatible,anthropic,gemini
```

Providers that are unavailable or not configured are reported as `error`; they do not silently pass.

## Security note

This codebase is **not Red Team certified**.
We have not yet systematically tried to evade, break, poison, or socially engineer the current checks and execution lanes.
Until that work happens, every certificate and execution artifact should be treated as an engineering prototype, not a hardened security guarantee.
Every generated output must continue to carry this warning explicitly: sandbox only, not Red Team certified, and currently protected only by manual prompt-injection guardrails.


## Trust policy for self-hosted issuance

The authoritative certificate is `certificate.json`. HTML/Markdown reports are **rendered views only**.

Audit-Proof currently distinguishes these self-hosted trust tiers:

- `self_hosted_non_audited_self_claim` — the runtime source cannot be shown to match the bundled stable release manifest
- `self_hosted_repo_matched` — the runtime source matches the bundled stable release manifest
- `self_hosted_release_matched_with_provenance` — the runtime source matches the signed stable release manifest and the local verifier chain succeeds
- `audited_or_witnessed` — reserved for future external audit / public witness / Red Team hardening

Every bundle now carries:

- `build_provenance.json`
- `artifact_bindings.json`
- `release_manifest.json`
- `release_manifest.signature.json`
- `release_verification.json`
- `transparency_record.json`
- `transparency_checkpoint_snapshot.json`
- `verification_receipts.json`
- `witness_record.json`
- `witness_checkpoint_snapshot.json`
- `published_checkpoint_reference.json`
- `issuer_trust_profile` inside `certificate.json`

To regenerate the stable release manifest:

```bash
python scripts/compute_release_manifest.py
```

To verify that the current runtime source matches the bundled stable release manifest:

```bash
python scripts/verify_release_match.py
```

A **published checkpoint** is simply a public copy of a checkpoint file or log summary that lives outside the local runtime — for example in a GitHub release, an object store, or a static public URL.
It does not change the certificate result by itself. Its purpose is only to make later tampering harder by giving the bundle something external to match against.

## Release discipline

Audit-Proof distinguishes between internal builds, PoC milestone releases, public alpha releases, and future production releases.

A serious release must do more than package code. It must freeze a clearly interpretable system state with:

- an explicit scope
- canonical artifact semantics
- a verification path
- declared limitations
- a release note that states both capabilities and non-claims

For this alpha, see:

- `RELEASE_NOTE_v0.6.0-alpha1.md`
- `docs/manuals/core/release-discipline.md`
- `docs/manuals/core/formal-proof-semantic-closure.md`

This is especially important for a certification system. Trust-bearing outputs should never depend on vague packaging, silent mutation, or overstated release language.

To verify a stored bundle end-to-end (canonical artifact bindings, local attestation, trust-tier recomputation, transparency-log inclusion, and witness-log / published-checkpoint inclusion):

```bash
python scripts/verify_bundle.py <bundle_id>
```

To verify only the bundle's local transparency-log inclusion:

```bash
python scripts/verify_transparency_log.py <bundle_id>
```

To generate a self-hosted release signing keypair, sign the manifest, and verify the local verifier chain:

```bash
python scripts/generate_release_signing_keypair.py
python scripts/compute_release_manifest.py
python scripts/sign_release_manifest.py
python scripts/verify_release_signature.py --write
```

## Plugin architecture

Audit-Proof resolves checks through a **check-runner registry**.
Policies declare runner `type`s, the registry resolves them, and workflows simply orchestrate them.

Current built-in runner families:

- `pattern_check`
- `llm_evidence_check`
- `computational_signal_check`
- `repo2docker_check` (execution-readiness + preflight plan stub)
- `formal_semantic_audit_check` (theorem-prover semantic-load audit)

See `docs/registry.md` for how to add a custom runner family.

## Repository map

- `apps/` — runtime entrypoints (UI, API, worker)
- `packages/` — reusable core modules
- `schemas/` — JSON schemas and profiles
- `configs/` — domain policies, prompts, runtime config
- `docs/` — architecture and specification documents
- `tests/` — unit, integration, and end-to-end tests
- `examples/` — sample papers and sample certificates
- `scripts/` — development and maintenance helpers

## First build target

The first real system pass should support:

1. PDF upload or DOI input
2. document hash generation
3. metadata fetch
4. GROBID-based document parsing
5. domain routing by explicit user choice
6. one configurable domain workflow
7. certificate issuance
8. RO-Crate bundle creation
9. signing-ready artifact manifest

## Guiding statement

> We do not replace scientific infrastructure. We make it buildable.

## Status

This repository is now a **post-freeze alpha build**.
It is no longer just a scaffold: it supports standards-bound certification paths, canonical bundle generation, provenance artifacts, verification, local transparency logging, witness-style multi-verifier checks, and now a first-class formal-proof semantic audit lane.

It is **not** a production release. The next phase is external calibration, real-paper validation, public release hardening, and broader formal-proof bundle ingestion.


## Included in v0.6 alpha

This repository now includes working certification paths for the `quant_experimental`, `computational`, and `formal_proof` certification types. The new v0.6 addition is the `formal_proof` lane, which audits theorem-prover artifacts for semantic load-bearingness rather than treating build-clean acceptance as enough proof by itself.

- text and file intake via FastAPI (`POST /intake/text`, `POST /intake/file`)
- local parsing and section splitting
- standards-bound quantitative experimental checks
- certificate JSON generation
- HTML audit report generation
- demo script writing example artifacts to `examples/example_certificates/`

Run the demo job:

```bash
python scripts/run_demo_job.py
```

Run the API locally:

```bash
python -m apps.api.main
```

Run the Gradio demo:

```bash
python apps/web/app.py
```


## Included in this alpha

- policy-driven quantitative experimental workflow via `configs/policies/quant_experimental.yaml`
- formal-proof semantic-load workflow via `configs/policies/formal_proof.yaml`
- local artifact bundle persistence under `.artifacts/bundles/`
- RO-Crate metadata export
- Sigstore-style attestation stub for next-phase signing integration
- local append-only transparency log + checkpoint witness layer
- file upload API endpoint at `POST /intake/file`
- `formal_semantic_audit.json` bundle artifact for formal-proof submissions


## Current runner families

- `pattern_check` for deterministic pattern-based checks
- `llm_evidence_check` for evidence extraction with an offline heuristic fallback and optional OpenAI-compatible backend
- `llm_interpretation_check` for higher-level interpretation checks such as overclaiming
- `computational_signal_check` for first-tier reproducibility signals such as repository links, environment specs, and rerun instructions
- `formal_semantic_audit_check` for theorem-prover semantic placeholder scans, semantic-load scoring, and anti-castle warning signals


## Registry endpoints

- `GET /registry/bundles` — list issued bundles
- `GET /registry/bundles/{bundle_id}` — fetch one bundle
- `GET /registry/runners` — list registered runner families, capabilities, and execution modes
- `GET /reports/{bundle_id}/repository-metadata` — fetch normalized / fetched repository metadata when present
- `GET /reports/{bundle_id}/execution-plan` — fetch execution-plan artifact when present


## Runner registry and operational profile

Audit-Proof exposes a capability-aware runner registry. Policies declare runner types; the registry resolves them to implementations; certificates record both the check results and the operational profile that produced them. This keeps the system extensible without hard-coding domain logic into a single workflow.


## Execution-plan artifacts

Computational and future execution-capable lanes can emit a typed `execution_plan.json` artifact.
This makes the execution trail a first-class artifact in the bundle rather than a detail hidden only inside the certificate.


## Third-party plugins

Audit-Proof can auto-discover runner plugins from the top-level `plugins/` package. The included `plugins.wordcount_plugin` shows how an external module can register a new check-runner family without changing the core registry.


## Recent additions

- `execution_receipts.json` as a controlled dry-run execution receipt artifact
- `execution_stub_outputs.json` as the local sandbox stub output log
- explicit `artifact_references` embedded in `certificate.json`
- separate API retrieval for execution receipts


## Planned and emerging lanes

- Literature reference audit lane: first-tier reference section, in-text citation, and DOI/URL richness checks are now scaffolded as a built-in runner and separate artifact.


## LLM provider model

The LLM evidence layer is provider-agnostic. `audit-proof` can run with:
- the built-in heuristic offline provider,
- any OpenAI-compatible server endpoint (including self-hosted open-weight deployments such as Meta/Llama-family models served behind an OpenAI-compatible API), or
- a custom Python provider loaded by import path (`custom:module:Class`).

This keeps the certification OS separate from any single commercial model vendor.


## Provider manuals

See `docs/manuals/` for provider contracts, prompting contracts, and operator manuals for heuristic, OpenAI-compatible, Anthropic, Gemini, vLLM, TGI, llama.cpp, and custom providers.


## Standards-bound certification types

The first social-science lane is not framed as `psychology` in the broad disciplinary sense. It is framed as the certification type `quant_experimental`, which targets quantitative experimental or controlled comparative studies and declares its standards basis in the issued certificate.

Current standards bindings:
- `quant_experimental`: APA JARS-Quant (2018), selected modules for quantitative/experimental/random-assignment reporting, plus selected TOP guideline modules for data/materials/preregistration signals.
- `computational`: FAIR Guiding Principles (2016), selected principles, plus selected TOP guideline modules for artifact openness signals.
- `formal_proof`: PoT Formal Proof v0.6 internal methodology standard for semantic closure, placeholder exclusion, dependency elimination, and theorem-surface honesty.


## Provider profiles and lane recommendations

We now ship code-level provider profiles and a matrix report that can recommend a provider **by certification lane** based on pinned evaluation results.
Export provider profiles:

```bash
python scripts/export_provider_profiles.py
```

Generate a matrix report with a lane recommendation:

```bash
python scripts/evaluate_provider_matrix.py --providers heuristic,openai-compatible,anthropic,gemini --markdown-output .artifacts/evaluations/quant_experimental_matrix.md
```


## Evaluation status

- The bundled `quant_experimental` gold-set is **synthetic** and exists for pinned regression testing.
- Real-paper evaluation is supported through `scripts/evaluate_real_papers.py` and a local manifest of open-access or user-supplied files.
- Do **not** claim validated accuracy from unlabeled real-paper runs; FP/FN metrics should only be reported for human-labeled cases.

## Security and trust notes

- `.artifacts/` is local-only and ignored by git.
- Generated HTML/Markdown reports are rendered views, not the authoritative certificate.
- Until Red Team review exists, treat all outputs as sandbox artifacts with manual prompt-injection guardrails only.


## External calibration note

A separate skeleton for the retrospective citation-uptake research note lives at `docs/manuals/core/external-calibration-note.md`. It is explicitly **not** part of issuance and does not change certificate decisions.

The local transparency-log design is documented at `docs/manuals/core/transparency-log.md`.
