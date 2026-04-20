from __future__ import annotations

from dataclasses import dataclass

from packages.core.models import CheckResult, DomainPolicy, IssuanceDecision


@dataclass
class _ParsedCondition:
    raw: str
    check_key: str
    expected_status: str


def _parse_condition(raw: str) -> _ParsedCondition | None:
    if '==' not in raw:
        return None
    left, right = raw.split('==', 1)
    check_key = left.strip()
    expected_status = right.strip().lower()
    if not check_key or not expected_status:
        return None
    return _ParsedCondition(raw=raw, check_key=check_key, expected_status=expected_status)


def _index_results(checks_run: list[CheckResult]) -> dict[str, CheckResult]:
    indexed: dict[str, CheckResult] = {}
    for check in checks_run:
        indexed[check.check_id] = check
        short_id = check.check_id.split('.')[-1]
        indexed[short_id] = check
    return indexed


def _match_condition(cond: _ParsedCondition, indexed_results: dict[str, CheckResult]) -> bool:
    check = indexed_results.get(cond.check_key)
    if check is None:
        return False
    return check.status.lower() == cond.expected_status


def evaluate_issuance(policy: DomainPolicy, checks_run: list[CheckResult]) -> IssuanceDecision:
    indexed_results = _index_results(checks_run)
    matched_fail_rules: list[str] = []
    matched_warning_rules: list[str] = []
    warnings: list[str] = []
    reasons: list[str] = []

    for raw in policy.issuance_rules.fail_if:
        parsed = _parse_condition(raw)
        if parsed and _match_condition(parsed, indexed_results):
            matched_fail_rules.append(parsed.raw)

    for raw in policy.issuance_rules.warning_if:
        parsed = _parse_condition(raw)
        if parsed and _match_condition(parsed, indexed_results):
            matched_warning_rules.append(parsed.raw)

    for configured_check in policy.checks:
        result = indexed_results.get(configured_check.id)
        if result is None:
            continue
        if configured_check.required and result.status in {'fail', 'error'}:
            reasons.append(f"Required check {configured_check.id} returned {result.status}.")
        elif configured_check.required and result.status == 'warning':
            warnings.append(f"Required check {configured_check.id} returned warning.")
        elif (not configured_check.required) and result.status in {'fail', 'warning'}:
            warnings.append(f"Optional check {configured_check.id} returned {result.status}.")

    if matched_fail_rules:
        reasons.extend([f"Matched fail rule: {rule}" for rule in matched_fail_rules])
    if matched_warning_rules:
        warnings.extend([f"Matched warning rule: {rule}" for rule in matched_warning_rules])

    any_errors = any(check.status == 'error' for check in checks_run)
    if any_errors:
        reasons.append('At least one check runner errored; withholding issuance in PoC mode.')

    if reasons:
        status = 'withheld'
    elif warnings:
        status = 'issued_with_warnings'
    else:
        status = 'issued'

    return IssuanceDecision(
        status=status,
        reasons=reasons,
        warnings=warnings,
        matched_fail_rules=matched_fail_rules,
        matched_warning_rules=matched_warning_rules,
    )
