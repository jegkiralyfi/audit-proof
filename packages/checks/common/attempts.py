from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from packages.core.hashing import sha256_text
from packages.checks.common.repo_identity import normalize_repository_identity
from packages.core.models import (
    Certificate,
    ExecutionAttemptEntry,
    ExecutionAttemptRecord,
    ExecutionAttemptsArtifact,
    ExecutionLifecycleStatus,
    ExecutionPlanArtifact,
    ExecutionReceiptRecord,
    ExecutionReceiptsArtifact,
)

VALID_ATTEMPT_STATUSES = {
    "not_attempted",
    "not_ready",
    "preflight_incomplete",
    "preflight_ready",
    "ready_without_url",
    "planned",
    "attempted",
    "succeeded",
    "failed",
}


def normalize_attempt_status(value: Any, default: str = "not_attempted") -> str:
    status = str(value or default).strip().lower()
    return status if status in VALID_ATTEMPT_STATUSES else default


def build_execution_plan_artifact(certificate: Certificate, *, bundle_id: str | None = None) -> ExecutionPlanArtifact | None:
    entries: list[ExecutionAttemptEntry] = []
    for check in certificate.checks_run:
        details = check.details or {}
        attempt_kind = details.get("attempt_kind")
        if not attempt_kind:
            continue
        runner = check.runner_metadata
        repository_url = details.get("repository_url")
        repository_provider = details.get("repository_provider")
        repo_identity = details.get("repository_identity")
        if not repo_identity and repository_url:
            repo_identity = normalize_repository_identity(repository_url, repository_provider).get('repository_identity')
        entries.append(
            ExecutionAttemptEntry(
                check_id=check.check_id,
                runner_type=runner.runner_type if runner else None,
                runner_family=runner.runner_family if runner else None,
                execution_mode=runner.execution_mode if runner else None,
                status=check.status,
                confidence=check.confidence,
                attempt_kind=str(attempt_kind),
                attempt_status=normalize_attempt_status(details.get("attempt_status")),
                repository_url=repository_url,
                repository_provider=repository_provider,
                repository_identity=repo_identity,
                candidate_urls=list(details.get("candidate_urls") or []),
                detected_signals={str(k): bool(v) for k, v in (details.get("detected_signals") or {}).items()},
                preflight_command=details.get("preflight_command"),
                next_step=details.get("next_step"),
            )
        )
    if not entries:
        return None
    return ExecutionPlanArtifact(bundle_id=bundle_id, doc_hash=certificate.doc_hash, domain=certificate.domain, entries=entries)


def _lifecycle_for_attempt(entry: ExecutionAttemptEntry) -> tuple[ExecutionLifecycleStatus, str, list[str]]:
    status = entry.attempt_status
    if status == "preflight_ready":
        return (
            "queued_stub",
            "Preflight signals indicate the execution lane could attempt a later repo2docker run.",
            [
                f"preflight status: {status}",
                "execution not yet performed in PoC mode",
                f"candidate command: {entry.preflight_command or 'n/a'}",
            ],
        )
    if status == "ready_without_url":
        return (
            "blocked",
            "Execution lane is almost ready but no repository URL was resolved.",
            [
                f"preflight status: {status}",
                "repository URL missing",
            ],
        )
    if status == "preflight_incomplete":
        return (
            "blocked",
            "Execution lane is blocked because the metadata trail is incomplete.",
            [
                f"preflight status: {status}",
                "missing one or more required execution signals",
            ],
        )
    if status == "not_ready":
        return (
            "blocked",
            "Execution lane is blocked because the paper does not advertise enough execution metadata.",
            [
                f"preflight status: {status}",
                "no execution attempt performed",
            ],
        )
    if status == "not_attempted":
        return (
            "skipped",
            "Execution lane was not attempted in this PoC run.",
            [f"preflight status: {status}"],
        )
    return (
        "queued_stub",
        "Execution lane is queued in stub mode for future integration.",
        [f"preflight status: {status}"],
    )


def build_execution_attempts_artifact(execution_plan: ExecutionPlanArtifact | None, *, bundle_id: str | None = None) -> ExecutionAttemptsArtifact | None:
    if execution_plan is None or not execution_plan.entries:
        return None
    attempts: list[ExecutionAttemptRecord] = []
    for index, entry in enumerate(execution_plan.entries, start=1):
        lifecycle_status, rationale, log_lines = _lifecycle_for_attempt(entry)
        attempts.append(
            ExecutionAttemptRecord(
                attempt_id=f"{bundle_id or 'bundle'}-attempt-{index:03d}",
                source_check_id=entry.check_id,
                attempt_kind=entry.attempt_kind,
                attempt_status=entry.attempt_status,
                lifecycle_status=lifecycle_status,
                executed=False,
                command_preview=entry.preflight_command,
                repository_url=entry.repository_url,
                repository_provider=entry.repository_provider,
                rationale=rationale,
                next_step=entry.next_step,
                generated_at=datetime.now(timezone.utc),
                log_lines=log_lines,
            )
        )
    return ExecutionAttemptsArtifact(
        bundle_id=bundle_id,
        doc_hash=execution_plan.doc_hash,
        domain=execution_plan.domain,
        attempts=attempts,
    )


def _receipt_status_for_attempt(lifecycle_status: ExecutionLifecycleStatus) -> str:
    if lifecycle_status == "queued_stub":
        return "prepared"
    if lifecycle_status == "executed_stub":
        return "stub_executed"
    if lifecycle_status == "skipped":
        return "skipped"
    return "blocked"


def build_execution_receipts_artifact(
    execution_attempts: ExecutionAttemptsArtifact | None,
    *,
    bundle_id: str | None = None,
) -> ExecutionReceiptsArtifact | None:
    if execution_attempts is None or not execution_attempts.attempts:
        return None
    receipts: list[ExecutionReceiptRecord] = []
    for index, attempt in enumerate(execution_attempts.attempts, start=1):
        command_preview = attempt.command_preview or "echo 'execution stub prepared; no external run performed'"
        receipts.append(
            ExecutionReceiptRecord(
                receipt_id=f"{bundle_id or 'bundle'}-receipt-{index:03d}",
                source_attempt_id=attempt.attempt_id,
                status=_receipt_status_for_attempt(attempt.lifecycle_status),
                execution_mode="dry-run",
                executed=attempt.lifecycle_status == "executed_stub",
                working_directory="/sandbox/dry-run",
                command_preview=command_preview,
                command_hash=sha256_text(command_preview),
                repository_url=attempt.repository_url,
                repository_provider=attempt.repository_provider,
                repository_identity=attempt.repository_identity,
                receipt_notes=(
                    "Controlled execution stub only. No external repository clone or environment build was performed."
                ),
                generated_at=datetime.now(timezone.utc),
            )
        )
    return ExecutionReceiptsArtifact(
        bundle_id=bundle_id,
        doc_hash=execution_attempts.doc_hash,
        domain=execution_attempts.domain,
        receipts=receipts,
    )
