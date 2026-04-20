from __future__ import annotations

from html import escape
import json

from packages.checks.common.attempts import build_execution_attempts_artifact, build_execution_plan_artifact, build_execution_receipts_artifact
from packages.core.models import Certificate, CheckResult, ExecutionAttemptsArtifact, ExecutionPlanArtifact, ExecutionReceiptsArtifact, ExecutionStubOutputsArtifact, RepositoryMetadataArtifact, ReferenceAuditArtifact, ReferenceResolutionArtifact
from packages.core.security import PROTOTYPE_SECURITY_SHORT


def _render_standard_refs(check: CheckResult) -> str:
    if not check.standard_refs:
        return ""
    items = []
    for ref in check.standard_refs:
        modules = f" | modules: {', '.join(escape(m) for m in ref.modules)}" if ref.modules else ""
        applicability = f" | applicability: {escape(ref.applicability)}" if ref.applicability else ""
        notes = f" | notes: {escape(ref.notes)}" if ref.notes else ""
        items.append(f"<li><strong>{escape(ref.standard_id)}</strong>{modules}{applicability}{notes}</li>")
    return f"<details><summary>Standard mapping</summary><ul>{''.join(items)}</ul></details>"


def _render_check(check: CheckResult) -> str:
    evidence_html = ""
    if check.evidence:
        items = []
        for ev in check.evidence:
            items.append(f"<li><strong>{escape(ev.section)}</strong>: {escape(ev.quote)}</li>")
        evidence_html = f"<details><summary>Evidence</summary><ul>{''.join(items)}</ul></details>"

    runner_meta_html = ""
    if check.runner_metadata is not None:
        caps = ', '.join(escape(cap) for cap in check.runner_metadata.capabilities) or 'none'
        source_bits = [escape(check.runner_metadata.source_kind)]
        if check.runner_metadata.source_module:
            source_bits.append(escape(check.runner_metadata.source_module))
        runner_meta_html = (
            "<div class='runner-meta'>"
            f"<p><strong>Runner:</strong> {escape(check.runner_metadata.runner_type)} (<em>{escape(check.runner_metadata.runner_family)}</em>)</p>"
            f"<p><strong>Execution mode:</strong> {escape(check.runner_metadata.execution_mode)}</p>"
            f"<p><strong>Capabilities:</strong> {caps}</p>"
            f"<p><strong>Source:</strong> {' | '.join(source_bits)}</p>"
            "</div>"
        )

    details_html = ""
    if check.details:
        payload = escape(json.dumps(check.details, indent=2, sort_keys=True, default=str))
        details_html = f"<details><summary>Runner details</summary><pre>{payload}</pre></details>"

    standard_refs_html = _render_standard_refs(check)
    return (
        f"<div class='check {escape(check.status)}'>"
        f"<h3>{escape(check.check_id)}</h3>"
        f"<p><strong>Status:</strong> {escape(check.status)} | <strong>Confidence:</strong> {check.confidence:.2f}</p>"
        f"<p>{escape(check.notes)}</p>"
        f"{runner_meta_html}"
        f"{standard_refs_html}"
        f"{details_html}"
        f"{evidence_html}"
        f"</div>"
    )


