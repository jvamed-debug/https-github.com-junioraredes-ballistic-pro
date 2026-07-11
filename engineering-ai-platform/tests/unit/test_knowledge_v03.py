"""Tests for Release 0.3 — Knowledge Engine modules."""

from __future__ import annotations

import sys
import os
import unittest
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from memory.rag.vector_store import InMemoryVectorStore, VectorDocument
from memory.rag.chunker import TextChunker
from memory.store.asset_store import AssetStore
from memory.store.adr_manager import ADRManager
from knowledge.patterns.pattern_library import PatternLibrary
from knowledge.templates.template_engine import TemplateEngine
from knowledge.snippets.snippet_store import SnippetStore, Snippet
from core.contracts.asset import (
    AssetType, AssetStatus, EngineeringAsset, EvidenceLevel, RiskLevel,
)


class TestVectorStore(unittest.TestCase):
    def test_add_and_search(self) -> None:
        store = InMemoryVectorStore(dimension=3)
        store.add(VectorDocument(id="v1", content="hello", embedding=[1.0, 0.0, 0.0]))
        store.add(VectorDocument(id="v2", content="world", embedding=[0.0, 1.0, 0.0]))
        results = store.search([1.0, 0.1, 0.0], top_k=1)
        assert len(results) == 1
        assert results[0].document.id == "v1"

    def test_delete(self) -> None:
        store = InMemoryVectorStore(dimension=3)
        store.add(VectorDocument(id="v1", content="test", embedding=[1.0, 0.0, 0.0]))
        store.delete("v1")
        assert store.get("v1") is None

    def test_count(self) -> None:
        store = InMemoryVectorStore(dimension=3)
        store.add(VectorDocument(id="v1", content="a", embedding=[1.0, 0.0, 0.0]))
        assert store.count == 1


class TestTextChunker(unittest.TestCase):
    def test_chunk_text(self) -> None:
        chunker = TextChunker(chunk_size=50, overlap=10)
        text = "A" * 120
        chunks = chunker.chunk(text)
        assert len(chunks) >= 2

    def test_small_text(self) -> None:
        chunker = TextChunker(chunk_size=500)
        chunks = chunker.chunk("Hello world")
        assert len(chunks) == 1

    def test_empty_text(self) -> None:
        chunker = TextChunker()
        chunks = chunker.chunk("")
        assert len(chunks) == 0


class TestAssetStore(unittest.TestCase):
    def _make_asset(self, asset_id: str, title: str) -> EngineeringAsset:
        now = datetime.now()
        return EngineeringAsset(
            id=asset_id, asset_type=AssetType.COMPONENT, version="1.0",
            author="test", created=now, updated=now, status=AssetStatus.DRAFT,
            owner="team", title=title, description="A test asset", domain="backend",
        )

    def test_save_and_get(self) -> None:
        store = AssetStore()
        asset = self._make_asset("ENG-COMP-000001", "Auth Service")
        store.save(asset)
        retrieved = store.get("ENG-COMP-000001")
        assert retrieved is not None
        assert retrieved.title == "Auth Service"

    def test_search(self) -> None:
        store = AssetStore()
        store.save(self._make_asset("A1", "Auth Service"))
        results = store.search("auth")
        assert len(results) >= 1

    def test_generate_id(self) -> None:
        store = AssetStore()
        id1 = store.generate_id(AssetType.COMPONENT)
        assert id1 == "ENG-COMP-000001"


class TestADRManager(unittest.TestCase):
    def test_create_and_accept(self) -> None:
        mgr = ADRManager()
        adr = mgr.create(
            title="Use PostgreSQL",
            context="Need a relational DB",
            decision="Use PostgreSQL",
            consequences="Team must learn SQL",
        )
        assert adr.id == "ADR-0001"
        accepted = mgr.accept(adr.id)
        assert accepted.status.value == "accepted"

    def test_search(self) -> None:
        mgr = ADRManager()
        mgr.create(title="Use Redis", context="Cache layer", decision="Redis", consequences="None")
        results = mgr.search("redis")
        assert len(results) == 1

    def test_to_markdown(self) -> None:
        mgr = ADRManager()
        adr = mgr.create(title="Test", context="C", decision="D", consequences="E")
        md = mgr.to_markdown(adr)
        assert "# ADR-0001: Test" in md


class TestPatternLibrary(unittest.TestCase):
    def test_defaults_loaded(self) -> None:
        lib = PatternLibrary()
        assert lib.count >= 5

    def test_search(self) -> None:
        lib = PatternLibrary()
        results = lib.search("circuit")
        assert len(results) >= 1

    def test_categories(self) -> None:
        lib = PatternLibrary()
        cats = lib.categories()
        assert "architecture" in cats


class TestTemplateEngine(unittest.TestCase):
    def test_defaults_loaded(self) -> None:
        engine = TemplateEngine()
        assert engine.count >= 4

    def test_render(self) -> None:
        engine = TemplateEngine()
        result = engine.render("TPL-SERVICE", {"name": "User", "description": "User management"})
        assert "UserService" in result

    def test_by_category(self) -> None:
        engine = TemplateEngine()
        code_templates = engine.by_category("code")
        assert len(code_templates) >= 2


class TestSnippetStore(unittest.TestCase):
    def test_add_and_search(self) -> None:
        store = SnippetStore()
        store.add(Snippet(
            id="S1", name="FastAPI Health", language="python",
            code="@app.get('/health')\ndef health(): return {'ok': True}",
            tags=["fastapi", "health"],
        ))
        results = store.search("health")
        assert len(results) == 1

    def test_by_language(self) -> None:
        store = SnippetStore()
        store.add(Snippet(id="S1", name="Hello", language="python", code="print('hi')"))
        store.add(Snippet(id="S2", name="Hello", language="javascript", code="console.log('hi')"))
        py = store.by_language("python")
        assert len(py) == 1


if __name__ == "__main__":
    unittest.main()
