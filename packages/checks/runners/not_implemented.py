from __future__ import annotations

from packages.checks.base import CheckRunner
from packages.checks.common.scoring import build_result
from packages.core.models import ParsedDocument, PolicyCheck


class NotImplementedRunner(CheckRunner):
    """Fallback runner that keeps the OS stable when a runner is declared but not built yet."""

    def run(self, document: ParsedDocument, configured_check: PolicyCheck, *, domain: str, context: dict | None = None):
        return build_result(
            check_id=f"{domain}.{configured_check.id}",
            status="error",
            confidence=0.0,
            notes=f"Runner type '{configured_check.type}' is not implemented yet.",
        )
