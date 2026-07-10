"""Vector Store — armazenamento e busca vetorial para RAG."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any


@dataclass
class VectorDocument:
    id: str
    content: str
    embedding: list[float]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class VectorSearchResult:
    document: VectorDocument
    score: float
    distance: float


class InMemoryVectorStore:
    """Store vetorial em memória com similaridade cosseno."""

    def __init__(self, dimension: int = 384) -> None:
        self._dimension = dimension
        self._documents: dict[str, VectorDocument] = {}

    def add(self, doc: VectorDocument) -> None:
        if len(doc.embedding) != self._dimension:
            raise ValueError(
                f"Expected dimension {self._dimension}, got {len(doc.embedding)}"
            )
        self._documents[doc.id] = doc

    def add_batch(self, docs: list[VectorDocument]) -> int:
        count = 0
        for doc in docs:
            self.add(doc)
            count += 1
        return count

    def search(
        self, query_embedding: list[float], top_k: int = 5, min_score: float = 0.0
    ) -> list[VectorSearchResult]:
        if len(query_embedding) != self._dimension:
            raise ValueError(
                f"Expected dimension {self._dimension}, got {len(query_embedding)}"
            )

        results: list[VectorSearchResult] = []
        for doc in self._documents.values():
            score = self._cosine_similarity(query_embedding, doc.embedding)
            if score >= min_score:
                results.append(VectorSearchResult(
                    document=doc,
                    score=score,
                    distance=1.0 - score,
                ))

        results.sort(key=lambda r: r.score, reverse=True)
        return results[:top_k]

    def get(self, doc_id: str) -> VectorDocument | None:
        return self._documents.get(doc_id)

    def delete(self, doc_id: str) -> bool:
        return self._documents.pop(doc_id, None) is not None

    @property
    def count(self) -> int:
        return len(self._documents)

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)
