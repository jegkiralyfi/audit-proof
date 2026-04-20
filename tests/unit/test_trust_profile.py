from packages.core.models import BuildProvenanceArtifact
from packages.provenance.trust import build_issuer_trust_profile


def test_trust_profile_repo_matched_when_release_matches() -> None:
    provenance = BuildProvenanceArtifact(
        project_root='.',
        repo_matches_release=True,
        source_tree_hash='sha256:test',
        release_manifest_hash='sha256:manifest',
    )
    trust = build_issuer_trust_profile(provenance)
    assert trust.trust_tier == 'self_hosted_repo_matched'
    assert trust.repo_matches_release is True
    assert trust.build_provenance_present is True


def test_trust_profile_self_claim_when_release_does_not_match() -> None:
    provenance = BuildProvenanceArtifact(
        project_root='.',
        repo_matches_release=False,
        source_tree_hash='sha256:test',
        release_manifest_hash='sha256:manifest',
    )
    trust = build_issuer_trust_profile(provenance)
    assert trust.trust_tier == 'self_hosted_non_audited_self_claim'
    assert trust.repo_matches_release is False
