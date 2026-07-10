"""Orchestrator Agent — coordena todos os agentes, roteia tarefas, gerencia ciclo de vida."""

from __future__ import annotations

import logging
from typing import Any

from core.contracts.agent import (
    AgentCapability,
    AgentContext,
    AgentInterface,
    AgentRole,
    AgentTask,
    TaskStatus,
)
from core.contracts.llm_provider import LLMProviderInterface
from core.kernel.engine import EngineeringEngine

logger = logging.getLogger(__name__)


class OrchestratorAgent:
    """Coordena a execução de tarefas entre agentes especializados."""

    def __init__(
        self,
        llm: LLMProviderInterface,
        engine: EngineeringEngine,
        agents: dict[AgentRole, AgentInterface] | None = None,
    ) -> None:
        self._llm = llm
        self._engine = engine
        self._agents: dict[AgentRole, AgentInterface] = agents or {}

    @property
    def role(self) -> AgentRole:
        return AgentRole.ORCHESTRATOR

    def register_agent(self, agent: AgentInterface) -> None:
        self._agents[agent.role] = agent
        logger.info("Registered agent: %s", agent.role.value)

    def get_agent(self, role: AgentRole) -> AgentInterface | None:
        return self._agents.get(role)

    @property
    def registered_agents(self) -> list[AgentRole]:
        return list(self._agents.keys())

    async def process_request(self, raw_input: str, context: AgentContext) -> dict[str, Any]:
        execution = self._engine.create_execution()

        classification = await self._engine.classify_input(raw_input, context)
        execution.artifacts["classification"] = classification

        tasks = await self._engine.plan_tasks(classification, context)

        results: list[dict[str, Any]] = []
        for task in self._resolve_execution_order(tasks):
            agent = self._agents.get(task.assigned_to)
            if agent is None:
                task.status = TaskStatus.FAILED
                task.error = f"No agent registered for role: {task.assigned_to.value}"
                results.append({"task": task.description, "status": "failed", "error": task.error})
                continue

            completed = await agent.execute(task, context)
            results.append({
                "task": completed.description,
                "status": completed.status.value,
                "result": completed.result,
                "error": completed.error,
            })

        return {
            "execution_id": execution.id,
            "classification": classification,
            "results": results,
        }

    def _resolve_execution_order(self, tasks: list[AgentTask]) -> list[AgentTask]:
        independent = [t for t in tasks if not t.dependencies]
        dependent = [t for t in tasks if t.dependencies]
        return independent + dependent
