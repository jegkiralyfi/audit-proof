from packages.core.models import Certificate, CertificateSummary, ExecutionPlanArtifact


def test_certificate_carries_security_notice():
    certificate = Certificate(doc_hash="sha256:test", domain="quant_experimental", tier="demo", summary=CertificateSummary())
    assert certificate.sandbox_only is True
    assert certificate.red_team_certified is False
    assert "NOT RED TEAM CERTIFIED" in certificate.security_notice


def test_execution_plan_artifact_carries_security_notice():
    artifact = ExecutionPlanArtifact(doc_hash="sha256:test", domain="computational")
    assert artifact.prompt_injection_protection == "manual-only"
