from packages.checks.runners.formal_proof import audit_formal_proof_text, FormalProofSemanticAuditRunner
from packages.core.models import PolicyCheck
from packages.ingest.parser import parse_text_to_document


def test_audit_formal_proof_text_detects_true_markers_and_empty_props():
    text = """
    theorem fakeSurface : Prop := True
    structure Witness where
      emptyCarrier : Prop
    lemma done : True := by
      exact True.intro
    """
    payload = audit_formal_proof_text(text)
    assert payload['true_fakes'] >= 2
    assert payload['empty_props'] >= 1
    assert payload['content_score'] <= 30
    assert 'TRUE_FAKE' in payload['issue_counts']


def test_runner_fails_when_vacuous_markers_present():
    text = "theorem fakeSurface : Prop := True\nlemma done : True := by\n  exact True.intro\n"
    document = parse_text_to_document(text=text, source_name='fake.lean', metadata={})
    runner = FormalProofSemanticAuditRunner()
    configured_check = PolicyCheck(
        id='no_vacuous_true_markers',
        required=True,
        type='formal_semantic_audit_check',
        params={
            'count_labels': ['TRUE_FAKE', 'TYPE_TRUE', 'TRUE_INTRO', 'TRIVIAL', 'EMPTY_PROP'],
            'fail_if_count_gt': 0,
            'note_on_fail': 'vacuous markers detected',
        },
    )
    result = runner.run(document=document, configured_check=configured_check, domain='formal_proof')
    assert result.status == 'fail'
    assert result.details['build_clean_is_not_content_complete'] is True
    assert result.details['formal_semantic_audit']['true_fakes'] >= 2
