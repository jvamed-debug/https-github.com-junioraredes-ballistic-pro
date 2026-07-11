"""Models Registry — registro centralizado de modelos e provedores LLM."""

from __future__ import annotations

import logging
from typing import Any

from core.contracts.llm_provider import LLMConfig, LLMProviderInterface

logger = logging.getLogger(__name__)


class ModelEntry:
    __slots__ = ("provider", "model_id", "config", "metadata")

    def __init__(
        self,
        provider: LLMProviderInterface,
        model_id: str,
        config: LLMConfig,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.provider = provider
        self.model_id = model_id
        self.config = config
        self.metadata = metadata or {}


class ModelsRegistry:
    """Registro centralizado de provedores e modelos disponíveis."""

    def __init__(self) -> None:
        self._models: dict[str, ModelEntry] = {}
        self._default: str | None = None

    def register(
        self,
        alias: str,
        provider: LLMProviderInterface,
        model_id: str,
        config: LLMConfig | None = None,
        metadata: dict[str, Any] | None = None,
        *,
        default: bool = False,
    ) -> None:
        entry = ModelEntry(
            provider=provider,
            model_id=model_id,
            config=config or LLMConfig(model=model_id),
            metadata=metadata,
        )
        self._models[alias] = entry
        if default or self._default is None:
            self._default = alias
        logger.info("Registered model '%s' (%s/%s)", alias, provider.provider_name, model_id)

    def get(self, alias: str) -> ModelEntry:
        if alias not in self._models:
            raise KeyError(f"Model '{alias}' not registered. Available: {list(self._models)}")
        return self._models[alias]

    def get_default(self) -> ModelEntry:
        if self._default is None:
            raise RuntimeError("No models registered")
        return self._models[self._default]

    def unregister(self, alias: str) -> None:
        self._models.pop(alias, None)
        if self._default == alias:
            self._default = next(iter(self._models), None)

    @property
    def aliases(self) -> list[str]:
        return list(self._models)

    @property
    def default_alias(self) -> str | None:
        return self._default

    async def health_check_all(self) -> dict[str, bool]:
        results: dict[str, bool] = {}
        for alias, entry in self._models.items():
            results[alias] = await entry.provider.health_check()
        return results
