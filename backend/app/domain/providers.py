"""
Domain layer: the set of supported AI providers and their static metadata
(default models, whether they need a base URL, etc). No I/O here.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Provider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    MISTRAL = "mistral"
    GROQ = "groq"
    DEEPSEEK = "deepseek"
    OPENROUTER = "openrouter"
    CUSTOM = "custom"


@dataclass(frozen=True)
class ProviderMetadata:
    id: Provider
    label: str
    default_model: str
    models: tuple[str, ...]
    default_base_url: str | None
    requires_base_url: bool
    supports_custom_model: bool = True
    supports_temperature: bool = True


PROVIDER_REGISTRY: dict[Provider, ProviderMetadata] = {
    Provider.OPENAI: ProviderMetadata(
        id=Provider.OPENAI,
        label="OpenAI",
        default_model="gpt-4.1",
        models=("gpt-4.1", "gpt-4.1-mini", "gpt-4o", "gpt-4o-mini", "o3-mini"),
        default_base_url=None,
        requires_base_url=False,
    ),
    Provider.ANTHROPIC: ProviderMetadata(
        id=Provider.ANTHROPIC,
        label="Anthropic Claude",
        default_model="claude-sonnet-4-6",
        models=("claude-sonnet-4-6", "claude-opus-4-6", "claude-haiku-4-5-20251001"),
        default_base_url=None,
        requires_base_url=False,
    ),
    Provider.GEMINI: ProviderMetadata(
        id=Provider.GEMINI,
        label="Google Gemini",
        default_model="gemini-2.5-flash",
        models=("gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash"),
        default_base_url=None,
        requires_base_url=False,
    ),
    Provider.MISTRAL: ProviderMetadata(
        id=Provider.MISTRAL,
        label="Mistral AI",
        default_model="mistral-large-latest",
        models=("mistral-large-latest", "mistral-small-latest", "codestral-latest"),
        default_base_url="https://api.mistral.ai/v1",
        requires_base_url=False,
    ),
    Provider.GROQ: ProviderMetadata(
        id=Provider.GROQ,
        label="Groq",
        default_model="llama-3.3-70b-versatile",
        models=("llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"),
        default_base_url="https://api.groq.com/openai/v1",
        requires_base_url=False,
    ),
    Provider.DEEPSEEK: ProviderMetadata(
        id=Provider.DEEPSEEK,
        label="DeepSeek",
        default_model="deepseek-chat",
        models=("deepseek-chat", "deepseek-reasoner"),
        default_base_url="https://api.deepseek.com",
        requires_base_url=False,
    ),
    Provider.OPENROUTER: ProviderMetadata(
        id=Provider.OPENROUTER,
        label="OpenRouter",
        default_model="openai/gpt-4.1",
        models=("openai/gpt-4.1", "anthropic/claude-sonnet-4.6", "google/gemini-2.5-flash", "meta-llama/llama-3.3-70b-instruct"),
        default_base_url="https://openrouter.ai/api/v1",
        requires_base_url=False,
    ),
    Provider.CUSTOM: ProviderMetadata(
        id=Provider.CUSTOM,
        label="Custom OpenAI-compatible API",
        default_model="",
        models=(),
        default_base_url=None,
        requires_base_url=True,
    ),
}


def get_provider_metadata(provider: Provider) -> ProviderMetadata:
    return PROVIDER_REGISTRY[provider]
