"""Qdrant Client — integração com Qdrant vector database."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class VectorPoint:
    id: str
    vector: list[float]
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchResult:
    id: str
    score: float
    payload: dict[str, Any] = field(default_factory=dict)


class QdrantClient:
    """Cliente para Qdrant vector database."""

    def __init__(self, url: str = "http://localhost:6333") -> None:
        self._url = url
        self._headers = {"Content-Type": "application/json"}

    async def create_collection(self, name: str, dimension: int = 384) -> None:
        payload = {
            "vectors": {
                "size": dimension,
                "distance": "Cosine",
            }
        }
        await self._request("PUT", f"/collections/{name}", json=payload)

    async def delete_collection(self, name: str) -> None:
        await self._request("DELETE", f"/collections/{name}")

    async def collection_exists(self, name: str) -> bool:
        try:
            await self._request("GET", f"/collections/{name}")
            return True
        except Exception:
            return False

    async def upsert_points(self, collection: str, points: list[VectorPoint]) -> None:
        payload = {
            "points": [
                {"id": p.id, "vector": p.vector, "payload": p.payload}
                for p in points
            ]
        }
        await self._request("PUT", f"/collections/{collection}/points", json=payload)

    async def search(
        self, collection: str, query_vector: list[float], limit: int = 10, filter_payload: dict[str, Any] | None = None
    ) -> list[SearchResult]:
        payload: dict[str, Any] = {
            "vector": query_vector,
            "limit": limit,
            "with_payload": True,
        }
        if filter_payload:
            payload["filter"] = filter_payload

        data = await self._request("POST", f"/collections/{collection}/points/search", json=payload)
        return [
            SearchResult(
                id=str(r.get("id", "")),
                score=r.get("score", 0.0),
                payload=r.get("payload", {}),
            )
            for r in data.get("result", [])
        ]

    async def get_point(self, collection: str, point_id: str) -> VectorPoint | None:
        try:
            data = await self._request("GET", f"/collections/{collection}/points/{point_id}")
            result = data.get("result", {})
            return VectorPoint(
                id=str(result.get("id", "")),
                vector=result.get("vector", []),
                payload=result.get("payload", {}),
            )
        except Exception:
            return None

    async def delete_points(self, collection: str, point_ids: list[str]) -> None:
        payload = {"points": point_ids}
        await self._request("POST", f"/collections/{collection}/points/delete", json=payload)

    async def count_points(self, collection: str) -> int:
        data = await self._request("POST", f"/collections/{collection}/points/count", json={"exact": True})
        return data.get("result", {}).get("count", 0)

    async def health_check(self) -> bool:
        try:
            await self._request("GET", "/healthz")
            return True
        except Exception:
            return False

    async def _request(
        self, method: str, path: str, json: dict[str, Any] | None = None
    ) -> Any:
        import httpx

        async with httpx.AsyncClient(base_url=self._url, headers=self._headers) as client:
            response = await client.request(method, path, json=json, timeout=30.0)
            response.raise_for_status()
            if response.headers.get("content-type", "").startswith("application/json"):
                return response.json()
            return {}
