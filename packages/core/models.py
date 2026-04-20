from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field

from packages.core.security import PROTOTYPE_SECURITY_NOTICE

TrustTier = Literal[
    "self_hosted_non_audited_self_claim",
    "self_hosted_repo_matched",
    "self_hosted_release_matched_with_provenance",
    "audited_or_witnessed",
]


class IssuerTrustProfile(BaseModel):
    issuer_mode: str = "self_hosted"
    trust_tier: TrustTier = "self_hosted_non_audited_self_claim"
    repo_url: str | None = None
    release_channel: str | None = "stable"
    release_tag: str | None = None
    release_commit: str | None = None
    runtime_commit: str | None = None
    source_tree_hash: str | None = None
    release_manifest_hash: str | None = None
    release_manifest_signed: bool = False
    release_signature_verified: bool = False
    release_signature_key_id: str | None = None
    verifier_chain_present: bool = False
    verifier_chain_verified: bool = False
    working_tree_clean: bool | None = None
    repo_matches_release: bool = False
    build_provenance_present: bool = False
    container_digest: str | None = None
    red_team_certified: bool = False
    external_audit_present: bool = False
    notes: list[str] = Field(default_factory=list)


class BuildProvenanceArtifact(BaseModel):
    artifact_version: str = "0.1.0"
    security_notice: str = PROTOTYPE_SECURITY_NOTICE
    sandbox_only: bool = True
    red_team_certified: bool = False
    prompt_injection_protection: str = "manual-only"
    project_root: str
    repo_url: str | None = None
    release_channel: str | None = "stable"
    release_tag: str | None = None
    release_commit: str | None = None
    runtime_commit: str | None = None
    source_tree_hash: str | None = None
    release_manifest_hash: str | None = None
    release_manifest_signed: bool = False
    release_signature_verified: bool = False
    release_signature_key_id: str | None = None
    verifier_chain_present: bool = False
    verifier_chain_verified: bool = False
    repo_matches_release: bool = False
    working_tree_clean: bool | None = None
    git_repo_present: bool = False
    branch: str | None = None
    file_count: int = 0
    container_digest: str | None = None
    build_command: str | None = None
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    notes: list[str] = Field(default_factory=list)
    external_audit_present: bool = False



class EvidenceSpan(BaseModel):
    section: str = Field(default="unknown")
    quote: str
    offset_start: int = Field(ge=0, default=0)
    offset_end: int = Field(ge=0, default=0)


class RunnerMetadata(BaseModel):
    runner_type: str
    runner_family: str = "generic"
    execution_mode: str = "deterministic"
    capabilities: list[str] = Field(default_factory=list)
    implementation: str | None = None
    description: str = ""
    source_kind: str = "builtin"
    source_module: str | None = None


class CheckResult(BaseModel):
    check_id: str
    status: Literal["pass", "warning", "fail", "not_applicable", "error"]
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)
    evidence: list[EvidenceSpan] = Field(default_factory=list)
    notes: str = ""
    runner_metadata: RunnerMetadata | None = None
    standard_refs: list[StandardReference] = Field(default_factory=list)
    details: dict[str, Any] = Field(default_factory=dict)


class ParsedSection(BaseModel):
    name: str
    text: str


class ParsedDocument(BaseModel):
    doc_hash: str
    title: str | None = None
    abstract: str | None = None
    sections: list[ParsedSection] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    source_name: str = ""
    raw_text: str = ""


class StandardReference(BaseModel):
    standard_id: str
    modules: list[str] = Field(default_factory=list)
    applicability: str | None = None
    notes: str | None = None


class PolicyCheck(BaseModel):
    id: str
    required: bool = True
    type: str = "rule"
    params: dict[str, Any] = Field(default_factory=dict)
    standard_refs: list[StandardReference] = Field(default_factory=list)


class IssuanceRules(BaseModel):
    fail_if: list[str] = Field(default_factory=list)
    warning_if: list[str] = Field(default_factory=list)


