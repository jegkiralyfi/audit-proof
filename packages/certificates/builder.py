from __future__ import annotations

from packages.certificates.hashes import compute_certificate_hash
from packages.certificates.report_html import render_html_report
from packages.certificates.schema import validate_certificate
from packages.checks.common.scoring import summarize_statuses
from packages.core.models import (
    Certificate,
    CertificateOperationalProfile,
    CertificateProvenance,
    CertificateSummary,
    CertificationProfile,
    DomainPolicy,
    ParsedDocument,
)
from packages.routing.policies import evaluate_issuance


def _build_operational_profile(policy: DomainPolicy, checks_run) -> CertificateOperationalProfile:
    runner_types = sorted({check.runner_metadata.runner_type for check in checks_run if check.runner_metadata})
    runner_families = sorted({check.runner_metadata.runner_family for check in checks_run if check.runner_metadata})
    capability_classes = sorted({cap for check in checks_run if check.runner_metadata for cap in check.runner_metadata.capabilities})
    execution_modes = sorted({check.runner_metadata.execution_mode for check in checks_run if check.runner_metadata})
    source_kinds = sorted({check.runner_metadata.source_kind for check in checks_run if check.runner_metadata})
    source_modules = sorted({check.runner_metadata.source_module for check in checks_run if check.runner_metadata and check.runner_metadata.source_module})
    required_checks = sum(1 for configured_check in policy.checks if configured_check.required)
    optional_checks = sum(1 for configured_check in policy.checks if not configured_check.required)
    return CertificateOperationalProfile(
        runner_types=runner_types,
        runner_families=runner_families,
        capability_classes=capability_classes,
        execution_modes=execution_modes,
        source_kinds=source_kinds,
        source_modules=source_modules,
        required_checks=required_checks,
        optional_checks=optional_checks,
    )


def _build_certification_profile(policy: DomainPolicy, checks_run) -> CertificationProfile | None:
    certification_type = policy.certification_type or policy.domain
    check_standard_index = {
        check.check_id: list(check.standard_refs)
        for check in checks_run
        if getattr(check, "standard_refs", None)
    }
    return CertificationProfile(
        certification_type=certification_type,
        scope_label=policy.scope_label,
        declared_standards=list(policy.declared_standards),
        certification_lanes=list(policy.certification_lanes),
        check_standard_index=check_standard_index,
    )


def build_certificate(
    document: ParsedDocument,
    domain: str,
    checks_run,
    policy: DomainPolicy,
    notes: str = '',
) -> tuple[Certificate, str]:
    status_counts = summarize_statuses(checks_run)
    summary = CertificateSummary(
        passed=status_counts.get('pass', 0),
        warnings=status_counts.get('warning', 0),
        failed=status_counts.get('fail', 0),
        not_applicable=status_counts.get('not_applicable', 0),
        errors=status_counts.get('error', 0),
    )
    issuance = evaluate_issuance(policy=policy, checks_run=checks_run)
    operational_profile = _build_operational_profile(policy=policy, checks_run=checks_run)
    certificate = Certificate(
        doc_hash=document.doc_hash,
        domain=domain,
        tier=policy.tier,
        certification_profile=_build_certification_profile(policy, checks_run),
        title=document.title,
        doi=document.metadata.get('doi'),
        checks_run=checks_run,
        summary=summary,
        issuance=issuance,
        provenance=CertificateProvenance(
            policy_version=policy.policy_version,
            metadata_source=str(document.metadata.get('metadata_source', 'user-input')),
        ),
        operational_profile=operational_profile,
        notes=notes,
    )
    certificate = validate_certificate(certificate)
    certificate.cert_hash = compute_certificate_hash(certificate)
    html_report = render_html_report(certificate)
    return certificate, html_report
