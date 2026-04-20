from __future__ import annotations

import shlex
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from packages.core.hashing import sha256_text
from packages.core.models import (
    ExecutionAttemptRecord,
    ExecutionAttemptsArtifact,
    ExecutionReceiptRecord,
    ExecutionReceiptsArtifact,
    ExecutionStubOutputRecord,
    ExecutionStubOutputsArtifact,
)


def _safe_name(value: str) -> str:
    return ''.join(ch if ch.isalnum() or ch in {'-', '_'} else '_' for ch in value)


def _preview(text: str | None, limit: int = 800) -> str | None:
    if text is None:
        return None
    return text[:limit]


def _build_stub_command(attempt: ExecutionAttemptRecord, output_file: Path) -> list[str]:
    script = (
        "import json, os, platform, sys, pathlib; "
        "out = pathlib.Path(sys.argv[4]); "
        "payload = {"
        "'attempt_id': sys.argv[1], "
        "'repository_url': sys.argv[2], "
        "'repository_provider': sys.argv[3], "
        "'python_version': sys.version.split()[0], "
        "'platform': platform.platform(), "
        "'cwd': os.getcwd()}; "
        "out.write_text(json.dumps(payload, indent=2), encoding='utf-8'); "
        "print(json.dumps({'status':'stub-executed','attempt_id': sys.argv[1], 'result_file': str(out)}))"
    )
    return [
        sys.executable,
        "-c",
        script,
        attempt.attempt_id,
        attempt.repository_url or "",
        attempt.repository_provider or "",
        str(output_file),
    ]


def _nonexecuted_receipt_and_output(
    *,
    receipt_id: str,
    record_id: str,
    attempt: ExecutionAttemptRecord,
    workdir: Path,
    status: str,
    note: str,
) -> tuple[ExecutionReceiptRecord, ExecutionStubOutputRecord]:
    receipt = ExecutionReceiptRecord(
        receipt_id=receipt_id,
        source_attempt_id=attempt.attempt_id,
        status=status,
        execution_mode="local-sandbox-stub",
        executed=False,
        working_directory=str(workdir),
        command_preview=attempt.command_preview,
        command_hash=sha256_text(attempt.command_preview) if attempt.command_preview else None,
        repository_url=attempt.repository_url,
        repository_provider=attempt.repository_provider,
        receipt_notes=note,
    )
    output = ExecutionStubOutputRecord(
        record_id=record_id,
        source_attempt_id=attempt.attempt_id,
        source_receipt_id=receipt_id,
        status="blocked" if status == "blocked" else "skipped",
        executed=False,
        working_directory=str(workdir),
        command_preview=attempt.command_preview,
        repository_url=attempt.repository_url,
        repository_provider=attempt.repository_provider,
        repository_identity=attempt.repository_identity,
    )
    return receipt, output


