from __future__ import annotations

import re
from typing import Any

from packages.checks.base import CheckRunner
from packages.checks.common.scoring import build_result, normalize_confidence, normalize_status
from packages.core.models import EvidenceSpan, ParsedDocument, PolicyCheck


_EMPTY_PATTERNS: list[tuple[str, str, int]] = [
    (r':=\s*True\b', 'TRUE_FAKE', 0),
    (r':\s*True\b\s*$', 'TYPE_TRUE', 0),
    (r'\bTrue\.intro\b', 'TRUE_INTRO', 0),
    (r'\btrivial\b', 'TRIVIAL', 5),
    (r'\bsorry\b', 'SORRY', 0),
    (r'\badmit\b', 'ADMIT', 0),
    (r'^\s*axiom\b(?!.*--.*\[)', 'AXIOM_NO_REF', 15),
    (r'^\s*axiom\b.*--.*\[', 'AXIOM_CITED', 60),
    (r'^\s+\w[\w\']*\s*:\s*Prop\s*$', 'EMPTY_PROP', 5),
    (r'\b(Bridge|Surface|Wrapper|Visibility|Integrated|Canonical)\b', 'SURFACE_TERM', 0),
]

_STRONG_PATTERNS: list[tuple[str, str, int]] = [
    (r'\bexact\b', 'EXACT', 80),
    (r'\bapply\b', 'APPLY', 75),
    (r'\bnorm_num\b', 'NORM_NUM', 85),
    (r'\blinarith\b', 'LINARITH', 85),
    (r'\bsimp\s*\[', 'SIMP_LEMMA', 70),
    (r'\brfl\b', 'RFL', 80),
    (r'\brefine\b', 'REFINE', 75),
    (r'\bobtain\b', 'OBTAIN', 80),
    (r'\bhave\b.*:=', 'HAVE', 75),
    (r'\bcalc\b', 'CALC', 80),
    (r'\bfunext\b', 'FUNEXT', 80),
    (r'\brcases\b', 'RCASES', 78),
    (r'\binduction\b', 'INDUCTION', 80),
]

_TRUE_FAKE_LABELS = {'TRUE_FAKE', 'TYPE_TRUE', 'TRUE_INTRO', 'TRIVIAL', 'SORRY', 'ADMIT'}


def _build_span(section: str, line: str, line_no: int, match: re.Match[str]) -> EvidenceSpan:
    start, end = match.span()
    quote = line.strip()
    return EvidenceSpan(section=section, quote=f"L{line_no}: {quote}", offset_start=start, offset_end=end)


def audit_formal_proof_text(text: str, *, section_name: str = 'full_text') -> dict[str, Any]:
    lines = text.splitlines()
    issues: list[dict[str, Any]] = []
    evidence_by_label: dict[str, list[EvidenceSpan]] = {}

    for i, line in enumerate(lines, start=1):
        for pattern, label, score in _EMPTY_PATTERNS:
            match = re.search(pattern, line, flags=re.IGNORECASE)
            if not match:
                continue
            span = _build_span(section_name, line, i, match)
            issue = {
                'line': i,
                'type': label,
                'score': score,
                'content': line.strip()[:200],
                'evidence': span,
            }
            issues.append(issue)
            evidence_by_label.setdefault(label, []).append(span)

    theorem_count = len(re.findall(r'^\s*theorem\s', text, re.MULTILINE))
    lemma_count = len(re.findall(r'^\s*lemma\s', text, re.MULTILINE))
    def_count = len(re.findall(r'^\s*def\s', text, re.MULTILINE))
    structure_count = len(re.findall(r'^\s*structure\s', text, re.MULTILINE))
    strong_count = sum(1 for pattern, _, _ in _STRONG_PATTERNS if re.search(pattern, text))

    true_fakes = sum(1 for issue in issues if issue['type'] in _TRUE_FAKE_LABELS)
    empty_props = sum(1 for issue in issues if issue['type'] == 'EMPTY_PROP')
    cited_axioms = sum(1 for issue in issues if issue['type'] == 'AXIOM_CITED')
    uncited_axioms = sum(1 for issue in issues if issue['type'] == 'AXIOM_NO_REF')
    surface_terms = sum(1 for issue in issues if issue['type'] == 'SURFACE_TERM')

    total_provable = theorem_count + lemma_count
    if def_count == 0 and total_provable == 0 and not issues:
        category = 'INFRA'
        content_score = 50
    elif true_fakes > 0 and total_provable == 0:
        category = 'EMPTY'
        content_score = 0
    elif true_fakes > total_provable:
        category = 'MOSTLY_FAKE'
        content_score = 10
    elif true_fakes > 0 and total_provable > 0:
        ratio = true_fakes / max(total_provable, 1)
        content_score = max(5, int(30 * (1 - ratio)))
        category = 'MIXED'
    elif empty_props > 0 and total_provable > 0:
        category = 'SCAFFOLD'
        content_score = 40
    elif uncited_axioms > 0:
        category = 'AXIOM_REF_NEEDED'
        content_score = 35
    elif cited_axioms > 0:
        category = 'AXIOM_CITED'
        content_score = 60
    elif total_provable > 0 and strong_count > 0:
        category = 'REAL_PROOF'
        content_score = 85
    elif total_provable > 0:
        category = 'REAL_PROOF'
        content_score = 70
    elif def_count > 0 or structure_count > 0:
        category = 'INFRA'
        content_score = 50
    else:
        category = 'UNKNOWN'
        content_score = 20

    return {
        'category': category,
        'content_score': content_score,
        'theorem_count': theorem_count,
        'lemma_count': lemma_count,
        'def_count': def_count,
        'structure_count': structure_count,
        'strong_tactics': strong_count,
        'true_fakes': true_fakes,
        'empty_props': empty_props,
        'cited_axioms': cited_axioms,
        'uncited_axioms': uncited_axioms,
        'surface_terms': surface_terms,
        'issues': [
            {
                'line': issue['line'],
                'type': issue['type'],
                'content': issue['content'],
            }
            for issue in issues
        ],
        'issue_counts': {
            label: sum(1 for issue in issues if issue['type'] == label)
            for label in sorted({issue['type'] for issue in issues})
        },
        'evidence_by_label': evidence_by_label,
    }


