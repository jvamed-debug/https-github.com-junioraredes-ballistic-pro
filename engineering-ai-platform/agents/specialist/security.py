"""Security Agent — análise de segurança, DevSecOps, compliance."""

from __future__ import annotations

from typing import Any

from core.contracts.agent import AgentCapability, AgentContext, AgentRole, AgentTask
from core.contracts.llm_provider import LLMProviderInterface, LLMResponse
from agents.base import BaseAgent


class SecurityAgent(BaseAgent):

    def __init__(self, llm: LLMProviderInterface, config: dict[str, Any] | None = None) -> None:
        super().__init__(llm, config)

    @property
    def role(self) -> AgentRole:
        return AgentRole.SECURITY

    @property
    def capabilities(self) -> list[AgentCapability]:
        return [
            AgentCapability(
                name="security_review",
                description="Revisão de segurança de código e arquitetura",
            ),
            AgentCapability(
                name="threat_modeling",
                description="Modelagem de ameaças STRIDE/DREAD",
            ),
            AgentCapability(
                name="compliance_check",
                description="Verificação de compliance (OWASP, CIS, etc.)",
            ),
            AgentCapability(
                name="generate_policy",
                description="Gera políticas de segurança",
            ),
        ]

    async def can_handle(self, task: AgentTask) -> bool:
        keywords = ["security", "segurança", "vulnerability", "threat", "compliance", "owasp"]
        return any(kw in task.description.lower() for kw in keywords)

    def _system_prompt(self, context: AgentContext) -> str:
        base = super()._system_prompt(context)
        return (
            f"{base}\n"
            "Especialidade: Segurança de Software e DevSecOps.\n"
            "Princípios: Security by Design, Least Privilege, Zero Trust, Defense in Depth.\n"
            "Frameworks: OWASP Top 10, CIS Benchmarks, NIST, STRIDE.\n"
            "Classifique vulnerabilidades por severidade (Critical/High/Medium/Low).\n"
        )

    def _process_response(self, response: LLMResponse, task: AgentTask) -> dict[str, Any]:
        base_result = super()._process_response(response, task)
        base_result["artifact_type"] = "security_report"
        return base_result