class StandardDeclaration(BaseModel):
    id: str
    label: str
    version: str | None = None
    standard_family: str = "reporting-guideline"
    declaration_mode: str = "full"
    modules: list[str] = Field(default_factory=list)
    applicability: str | None = None


class CertificationProfile(BaseModel):
    certification_type: str
    scope_label: str | None = None
    declared_standards: list[StandardDeclaration] = Field(default_factory=list)
    certification_lanes: list[str] = Field(default_factory=list)
    check_standard_index: dict[str, list[StandardReference]] = Field(default_factory=dict)


class DomainPolicy(BaseModel):
    domain: str
    certification_type: str | None = None
    scope_label: str | None = None
    declared_standards: list[StandardDeclaration] = Field(default_factory=list)
    certification_lanes: list[str] = Field(default_factory=list)
    tier: str
    policy_version: str = "unversioned"
    checks: list[PolicyCheck] = Field(default_factory=list)
    issuance_rules: IssuanceRules = Field(default_factory=IssuanceRules)


class IntakeRequest(BaseModel):
    doi: str | None = None
    domain: str = "quant_experimental"
    contributor_id: str | None = None
    title: str | None = None
    abstract: str | None = None
    text: str | None = None
    source_name: str = "inline-text"
    llm_provider: str | None = None
    llm_model: str | None = None
    llm_base_url: str | None = None
    llm_api_key_env: str | None = None


class ArtifactBundleRef(BaseModel):
    bundle_id: str
    bundle_dir: str
    certificate_path: str
    report_path: str
    rocrate_path: str
    manifest_path: str
    attestation_path: str
    execution_plan_path: str | None = None
    execution_attempts_path: str | None = None
    execution_receipts_path: str | None = None
    artifact_bindings_path: str | None = None
    build_provenance_path: str | None = None
    execution_stub_outputs_path: str | None = None
    release_manifest_path: str | None = None
    release_signature_path: str | None = None
    release_verification_path: str | None = None
    release_public_key_path: str | None = None
    repository_metadata_path: str | None = None
    reference_audit_path: str | None = None
    reference_resolution_path: str | None = None
    transparency_record_path: str | None = None
    transparency_checkpoint_path: str | None = None
    verification_receipts_path: str | None = None
    witness_record_path: str | None = None
    witness_checkpoint_path: str | None = None
    published_checkpoint_reference_path: str | None = None
    formal_semantic_audit_path: str | None = None


class IntakeResponse(BaseModel):
    ok: bool = True
    message: str
    certificate: dict[str, Any]
    html_report: str
    artifacts: ArtifactBundleRef | None = None


class CertificateSummary(BaseModel):
    passed: int = 0
    warnings: int = 0
    failed: int = 0
    not_applicable: int = 0
    errors: int = 0


class CertificateProvenance(BaseModel):
    checker_bundle_version: str = "0.1.0"
    parser_version: str = "0.1.0"
    model_version: str = "rule-based-v0"
    prompt_bundle_version: str = "promptless-v0"
    policy_version: str = "unversioned"
    metadata_source: str = "user-input"
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CertificateOperationalProfile(BaseModel):
    runner_types: list[str] = Field(default_factory=list)
    runner_families: list[str] = Field(default_factory=list)
    capability_classes: list[str] = Field(default_factory=list)
    execution_modes: list[str] = Field(default_factory=list)
    source_kinds: list[str] = Field(default_factory=list)
    source_modules: list[str] = Field(default_factory=list)
    required_checks: int = 0
    optional_checks: int = 0


class ArtifactReference(BaseModel):
    artifact_name: str
    path: str
    role: str
    media_type: str
    generated_by: str = "audit-proof"
    optional: bool = False


class IssuanceDecision(BaseModel):
    status: Literal["issued", "issued_with_warnings", "withheld"] = "issued"
    reasons: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    matched_fail_rules: list[str] = Field(default_factory=list)
    matched_warning_rules: list[str] = Field(default_factory=list)


