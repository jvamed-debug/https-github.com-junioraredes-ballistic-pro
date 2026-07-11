"""Documentation Agent — gera e mantém documentação técnica automatizada."""

from __future__ import annotations

from typing import Any

from core.contracts.agent import AgentCapability, AgentContext, AgentRole, AgentTask
from core.contracts.llm_provider import LLMProviderInterface, LLMResponse
from agents.base import BaseAgent


class DocumentationAgent(BaseAgent):

    def __init__(self, llm: LLMProviderInterface, config: dict[str, Any] | None = None) -> None:
        super().__init__(llm, config)

    @property
    def role(self) -> AgentRole:
        return AgentRole.DOCUMENTATION

    @property
    def capabilities(self) -> list[AgentCapability]:
        return [
            AgentCapability(
                name="generate_docs",
                description="Gera documentação técnica a partir de código",
            ),
            AgentCapability(
                name="generate_api_docs",
                description="Gera documentação de APIs (OpenAPI/Swagger)",
            ),
            AgentCapability(
                name="generate_runbook",
                description="Gera runbooks operacionais",
            ),
            AgentCapability(
                name="update_readme",
                description="Atualiza README e guias de contribuição",
            ),
        ]

    async def can_handle(self, task: AgentTask) -> bool:
        keywords = [
            "documentation", "documentação", "docs", "readme",
            "api docs", "runbook", "guia", "guide",
        ]
        return any(kw in task.description.lower() for kw in keywords)

    def _system_prompt(self, context: AgentContext) -> str:
        base = super()._system_prompt(context)
        return (
            f"{base}\n"
            "Especialidade: Documentação Técnica.\n"
            "Gere documentação clara, concisa e versionável.\n"
            "Formatos: Markdown, OpenAPI, Mermaid diagrams.\n"
            "Mantenha consistência com o código-fonte.\n"
            "Inclua exemplos práticos e referências cruzadas.\n"
        )

    def _process_response(self, response: LLMResponse, task: AgentTask) -> dict[str, Any]:
        base_result = super()._process_response(response, task)
        base_result["artifact_type"] = "documentation"
        return base_result
