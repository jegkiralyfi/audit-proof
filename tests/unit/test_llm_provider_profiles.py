from packages.core.config import RuntimeConfig
from packages.llm.providers import AnthropicEvidenceProvider, GeminiEvidenceProvider, OpenAICompatibleEvidenceProvider, build_provider


def test_build_provider_supports_anthropic():
    provider = build_provider(RuntimeConfig(llm_provider="anthropic", llm_model="claude-test", llm_api_key_env="ANTHROPIC_API_KEY"))
    assert isinstance(provider, AnthropicEvidenceProvider)


def test_build_provider_supports_gemini():
    provider = build_provider(RuntimeConfig(llm_provider="gemini", llm_model="gemini-2.5-flash", llm_api_key_env="GEMINI_API_KEY"))
    assert isinstance(provider, GeminiEvidenceProvider)


def test_build_provider_supports_openai_compatible():
    provider = build_provider(RuntimeConfig(llm_provider="openai-compatible", llm_model="demo", llm_base_url="http://localhost:8000", llm_api_key_env="OPENAI_API_KEY"))
    assert isinstance(provider, OpenAICompatibleEvidenceProvider)
