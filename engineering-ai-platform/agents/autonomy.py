"""Agent Autonomy — níveis de autonomia e controle de decisões dos agentes."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class AutonomyLevel(str, Enum):
    SUPERVISED = "supervised"
    SEMI_AUTONOMOUS = "semi_autonomous"
    AUTONOMOUS = "autonomous"
    FULL_AUTONOMOUS = "full_autonomous"


@dataclass
class AutonomyPolicy:
    level: AutonomyLevel
    requires_approval: list[str] = field(default_factory=list)
    auto_approve: list[str] = field(default_factory=list)
    max_cost_usd: float = 0.0
    max_tokens_per_task: int = 0
    allowed_tools: list[str] = field(default_factory=list)
    blocked_actions: list[str] = field(default_factory=list)


@dataclass
class ApprovalRequest:
    id: str
    agent_id: str
    action: str
    description: str
    estimated_cost: float = 0.0
    approved: bool | None = None
    reviewer: str = ""


DEFAULT_POLICIES: dict[AutonomyLevel, AutonomyPolicy] = {
    AutonomyLevel.SUPERVISED: AutonomyPolicy(
        level=AutonomyLevel.SUPERVISED,
        requires_approval=["*"],
        auto_approve=[],
        max_cost_usd=0.0,
    ),
    AutonomyLevel.SEMI_AUTONOMOUS: AutonomyPolicy(
        level=AutonomyLevel.SEMI_AUTONOMOUS,
        requires_approval=["deploy", "delete", "create_pr", "merge"],
        auto_approve=["read", "analyze", "generate", "review"],
        max_cost_usd=1.0,
        max_tokens_per_task=8192,
    ),
    AutonomyLevel.AUTONOMOUS: AutonomyPolicy(
        level=AutonomyLevel.AUTONOMOUS,
        requires_approval=["deploy", "merge"],
        auto_approve=["read", "analyze", "generate", "review", "create_pr", "commit"],
        max_cost_usd=10.0,
        max_tokens_per_task=32768,
    ),
    AutonomyLevel.FULL_AUTONOMOUS: AutonomyPolicy(
        level=AutonomyLevel.FULL_AUTONOMOUS,
        requires_approval=[],
        auto_approve=["*"],
        max_cost_usd=100.0,
        max_tokens_per_task=0,
    ),
}


class AutonomyManager:
    """Gerencia níveis de autonomia e aprovações de agentes."""

    def __init__(self, default_level: AutonomyLevel = AutonomyLevel.SEMI_AUTONOMOUS) -> None:
        self._agent_policies: dict[str, AutonomyPolicy] = {}
        self._default_level = default_level
        self._pending_approvals: dict[str, ApprovalRequest] = {}
        self._approval_counter = 0

    def set_policy(self, agent_id: str, policy: AutonomyPolicy) -> None:
        self._agent_policies[agent_id] = policy

    def set_level(self, agent_id: str, level: AutonomyLevel) -> None:
        self._agent_policies[agent_id] = DEFAULT_POLICIES[level]

    def get_policy(self, agent_id: str) -> AutonomyPolicy:
        return self._agent_policies.get(agent_id, DEFAULT_POLICIES[self._default_level])

    def can_execute(self, agent_id: str, action: str, estimated_cost: float = 0.0) -> bool:
        policy = self.get_policy(agent_id)

        if policy.blocked_actions and action in policy.blocked_actions:
            return False

        if policy.max_cost_usd > 0 and estimated_cost > policy.max_cost_usd:
            return False

        if "*" in policy.auto_approve:
            return True

        if action in policy.auto_approve:
            return True

        if "*" in policy.requires_approval:
            return False

        if action in policy.requires_approval:
            return False

        return True

    def request_approval(self, agent_id: str, action: str, description: str,
                         estimated_cost: float = 0.0) -> ApprovalRequest:
        self._approval_counter += 1
        request = ApprovalRequest(
            id=f"APR-{self._approval_counter:06d}",
            agent_id=agent_id,
            action=action,
            description=description,
            estimated_cost=estimated_cost,
        )
        self._pending_approvals[request.id] = request
        return request

    def approve(self, request_id: str, reviewer: str = "") -> bool:
        req = self._pending_approvals.get(request_id)
        if req is None:
            return False
        req.approved = True
        req.reviewer = reviewer
        return True

    def deny(self, request_id: str, reviewer: str = "") -> bool:
        req = self._pending_approvals.get(request_id)
        if req is None:
            return False
        req.approved = False
        req.reviewer = reviewer
        return True

    def pending_approvals(self, agent_id: str | None = None) -> list[ApprovalRequest]:
        approvals = [a for a in self._pending_approvals.values() if a.approved is None]
        if agent_id:
            approvals = [a for a in approvals if a.agent_id == agent_id]
        return approvals
