from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

from packages.checks.base import CheckRunner
from packages.checks.common.attempts import normalize_attempt_status
from packages.checks.common.repo_identity import normalize_repository_identity
from packages.checks.common.scoring import build_result, normalize_confidence, normalize_status
from packages.core.models import EvidenceSpan, ParsedDocument, PolicyCheck


def _compile_patterns(values: list[str]) -> list[re.Pattern[str]]:
    return [re.compile(value, flags=re.IGNORECASE | re.MULTILINE) for value in values]


def _first_match(text: str, patterns: list[str], section_name: str) -> EvidenceSpan | None:
    for pattern in _compile_patterns(patterns):
        match = pattern.search(text)
        if match:
            start, end = match.span()
            quote_start = max(0, start - 50)
            quote_end = min(len(text), end + 120)
            quote = text[quote_start:quote_end].strip().replace("\n", " ")
            return EvidenceSpan(section=section_name, quote=quote, offset_start=start, offset_end=end)
    return None


def _collect_scope(document: ParsedDocument, preferred_sections: tuple[str, ...], scope: str = "preferred") -> tuple[str, str]:
    if scope == "full_text":
        return "full_text", document.raw_text
    normalized = tuple(s.lower() for s in preferred_sections)
    chunks: list[str] = []
    names: list[str] = []
    for section in document.sections:
        if section.name.lower() in normalized:
            chunks.append(section.text)
            names.append(section.name)
    if chunks:
        return ", ".join(names), "\n\n".join(chunks)
    return "full_text", document.raw_text


def _extract_candidate_urls(text: str) -> list[str]:
    pattern = re.compile(r"https?://[^\s)\]>\"]+", flags=re.IGNORECASE)
    urls = []
    seen = set()
    for match in pattern.finditer(text):
        url = match.group(0).rstrip('.,;')
        if url not in seen:
            urls.append(url)
            seen.add(url)
    return urls


def _pick_repository_url(urls: list[str]) -> str | None:
    preferred_hosts = ("github.com", "gitlab.com", "bitbucket.org", "osf.io", "zenodo.org", "figshare.com", "softwareheritage.org")
    for url in urls:
        host = urlparse(url).netloc.lower()
        if any(h in host for h in preferred_hosts):
            return url
    return urls[0] if urls else None


def _guess_provider(url: str | None) -> str | None:
    if not url:
        return None
    host = urlparse(url).netloc.lower()
    mapping = {
        "github.com": "github",
        "gitlab.com": "gitlab",
        "bitbucket.org": "bitbucket",
        "osf.io": "osf",
        "zenodo.org": "zenodo",
        "figshare.com": "figshare",
        "softwareheritage.org": "software-heritage",
    }
    for key, value in mapping.items():
        if key in host:
            return value
    return host or None


class Repo2DockerCheckRunner(CheckRunner):
    """Execution-readiness and preflight-attempt stub for later repo2docker integration.

    This runner does not build environments yet. It issues a bounded signal about
    whether the paper advertises enough execution metadata that a future
    repo2docker-based run could plausibly be attempted, and emits a preflight
    attempt plan as structured details.
    """

    def run(
        self,
        document: ParsedDocument,
        configured_check: PolicyCheck,
        *,
        domain: str,
        context: dict[str, Any] | None = None,
    ):
        params = configured_check.params or {}
        preferred_sections = tuple(params.get("preferred_sections", []))
        search_scope = str(params.get("search_scope", "preferred"))
        section_name, text = _collect_scope(document, preferred_sections, scope=search_scope)

        artifact_patterns = list(params.get("artifact_patterns", []))
        environment_patterns = list(params.get("environment_patterns", []))
        execution_patterns = list(params.get("execution_patterns", []))
        evidence_limit = int(params.get("evidence_limit", 3))

        artifact_span = _first_match(text, artifact_patterns, section_name)
        environment_span = _first_match(text, environment_patterns, section_name)
        execution_span = _first_match(text, execution_patterns, section_name)

        evidence = [span for span in [artifact_span, environment_span, execution_span] if span][:evidence_limit]
        found = {
            "artifact": artifact_span is not None,
            "environment": environment_span is not None,
            "execution": execution_span is not None,
        }

        urls = _extract_candidate_urls(text)
        repo_url = _pick_repository_url(urls)
        provider = _guess_provider(repo_url)
        repo_identity = normalize_repository_identity(repo_url, provider).get('repository_identity') if repo_url else None

        details = {
            "attempt_kind": "repo2docker-preflight",
            "repository_url": repo_url,
            "repository_provider": provider,
            "repository_identity": repo_identity,
            "candidate_urls": urls[:10],
            "detected_signals": found,
            "preflight_command": f"repo2docker {repo_url}" if repo_url else None,
            "attempt_status": normalize_attempt_status("not_attempted"),
            "next_step": "awaiting-execution-runner",
        }

        on_pass_status = normalize_status(params.get("on_pass_status", "pass"), "pass")
        on_warning_status = normalize_status(params.get("on_warning_status", "warning"), "warning")
        on_fail_status = normalize_status(params.get("on_fail_status", "fail"), "fail")
        pass_conf = normalize_confidence(params.get("on_pass_confidence", 0.82), 0.82)
        warn_conf = normalize_confidence(params.get("on_warning_confidence", 0.68), 0.68)
        fail_conf = normalize_confidence(params.get("on_fail_confidence", 0.8), 0.8)

        note_on_pass = str(params.get("note_on_pass", "The paper advertises enough execution metadata to attempt a later repo2docker-based run."))
        note_on_warning = str(params.get("note_on_warning", "Some execution-readiness signals are present, but the future repo2docker lane would still be incomplete."))
        note_on_fail = str(params.get("note_on_fail", "The paper does not advertise enough execution metadata for a future repo2docker lane."))

        if found["artifact"] and found["environment"] and found["execution"]:
            details["attempt_status"] = normalize_attempt_status("preflight_ready" if repo_url else "ready_without_url")
            details["next_step"] = "execution-runner-can-attempt-build"
            notes = f"{note_on_pass} Found artifact, environment, and execution signals."
            return build_result(check_id=f"{domain}.{configured_check.id}", status=on_pass_status, confidence=pass_conf, evidence=evidence, notes=notes, details=details)

        if found["artifact"] and (found["environment"] or found["execution"]):
            missing = [name for name, present in found.items() if not present]
            details["attempt_status"] = normalize_attempt_status("preflight_incomplete")
            details["missing_signals"] = missing
            details["next_step"] = "augment-paper-or-repository-metadata"
            notes = f"{note_on_warning} Missing: {', '.join(missing)}."
            return build_result(check_id=f"{domain}.{configured_check.id}", status=on_warning_status, confidence=warn_conf, evidence=evidence, notes=notes, details=details)

        details["attempt_status"] = normalize_attempt_status("not_ready")
        details["missing_signals"] = [name for name, present in found.items() if not present]
        details["next_step"] = "add-repository-environment-and-execution-trail"
        notes = f"{note_on_fail} No complete execution-readiness trail was detected."
        return build_result(check_id=f"{domain}.{configured_check.id}", status=on_fail_status, confidence=fail_conf, evidence=evidence, notes=notes, details=details)
