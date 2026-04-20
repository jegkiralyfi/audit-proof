from __future__ import annotations

from packages.checks.base import Workflow
from packages.checks.registry import get_default_registry
from packages.core.models import CheckResult, DomainPolicy, ParsedDocument, RunnerMetadata


def _attach_runner_metadata(result: CheckResult, descriptor) -> CheckResult:
    if descriptor is None:
        return result
    result.runner_metadata = RunnerMetadata(
        runner_type=str(descriptor.runner_type),
        runner_family=str(descriptor.runner_family),
        execution_mode=str(descriptor.execution_mode),
        capabilities=list(descriptor.capabilities),
        implementation=descriptor.implementation,
        description=descriptor.description,
        source_kind=str(descriptor.source_kind),
        source_module=descriptor.source_module,
    )
    return result

def _attach_standard_refs(result: CheckResult, configured_check) -> CheckResult:
    result.standard_refs = list(configured_check.standard_refs)
    return result


class ComputationalWorkflow(Workflow):
    def __init__(self, policy: DomainPolicy):
        self.policy = policy
        self.registry = get_default_registry()

    def run(self, document: ParsedDocument, context: dict | None = None) -> list[CheckResult]:
        results: list[CheckResult] = []
        for configured_check in self.policy.checks:
            descriptor = self.registry.describe(configured_check.type)
            runner = self.registry.create(configured_check.type)
            try:
                result = runner.run(
                    document=document,
                    configured_check=configured_check,
                    domain=self.policy.domain,
                    context={
                        "policy_version": self.policy.policy_version,
                        "tier": self.policy.tier,
                        "runner_type": configured_check.type,
                        **(context or {}),
                    },
                )
                results.append(_attach_standard_refs(_attach_runner_metadata(result, descriptor), configured_check))
            except Exception as exc:
                error_result = CheckResult(
                    check_id=f"{self.policy.domain}.{configured_check.id}",
                    status='error',
                    confidence=0.0,
                    notes=f'Configured runner failed for {configured_check.id}: {exc}',
                )
                results.append(_attach_standard_refs(_attach_runner_metadata(error_result, descriptor), configured_check))
        return results
