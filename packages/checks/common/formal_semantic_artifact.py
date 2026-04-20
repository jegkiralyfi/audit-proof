from __future__ import annotations

from typing import Any

from packages.core.models import Certificate, CheckResult


def extract_formal_semantic_audit(certificate: Certificate) -> dict[str, Any] | None:
    entries: list[dict[str, Any]] = []
    total_selected_count = 0
    categories: set[str] = set()

    for check in certificate.checks_run:
        details = check.details or {}
        payload = details.get('formal_semantic_audit')
        if not isinstance(payload, dict):
            continue
        categories.add(str(payload.get('category', 'unknown')))
        selected_count = int(details.get('selected_label_count', 0) or 0)
        total_selected_count += selected_count
        entries.append(
            {
                'check_id': check.check_id,
                'status': check.status,
                'confidence': check.confidence,
                'notes': check.notes,
                'selected_label_count': selected_count,
                'selected_labels': list(details.get('selected_labels', [])),
                'semantic_rule': details.get('semantic_rule'),
                'audit': payload,
            }
        )

    if not entries:
        return None

    return {
        'artifact_version': '0.6.0',
        'domain': certificate.domain,
        'doc_hash': certificate.doc_hash,
        'certificate_hash': certificate.cert_hash,
        'build_clean_is_not_content_complete': True,
        'categories_observed': sorted(categories),
        'semantic_placeholder_events': total_selected_count,
        'entries': entries,
    }
