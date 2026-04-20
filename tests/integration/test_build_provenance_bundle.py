from apps.api.routes.intake import intake_text
from packages.core.models import IntakeRequest


def test_build_provenance_artifact_is_persisted() -> None:
    req = IntakeRequest(
        domain='quant_experimental',
        title='Build provenance test',
        text='Methods\nParticipants (n = 40) were randomly assigned to control and treatment groups. Results\np = 0.04; Cohen\'s d = 0.5. Data available at https://osf.io/qwert/.',
    )
    response = intake_text(req)
    assert response.artifacts is not None
    assert response.certificate['issuer_trust_profile']['trust_tier'] in {
        'self_hosted_release_matched_with_provenance',
        'self_hosted_repo_matched',
        'self_hosted_non_audited_self_claim',
    }
    assert response.artifacts.build_provenance_path is not None
