"""OpenAI Provider — implementação para modelos OpenAI."""

from __future__ import annotations

from typing import Any, AsyncIterator

from core.contracts.llm_provider import (
    LLMConfig,
    LLMMessage,
    LLMProviderInterface,
    LLMResponse,
)


class OpenAIProvider(LLMProviderInterface):
    """Provedor OpenAI (GPT-4, GPT-4o, etc.)."""

    def __init__(self, api_key: str, base_url: str | None = None) -> None:
        self._api_key = api_key
        self._base_url = base_url

    @property
    def provider_name(self) -> str:
        return "openai"

    async def complete(
        self,
        messages: list[LLMMessage],
        config: LLMConfig,
    ) -> LLMResponse:
        try:
            from openai import AsyncOpenAI
        except ImportError as e:
            raise ImportError("Install openai: pip install 'engineering-ai-platform[openai]'") from e

        client = AsyncOpenAI(api_key=self._api_key, base_url=self._base_url)
        response = await client.chat.completions.create(
            model=config.model,
            messages=[{"role": m.role.value, "content": m.content} for m in messages],
            temperature=config.temperature,
            max_tokens=config.max_tokens,
        )

        choice = response.choices[0]
        usage = response.usage

        return LLMResponse(
            content=choice.message.content or "",
            model=config.model,
            provider=self.provider_name,
            usage={
                "prompt_tokens": usage.prompt_tokens if usage else 0,
                "completion_tokens": usage.completion_tokens if usage else 0,
            },
        )

    async def stream(
        self,
        messages: list[LLMMessage],
        config: LLMConfig,
    ) -> AsyncIterator[str]:
        try:
            from openai import AsyncOpenAI
        except ImportError as e:
            raise ImportError("Install openai: pip install 'engineering-ai-platform[openai]'") from e

        client = AsyncOpenAI(api_key=self._api_key, base_url=self._base_url)
        stream = await client.chat.completions.create(
            model=config.model,
            messages=[{"role": m.role.value, "content": m.content} for m in messages],
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            stream=True,
        )

        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def health_check(self) -> bool:
        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(api_key=self._api_key, base_url=self._base_url)
            await client.models.list()
            return True
        except Exception:
            return False
