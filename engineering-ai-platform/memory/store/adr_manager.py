"""ADR Manager — gestão de Architecture Decision Records."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class ADRStatus(str, Enum):
    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    DEPRECATED = "deprecated"
    SUPERSEDED = "superseded"


@dataclass
class ADR:
    id: str
    title: str
    status: ADRStatus
    context: str
    decision: str
    consequences: str
    created: datetime = field(default_factory=datetime.now)
    updated: datetime = field(default_factory=datetime.now)
    author: str = ""
    superseded_by: str | None = None
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class ADRManager:
    """Gerencia Architecture Decision Records."""

    def __init__(self) -> None:
        self._adrs: dict[str, ADR] = {}
        self._counter = 0

    def create(
        self,
        title: str,
        context: str,
        decision: str,
        consequences: str,
        author: str = "",
        tags: list[str] | None = None,
    ) -> ADR:
        self._counter += 1
        adr_id = f"ADR-{self._counter:04d}"
        adr = ADR(
            id=adr_id,
            title=title,
            status=ADRStatus.PROPOSED,
            context=context,
            decision=decision,
            consequences=consequences,
            author=author,
            tags=tags or [],
        )
        self._adrs[adr_id] = adr
        return adr

    def accept(self, adr_id: str) -> ADR:
        adr = self._get_or_raise(adr_id)
        adr.status = ADRStatus.ACCEPTED
        adr.updated = datetime.now()
        return adr

    def deprecate(self, adr_id: str) -> ADR:
        adr = self._get_or_raise(adr_id)
        adr.status = ADRStatus.DEPRECATED
        adr.updated = datetime.now()
        return adr

    def supersede(self, old_id: str, new_id: str) -> tuple[ADR, ADR]:
        old = self._get_or_raise(old_id)
        new = self._get_or_raise(new_id)
        old.status = ADRStatus.SUPERSEDED
        old.superseded_by = new_id
        old.updated = datetime.now()
        return old, new

    def get(self, adr_id: str) -> ADR | None:
        return self._adrs.get(adr_id)

    def list_all(self, status: ADRStatus | None = None) -> list[ADR]:
        adrs = list(self._adrs.values())
        if status:
            adrs = [a for a in adrs if a.status == status]
        return sorted(adrs, key=lambda a: a.id)

    def search(self, query: str) -> list[ADR]:
        q = query.lower()
        return [
            a for a in self._adrs.values()
            if q in a.title.lower() or q in a.context.lower() or q in a.decision.lower()
        ]

    def to_markdown(self, adr: ADR) -> str:
        return (
            f"# {adr.id}: {adr.title}\n\n"
            f"**Status:** {adr.status.value}\n"
            f"**Date:** {adr.created.strftime('%Y-%m-%d')}\n"
            f"**Author:** {adr.author}\n\n"
            f"## Context\n\n{adr.context}\n\n"
            f"## Decision\n\n{adr.decision}\n\n"
            f"## Consequences\n\n{adr.consequences}\n"
        )

    @property
    def count(self) -> int:
        return len(self._adrs)

    def _get_or_raise(self, adr_id: str) -> ADR:
        adr = self._adrs.get(adr_id)
        if adr is None:
            raise KeyError(f"ADR '{adr_id}' not found")
        return adr
