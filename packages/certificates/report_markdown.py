from __future__ import annotations

from packages.core.models import Certificate



def render_markdown_report(certificate: Certificate) -> str:
    lines = [
        "# Audit-Proof Certificate",
        "",
        f"- **Title:** {certificate.title or 'Untitled document'}",
        f"- **Domain:** {certificate.domain}",
        f"- **Tier:** {certificate.tier}",
        f"- **Document hash:** `{certificate.doc_hash}`",
        f"- **Certificate hash:** `{certificate.cert_hash or ''}`",
        f"- **Summary:** {certificate.summary.passed} passed / {certificate.summary.warnings} warnings / {certificate.summary.failed} failed",
        "",
        "## Checks",
    ]
    for check in certificate.checks_run:
        lines.extend([
            f"### {check.check_id}",
            f"- Status: **{check.status}**",
            f"- Confidence: {check.confidence:.2f}",
            f"- Notes: {check.notes}",
            "",
        ])
    return "\n".join(lines)
