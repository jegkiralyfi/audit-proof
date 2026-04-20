# Release signing keys

`release_signing_public_key.pem` is the public key used to verify the current signed `release_manifest.json`.

The corresponding private key **must not** be committed.

This project currently supports self-hosted release signing for provenance and release-match verification. This is still **not** a substitute for external audit, Red Team review, or witness/transparency infrastructure.
