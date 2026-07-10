"""Knowledge Graph — grafo de relações entre ativos de engenharia."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class GraphNode:
    id: str
    label: str
    node_type: str
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass
class GraphEdge:
    source: str
    target: str
    relation: str
    properties: dict[str, Any] = field(default_factory=dict)


class KnowledgeGraph:
    """Grafo de conhecimento em memória para relações entre ativos."""

    def __init__(self) -> None:
        self._nodes: dict[str, GraphNode] = {}
        self._edges: list[GraphEdge] = []

    def add_node(self, node: GraphNode) -> None:
        self._nodes[node.id] = node

    def add_edge(self, edge: GraphEdge) -> None:
        self._edges.append(edge)

    def get_node(self, node_id: str) -> GraphNode | None:
        return self._nodes.get(node_id)

    def get_neighbors(self, node_id: str) -> list[tuple[GraphEdge, GraphNode]]:
        results = []
        for edge in self._edges:
            if edge.source == node_id:
                target = self._nodes.get(edge.target)
                if target:
                    results.append((edge, target))
            elif edge.target == node_id:
                source = self._nodes.get(edge.source)
                if source:
                    results.append((edge, source))
        return results

    def query(self, node_type: str | None = None, relation: str | None = None) -> list[GraphNode]:
        nodes = list(self._nodes.values())
        if node_type:
            nodes = [n for n in nodes if n.node_type == node_type]
        if relation:
            connected_ids = set()
            for edge in self._edges:
                if edge.relation == relation:
                    connected_ids.add(edge.source)
                    connected_ids.add(edge.target)
            nodes = [n for n in nodes if n.id in connected_ids]
        return nodes

    @property
    def node_count(self) -> int:
        return len(self._nodes)

    @property
    def edge_count(self) -> int:
        return len(self._edges)
