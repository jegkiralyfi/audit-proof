from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict, dataclass, field

from packages.checks.base import CheckRunner
from packages.checks.runners.computational import ComputationalSignalCheckRunner
from packages.checks.runners.formal_proof import FormalProofSemanticAuditRunner
from packages.checks.runners.llm_evidence import LLMEvidenceCheckRunner
from packages.checks.runners.not_implemented import NotImplementedRunner
from packages.checks.runners.pattern import PatternCheckRunner
from packages.checks.runners.references import ReferenceIntegrityCheckRunner
from packages.checks.runners.repo2docker import Repo2DockerCheckRunner
from packages.checks.plugin_loader import load_configured_plugins

RunnerFactory = Callable[[], CheckRunner]


@dataclass
class RunnerDescriptor:
    runner_type: str
    factory: RunnerFactory
    runner_family: str = 'generic'
    execution_mode: str = 'deterministic'
    capabilities: list[str] = field(default_factory=list)
    implementation: str | None = None
    description: str = ''
    source_kind: str = 'builtin'
    source_module: str | None = None

    def to_public_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload.pop('factory', None)
        return payload


class CheckRunnerRegistry:
    """Registry that resolves policy-declared runner types into executable check runners."""

    def __init__(self) -> None:
        self._descriptors: dict[str, RunnerDescriptor] = {}

    def register(
        self,
        runner_type: str,
        factory: RunnerFactory,
        *,
        runner_family: str = 'generic',
        execution_mode: str = 'deterministic',
        capabilities: list[str] | None = None,
        implementation: str | None = None,
        description: str = '',
        source_kind: str = 'builtin',
        source_module: str | None = None,
    ) -> None:
        key = runner_type.strip().lower()
        self._descriptors[key] = RunnerDescriptor(
            runner_type=key,
            factory=factory,
            runner_family=runner_family,
            execution_mode=execution_mode,
            capabilities=sorted(set(capabilities or [])),
            implementation=implementation,
            description=description,
            source_kind=source_kind,
            source_module=source_module,
        )

    def has(self, runner_type: str) -> bool:
        return runner_type.strip().lower() in self._descriptors

    def create(self, runner_type: str) -> CheckRunner:
        descriptor = self.describe(runner_type)
        if descriptor is None:
            return NotImplementedRunner()
        return descriptor.factory()

    def describe(self, runner_type: str) -> RunnerDescriptor | None:
        return self._descriptors.get(runner_type.strip().lower())

    def available_types(self) -> list[str]:
        return sorted(self._descriptors.keys())

    def list_descriptors(self) -> list[dict[str, object]]:
        return [self._descriptors[key].to_public_dict() for key in sorted(self._descriptors.keys())]


_DEFAULT_REGISTRY: CheckRunnerRegistry | None = None


def build_default_registry() -> CheckRunnerRegistry:
    registry = CheckRunnerRegistry()
    registry.register(
        'pattern_check',
        PatternCheckRunner,
        runner_family='pattern',
        execution_mode='deterministic',
        capabilities=['evidence-spans', 'regex-signals', 'section-scoped'],
        implementation='packages.checks.runners.pattern.PatternCheckRunner',
        description='Deterministic pattern-based checker for first-tier evidence signals.',
    )
    registry.register(
        'rule_check',
        PatternCheckRunner,
        runner_family='pattern',
        execution_mode='deterministic',
        capabilities=['evidence-spans', 'regex-signals', 'section-scoped'],
        implementation='packages.checks.runners.pattern.PatternCheckRunner',
        description='Alias of the generic pattern-based checker.',
    )
    registry.register(
        'llm_evidence_check',
        LLMEvidenceCheckRunner,
        runner_family='llm-assisted',
        execution_mode='llm-assisted',
        capabilities=['evidence-spans', 'heuristic-fallback', 'prompted-audit'],
        implementation='packages.checks.runners.llm_evidence.LLMEvidenceCheckRunner',
        description='Evidence-oriented LLM-assisted checker with offline fallback.',
    )
    registry.register(
        'llm_interpretation_check',
        LLMEvidenceCheckRunner,
        runner_family='llm-assisted',
        execution_mode='llm-assisted',
        capabilities=['evidence-spans', 'heuristic-fallback', 'interpretation-audit'],
        implementation='packages.checks.runners.llm_evidence.LLMEvidenceCheckRunner',
        description='Interpretation-focused LLM-assisted checker with offline fallback.',
    )
    registry.register(
        'computational_signal_check',
        ComputationalSignalCheckRunner,
        runner_family='computational',
        execution_mode='deterministic',
        capabilities=['reproducibility-signals', 'artifact-discovery', 'section-scoped'],
        implementation='packages.checks.runners.computational.ComputationalSignalCheckRunner',
        description='Detects first-tier reproducibility signals in computational papers.',
    )
    registry.register(
        'reference_integrity_check',
        ReferenceIntegrityCheckRunner,
        runner_family='references',
        execution_mode='deterministic',
        capabilities=['reference-section-detection', 'citation-signals', 'doi-url-richness', 'literature-audit'],
        implementation='packages.checks.runners.references.ReferenceIntegrityCheckRunner',
        description='First-tier literature-reference audit for references sections, in-text citations, and DOI/URL richness.',
    )
    registry.register(
        'formal_semantic_audit_check',
        FormalProofSemanticAuditRunner,
        runner_family='formal-proof',
        execution_mode='deterministic',
        capabilities=['semantic-placeholder-audit', 'formal-proof-load-audit', 'anti-castle-signals'],
        implementation='packages.checks.runners.formal_proof.FormalProofSemanticAuditRunner',
        description='Deterministic audit of theorem-prover artifacts for vacuous placeholders, surface pressure, and semantic load-bearingness signals.',
    )

    registry.register(
        'repo2docker_check',
        Repo2DockerCheckRunner,
        runner_family='execution',
        execution_mode='preflight-attempt',
        capabilities=['repo2docker-readiness', 'artifact-discovery', 'execution-trail', 'execution-attempt-stub', 'plan-generation'],
        implementation='packages.checks.runners.repo2docker.Repo2DockerCheckRunner',
        description='Preflight execution-attempt stub for a future repo2docker-based lane.',
    )
    load_configured_plugins(registry)
    return registry


def get_default_registry() -> CheckRunnerRegistry:
    global _DEFAULT_REGISTRY
    if _DEFAULT_REGISTRY is None:
        _DEFAULT_REGISTRY = build_default_registry()
    return _DEFAULT_REGISTRY
