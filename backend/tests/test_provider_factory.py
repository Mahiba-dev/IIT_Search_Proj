import pytest

from app.domain.providers import Provider
from app.infrastructure.providers.anthropic_provider import AnthropicGateway
from app.infrastructure.providers.base import UnsupportedProviderConfigError
from app.infrastructure.providers.factory import build_gateway
from app.infrastructure.providers.gemini_provider import GeminiGateway
from app.infrastructure.providers.openai_compatible import OpenAICompatibleGateway


def test_build_gateway_openai_uses_openai_compatible():
    gw = build_gateway(Provider.OPENAI, api_key="sk-test", model=None, base_url=None)
    assert isinstance(gw, OpenAICompatibleGateway)


def test_build_gateway_anthropic_uses_anthropic_gateway():
    gw = build_gateway(Provider.ANTHROPIC, api_key="test-key", model=None, base_url=None)
    assert isinstance(gw, AnthropicGateway)


def test_build_gateway_gemini_uses_gemini_gateway():
    gw = build_gateway(Provider.GEMINI, api_key="test-key", model=None, base_url=None)
    assert isinstance(gw, GeminiGateway)


def test_build_gateway_groq_defaults_base_url():
    gw = build_gateway(Provider.GROQ, api_key="gsk-test", model=None, base_url=None)
    assert isinstance(gw, OpenAICompatibleGateway)


def test_build_gateway_custom_requires_base_url():
    with pytest.raises(UnsupportedProviderConfigError):
        build_gateway(Provider.CUSTOM, api_key="key", model="some-model", base_url=None)


def test_build_gateway_custom_requires_model():
    with pytest.raises(UnsupportedProviderConfigError):
        build_gateway(Provider.CUSTOM, api_key="key", model=None, base_url="https://example.com/v1")


def test_build_gateway_custom_with_base_url_and_model_succeeds():
    gw = build_gateway(
        Provider.CUSTOM, api_key="key", model="local-llama", base_url="https://example.com/v1"
    )
    assert isinstance(gw, OpenAICompatibleGateway)
