"""Testes do Engineering Engine."""

from __future__ import annotations

import pytest

from core.contracts.agent import AgentContext, AgentRole
from core.kernel.engine import EngineeringEngine


@pytest.fixture
def engine() -> EngineeringEngine:
    return EngineeringEngine()


@pytest.fixture
def context() -> AgentContext:
    return AgentContext(
        project_dna={"project": {"name": "test"}, "language": "python"},
    )


class TestEngineeringEngine:
    async def test_create_execution(self, engine: EngineeringEngine) -> None:
        execution = engine.create_execution()
        assert execution.id is not None
        assert engine.get_execution(execution.id) is execution

    async def test_classify_architecture(
        self, engine: EngineeringEngine, context: AgentContext
    ) -> None:
        result = await engine.classify_input("Projetar a arquitetura do sistema", context)
        assert result["type"] == "architecture"

    async def test_classify_implementation(
        self, engine: EngineeringEngine, context: AgentContext
    ) -> None:
        result = await engine.classify_input("Implementar o módulo de autenticação", context)
        assert result["type"] == "implementation"

    async def test_classify_review(
        self, engine: EngineeringEngine, context: AgentContext
    ) -> None:
        result = await engine.classify_input("Revisar o código do serviço", context)
        assert result["type"] == "review"

    async def test_plan_tasks_architecture(
        self, engine: EngineeringEngine, context: AgentContext
    ) -> None:
        classification = {"type": "architecture", "input": "design system"}
        tasks = await engine.plan_tasks(classification, context)
        roles = {t.assigned_to for t in tasks}
        assert AgentRole.ARCHITECT in roles
        assert AgentRole.SECURITY in roles

    async def test_detect_domains(self, engine: EngineeringEngine) -> None:
        domains = engine._detect_domains("API backend com PostgreSQL e Docker")
        assert "backend" in domains
        assert "database" in domains
        assert "infrastructure" in domains
