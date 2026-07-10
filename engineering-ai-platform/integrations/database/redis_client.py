"""Redis Client — integração com Redis para cache e filas."""

from __future__ import annotations

from typing import Any


class RedisClient:
    """Cliente para Redis — cache, filas e pub/sub."""

    def __init__(self, url: str = "redis://localhost:6379/0") -> None:
        self._url = url
        self._client: Any = None

    async def connect(self) -> None:
        try:
            import redis.asyncio as aioredis
            self._client = aioredis.from_url(self._url, decode_responses=True)
        except ImportError:
            raise ImportError("redis is required: pip install redis")

    async def disconnect(self) -> None:
        if self._client:
            await self._client.close()
            self._client = None

    async def get(self, key: str) -> str | None:
        if not self._client:
            raise RuntimeError("Not connected — call connect() first")
        return await self._client.get(key)

    async def set(self, key: str, value: str, ttl: int | None = None) -> None:
        if not self._client:
            raise RuntimeError("Not connected — call connect() first")
        if ttl:
            await self._client.setex(key, ttl, value)
        else:
            await self._client.set(key, value)

    async def delete(self, key: str) -> bool:
        if not self._client:
            raise RuntimeError("Not connected — call connect() first")
        return bool(await self._client.delete(key))

    async def exists(self, key: str) -> bool:
        if not self._client:
            raise RuntimeError("Not connected — call connect() first")
        return bool(await self._client.exists(key))

    async def lpush(self, key: str, *values: str) -> int:
        if not self._client:
            raise RuntimeError("Not connected — call connect() first")
        return await self._client.lpush(key, *values)

    async def rpop(self, key: str) -> str | None:
        if not self._client:
            raise RuntimeError("Not connected — call connect() first")
        return await self._client.rpop(key)

    async def lrange(self, key: str, start: int = 0, end: int = -1) -> list[str]:
        if not self._client:
            raise RuntimeError("Not connected — call connect() first")
        return await self._client.lrange(key, start, end)

    async def publish(self, channel: str, message: str) -> int:
        if not self._client:
            raise RuntimeError("Not connected — call connect() first")
        return await self._client.publish(channel, message)

    async def hset(self, name: str, mapping: dict[str, str]) -> int:
        if not self._client:
            raise RuntimeError("Not connected — call connect() first")
        return await self._client.hset(name, mapping=mapping)

    async def hgetall(self, name: str) -> dict[str, str]:
        if not self._client:
            raise RuntimeError("Not connected — call connect() first")
        return await self._client.hgetall(name)

    async def health_check(self) -> bool:
        try:
            if not self._client:
                return False
            return await self._client.ping()
        except Exception:
            return False
