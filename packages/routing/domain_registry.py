from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

from packages.core.models import DomainPolicy


ROOT = Path(__file__).resolve().parents[2]
POLICY_DIR = ROOT / "configs" / "policies"
DOMAIN_ALIASES = {
    "psychology": "quant_experimental",
    "experimental_social_science": "quant_experimental",
    "experimental_social_sciences": "quant_experimental",
    "formal": "formal_proof",
    "lean": "formal_proof",
    "lean4": "formal_proof",
    "theorem_prover": "formal_proof",
    "formal_verification": "formal_proof",
}


@lru_cache(maxsize=1)
def load_domain_policies() -> dict[str, DomainPolicy]:
    policies: dict[str, DomainPolicy] = {}
    for path in sorted(POLICY_DIR.glob('*.yaml')):
        payload = yaml.safe_load(path.read_text(encoding='utf-8')) or {}
        policy = DomainPolicy.model_validate(payload)
        policies[policy.domain.strip().lower()] = policy
    return policies


def normalize_domain(domain: str) -> str:
    normalized = domain.strip().lower()
    return DOMAIN_ALIASES.get(normalized, normalized)


def get_domain_policy(domain: str) -> DomainPolicy:
    normalized = normalize_domain(domain)
    policies = load_domain_policies()
    if normalized not in policies:
        raise KeyError(f'No policy configured for domain: {domain}')
    return policies[normalized]


def list_domains() -> list[str]:
    return sorted(load_domain_policies().keys())
