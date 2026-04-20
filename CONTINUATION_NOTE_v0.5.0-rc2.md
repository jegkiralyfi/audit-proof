# Continuation note — v0.5.0-rc2

This release candidate freezes the first coherent PoC milestone of Audit-Proof.

## What changed

- Added `RELEASE_NOTE_v0.5.0-rc2.md`.
- Added `docs/manuals/core/release-discipline.md`.
- Added `CHANGELOG.md`.
- Updated `README.md` to reflect PoC freeze status and link the new release-discipline materials.
- Updated package version metadata to `0.5.0rc2`.

## Why this matters

Earlier builds already had the core operating-system pieces, but the repository still described itself in several places as an early skeleton. This RC closes that mismatch.

The code, the documentation, and the release framing now say the same thing: this is a PoC freeze candidate with a coherent certification OS core, not merely an exploratory repo scaffold.

## Intentionally unfinished

The following remain future work and are not being misrepresented as complete in this RC:

- hand-labeled real-paper validation corpus
- external calibration note beyond skeleton form
- real public checkpoint publication
- production-grade hardening and external audit

---

# Continuation Note — v0.5.0-rc2

This release candidate fixes two version-label consistency issues discovered during pre-GitHub release review.

## Fixes

1. `apps/api/main.py` now reports the API version as `0.5.0rc2` instead of `0.1.0`.
2. `apps/web/app.py` now displays `Audit-Proof v0.5.0 RC2` instead of the stale `v0.4.6` header.
3. `pyproject.toml` has been bumped to `0.5.0rc2` to keep machine-readable packaging metadata aligned with the API and UI surfaces.

## Why this matters

These were not functional defects in the certification flow, but they were release-discipline defects. Leaving them in place would create avoidable confusion during live testing and GitHub publication.

The purpose of `v0.5.0-rc2` is to make the release candidate externally legible and internally version-consistent.


## Release-signing note

`v0.5.0-rc2` was re-signed with a fresh self-hosted release-signing keypair because the prior RC archive did not include the private signing key needed to reproduce the signature locally. The repository continues to publish only the public verification key.
