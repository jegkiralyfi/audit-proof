from __future__ import annotations

PROTOTYPE_SECURITY_NOTICE = (
    "SANDBOX / PROTOTYPE ONLY — NOT RED TEAM CERTIFIED. "
    "Manual prompt-injection hardening only. "
    "Do not treat any certificate, artifact, report, or execution record as a hardened security boundary or production-grade validation guarantee."
)

PROTOTYPE_SECURITY_SHORT = "SANDBOX ONLY · NOT RED TEAM CERTIFIED · MANUAL PROMPT-INJECTION GUARDRAILS"

PROTOTYPE_SECURITY_FLAGS = {
    "sandbox_only": True,
    "red_team_certified": False,
    "prompt_injection_protection": "manual-only",
}
