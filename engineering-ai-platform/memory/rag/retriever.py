"""Knowledge Retriever — recupera conhecimento relevante da base."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class RetrievalResult:
    content: str
    source: str
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)


class KnowledgeRetriever:
    """Recupera documentos e ativos relevantes para contextualizar agentes."""

    def __init__(self) -> None:
        self._documents: list[dict[str, Any]] = []

    def add_document(self, content: str, source: str, metadata: dict[str, Any] | None = None) -> None:
        self._documents.append({
            "content": content,
            "source": source,
            "metadata": metadata or {},
        })

    def retrieve(self, query: str, top_k: int = 5) -> list[RetrievalResult]:
        scored = []
        query_terms = set(query.lower().split())
        for doc in self._documents:
            doc_terms = set(doc["content"].lower().split())
            overlap = len(query_terms & doc_terms)
            if overlap > 0:
                score = overlap / max(len(query_terms), 1)
                scored.append(RetrievalResult(
                    content=doc["content"],
                    source=doc["source"],
                    score=score,
                    metadata=doc["metadata"],
                ))
        scored.sort(key=lambda r: r.score, reverse=True)
        return scored[:top_k]

    @property
    def document_count(self) -> int:
        return len(self._documents)