class Certificate(BaseModel):
    certificate_version: str = "0.1.0"
    security_notice: str = PROTOTYPE_SECURITY_NOTICE
    sandbox_only: bool = True
    red_team_certified: bool = False
    prompt_injection_protection: str = "manual-only"
    doc_hash: str
    cert_hash: str | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    domain: str
    tier: str
    certification_profile: CertificationProfile | None = None
    title: str | None = None
    doi: str | None = None
    checks_run: list[CheckResult] = Field(default_factory=list)
    summary: CertificateSummary
    issuance: IssuanceDecision = Field(default_factory=IssuanceDecision)
    provenance: CertificateProvenance = Field(default_factory=CertificateProvenance)
    operational_profile: CertificateOperationalProfile = Field(default_factory=CertificateOperationalProfile)
    issuer_trust_profile: IssuerTrustProfile = Field(default_factory=IssuerTrustProfile)
    artifact_references: list[ArtifactReference] = Field(default_factory=list)
    notes: str = ""


AttemptStatus = Literal[
    "not_attempted",
    "not_ready",
    "preflight_incomplete",
    "preflight_ready",
    "ready_without_url",
    "planned",
    "attempted",
    "succeeded",
    "failed",
]


class ExecutionAttemptEntry(BaseModel):
    check_id: str
    runner_type: str | None = None
    runner_family: str | None = None
    execution_mode: str | None = None
    status: Literal["pass", "warning", "fail", "not_applicable", "error"]
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)
    attempt_kind: str
    attempt_status: AttemptStatus
    repository_url: str | None = None
    repository_provider: str | None = None
    repository_identity: str | None = None
    candidate_urls: list[str] = Field(default_factory=list)
    detected_signals: dict[str, bool] = Field(default_factory=dict)
    preflight_command: str | None = None
    next_step: str | None = None


class ExecutionPlanArtifact(BaseModel):
    artifact_version: str = "0.1.0"
    security_notice: str = PROTOTYPE_SECURITY_NOTICE
    sandbox_only: bool = True
    red_team_certified: bool = False
    prompt_injection_protection: str = "manual-only"
    bundle_id: str | None = None
    doc_hash: str
    domain: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    entries: list[ExecutionAttemptEntry] = Field(default_factory=list)


ExecutionLifecycleStatus = Literal[
    "blocked",
    "queued_stub",
    "skipped",
    "executed_stub",
]


class ExecutionAttemptRecord(BaseModel):
    attempt_id: str
    source_check_id: str
    attempt_kind: str
    attempt_status: AttemptStatus
    lifecycle_status: ExecutionLifecycleStatus
    executed: bool = False
    command_preview: str | None = None
    repository_url: str | None = None
    repository_provider: str | None = None
    repository_identity: str | None = None
    rationale: str = ""
    next_step: str | None = None
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    log_lines: list[str] = Field(default_factory=list)


class ExecutionAttemptsArtifact(BaseModel):
    artifact_version: str = "0.1.0"
    security_notice: str = PROTOTYPE_SECURITY_NOTICE
    sandbox_only: bool = True
    red_team_certified: bool = False
    prompt_injection_protection: str = "manual-only"
    bundle_id: str | None = None
    doc_hash: str
    domain: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    attempts: list[ExecutionAttemptRecord] = Field(default_factory=list)


ExecutionReceiptStatus = Literal[
    "prepared",
    "blocked",
    "skipped",
    "stub_executed",
    "failed",
]


