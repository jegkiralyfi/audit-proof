# Transparency log and witness layer

Audit-Proof includes a local append-only transparency log for issued bundles.
This layer is **not** part of issuance and does **not** change the certificate decision.
It is a witness-style provenance layer that records that a specific bundle state was emitted and later remained reproducible.

## Why this exists

The bundle verify path already checks canonical artifact bindings, the local attestation, and trust-tier recomputation.
The transparency log adds one more question:

> Was this exact bundle state recorded in an append-only witness ledger, and does the current bundle still match that recorded state?

This is useful because it separates:

- certificate issuance
- bundle integrity
- witness/inclusion evidence

## Current PoC design

The current implementation is intentionally local and prototype-grade:

- append-only log file: `.artifacts/transparency/transparency_log.jsonl`
- signed checkpoint: `.artifacts/transparency/transparency_checkpoint.json`
- per-bundle snapshot files:
  - `transparency_record.json`
  - `transparency_checkpoint_snapshot.json`

The checkpoint is locally HMAC-signed.
This is **not** equivalent to a public transparency service, external witness, or third-party audit.

## What is logged

Each entry binds the bundle to:

- `bundle_id`
- `certificate_sha256`
- `manifest_sha256`
- `artifact_bindings_sha256`
- `attestation_sha256`
- `bundle_fingerprint_sha256`
- `trust_tier`
- `previous_entry_hash`
- `entry_hash`

The chain is linear and append-only.
Every new entry points to the previous entry hash.

## What verification checks

Transparency verification currently checks:

1. the log file exists
2. the checkpoint exists
3. the append-only chain is internally consistent
4. the checkpoint signature matches
5. the checkpoint hash matches the current log file
6. the bundle is included in the log
7. the logged bundle values still match the current bundle state
8. the bundle's snapshot files match the active log and checkpoint

## Important separation principle

This local transparency log does **not** upgrade the trust tier to `audited_or_witnessed`.
That tier remains reserved for materially stronger external evidence, such as true third-party audit, witness infrastructure, or formal Red Team hardening.

So the correct interpretation is:

- trust tier = self-hosted provenance claim quality
- transparency log = local witness/inclusion evidence

## Commands

Verify a bundle end-to-end:

```bash
python scripts/verify_bundle.py <bundle_id>
```

Verify only the transparency-log inclusion for a bundle:

```bash
python scripts/verify_transparency_log.py <bundle_id>
```

## Future direction

A stronger next step would be to replace the local checkpoint with:

- external witness service
- public append-only transparency log
- signed checkpoint publication
- multiple witness signatures
- independent verifier replay

That would justify revisiting whether a higher trust tier should depend on witness evidence.
