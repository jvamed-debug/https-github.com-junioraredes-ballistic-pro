"""Ollama Provider — provedor LLM local via Ollama."""

from __future__ import annotations

from typing import Any

from core.contracts.llm_provider import (
    LLMConfig,
    LLMMessage,
    LLMProviderInterface,
    LLMResponse,
)


class OllamaProvider(LLMProviderInterface):
    """Provedor LLM usando Ollama para modelos locais."""

    def __init__(self, base_url: str = "http://localhost:11434") -> None:
        self._base_url = base_url
        self._config = LLMConfig(provider="ollama", model="llama3")

    async def generate(self, messages: list[LLMMessage], **kwargs: Any) -> LLMResponse:
        import httpx

        payload = {
            "model": kwargs.get("model", self._config.model),
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": False,
        }
        if self._config.temperature is not None:
            payload["options"] = {"temperature": self._config.temperature}

        async with httpx.AsyncClient(base_url=self._base_url) as client:
            response = await client.post("/api/chat", json=payload, timeout=120.0)
            response.raise_for_status()
            data = response.json()

        message = data.get("message", {})
        return LLMResponse(
            content=message.get("content", ""),
            model=data.get("model", self._config.model),
            usage={
                "prompt_tokens": data.get("prompt_eval_count", 0),
                "completion_tokens": data.get("eval_count", 0),
            },
        )

    async def stream(self, messages: list[LLMMessage], **kwargs: Any) -> Any:
        import httpx

        payload = {
            "model": kwargs.get("model", self._config.model),
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": True,
        }

        async with httpx.AsyncClient(base_url=self._base_url) as client:
            async with client.stream("POST", "/api/chat", json=payload, timeout=120.0) as response:
                import json as json_mod

                async for line in response.aiter_lines():
                    if line.strip():
                        chunk = json_mod.loads(line)
                        content = chunk.get("message", {}).get("content", "")
                        if content:
                            yield content

    def configure(self, config: LLMConfig) -> None:
        self._config = config

    @property
    def provider_name(self) -> str:
        return "ollama"

    async def list_models(self) -> list[str]:
        import httpx

        async with httpx.AsyncClient(base_url=self._base_url) as client:
            response = await client.get("/api/tags")
            response.raise_for_status()
            data = response.json()
        return [m.get("name", "") for m in data.get("models", [])]

    async def health_check(self) -> bool:
        import httpx

        try:
            async with httpx.AsyncClient(base_url=self._base_url) as client:
                response = await client.get("/api/tags", timeout=5.0)
                return response.status_code == 200
        except (httpx.HTTPError, OSError):
            return False
