"""Testes do Knowledge Graph."""

from __future__ import annotations

from memory.graph.knowledge_graph import GraphEdge, GraphNode, KnowledgeGraph


class TestKnowledgeGraph:
    def test_add_and_get_node(self) -> None:
        graph = KnowledgeGraph()
        node = GraphNode(id="fastapi", label="FastAPI", node_type="technology")
        graph.add_node(node)
        assert graph.get_node("fastapi") is node
        assert graph.node_count == 1

    def test_add_edge_and_neighbors(self) -> None:
        graph = KnowledgeGraph()
        graph.add_node(GraphNode(id="fastapi", label="FastAPI", node_type="technology"))
        graph.add_node(GraphNode(id="postgres", label="PostgreSQL", node_type="database"))
        graph.add_edge(GraphEdge(source="fastapi", target="postgres", relation="uses"))

        neighbors = graph.get_neighbors("fastapi")
        assert len(neighbors) == 1
        assert neighbors[0][1].id == "postgres"
        assert neighbors[0][0].relation == "uses"

    def test_query_by_type(self) -> None:
        graph = KnowledgeGraph()
        graph.add_node(GraphNode(id="fastapi", label="FastAPI", node_type="technology"))
        graph.add_node(GraphNode(id="postgres", label="PostgreSQL", node_type="database"))

        techs = graph.query(node_type="technology")
        assert len(techs) == 1
        assert techs[0].id == "fastapi"

    def test_query_by_relation(self) -> None:
        graph = KnowledgeGraph()
        graph.add_node(GraphNode(id="a", label="A", node_type="x"))
        graph.add_node(GraphNode(id="b", label="B", node_type="x"))
        graph.add_node(GraphNode(id="c", label="C", node_type="x"))
        graph.add_edge(GraphEdge(source="a", target="b", relation="uses"))

        nodes = graph.query(relation="uses")
        ids = {n.id for n in nodes}
        assert "a" in ids
        assert "b" in ids
        assert "c" not in ids
