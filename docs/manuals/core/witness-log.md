# Witness log and published checkpoint

This layer sits **above** bundle issuance and the local transparency log.
It does not change issuance and it does not increase the trust tier by itself.

## Purpose

The witness layer adds three PoC capabilities:

1. multi-verifier receipts (`verification_receipts.json`)
2. append-only witness-log inclusion (`witness_record.json`)
3. a local published-checkpoint placeholder (`published_checkpoint_reference.json`)

## Why this exists

The transparency log proves local inclusion. The witness layer goes one step further and records that:

- multiple verifier views were executed,
- their result bundle was snapshotted, and
- the resulting checkpoint received a separate publication-style reference.

In this PoC the publication channel is still local. It is **not** an external witness service.

## Files

Bundle-local files:

- `verification_receipts.json`
- `witness_record.json`
- `witness_checkpoint_snapshot.json`
- `published_checkpoint_reference.json`

Workspace-level files:

- `.artifacts/witness/witness_log.jsonl`
- `.artifacts/witness/witness_checkpoint.json`
- `.artifacts/witness/published_checkpoint.json`

## Current verifier set

- `canonical_bundle_verifier_v1`
- `attestation_verifier_v1`
- `transparency_inclusion_verifier_v1`

## Important limitation

This is still a local, self-hosted witness layer. It should be read as a better PoC integrity discipline, not as an external audit or public transparency service.
