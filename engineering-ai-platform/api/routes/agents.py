"""Agent Routes — endpoints REST para gerenciamento de agentes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from core.contracts.agent import AgentRole


@dataclass
class AgentInfo:
    role: str
    status: str
    capabilities: list[str] = field(default_factory=list)
    tasks_completed: int = 0
    autonomy_level: str = "semi_autonomous"


@dataclass
class AgentRouteResponse:
    success: bool
    data: Any = None
    error: str = ""


class AgentRoutes:
    """Handlers para endpoints de agentes."""

    def __init__(self) -> None:
        self._agents: dict[str, AgentInfo] = {}
        self._init_defaults()

    def _init_defaults(self) -> None:
        for role in AgentRole:
            self._agents[role.value] = AgentInfo(
                role=role.value,
                status="active" if role.value not in ("knowledge", "documentation") else "available",
                capabilities=self._default_capabilities(role),
            )

    @staticmethod
    def _default_capabilities(role: AgentRole) -> list[str]:
        caps: dict[str, list[str]] = {
            "orchestrator": ["coordinate", "route", "manage_lifecycle"],
            "architect": ["design_architecture", "generate_adr", "validate_design"],
            "developer": ["generate_code", "refactor", "implement"],
            "reviewer": ["code_review", "static_analysis", "test_validation"],
            "security": ["vulnerability_scan", "audit", "threat_model"],
            "planner": ["decompose_task", "estimate", "prioritize"],
            "knowledge": ["search_knowledge", "index_artifact", "recommend_patterns"],
            "documentation": ["generate_docs", "generate_api_docs", "generate_runbook"],
        }
        return caps.get(role.value, [])

    def list_agents(self) -> AgentRouteResponse:
        return AgentRouteResponse(
            success=True,
            data=[vars(a) for a in self._agents.values()],
        )

    def get_agent(self, role: str) -> AgentRouteResponse:
        agent = self._agents.get(role)
        if not agent:
            return AgentRouteResponse(success=False, error=f"Agent '{role}' not found")
        return AgentRouteResponse(success=True, data=vars(agent))

    def update_agent_status(self, role: str, status: str) -> AgentRouteResponse:
        agent = self._agents.get(role)
        if not agent:
            return AgentRouteResponse(success=False, error=f"Agent '{role}' not found")
        agent.status = status
        return AgentRouteResponse(success=True, data=vars(agent))

    def get_agent_tasks(self, role: str) -> AgentRouteResponse:
        agent = self._agents.get(role)
        if not agent:
            return AgentRouteResponse(success=False, error=f"Agent '{role}' not found")
        return AgentRouteResponse(success=True, data={
            "role": role,
            "tasks_completed": agent.tasks_completed,
        })