class FormalProofSemanticAuditRunner(CheckRunner):
    """Audit theorem-prover artifacts for semantic placeholders and surface-only closure signals."""

    def run(
        self,
        document: ParsedDocument,
        configured_check: PolicyCheck,
        *,
        domain: str,
        context: dict[str, Any] | None = None,
    ):
        params = configured_check.params or {}
        audit = audit_formal_proof_text(document.raw_text or '', section_name='full_text')
        issue_counts = audit['issue_counts']
        count_labels = [str(label) for label in params.get('count_labels', [])]
        selected_count = sum(int(issue_counts.get(label, 0)) for label in count_labels) if count_labels else 0
        max_evidence = int(params.get('evidence_limit', 3))

        evidence: list[EvidenceSpan] = []
        if count_labels:
            for label in count_labels:
                evidence.extend(audit['evidence_by_label'].get(label, [])[:max_evidence])
                if len(evidence) >= max_evidence:
                    evidence = evidence[:max_evidence]
                    break

        fail_if_count_gt = params.get('fail_if_count_gt')
        warning_if_count_gt = params.get('warning_if_count_gt')
        min_content_score = params.get('min_content_score')
        warning_content_score_below = params.get('warning_content_score_below')

        status = normalize_status(params.get('on_pass_status', 'pass'), 'pass')
        confidence = normalize_confidence(params.get('on_pass_confidence', 0.9), 0.9)
        notes = str(params.get('note_on_pass', 'Formal-proof semantic audit passed.'))

        if fail_if_count_gt is not None and selected_count > int(fail_if_count_gt):
            status = normalize_status(params.get('on_fail_status', 'fail'), 'fail')
            confidence = normalize_confidence(params.get('on_fail_confidence', 0.95), 0.95)
            notes = str(params.get('note_on_fail', 'Semantic-placeholder audit failed.'))
        elif warning_if_count_gt is not None and selected_count > int(warning_if_count_gt):
            status = normalize_status(params.get('on_warning_status', 'warning'), 'warning')
            confidence = normalize_confidence(params.get('on_warning_confidence', 0.8), 0.8)
            notes = str(params.get('note_on_warning', 'Semantic-placeholder audit raised warnings.'))
        elif min_content_score is not None and int(audit['content_score']) < int(min_content_score):
            status = normalize_status(params.get('content_fail_status', 'fail'), 'fail')
            confidence = normalize_confidence(params.get('content_fail_confidence', 0.85), 0.85)
            notes = str(params.get('content_fail_note', 'The formal artifact appears build-clean but too semantically thin for strong Proof of Thought.'))
        elif warning_content_score_below is not None and int(audit['content_score']) < int(warning_content_score_below):
            status = normalize_status(params.get('content_warning_status', 'warning'), 'warning')
            confidence = normalize_confidence(params.get('content_warning_confidence', 0.7), 0.7)
            notes = str(params.get('content_warning_note', 'The formal artifact may still be surface-heavy relative to its visible proof content.'))

        details = {
            'formal_semantic_audit': audit,
            'selected_label_count': selected_count,
            'selected_labels': count_labels,
            'semantic_rule': str(params.get('semantic_rule', configured_check.id)),
            'build_clean_is_not_content_complete': True,
        }
        return build_result(
            check_id=f"{domain}.{configured_check.id}",
            status=status,
            confidence=confidence,
            evidence=evidence,
            notes=notes,
            details=details,
        )
