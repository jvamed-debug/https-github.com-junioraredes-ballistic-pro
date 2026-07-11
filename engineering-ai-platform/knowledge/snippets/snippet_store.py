"""Snippet Store — armazenamento de snippets de código reutilizáveis."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Snippet:
    id: str
    name: str
    language: str
    code: str
    description: str = ""
    tags: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)


class SnippetStore:
    """Armazena e busca snippets de código."""

    def __init__(self) -> None:
        self._snippets: dict[str, Snippet] = {}

    def add(self, snippet: Snippet) -> None:
        self._snippets[snippet.id] = snippet

    def get(self, snippet_id: str) -> Snippet | None:
        return self._snippets.get(snippet_id)

    def search(self, query: str, language: str | None = None) -> list[Snippet]:
        q = query.lower()
        results = [
            s for s in self._snippets.values()
            if q in s.name.lower()
            or q in s.description.lower()
            or any(q in t.lower() for t in s.tags)
        ]
        if language:
            results = [s for s in results if s.language == language]
        return results

    def by_language(self, language: str) -> list[Snippet]:
        return [s for s in self._snippets.values() if s.language == language]

    @property
    def count(self) -> int:
        return len(self._snippets)
