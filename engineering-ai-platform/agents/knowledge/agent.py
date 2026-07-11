"""Knowledge Agent — gerencia memória organizacional, RAG, padrões e snippets."""

from __future__ import annotations

from typing import Any

from core.contracts.agent import AgentCapability, AgentContext, AgentRole, AgentTask
from core.contracts.llm_provider import LLMProviderInterface, LLMResponse
from agents.base import BaseAgent


class KnowledgeAgent(BaseAgent):

    def __init__(self, llm: LLMProviderInterface, config: dict[str, Any] | None = None) -> None:
        super().__init__(llm, config)
        self._knowledge_sources: list[str] = []

    @property
    def role(self) -> AgentRole:
        return AgentRole.KNOWLEDGE

    @property
    def capabilities(self) -> list[AgentCapability]:
        return [
            AgentCapability(
                name="search_knowledge",
                description="Busca informações na base de conhecimento organizacional",
            ),
            AgentCapability(
                name="index_artifact",
                description="Indexa artefatos de engenharia no RAG",
            ),
            AgentCapability(
                name="recommend_patterns",
                description="Recomenda padrões e melhores práticas",
            ),
            AgentCapability(
                name="manage_adrs",
                description="Gerencia Architecture Decision Records",
            ),
        ]

    async def can_handle(self, task: AgentTask) -> bool:
        keywords = [
            "knowledge", "conhecimento", "rag", "buscar", "search",
            "pattern", "padrão", "adr", "snippet", "template",
        ]
        return any(kw in task.description.lower() for kw in keywords)

    def add_source(self, source: str) -> None:
        self._knowledge_sources.append(source)

    def _system_prompt(self, context: AgentContext) -> str:
        base = super()._system_prompt(context)
        kb = context.knowledge_base
        sources_info = f"Sources: {len(self._knowledge_sources)}" if self._knowledge_sources else ""
        return (
            f"{base}\n"
            "Especialidade: Gestão de Conhecimento Organizacional.\n"
            "Busque e correlacione informações de ADRs, padrões, snippets e artefatos.\n"
            "Recomende padrões com base em evidências (E0-E5).\n"
            "Mantenha a rastreabilidade entre decisões e implementações.\n"
            f"Knowledge base entries: {len(kb)}\n"
            f"{sources_info}\n"
        )

    def _process_response(self, response: LLMResponse, task: AgentTask) -> dict[str, Any]:
        base_result = super()._process_response(response, task)
        base_result["artifact_type"] = "knowledge"
        base_result["sources"] = list(self._knowledge_sources)
        return base_result
