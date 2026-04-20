from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from packages.core.models import CheckResult, ParsedDocument, PolicyCheck


class Workflow(ABC):
    @abstractmethod
    def run(self, document: ParsedDocument, context: dict[str, Any] | None = None) -> list[CheckResult]:
        raise NotImplementedError


class CheckRunner(ABC):
    """A pluggable runner for a single configured policy check."""

    @abstractmethod
    def run(
        self,
        document: ParsedDocument,
        configured_check: PolicyCheck,
        *,
        domain: str,
        context: dict[str, Any] | None = None,
    ) -> CheckResult:
        raise NotImplementedError
