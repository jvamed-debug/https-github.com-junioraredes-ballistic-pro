"""Testes do Knowledge Retriever."""

from __future__ import annotations

from memory.rag.retriever import KnowledgeRetriever


class TestKnowledgeRetriever:
    def test_add_and_count(self) -> None:
        r = KnowledgeRetriever()
        r.add_document("FastAPI authentication guide", "docs/auth.md")
        assert r.document_count == 1

    def test_retrieve_relevant(self) -> None:
        r = KnowledgeRetriever()
        r.add_document("FastAPI authentication with OAuth2", "docs/auth.md")
        r.add_document("PostgreSQL indexing strategies", "docs/db.md")
        r.add_document("Docker deployment guide", "docs/deploy.md")

        results = r.retrieve("FastAPI OAuth2 authentication")
        assert len(results) > 0
        assert results[0].source == "docs/auth.md"

    def test_retrieve_empty_for_no_match(self) -> None:
        r = KnowledgeRetriever()
        r.add_document("FastAPI guide", "docs/api.md")
        results = r.retrieve("kubernetes helm chart")
        assert len(results) == 0