class ExecutionReceiptRecord(BaseModel):
    receipt_id: str
    source_attempt_id: str
    status: ExecutionReceiptStatus
    execution_mode: str = "dry-run"
    executed: bool = False
    working_directory: str = "/sandbox/dry-run"
    command_preview: str | None = None
    command_hash: str | None = None
    repository_url: str | None = None
    repository_provider: str | None = None
    repository_identity: str | None = None
    receipt_notes: str = ""
    return_code: int | None = None
    stdout_preview: str | None = None
    stderr_preview: str | None = None
    produced_files: list[str] = Field(default_factory=list)
    started_at: datetime | None = None
    finished_at: datetime | None = None
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ExecutionReceiptsArtifact(BaseModel):
    artifact_version: str = "0.1.0"
    security_notice: str = PROTOTYPE_SECURITY_NOTICE
    sandbox_only: bool = True
    red_team_certified: bool = False
    prompt_injection_protection: str = "manual-only"
    bundle_id: str | None = None
    doc_hash: str
    domain: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    receipts: list[ExecutionReceiptRecord] = Field(default_factory=list)


ExecutionStubOutputStatus = Literal[
    "not_run",
    "blocked",
    "skipped",
    "stub_executed",
    "failed",
]


class ExecutionStubOutputRecord(BaseModel):
    record_id: str
    source_attempt_id: str
    source_receipt_id: str | None = None
    status: ExecutionStubOutputStatus
    executed: bool = False
    execution_mode: str = "local-sandbox-stub"
    working_directory: str = "/sandbox/dry-run"
    command_argv: list[str] = Field(default_factory=list)
    command_preview: str | None = None
    repository_url: str | None = None
    repository_provider: str | None = None
    repository_identity: str | None = None
    return_code: int | None = None
    stdout_preview: str | None = None
    stderr_preview: str | None = None
    produced_files: list[str] = Field(default_factory=list)
    started_at: datetime | None = None
    finished_at: datetime | None = None
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ExecutionStubOutputsArtifact(BaseModel):
    artifact_version: str = "0.1.0"
    security_notice: str = PROTOTYPE_SECURITY_NOTICE
    sandbox_only: bool = True
    red_team_certified: bool = False
    prompt_injection_protection: str = "manual-only"
    bundle_id: str | None = None
    doc_hash: str
    domain: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    records: list[ExecutionStubOutputRecord] = Field(default_factory=list)


RepositoryMetadataFetchStatus = Literal[
    "fetch_disabled",
    "normalized_only",
    "unsupported_provider",
    "fetched",
    "fetch_failed",
]


class RepositoryMetadataEntry(BaseModel):
    source_check_id: str
    repository_url: str
    repository_provider: str | None = None
    repository_identity: str | None = None
    fetch_status: RepositoryMetadataFetchStatus = "normalized_only"
    normalized_owner: str | None = None
    normalized_repo: str | None = None
    normalized_full_name: str | None = None
    api_url: str | None = None
    default_branch: str | None = None
    stars: int | None = None
    archived: bool | None = None
    visibility: str | None = None
    license_name: str | None = None
    description: str | None = None
    homepage: str | None = None
    topics: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    fetched_at: datetime | None = None


class RepositoryMetadataArtifact(BaseModel):
    artifact_version: str = "0.1.0"
    security_notice: str = PROTOTYPE_SECURITY_NOTICE
    sandbox_only: bool = True
    red_team_certified: bool = False
    prompt_injection_protection: str = "manual-only"
    bundle_id: str | None = None
    doc_hash: str
    domain: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    repositories: list[RepositoryMetadataEntry] = Field(default_factory=list)


ReferenceResolutionStatus = Literal[
    "no_doi_detected",
    "normalized_only",
    "fetch_disabled",
    "resolved",
    "resolution_failed",
]


class ReferenceResolutionEntry(BaseModel):
    source_check_id: str
    doi_original: str
    doi_normalized: str
    resolution_status: ReferenceResolutionStatus = "normalized_only"
    reference_snippet: str | None = None
    resolution_source: str = "crossref"
    crossref_title: str | None = None
    crossref_journal: str | None = None
    crossref_published_year: int | None = None
    crossref_publisher: str | None = None
    notes: list[str] = Field(default_factory=list)


