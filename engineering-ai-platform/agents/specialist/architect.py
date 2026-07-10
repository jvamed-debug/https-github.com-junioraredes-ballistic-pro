"""Architect Agent — projeta arquiteturas, gera ADRs, valida decisões técnicas."""

from __future__ import annotations

from typing import Any

from core.contracts.agent import AgentCapability, AgentContext, AgentRole, AgentTask
from core.contracts.llm_provider import LLMProviderInterface, LLMResponse
from agents.base import BaseAgent


class ArchitectAgent(BaseAgent):

    def __init__(self, llm: LLMProviderInterface, config: dict[str, Any] | None = None) -> None:
        super().__init__(llm, config)

    @property
    def role(self) -> AgentRole:
        return AgentRole.ARCHITECT

    @property
    def capabilities(self) -> list[AgentCapability]:
        return [
            AgentCapability(
                name="design_architecture",
                description="Projeta arquitetura de sistemas completos",
            ),
            AgentCapability(
                name="generate_adr",
                description="Gera Architecture Decision Records",
            ),
            AgentCapability(
                name="validate_design",
                description="Valida decisões de design contra padrões conhecidos",
            ),
            AgentCapability(
                name="generate_diagrams",
                description="Gera diagramas de arquitetura em Mermaid/PlantUML",
            ),
        ]

    async def can_handle(self, task: AgentTask) -> bool:
        keywords = ["arquitetura", "architecture", "design", "adr", "diagrama", "componentes"]
        return any(kw in task.description.lower() for kw in keywords)

    def _system_prompt(self, context: AgentContext) -> str:
        base = super()._system_prompt(context)
        return (
            f"{base}\n"
            "Especialidade: Arquitetura de Software.\n"
            "Princípios: Clean Architecture, SOLID, DDD, Event-Driven.\n"
            "Produza artefatos versionáveis: ADRs, diagramas, decisões documentadas.\n"
            "Classifique recomendações pelo nível de evidência (E0-E5).\n"
        )

    def _process_response(self, response: LLMResponse, task: AgentTask) -> dict[str, Any]:
        base_result = super()._process_response(response, task)
        base_result["artifact_type"] = "architecture"
        return base_result
