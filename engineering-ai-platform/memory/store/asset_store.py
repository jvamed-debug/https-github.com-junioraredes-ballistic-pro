"""Asset Store — armazenamento e consulta de ativos de engenharia."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from core.contracts.asset import AssetStatus, AssetType, EngineeringAsset


class AssetStore:
    """Armazenamento em memória de ativos de engenharia com busca."""

    def __init__(self) -> None:
        self._assets: dict[str, EngineeringAsset] = {}
        self._counter: dict[str, int] = {}

    def generate_id(self, asset_type: AssetType) -> str:
        key = asset_type.value
        self._counter[key] = self._counter.get(key, 0) + 1
        return f"ENG-{key}-{self._counter[key]:06d}"

    def save(self, asset: EngineeringAsset) -> EngineeringAsset:
        asset.updated = datetime.now()
        self._assets[asset.id] = asset
        return asset

    def get(self, asset_id: str) -> EngineeringAsset | None:
        return self._assets.get(asset_id)

    def delete(self, asset_id: str) -> bool:
        return self._assets.pop(asset_id, None) is not None

    def list_all(
        self,
        asset_type: AssetType | None = None,
        status: AssetStatus | None = None,
        domain: str | None = None,
        project: str | None = None,
        tags: list[str] | None = None,
    ) -> list[EngineeringAsset]:
        results = list(self._assets.values())

        if asset_type:
            results = [a for a in results if a.asset_type == asset_type]
        if status:
            results = [a for a in results if a.status == status]
        if domain:
            results = [a for a in results if a.domain == domain]
        if project:
            results = [a for a in results if a.project == project]
        if tags:
            tag_set = set(tags)
            results = [a for a in results if tag_set.issubset(set(a.tags))]

        return results

    def search(self, query: str) -> list[EngineeringAsset]:
        query_lower = query.lower()
        return [
            a for a in self._assets.values()
            if query_lower in a.title.lower()
            or query_lower in a.description.lower()
            or any(query_lower in t.lower() for t in a.tags)
        ]

    @property
    def count(self) -> int:
        return len(self._assets)

    def stats(self) -> dict[str, Any]:
        by_type: dict[str, int] = {}
        by_status: dict[str, int] = {}
        by_domain: dict[str, int] = {}
        for a in self._assets.values():
            by_type[a.asset_type.value] = by_type.get(a.asset_type.value, 0) + 1
            by_status[a.status.value] = by_status.get(a.status.value, 0) + 1
            by_domain[a.domain] = by_domain.get(a.domain, 0) + 1
        return {
            "total": self.count,
            "by_type": by_type,
            "by_status": by_status,
            "by_domain": by_domain,
        }