class ReferenceResolutionArtifact(BaseModel):
    artifact_version: str = "0.1.0"
    security_notice: str = PROTOTYPE_SECURITY_NOTICE
    sandbox_only: bool = True
    red_team_certified: bool = False
    prompt_injection_protection: str = "manual-only"
    bundle_id: str | None = None
    doc_hash: str
    domain: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    entries: list[ReferenceResolutionEntry] = Field(default_factory=list)


class BundleSummary(BaseModel):
    security_notice: str = PROTOTYPE_SECURITY_NOTICE
    sandbox_only: bool = True
    red_team_certified: bool = False
    prompt_injection_protection: str = "manual-only"
    bundle_id: str
    created_at: str
    doc_hash: str | None = None
    domain: str | None = None
    title: str | None = None
    doi: str | None = None
    issuance_status: str | None = None
    runner_families: list[str] = Field(default_factory=list)
    capability_classes: list[str] = Field(default_factory=list)
    source_kinds: list[str] = Field(default_factory=list)
    trust_tier: str | None = None
    repo_matches_release: bool | None = None
    execution_attempts: int = 0
    summary: dict[str, int] = Field(default_factory=dict)


class BundleDetail(BaseModel):
    security_notice: str = PROTOTYPE_SECURITY_NOTICE
    sandbox_only: bool = True
    red_team_certified: bool = False
    prompt_injection_protection: str = "manual-only"
    bundle_id: str
    bundle_dir: str
    certificate: dict[str, Any] = Field(default_factory=dict)
    manifest: dict[str, Any] = Field(default_factory=dict)
    artifact_bindings: dict[str, Any] = Field(default_factory=dict)
    build_provenance: dict[str, Any] = Field(default_factory=dict)
    report_path: str | None = None
    rocrate_path: str | None = None
    attestation_path: str | None = None
    execution_plan_path: str | None = None
    execution_attempts_path: str | None = None
    execution_receipts_path: str | None = None
    artifact_bindings_path: str | None = None
    build_provenance_path: str | None = None
    execution_stub_outputs_path: str | None = None
    release_manifest_path: str | None = None
    release_signature_path: str | None = None
    release_verification_path: str | None = None
    release_public_key_path: str | None = None
    repository_metadata_path: str | None = None
    reference_audit_path: str | None = None
    reference_resolution_path: str | None = None
    transparency_record_path: str | None = None
    transparency_checkpoint_path: str | None = None
    verification_receipts_path: str | None = None
    witness_record_path: str | None = None
    witness_checkpoint_path: str | None = None
    published_checkpoint_reference_path: str | None = None
    formal_semantic_audit_path: str | None = None


class ArtifactBinding(BaseModel):
    path: str
    sha256: str
    size_bytes: int


class ArtifactBindingsDocument(BaseModel):
    artifact_version: str = "0.1.0"
    security_notice: str = PROTOTYPE_SECURITY_NOTICE
    sandbox_only: bool = True
    red_team_certified: bool = False
    prompt_injection_protection: str = "manual-only"
    bundle_id: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    bindings: dict[str, ArtifactBinding] = Field(default_factory=dict)


ReferenceAuditStatus = Literal[
    "no_references_detected",
    "references_detected",
    "references_and_citations_detected",
    "metadata_rich",
]


class ReferenceAuditEntry(BaseModel):
    source_check_id: str
    status: ReferenceAuditStatus = "no_references_detected"
    references_section_name: str | None = None
    reference_count: int = 0
    in_text_citation_count: int = 0
    doi_count: int = 0
    url_count: int = 0
    year_count: int = 0
    style_guess: str | None = None
    representative_references: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class ReferenceAuditArtifact(BaseModel):
    artifact_version: str = "0.1.0"
    security_notice: str = PROTOTYPE_SECURITY_NOTICE
    sandbox_only: bool = True
    red_team_certified: bool = False
    prompt_injection_protection: str = "manual-only"
    bundle_id: str | None = None
    doc_hash: str
    domain: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    entries: list[ReferenceAuditEntry] = Field(default_factory=list)