def render_html_report(
    certificate: Certificate,
    artifact_bindings: dict | None = None,
    build_provenance: dict | None = None,
    execution_plan: ExecutionPlanArtifact | None = None,
    execution_attempts: ExecutionAttemptsArtifact | None = None,
    execution_receipts: ExecutionReceiptsArtifact | None = None,
    execution_stub_outputs: ExecutionStubOutputsArtifact | None = None,
    repository_metadata: RepositoryMetadataArtifact | None = None,
    reference_audit: ReferenceAuditArtifact | None = None,
    reference_resolution: ReferenceResolutionArtifact | None = None,
) -> str:
    checks_html = "\n".join(_render_check(check) for check in certificate.checks_run)
    reasons = ''.join(f'<li>{escape(reason)}</li>' for reason in certificate.issuance.reasons) or '<li>None</li>'
    warnings = ''.join(f'<li>{escape(warning)}</li>' for warning in certificate.issuance.warnings) or '<li>None</li>'
    runner_types = ', '.join(escape(value) for value in certificate.operational_profile.runner_types) or 'none'
    runner_families = ', '.join(escape(value) for value in certificate.operational_profile.runner_families) or 'none'
    capability_classes = ', '.join(escape(value) for value in certificate.operational_profile.capability_classes) or 'none'
    execution_modes = ', '.join(escape(value) for value in certificate.operational_profile.execution_modes) or 'none'
    source_kinds = ', '.join(escape(value) for value in certificate.operational_profile.source_kinds) or 'none'
    source_modules = ', '.join(escape(value) for value in certificate.operational_profile.source_modules) or 'none'

    certification_profile_html = ''
    if certificate.certification_profile is not None:
        standards_rows = []
        for standard in certificate.certification_profile.declared_standards:
            modules = ', '.join(escape(m) for m in standard.modules) or '—'
            standards_rows.append(
                '<tr>'
                f'<td>{escape(standard.id)}</td>'
                f'<td>{escape(standard.label)}</td>'
                f'<td>{escape(standard.version or "")}</td>'
                f'<td>{escape(standard.standard_family)}</td>'
                f'<td>{escape(standard.declaration_mode)}</td>'
                f'<td>{modules}</td>'
                f'<td>{escape(standard.applicability or "")}</td>'
                '</tr>'
            )
        lanes = ', '.join(escape(v) for v in certificate.certification_profile.certification_lanes) or 'none'
        coverage_rows = []
        for check_id, refs in certificate.certification_profile.check_standard_index.items():
            rendered = []
            for ref in refs:
                modules = f" ({', '.join(escape(m) for m in ref.modules)})" if ref.modules else ""
                rendered.append(f"<li><strong>{escape(ref.standard_id)}</strong>{modules}</li>")
            coverage_rows.append(
                '<tr>'
                f'<td>{escape(check_id)}</td>'
                f"<td><ul>{''.join(rendered)}</ul></td>"
                '</tr>'
            )
        coverage_html = ""
        if coverage_rows:
            coverage_html = (
                "<h3>Check-to-standard mapping</h3>"
                "<table border='1' cellpadding='6' cellspacing='0' style='border-collapse: collapse; width: 100%;'>"
                "<thead><tr><th>Check</th><th>Standard refs</th></tr></thead>"
                f"<tbody>{''.join(coverage_rows)}</tbody></table>"
            )
        certification_profile_html = (
            "<div class='card'>"
            "<h2>Certification profile</h2>"
            f"<p><strong>Certification type:</strong> {escape(certificate.certification_profile.certification_type)}</p>"
            f"<p><strong>Scope:</strong> {escape(certificate.certification_profile.scope_label or '')}</p>"
            f"<p><strong>Lanes:</strong> {lanes}</p>"
            "<table border='1' cellpadding='6' cellspacing='0' style='border-collapse: collapse; width: 100%;'>"
            "<thead><tr><th>ID</th><th>Standard</th><th>Version</th><th>Family</th><th>Declaration</th><th>Modules</th><th>Applicability</th></tr></thead>"
            f"<tbody>{''.join(standards_rows)}</tbody></table>"
            f"{coverage_html}"
            "</div>"
        )

    trust = certificate.issuer_trust_profile
    trust_notes = ''.join(f'<li>{escape(note)}</li>' for note in trust.notes) or '<li>None</li>'
    release_verification_html = ""
    if build_provenance and (build_provenance.get("release_signature_verified") is not None or build_provenance.get("verifier_chain_present") is not None):
        release_verification_html = (
            "<div class='card'>"
            "<h2>Release verification</h2>"
            f"<p><strong>Release manifest signed:</strong> {escape(str(build_provenance.get('release_manifest_signed', False)).lower())}</p>"
            f"<p><strong>Signature verified:</strong> {escape(str(build_provenance.get('release_signature_verified', False)).lower())}</p>"
            f"<p><strong>Verifier chain present:</strong> {escape(str(build_provenance.get('verifier_chain_present', False)).lower())}</p>"
            f"<p><strong>Verifier chain verified:</strong> {escape(str(build_provenance.get('verifier_chain_verified', False)).lower())}</p>"
            f"<p><strong>Release signing key id:</strong> <code>{escape(build_provenance.get('release_signature_key_id') or 'unknown')}</code></p>"
            "</div>"
        )

    trust_card_html = (
        "<div class='card trust-card'>"
        "<h2>Issuer trust profile</h2>"
        f"<p><strong>Issuer mode:</strong> {escape(trust.issuer_mode)}</p>"
        f"<p><strong>Trust tier:</strong> {escape(trust.trust_tier)}</p>"
        f"<p><strong>Repo matches stable release:</strong> {escape(str(trust.repo_matches_release).lower())}</p>"
        f"<p><strong>Working tree clean:</strong> {escape(str(trust.working_tree_clean).lower() if trust.working_tree_clean is not None else 'unknown')}</p>"
        f"<p><strong>Release manifest signed:</strong> {escape(str(trust.release_manifest_signed).lower())}</p>"
        f"<p><strong>Release signature verified:</strong> {escape(str(trust.release_signature_verified).lower())}</p>"
        f"<p><strong>Verifier chain present:</strong> {escape(str(trust.verifier_chain_present).lower())}</p>"
        f"<p><strong>Verifier chain verified:</strong> {escape(str(trust.verifier_chain_verified).lower())}</p>"
        f"<p><strong>Release signing key id:</strong> <code>{escape(trust.release_signature_key_id or 'unknown')}</code></p>"
        f"<p><strong>Runtime commit:</strong> <code>{escape(trust.runtime_commit or 'unknown')}</code></p>"
        f"<p><strong>Release commit:</strong> <code>{escape(trust.release_commit or 'unknown')}</code></p>"
        f"<p><strong>Source tree hash:</strong> <code>{escape(trust.source_tree_hash or '')}</code></p>"
        f"<p><strong>Release manifest hash:</strong> <code>{escape(trust.release_manifest_hash or '')}</code></p>"
        f"<p><strong>Red team certified:</strong> {escape(str(trust.red_team_certified).lower())}</p>"
        f"<p><strong>External audit present:</strong> {escape(str(trust.external_audit_present).lower())}</p>"
        f"<ul>{trust_notes}</ul>"
        "</div>"
    )

    build_provenance_html = ''
    if build_provenance:
        payload = escape(json.dumps(build_provenance, indent=2, sort_keys=True, default=str))
        build_provenance_html = f"<div class='card'><h2>Build provenance</h2><pre>{payload}</pre></div>"

    artifact_refs_html = ''
    if certificate.artifact_references:
        rows = []
        for ref in certificate.artifact_references:
            rows.append('<tr>'
                        f'<td>{escape(ref.artifact_name)}</td>'
                        f'<td>{escape(ref.role)}</td>'
                        f'<td><code>{escape(ref.path)}</code></td>'
                        f'<td>{escape(ref.media_type)}</td>'
                        f'<td>{escape(str(ref.optional).lower())}</td>'
                        '</tr>')
        artifact_refs_html = (
            "<div class='card'>"
            "<h2>Artifact references</h2>"
            "<table border='1' cellpadding='6' cellspacing='0' style='border-collapse: collapse; width: 100%;'>"
            "<thead><tr><th>Artifact</th><th>Role</th><th>Path</th><th>Media type</th><th>Optional</th></tr></thead>"
            f"<tbody>{''.join(rows)}</tbody></table>"
            "</div>"
        )

    artifact_bindings_html = ''
    if artifact_bindings and artifact_bindings.get('bindings'):
        rows = []
        for key, binding in sorted(artifact_bindings.get('bindings', {}).items()):
            rows.append('<tr>'
                        f'<td>{escape(key)}</td>'
                        f'<td><code>{escape(binding.get("sha256", ""))}</code></td>'
                        f'<td>{binding.get("size_bytes", "")}</td>'
                        '</tr>')
        artifact_bindings_html = (
            "<div class='card'>"
            "<h2>Artifact bindings</h2>"
            "<table border='1' cellpadding='6' cellspacing='0' style='border-collapse: collapse; width: 100%;'>"
            "<thead><tr><th>Artifact</th><th>SHA-256</th><th>Size (bytes)</th></tr></thead>"
            f"<tbody>{''.join(rows)}</tbody></table>"
            "</div>"
        )

    if execution_plan is None:
        execution_plan = build_execution_plan_artifact(certificate)
    execution_plan_html = ''
    if execution_plan is not None:
        rows = []
        for entry in execution_plan.entries:
            rows.append(
                '<tr>'
                f'<td>{escape(entry.check_id)}</td>'
                f'<td>{escape(entry.attempt_kind)}</td>'
                f'<td>{escape(entry.attempt_status)}</td>'
                f'<td>{escape(entry.repository_provider or "")}</td>'
                f'<td>{escape(entry.repository_identity or "")}</td>'
                f'<td>{escape(entry.repository_url or "")}</td>'
                f'<td>{escape(entry.next_step or "")}</td>'
                '</tr>'
            )
        execution_plan_html = (
            "<div class='card'>"
            "<h2>Execution plan</h2>"
            f"<p><strong>Attempt entries:</strong> {len(execution_plan.entries)}</p>"
            "<table border='1' cellpadding='6' cellspacing='0' style='border-collapse: collapse; width: 100%;'>"
            "<thead><tr><th>Check</th><th>Attempt kind</th><th>Status</th><th>Provider</th><th>Identity</th><th>Repository</th><th>Next step</th></tr></thead>"
            f"<tbody>{''.join(rows)}</tbody></table>"
            "</div>"
        )

    if execution_attempts is None:
        execution_attempts = build_execution_attempts_artifact(execution_plan)
    execution_attempts_html = ''
    if execution_attempts is not None:
        rows = []
        for attempt in execution_attempts.attempts:
            rows.append(
                '<tr>'
                f'<td>{escape(attempt.attempt_id)}</td>'
                f'<td>{escape(attempt.source_check_id)}</td>'
                f'<td>{escape(attempt.lifecycle_status)}</td>'
                f'<td>{escape(str(attempt.executed).lower())}</td>'
                f'<td>{escape(attempt.repository_provider or "")}</td>'
                f'<td>{escape(attempt.repository_identity or "")}</td>'
                f'<td>{escape(attempt.command_preview or "")}</td>'
                '</tr>'
            )
        execution_attempts_html = (
            "<div class='card'>"
            "<h2>Execution attempt log</h2>"
            f"<p><strong>Attempt records:</strong> {len(execution_attempts.attempts)}</p>"
            "<table border='1' cellpadding='6' cellspacing='0' style='border-collapse: collapse; width: 100%;'>"
            "<thead><tr><th>Attempt id</th><th>Source check</th><th>Lifecycle</th><th>Executed</th><th>Provider</th><th>Identity</th><th>Command preview</th></tr></thead>"
            f"<tbody>{''.join(rows)}</tbody></table>"
            "</div>"
        )

    if execution_receipts is None:
        execution_receipts = build_execution_receipts_artifact(execution_attempts)
    execution_receipts_html = ''
    if execution_receipts is not None:
        rows = []
        for receipt in execution_receipts.receipts:
            produced = ', '.join(receipt.produced_files) if receipt.produced_files else ''
            rows.append(
                '<tr>'
                f'<td>{escape(receipt.receipt_id)}</td>'
                f'<td>{escape(receipt.source_attempt_id)}</td>'
                f'<td>{escape(receipt.status)}</td>'
                f'<td>{escape(receipt.execution_mode)}</td>'
                f'<td>{escape(str(receipt.executed).lower())}</td>'
                f'<td>{receipt.return_code if receipt.return_code is not None else ""}</td>'
                f'<td>{escape(produced)}</td>'
                '</tr>'
            )
        execution_receipts_html = (
            "<div class='card'>"
            "<h2>Execution receipts</h2>"
            f"<p><strong>Receipt records:</strong> {len(execution_receipts.receipts)}</p>"
            "<table border='1' cellpadding='6' cellspacing='0' style='border-collapse: collapse; width: 100%;'>"
            "<thead><tr><th>Receipt id</th><th>Source attempt</th><th>Status</th><th>Mode</th><th>Executed</th><th>Return code</th><th>Produced files</th></tr></thead>"
            f"<tbody>{''.join(rows)}</tbody></table>"
            "</div>"
        )


    reference_audit_html = ''
    if reference_audit is not None:
        rows = []
        for entry in reference_audit.entries:
            representative = '; '.join(entry.representative_references[:2])
            rows.append(
                '<tr>'
                f'<td>{escape(entry.source_check_id)}</td>'
                f'<td>{escape(entry.status)}</td>'
                f'<td>{escape(entry.references_section_name or "")}</td>'
                f'<td>{entry.reference_count}</td>'
                f'<td>{entry.in_text_citation_count}</td>'
                f'<td>{entry.doi_count}</td>'
                f'<td>{escape(entry.style_guess or "")}</td>'
                f'<td>{escape(representative)}</td>'
                '</tr>'
            )
        reference_audit_html = (
            "<div class='card'>"
            "<h2>Literature reference audit</h2>"
            f"<p><strong>Reference audit entries:</strong> {len(reference_audit.entries)}</p>"
            "<table border='1' cellpadding='6' cellspacing='0' style='border-collapse: collapse; width: 100%;'>"
            "<thead><tr><th>Source check</th><th>Status</th><th>Section</th><th>References</th><th>In-text citations</th><th>DOIs</th><th>Style guess</th><th>Representative references</th></tr></thead>"
            f"<tbody>{''.join(rows)}</tbody></table>"
            "</div>"
        )

    reference_resolution_html = ''
    if reference_resolution is not None:
        rows = []
        for entry in reference_resolution.entries:
            rows.append(
                '<tr>'
                f'<td>{escape(entry.source_check_id)}</td>'
                f'<td>{escape(entry.doi_normalized or entry.doi_original or "")}</td>'
                f'<td>{escape(entry.resolution_status)}</td>'
                f'<td>{escape(entry.crossref_title or "")}</td>'
                f'<td>{escape(entry.crossref_journal or "")}</td>'
                f'<td>{entry.crossref_published_year if entry.crossref_published_year is not None else ""}</td>'
                '</tr>'
            )
        reference_resolution_html = (
            "<div class='card'>"
            "<h2>Reference DOI resolution</h2>"
            f"<p><strong>Resolution entries:</strong> {len(reference_resolution.entries)}</p>"
            "<table border='1' cellpadding='6' cellspacing='0' style='border-collapse: collapse; width: 100%;'>"
            "<thead><tr><th>Source check</th><th>DOI</th><th>Status</th><th>Crossref title</th><th>Journal</th><th>Year</th></tr></thead>"
            f"<tbody>{''.join(rows)}</tbody></table>"
            "</div>"
        )

    repository_metadata_html = ''
    if repository_metadata is not None:
        rows = []
        for repo in repository_metadata.repositories:
            rows.append(
                '<tr>'
                f'<td>{escape(repo.source_check_id)}</td>'
                f'<td>{escape(repo.repository_provider or "")}</td>'
                f'<td>{escape(repo.repository_identity or "")}</td>'
                f'<td>{escape(repo.normalized_full_name or "")}</td>'
                f'<td>{escape(repo.fetch_status)}</td>'
                f'<td>{repo.stars if repo.stars is not None else ""}</td>'
                f'<td>{escape(repo.default_branch or "")}</td>'
                '</tr>'
            )
        repository_metadata_html = (
            "<div class='card'>"
            "<h2>Repository metadata</h2>"
            f"<p><strong>Repository records:</strong> {len(repository_metadata.repositories)}</p>"
            "<table border='1' cellpadding='6' cellspacing='0' style='border-collapse: collapse; width: 100%;'>"
            "<thead><tr><th>Source check</th><th>Provider</th><th>Identity</th><th>Normalized repo</th><th>Fetch status</th><th>Stars</th><th>Default branch</th></tr></thead>"
            f"<tbody>{''.join(rows)}</tbody></table>"
            "</div>"
        )

    execution_stub_outputs_html = ''
    if execution_stub_outputs is not None:
        rows = []
        for record in execution_stub_outputs.records:
            produced = ', '.join(record.produced_files) if record.produced_files else ''
            rows.append(
                '<tr>'
                f'<td>{escape(record.record_id)}</td>'
                f'<td>{escape(record.source_attempt_id)}</td>'
                f'<td>{escape(record.status)}</td>'
                f'<td>{escape(str(record.executed).lower())}</td>'
                f'<td>{record.return_code if record.return_code is not None else ""}</td>'
                f'<td>{escape(produced)}</td>'
                '</tr>'
            )
        execution_stub_outputs_html = (
            "<div class='card'>"
            "<h2>Execution stub outputs</h2>"
            f"<p><strong>Output records:</strong> {len(execution_stub_outputs.records)}</p>"
            "<table border='1' cellpadding='6' cellspacing='0' style='border-collapse: collapse; width: 100%;'>"
            "<thead><tr><th>Record id</th><th>Source attempt</th><th>Status</th><th>Executed</th><th>Return code</th><th>Produced files</th></tr></thead>"
            f"<tbody>{''.join(rows)}</tbody></table>"
            "</div>"
        )

    return f"""
<!doctype html>
<html>
<head>
<meta charset='utf-8'>
<title>Audit-Proof Certificate</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 2rem; max-width: 1100px; }}
.warning-banner {{ background: #7f1d1d; color: white; padding: 1rem; border-radius: 8px; margin-bottom: 1rem; font-weight: bold; }}
.pass {{ border-left: 4px solid #2e7d32; padding-left: 1rem; margin-bottom: 1rem; }}
.warning {{ border-left: 4px solid #ed6c02; padding-left: 1rem; margin-bottom: 1rem; }}
.fail {{ border-left: 4px solid #d32f2f; padding-left: 1rem; margin-bottom: 1rem; }}
.not_applicable, .error {{ border-left: 4px solid #455a64; padding-left: 1rem; margin-bottom: 1rem; }}
code {{ background: #f3f3f3; padding: .1rem .3rem; }}
.card {{ background: #fafafa; border: 1px solid #ddd; padding: 1rem; margin-bottom: 1rem; }}
.runner-meta {{ background: #fff; border: 1px dashed #ddd; padding: .6rem .8rem; margin: .75rem 0; }}
.grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }}
</style>
</head>
<body>
<div class='warning-banner'>{escape(PROTOTYPE_SECURITY_SHORT)}<br/>{escape(certificate.security_notice)}<br/>VIEW ONLY — verify the signed JSON payload, artifact bindings, and build provenance before relying on this report.</div>
<h1>Audit-Proof Certificate</h1>
<p><strong>Title:</strong> {escape(certificate.title or 'Untitled document')}</p>
<p><strong>Domain:</strong> {escape(certificate.domain)} | <strong>Tier:</strong> {escape(certificate.tier)}</p>
<p><strong>Issuance:</strong> {escape(certificate.issuance.status)}</p>
<p><strong>Document hash:</strong> <code>{escape(certificate.doc_hash)}</code></p>
<p><strong>Certificate hash:</strong> <code>{escape(certificate.cert_hash or '')}</code></p>
<p><strong>Metadata source:</strong> {escape(certificate.provenance.metadata_source)}</p>
<p><strong>Summary:</strong> {certificate.summary.passed} passed, {certificate.summary.warnings} warnings, {certificate.summary.failed} failed, {certificate.summary.errors} errors</p>
<div class='grid'>
<div class='card'>
<h2>Issuance decision</h2>
<p><strong>Status:</strong> {escape(certificate.issuance.status)}</p>
<p><strong>Reasons:</strong></p>
<ul>{reasons}</ul>
<p><strong>Warnings:</strong></p>
<ul>{warnings}</ul>
</div>
<div class='card'>
<h2>Operational profile</h2>
<p><strong>Policy version:</strong> {escape(certificate.provenance.policy_version)}</p>
<p><strong>Runner types:</strong> {runner_types}</p>
<p><strong>Runner families:</strong> {runner_families}</p>
<p><strong>Capability classes:</strong> {capability_classes}</p>
<p><strong>Execution modes:</strong> {execution_modes}</p>
<p><strong>Source kinds:</strong> {source_kinds}</p>
<p><strong>Source modules:</strong> {source_modules}</p>
<p><strong>Required / optional checks:</strong> {certificate.operational_profile.required_checks} / {certificate.operational_profile.optional_checks}</p>
</div>
</div>
{certification_profile_html}
{trust_card_html}
{build_provenance_html}
{release_verification_html}
{artifact_refs_html}
{artifact_bindings_html}
{reference_audit_html}
{reference_resolution_html}
{repository_metadata_html}
{execution_plan_html}
{execution_attempts_html}
{execution_receipts_html}
{execution_stub_outputs_html}
<h2>Checks</h2>
{checks_html}
</body>
</html>
""".strip()
