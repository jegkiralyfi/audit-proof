# Audit-Proof v0.5.0-rc2

## Release status

This release marks the first internally coherent milestone of the Audit-Proof certification operating system.

It is a **PoC freeze release candidate**, not a production release.

Audit-Proof now supports a full standards-bound certification flow from intake to canonical bundle generation, attestation, verification, transparency logging, and witness-style multi-verifier checking. The purpose of this release is to freeze the operating-system layer in a form that is coherent, inspectable, and testable, so that future work can focus on external calibration, real-paper validation, and release hardening rather than continued architectural drift.

## What this release establishes

Audit-Proof now provides:

- standards-bound certification checks
- canonical certificate and bundle generation
- provenance artifacts and artifact bindings
- first-class verification through script, API, and UI paths
- append-only transparency logging with checkpoints
- witness-style multi-verifier receipts
- explicit trust-tier and verification semantics
- documentation that clearly states what the system certifies and what it does not certify

This means the PoC is no longer merely a certificate generator. It is now a small but coherent certification operating system with verifiable outputs.

## Core principle

Audit-Proof does not certify truth, authorship, or tool identity.

It certifies whether a document meets the methodological commitments declared by the certification profile under which it is evaluated.

The system does not attempt to detect AI-generated text. Our position is simple: AI is a writing tool, not a category of fraud. We do not audit the tools. We audit the work.

What we certify is not the path. It is whether the destination was reached.

## On AI assistance and Proof of Thought

Audit-Proof intentionally does not detect or flag AI-generated text.

Our position is that AI is a writing tool, not a category of fraud. The same logic applies to every tool that has ever accelerated scientific work — statistical packages, spreadsheets, word processors, email, or the car that drove a researcher to the lab. We do not audit the tools. We audit the work.

The certification checks — sample size stated, control condition present, effect size reported, conclusion grounded in the data, raw data available — form a framework for a different question: does this paper contain evidence of high-agency intellectual contribution? Did someone actually think about the design, execute a study, interpret results, and take responsibility for a claim?

This is what we call **Proof of Thought**: not a guarantee of human authorship, but a machine-readable signal that the work meets the methodological commitments its authors declared.

What we do not certify is the physical reality of a study, the originality of the prose, or the identity of the tools used to produce it. Those questions belong to community judgment, ethics boards, and peer review — not to a methodological audit layer.

What we do certify is harder to fake than any of the above: that a claim is grounded, a method is stated, a conclusion follows from the evidence, and the work is open enough to be challenged. A paper that cannot pass these checks has not earned the right to ask for trust — regardless of how it was written or by whom.

## Included system capabilities

This release includes:

- intake paths for supported document types
- certification bundle generation
- canonical `certificate.json`
- provenance artifacts including manifest, bindings, and attestation
- bundle verification through script and API
- trust-tier recomputation during verification
- transparency-log inclusion and checkpoint verification
- witness-style multi-verifier receipts
- UI-level verification visibility
- gold-set and evaluation harnesses
- real-paper evaluation harness scaffolding
- documentation for external calibration as a separate future layer

## Canonical interpretation of artifacts

Within a certification bundle, the canonical artifact is the machine-readable certificate and its stable provenance-linked records.

Rendered views such as HTML or Markdown reports are convenience outputs for human reading. They are not authoritative truth anchors and must not be treated as canonical evidence in place of the certificate and its provenance records.

## What this release does **not** claim

This release does **not** claim:

- production readiness
- external audit completion
- truth-validation of scientific claims
- authorship detection
- AI-origin detection
- hand-labeled real-paper validation completeness
- public checkpoint publication as a finished external witness layer

These remain out of scope for the PoC freeze.

## Known limitations

The following are intentionally not closed in this release:

- no hand-labeled real-paper benchmark corpus is yet frozen into the repo
- the external calibration note is present only as a skeleton
- published external checkpoints are modeled, but not yet fully operationalized as a public reference layer
- production-grade hardening, deployment discipline, and external witness publication remain future work

## Why freeze here

A PoC must eventually stop expanding and become legible.

This release freezes the operating-system layer because the architecture is now coherent enough to support the next phase of work without constant foundational redesign. From this point onward, the strongest next steps are empirical validation, external calibration, public packaging, and release hardening.

## Recommended next phase

The work after `v0.5.0-rc2` should focus on:

1. hand-labeled real-paper validation
2. experimental validity accompanying note / external calibration note
3. public checkpoint publication
4. production-grade release discipline and hardening

## Final status statement

**Audit-Proof v0.5.0-rc2 is the first internally coherent milestone of the certification operating system.**  
It supports standards-bound certification, canonical bundle generation, attestation, verification, transparency logging, and witness-style multi-verifier checks.  
It is a PoC freeze release candidate, not a production release.
