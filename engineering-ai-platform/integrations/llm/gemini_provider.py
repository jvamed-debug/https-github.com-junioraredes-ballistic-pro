"""Gemini Provider — provedor LLM via Google Gemini API."""

from __future__ import annotations

from typing import Any

from core.contracts.llm_provider import (
    LLMConfig,
    LLMMessage,
    LLMProviderInterface,
    LLMResponse,
)


class GeminiProvider(LLMProviderInterface):
    """Provedor LLM usando Google Gemini API."""

    def __init__(self, api_key: str = "") -> None:
        self._api_key = api_key
        self._base_url = "https://generativelanguage.googleapis.com/v1beta"
        self._config = LLMConfig(provider="gemini", model="gemini-pro")

    async def generate(self, messages: list[LLMMessage], **kwargs: Any) -> LLMResponse:
        import httpx

        model = kwargs.get("model", self._config.model)
        contents = self._format_messages(messages)
        payload: dict[str, Any] = {"contents": contents}

        generation_config: dict[str, Any] = {}
        if self._config.temperature is not None:
            generation_config["temperature"] = self._config.temperature
        if self._config.max_tokens:
            generation_config["maxOutputTokens"] = self._config.max_tokens
        if generation_config:
            payload["generationConfig"] = generation_config

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self._base_url}/models/{model}:generateContent",
                params={"key": self._api_key},
                json=payload,
                timeout=60.0,
            )
            response.raise_for_status()
            data = response.json()

        candidates = data.get("candidates", [{}])
        text = ""
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            text = "".join(p.get("text", "") for p in parts)

        usage_meta = data.get("usageMetadata", {})
        return LLMResponse(
            content=text,
            model=model,
            usage={
                "prompt_tokens": usage_meta.get("promptTokenCount", 0),
                "completion_tokens": usage_meta.get("candidatesTokenCount", 0),
            },
        )

    async def stream(self, messages: list[LLMMessage], **kwargs: Any) -> Any:
        raise NotImplementedError("Gemini streaming not yet implemented")

    def configure(self, config: LLMConfig) -> None:
        self._config = config

    @property
    def provider_name(self) -> str:
        return "gemini"

    def _format_messages(self, messages: list[LLMMessage]) -> list[dict[str, Any]]:
        contents: list[dict[str, Any]] = []
        for m in messages:
            role = "model" if m.role == "assistant" else "user"
            contents.append({"role": role, "parts": [{"text": m.content}]})
        return contents
