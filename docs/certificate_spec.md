# Audit-Proof Certificate Specification (Draft v0.1)

## 1. Purpose

The Audit-Proof certificate is a machine-readable audit record attached to a scientific document or research artifact.

It does **not** certify ultimate truth.
It certifies:

- which checks were run
- under which declared policy
- on which exact source artifact
- with what outputs, evidence, and limitations

## 2. Design goals

The certificate must be:

- open
- hash-stable
- machine-readable
- human-auditable
- domain-extensible
- reducible to smaller deployments
- explicit about scope and limitations

## 3. Certificate layers

Every certificate has three conceptual layers.

### Identity layer
The exact thing audited.

Includes:
- document hash
- source filename or source URI
- DOI if present
- contributor identifier if present
- timestamp

### Policy layer
The declared audit regime.

Includes:
- domain
- tier
- policy version
- check list
- issuance ruleset version

### Outcome layer
The result of the audit.

Includes:
- per-check results
- evidence
- summary counts
- warnings
- certificate status
- certificate hash

## 4. Required top-level fields

```json
{
  "certificate_version": "0.1.0",
  "doc_hash": "sha256:...",
  "cert_hash": "sha256:...",
  "timestamp": "2026-03-17T12:34:56Z",
  "domain": "psychology",
  "tier": "method-data-statistics-interpretation",
  "policy_version": "quant-experimental-v0.1",
  "checks_run": [],
  "summary": {},
  "provenance": {},
  "artifacts": {}
}
```

## 5. Certificate semantics

### A certificate means
A declared set of checks was executed against a declared source artifact under a declared policy.

### A certificate does not mean
- that the paper is true
- that the research is important
- that publication quality is high
- that the absence of a warning proves methodological perfection

## 6. Check result model

Each check result must include:

- `check_id`
- `status`
- `confidence`
- `evidence`
- `notes`
- `checker`
- `checker_version`

Example:

```json
{
  "check_id": "quant_experimental.control_group_present",
  "status": "pass",
  "confidence": 0.92,
  "evidence": [
    {
      "section": "Methods",
      "quote": "participants were assigned to treatment and control conditions",
      "offset_start": 1082,
      "offset_end": 1152
    }
  ],
  "notes": "Control-group language detected.",
  "checker": "llm_evidence_check",
  "checker_version": "0.1.0"
}
```

## 7. Status vocabulary

Recommended base vocabulary:

- `pass`
- `fail`
- `warning`
- `not_applicable`
- `not_run`
- `uncertain`

This vocabulary should remain small and stable.

## 8. Evidence model

Every non-trivial result should bind to evidence whenever possible.

Evidence may be:
- text span evidence
- metadata evidence
- execution log evidence
- file presence evidence
- derived statistics evidence

Evidence must remain inspectable.

## 9. Summary model

The summary block should include at minimum:

- number of checks run
- number passed
- number failed
- number warnings
- certificate issuance status

Example:

```json
{
  "issued": true,
  "passed": 7,
  "failed": 1,
  "warnings": 2,
  "not_run": 0
}
```

## 10. Issuance logic

Issuance is policy-dependent.

The certificate layer should separate:

- **check outputs**
- **issuance rules**

This allows the same check results to be interpreted differently across domains or deployment contexts.

## 11. Hashing

Two hashes are fundamental.

### Document hash
Hash of the exact source document or canonical source bundle.

### Certificate hash
Hash of the canonical serialized certificate content.

Later, we may also add:
- report hash
- artifact bundle hash
- execution log hash

## 12. Provenance block

The provenance block should capture:

- parser version
- policy bundle version
- checker versions
- prompt bundle version when applicable
- model version when applicable
- runtime ID later

This is essential for reproducibility and auditability.

## 13. Artifact outputs

A certificate run may generate multiple artifacts:

- JSON certificate
- HTML report
- Markdown report
- RO-Crate package
- signing payload

The certificate should reference these outputs by stable path or URI.

## 14. Compatibility direction

The v0.1 draft should remain compatible in spirit with:

- RO-Crate for packaging
- JSON Schema for validation
- later W3C Verifiable Credentials wrapping

We should not over-standardize too early, but we should avoid dead-end proprietary structure.

## 15. Philosophy

The certificate is not a claim of authority.
It is a transparent audit artifact.

That distinction is the core of the system.


## Certification profile

Each certificate now declares a `certification_profile` containing:
- `certification_type`
- `scope_label`
- `declared_standards`
- `certification_lanes`

This allows the system to state not only what it checked, but under which accepted reporting or openness standards the audit was scoped.
