"""Developer Agent — gera código de qualidade corporativa, aplica padrões."""

from __future__ import annotations

from typing import Any

from core.contracts.agent import AgentCapability, AgentContext, AgentRole, AgentTask
from core.contracts.llm_provider import LLMProviderInterface, LLMResponse
from agents.base import BaseAgent


class DeveloperAgent(BaseAgent):

    def __init__(self, llm: LLMProviderInterface, config: dict[str, Any] | None = None) -> None:
        super().__init__(llm, config)

    @property
    def role(self) -> AgentRole:
        return AgentRole.DEVELOPER

    @property
    def capabilities(self) -> list[AgentCapability]:
        return [
            AgentCapability(
                name="generate_code",
                description="Gera código seguindo padrões corporativos",
            ),
            AgentCapability(
                name="refactor",
                description="Refatora código existente",
            ),
            AgentCapability(
                name="generate_tests",
                description="Gera testes unitários e de integração",
            ),
        ]

    async def can_handle(self, task: AgentTask) -> bool:
        keywords = ["código", "code", "implement", "develop", "gerar", "refactor"]
        return any(kw in task.description.lower() for kw in keywords)

    def _system_prompt(self, context: AgentContext) -> str:
        base = super()._system_prompt(context)
        dna = context.project_dna
        return (
            f"{base}\n"
            "Especialidade: Desenvolvimento de Software.\n"
            f"Linguagem: {dna.get('language', 'python')}\n"
            f"Framework: {dna.get('framework', '')}\n"
            "Princípios: Clean Code, SOLID, testes, documentação.\n"
            "Produza código pronto para produção, seguro e testável.\n"
        )

    def _process_response(self, response: LLMResponse, task: AgentTask) -> dict[str, Any]:
        base_result = super()._process_response(response, task)
        base_result["artifact_type"] = "code"
        return base_result
