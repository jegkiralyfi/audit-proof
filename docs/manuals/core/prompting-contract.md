# Prompting contract

Audit-Proof separates three layers:
1. system / guardrail instruction
2. domain instruction
3. check-specific task instruction

## Required behavior

The model must:
- return JSON only
- never invent evidence
- prefer warning over unsupported certainty
- emit evidence spans or explicit absence of evidence

## Injection posture

Current protection is manual and prompt-level only.
This is a prototype. It is not hardened against adversarial prompt injection.
