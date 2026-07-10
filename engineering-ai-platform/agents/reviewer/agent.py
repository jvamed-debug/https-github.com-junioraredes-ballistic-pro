"""Reviewer Agent — revisão de código, análise estática, validação de qualidade."""

from __future__ import annotations

from typing import Any

from core.contracts.agent import AgentCapability, AgentContext, AgentRole, AgentTask
from core.contracts.llm_provider import LLMProviderInterface, LLMResponse
from agents.base import BaseAgent


class ReviewerAgent(BaseAgent):

    def __init__(self, llm: LLMProviderInterface, config: dict[str, Any] | None = None) -> None:
        super().__init__(llm, config)

    @property
    def role(self) -> AgentRole:
        return AgentRole.REVIEWER

    @property
    def capabilities(self) -> list[AgentCapability]:
        return [
            AgentCapability(
                name="code_review",
                description="Revisão de código com foco em qualidade e padrões",
            ),
            AgentCapability(
                name="static_analysis",
                description="Análise estática de código",
            ),
            AgentCapability(
                name="test_validation",
                description="Valida cobertura e qualidade de testes",
            ),
        ]

    async def can_handle(self, task: AgentTask) -> bool:
        keywords = ["review", "revisar", "análise", "qualidade", "code review"]
        return any(kw in task.description.lower() for kw in keywords)

    def _system_prompt(self, context: AgentContext) -> str:
        base = super()._system_prompt(context)
        return (
            f"{base}\n"
            "Especialidade: Revisão de Código e Qualidade.\n"
            "Verifique: bugs, performance, segurança, legibilidade, testes.\n"
            "Classifique issues por severidade e impacto.\n"
            "Sugira melhorias com exemplos concretos.\n"
        )

    def _process_response(self, response: LLMResponse, task: AgentTask) -> dict[str, Any]:
        base_result = super()._process_response(response, task)
        base_result["artifact_type"] = "review_report"
        return base_result
