"""Agent Contract — interface base para todos os agentes da plataforma."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class AgentRole(str, Enum):
    ORCHESTRATOR = "orchestrator"
    ARCHITECT = "architect"
    DEVELOPER = "developer"
    REVIEWER = "reviewer"
    SECURITY = "security"
    PLANNER = "planner"
    KNOWLEDGE = "knowledge"
    DOCUMENTATION = "documentation"


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


@dataclass
class AgentTask:
    id: str
    description: str
    assigned_to: AgentRole
    status: TaskStatus = TaskStatus.PENDING
    context: dict[str, Any] = field(default_factory=dict)
    dependencies: list[str] = field(default_factory=list)
    result: Any = None
    error: str | None = None


@dataclass
class AgentCapability:
    name: str
    description: str
    input_schema: dict[str, Any] = field(default_factory=dict)
    output_schema: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AgentContext:
    project_dna: dict[str, Any] = field(default_factory=dict)
    knowledge_base: dict[str, Any] = field(default_factory=dict)
    conversation_history: list[dict[str, Any]] = field(default_factory=list)
    active_tasks: list[AgentTask] = field(default_factory=list)


class AgentInterface(ABC):
    """Interface base para todos os agentes."""

    @property
    @abstractmethod
    def role(self) -> AgentRole:
        ...

    @property
    @abstractmethod
    def capabilities(self) -> list[AgentCapability]:
        ...

    @abstractmethod
    async def execute(self, task: AgentTask, context: AgentContext) -> AgentTask:
        ...

    @abstractmethod
    async def can_handle(self, task: AgentTask) -> bool:
        ...
