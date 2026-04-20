from __future__ import annotations

from packages.checks.runners.pattern import PatternCheckRunner
from packages.core.models import CheckResult, ParsedDocument, PolicyCheck


def run_configured_pattern_check(document: ParsedDocument, configured_check: PolicyCheck) -> CheckResult:
    """Backward-compatible wrapper around the generic pattern runner."""
    return PatternCheckRunner().run(document=document, configured_check=configured_check, domain='psychology')
