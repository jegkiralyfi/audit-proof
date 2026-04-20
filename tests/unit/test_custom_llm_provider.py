from packages.core.config import RuntimeConfig
from packages.llm.providers import EvidenceProvider, build_provider
from packages.llm.schemas import EvidenceRequest, EvidenceResponse


class DummyProvider(EvidenceProvider):
    def __init__(self, _config):
        self.name = "dummy"

    def analyze(self, request: EvidenceRequest) -> EvidenceResponse:
        return EvidenceResponse(status="pass", confidence=0.9, notes="ok", provider="dummy")


def test_custom_provider_import_path_works(monkeypatch):
    import sys
    module = type(sys)("tests.unit.fake_provider_mod")
    module.DummyProvider = DummyProvider
    sys.modules[module.__name__] = module

    cfg = RuntimeConfig(llm_provider=f"custom:{module.__name__}:DummyProvider")
    provider = build_provider(cfg)
    assert isinstance(provider, DummyProvider)
