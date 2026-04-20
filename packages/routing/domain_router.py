from __future__ import annotations

from packages.checks.domains.computational.workflow import ComputationalWorkflow
from packages.checks.domains.formal_proof.workflow import FormalProofWorkflow
from packages.checks.domains.psychology.workflow import PsychologyWorkflow
from packages.checks.domains.quant_experimental.workflow import QuantExperimentalWorkflow
from packages.core.errors import UnsupportedDomainError
from packages.routing.domain_registry import get_domain_policy, normalize_domain


WORKFLOWS = {
    'quant_experimental': QuantExperimentalWorkflow,
    'psychology': PsychologyWorkflow,
    'computational': ComputationalWorkflow,
    'formal_proof': FormalProofWorkflow,
}


def get_workflow(domain: str):
    normalized = normalize_domain(domain)
    if normalized not in WORKFLOWS:
        raise UnsupportedDomainError(f"Unsupported domain for PoC: {domain}")
    policy = get_domain_policy(normalized)
    return WORKFLOWS[normalized](policy=policy)