def materialize_controlled_execution_stub(
    execution_attempts: ExecutionAttemptsArtifact | None,
    *,
    bundle_dir: str | Path,
    enabled: bool = True,
    timeout_seconds: int = 5,
) -> tuple[ExecutionAttemptsArtifact | None, ExecutionReceiptsArtifact | None, ExecutionStubOutputsArtifact | None]:
    if execution_attempts is None or not execution_attempts.attempts:
        return execution_attempts, None, None

    bundle_path = Path(bundle_dir)
    root = bundle_path / "execution_stub"
    root.mkdir(parents=True, exist_ok=True)

    receipts: list[ExecutionReceiptRecord] = []
    outputs: list[ExecutionStubOutputRecord] = []

    for index, attempt in enumerate(execution_attempts.attempts, start=1):
        receipt_id = f"{execution_attempts.bundle_id or 'bundle'}-receipt-{index:03d}"
        record_id = f"{execution_attempts.bundle_id or 'bundle'}-stub-{index:03d}"
        workdir = root / _safe_name(attempt.attempt_id)
        workdir.mkdir(parents=True, exist_ok=True)

        if not enabled:
            receipt, output = _nonexecuted_receipt_and_output(
                receipt_id=receipt_id,
                record_id=record_id,
                attempt=attempt,
                workdir=workdir,
                status="skipped",
                note="Execution stub disabled by runtime configuration.",
            )
            receipts.append(receipt)
            outputs.append(output)
            continue

        if attempt.lifecycle_status != "queued_stub":
            status = "blocked" if attempt.lifecycle_status == "blocked" else "skipped"
            receipt, output = _nonexecuted_receipt_and_output(
                receipt_id=receipt_id,
                record_id=record_id,
                attempt=attempt,
                workdir=workdir,
                status=status,
                note="No local stub execution performed for this attempt state.",
            )
            receipts.append(receipt)
            outputs.append(output)
            continue

        output_file = workdir / "stub_result.json"
        argv = _build_stub_command(attempt, output_file)
        cmd_preview = ' '.join(shlex.quote(x) for x in argv)
        started_at = datetime.now(timezone.utc)
        try:
            completed = subprocess.run(
                argv,
                cwd=workdir,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                check=False,
            )
            finished_at = datetime.now(timezone.utc)
            produced_files = []
            if output_file.exists():
                produced_files.append(str(output_file.relative_to(bundle_path)))

            if completed.returncode == 0:
                attempt.lifecycle_status = "executed_stub"
                attempt.executed = True
                attempt.log_lines.extend([
                    f"local stub executed in {workdir}",
                    f"return code: {completed.returncode}",
                ])
                receipt_status = "stub_executed"
                output_status = "stub_executed"
                receipt_note = "Controlled local stub executed successfully. No external repository clone or environment build was performed."
            else:
                attempt.lifecycle_status = "blocked"
                attempt.executed = False
                attempt.log_lines.extend([
                    f"local stub failed in {workdir}",
                    f"return code: {completed.returncode}",
                ])
                receipt_status = "failed"
                output_status = "failed"
                receipt_note = "Controlled local stub failed."

            receipt = ExecutionReceiptRecord(
                receipt_id=receipt_id,
                source_attempt_id=attempt.attempt_id,
                status=receipt_status,
                execution_mode="local-sandbox-stub",
                executed=completed.returncode == 0,
                working_directory=str(workdir),
                command_preview=cmd_preview,
                command_hash=sha256_text(cmd_preview),
                repository_url=attempt.repository_url,
                repository_provider=attempt.repository_provider,
                receipt_notes=receipt_note,
                return_code=completed.returncode,
                stdout_preview=_preview(completed.stdout),
                stderr_preview=_preview(completed.stderr),
                produced_files=produced_files,
                started_at=started_at,
                finished_at=finished_at,
            )
            output = ExecutionStubOutputRecord(
                record_id=record_id,
                source_attempt_id=attempt.attempt_id,
                source_receipt_id=receipt_id,
                status=output_status,
                executed=completed.returncode == 0,
                working_directory=str(workdir),
                command_argv=argv,
                command_preview=cmd_preview,
                repository_url=attempt.repository_url,
                repository_provider=attempt.repository_provider,
                repository_identity=attempt.repository_identity,
                return_code=completed.returncode,
                stdout_preview=_preview(completed.stdout),
                stderr_preview=_preview(completed.stderr),
                produced_files=produced_files,
                started_at=started_at,
                finished_at=finished_at,
            )
        except subprocess.TimeoutExpired as exc:
            finished_at = datetime.now(timezone.utc)
            attempt.lifecycle_status = "blocked"
            attempt.executed = False
            attempt.log_lines.append(f"local stub timed out after {timeout_seconds}s")
            receipt = ExecutionReceiptRecord(
                receipt_id=receipt_id,
                source_attempt_id=attempt.attempt_id,
                status="failed",
                execution_mode="local-sandbox-stub",
                executed=False,
                working_directory=str(workdir),
                command_preview=cmd_preview,
                command_hash=sha256_text(cmd_preview),
                repository_url=attempt.repository_url,
                repository_provider=attempt.repository_provider,
                receipt_notes=f"Controlled local stub timed out after {timeout_seconds} seconds.",
                return_code=None,
                stdout_preview=_preview(exc.stdout),
                stderr_preview=_preview(exc.stderr),
                produced_files=[],
                started_at=started_at,
                finished_at=finished_at,
            )
            output = ExecutionStubOutputRecord(
                record_id=record_id,
                source_attempt_id=attempt.attempt_id,
                source_receipt_id=receipt_id,
                status="failed",
                executed=False,
                working_directory=str(workdir),
                command_argv=argv,
                command_preview=cmd_preview,
                repository_url=attempt.repository_url,
                repository_provider=attempt.repository_provider,
                repository_identity=attempt.repository_identity,
                return_code=None,
                stdout_preview=_preview(exc.stdout),
                stderr_preview=_preview(exc.stderr),
                produced_files=[],
                started_at=started_at,
                finished_at=finished_at,
            )

        receipts.append(receipt)
        outputs.append(output)

    receipts_artifact = ExecutionReceiptsArtifact(
        bundle_id=execution_attempts.bundle_id,
        doc_hash=execution_attempts.doc_hash,
        domain=execution_attempts.domain,
        receipts=receipts,
    )
    outputs_artifact = ExecutionStubOutputsArtifact(
        bundle_id=execution_attempts.bundle_id,
        doc_hash=execution_attempts.doc_hash,
        domain=execution_attempts.domain,
        records=outputs,
    )
    return execution_attempts, receipts_artifact, outputs_artifact
