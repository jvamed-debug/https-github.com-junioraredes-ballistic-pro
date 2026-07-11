"""Provider Factory — fábrica unificada de provedores LLM."""

from __future__ import annotations

from typing import Any

from core.contracts.llm_provider import LLMConfig, LLMProviderInterface


class ProviderFactory:
    """Cria instâncias de provedores LLM baseado em configuração."""

    _registry: dict[str, type] = {}

    @classmethod
    def register(cls, name: str, provider_class: type) -> None:
        cls._registry[name] = provider_class

    @classmethod
    def create(cls, config: LLMConfig, **kwargs: Any) -> LLMProviderInterface:
        provider_name = config.provider.lower()

        if provider_name in cls._registry:
            provider = cls._registry[provider_name](**kwargs)
            provider.configure(config)
            return provider

        if provider_name == "openai":
            from core.providers.openai_provider import OpenAIProvider
            provider = OpenAIProvider(api_key=kwargs.get("api_key", ""))
            provider.configure(config)
            return provider

        if provider_name == "anthropic":
            from core.providers.anthropic_provider import AnthropicProvider
            provider = AnthropicProvider(api_key=kwargs.get("api_key", ""))
            provider.configure(config)
            return provider

        if provider_name == "ollama":
            from integrations.llm.ollama_provider import OllamaProvider
            provider = OllamaProvider(base_url=kwargs.get("base_url", "http://localhost:11434"))
            provider.configure(config)
            return provider

        if provider_name == "gemini":
            from integrations.llm.gemini_provider import GeminiProvider
            provider = GeminiProvider(api_key=kwargs.get("api_key", ""))
            provider.configure(config)
            return provider

        raise ValueError(f"Unknown provider: {provider_name}")

    @classmethod
    def available_providers(cls) -> list[str]:
        builtin = ["openai", "anthropic", "ollama", "gemini"]
        return sorted(set(builtin) | set(cls._registry.keys()))
