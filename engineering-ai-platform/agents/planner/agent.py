"""Planner Agent — planejamento de tarefas, decomposição, estimativas."""

from __future__ import annotations

from typing import Any

from core.contracts.agent import AgentCapability, AgentContext, AgentRole, AgentTask
from core.contracts.llm_provider import LLMProviderInterface, LLMResponse
from agents.base import BaseAgent


class PlannerAgent(BaseAgent):

    def __init__(self, llm: LLMProviderInterface, config: dict[str, Any] | None = None) -> None:
        super().__init__(llm, config)

    @property
    def role(self) -> AgentRole:
        return AgentRole.PLANNER

    @property
    def capabilities(self) -> list[AgentCapability]:
        return [
            AgentCapability(
                name="decompose_task",
                description="Decompõe tarefas complexas em subtarefas",
            ),
            AgentCapability(
                name="estimate",
                description="Estima esforço e complexidade",
            ),
            AgentCapability(
                name="prioritize",
                description="Prioriza tarefas por impacto e dependências",
            ),
            AgentCapability(
                name="create_roadmap",
                description="Cria roadmap de execução",
            ),
        ]

    async def can_handle(self, task: AgentTask) -> bool:
        keywords = ["plan", "planejar", "decompor", "estimar", "priorizar", "roadmap"]
        return any(kw in task.description.lower() for kw in keywords)

    def _system_prompt(self, context: AgentContext) -> str:
        base = super()._system_prompt(context)
        return (
            f"{base}\n"
            "Especialidade: Planejamento e Decomposição de Tarefas.\n"
            "Produza planos acionáveis com critérios de aceite claros.\n"
            "Identifique dependências, riscos e caminhos críticos.\n"
            "Estime usando story points e complexidade relativa.\n"
        )

    def _process_response(self, response: LLMResponse, task: AgentTask) -> dict[str, Any]:
        base_result = super()._process_response(response, task)
        base_result["artifact_type"] = "plan"
        return base_result
