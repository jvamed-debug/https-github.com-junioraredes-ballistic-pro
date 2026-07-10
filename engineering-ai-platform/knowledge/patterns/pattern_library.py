"""Pattern Library — biblioteca de padrões de engenharia reutilizáveis."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Pattern:
    id: str
    name: str
    category: str
    description: str
    problem: str
    solution: str
    example: str = ""
    trade_offs: str = ""
    related_patterns: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    evidence_level: str = "E1"


class PatternLibrary:
    """Biblioteca de padrões de engenharia reutilizáveis."""

    def __init__(self) -> None:
        self._patterns: dict[str, Pattern] = {}
        self._load_defaults()

    def add(self, pattern: Pattern) -> None:
        self._patterns[pattern.id] = pattern

    def get(self, pattern_id: str) -> Pattern | None:
        return self._patterns.get(pattern_id)

    def search(self, query: str) -> list[Pattern]:
        q = query.lower()
        return [
            p for p in self._patterns.values()
            if q in p.name.lower()
            or q in p.description.lower()
            or q in p.category.lower()
            or any(q in t.lower() for t in p.tags)
        ]

    def by_category(self, category: str) -> list[Pattern]:
        return [p for p in self._patterns.values() if p.category == category]

    def categories(self) -> list[str]:
        return sorted({p.category for p in self._patterns.values()})

    @property
    def count(self) -> int:
        return len(self._patterns)

    def _load_defaults(self) -> None:
        defaults = [
            Pattern(
                id="PAT-001", name="Repository Pattern", category="architecture",
                description="Abstrai acesso a dados atrás de uma interface",
                problem="Acoplamento direto entre lógica de negócio e persistência",
                solution="Interface de repositório com implementação concreta separada",
                tags=["backend", "database", "clean-architecture"],
                evidence_level="E2",
            ),
            Pattern(
                id="PAT-002", name="CQRS", category="architecture",
                description="Separa leituras e escritas em modelos distintos",
                problem="Modelo único para read/write limita escalabilidade",
                solution="Command model para escritas, Query model para leituras",
                tags=["backend", "scalability", "event-driven"],
                evidence_level="E2",
            ),
            Pattern(
                id="PAT-003", name="Circuit Breaker", category="resilience",
                description="Previne falhas em cascata em sistemas distribuídos",
                problem="Chamadas a serviços instáveis propagam falhas",
                solution="Estado aberto/fechado/meio-aberto para controlar chamadas",
                tags=["microservices", "resilience", "distributed"],
                evidence_level="E3",
            ),
            Pattern(
                id="PAT-004", name="Strangler Fig", category="migration",
                description="Migração gradual de sistemas legados",
                problem="Reescrever sistema inteiro é arriscado",
                solution="Substituir partes gradualmente mantendo o legado funcional",
                tags=["migration", "legacy", "architecture"],
                evidence_level="E1",
            ),
            Pattern(
                id="PAT-005", name="Event Sourcing", category="architecture",
                description="Armazena mudanças de estado como sequência de eventos",
                problem="Perda de histórico de mudanças no estado",
                solution="Persistir eventos imutáveis e derivar estado atual",
                tags=["event-driven", "audit", "cqrs"],
                evidence_level="E2",
            ),
        ]
        for p in defaults:
            self.add(p)
