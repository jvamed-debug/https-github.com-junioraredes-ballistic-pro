"""LLM Provider Interface — camada de abstração para modelos de IA.

Nenhum componente pode depender diretamente de um modelo de IA específico.
Todo acesso a LLM ocorre por esta interface.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, AsyncIterator


class LLMRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass(frozen=True)
class LLMMessage:
    role: LLMRole
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class LLMResponse:
    content: str
    model: str
    provider: str
    usage: dict[str, int] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class LLMConfig:
    model: str
    temperature: float = 0.7
    max_tokens: int = 4096
    top_p: float = 1.0
    stop_sequences: list[str] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)


class LLMProviderInterface(ABC):
    """Interface abstrata para provedores de LLM."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        ...

    @abstractmethod
    async def complete(
        self,
        messages: list[LLMMessage],
        config: LLMConfig,
    ) -> LLMResponse:
        ...

    @abstractmethod
    async def stream(
        self,
        messages: list[LLMMessage],
        config: LLMConfig,
    ) -> AsyncIterator[str]:
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        ...
