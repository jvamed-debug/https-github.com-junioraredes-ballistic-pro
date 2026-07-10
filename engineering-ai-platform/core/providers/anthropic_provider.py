"""Anthropic Provider — implementação para modelos Claude."""

from __future__ import annotations

from typing import Any, AsyncIterator

from core.contracts.llm_provider import (
    LLMConfig,
    LLMMessage,
    LLMProviderInterface,
    LLMResponse,
    LLMRole,
)


class AnthropicProvider(LLMProviderInterface):
    """Provedor Anthropic (Claude Sonnet, Opus, Haiku)."""

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    @property
    def provider_name(self) -> str:
        return "anthropic"

    async def complete(
        self,
        messages: list[LLMMessage],
        config: LLMConfig,
    ) -> LLMResponse:
        try:
            from anthropic import AsyncAnthropic
        except ImportError as e:
            raise ImportError("Install anthropic: pip install 'engineering-ai-platform[anthropic]'") from e

        client = AsyncAnthropic(api_key=self._api_key)

        system_msg = ""
        chat_messages = []
        for m in messages:
            if m.role == LLMRole.SYSTEM:
                system_msg = m.content
            else:
                chat_messages.append({"role": m.role.value, "content": m.content})

        response = await client.messages.create(
            model=config.model,
            system=system_msg,
            messages=chat_messages,
            max_tokens=config.max_tokens,
            temperature=config.temperature,
        )

        return LLMResponse(
            content=response.content[0].text if response.content else "",
            model=config.model,
            provider=self.provider_name,
            usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
        )

    async def stream(
        self,
        messages: list[LLMMessage],
        config: LLMConfig,
    ) -> AsyncIterator[str]:
        try:
            from anthropic import AsyncAnthropic
        except ImportError as e:
            raise ImportError("Install anthropic: pip install 'engineering-ai-platform[anthropic]'") from e

        client = AsyncAnthropic(api_key=self._api_key)

        system_msg = ""
        chat_messages = []
        for m in messages:
            if m.role == LLMRole.SYSTEM:
                system_msg = m.content
            else:
                chat_messages.append({"role": m.role.value, "content": m.content})

        async with client.messages.stream(
            model=config.model,
            system=system_msg,
            messages=chat_messages,
            max_tokens=config.max_tokens,
            temperature=config.temperature,
        ) as stream:
            async for text in stream.text_stream:
                yield text

    async def health_check(self) -> bool:
        try:
            from anthropic import AsyncAnthropic

            client = AsyncAnthropic(api_key=self._api_key)
            await client.messages.create(
                model="claude-haiku-4-5-20251001",
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=5,
            )
            return True
        except Exception:
            return False
