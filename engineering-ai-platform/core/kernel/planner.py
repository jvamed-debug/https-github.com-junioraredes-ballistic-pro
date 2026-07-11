"""Planner — planejamento avançado de execução com dependências e priorização."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from core.contracts.agent import AgentRole, AgentTask, TaskStatus


class Priority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class ExecutionPlan:
    id: str
    name: str
    phases: list[ExecutionPhase] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def total_tasks(self) -> int:
        return sum(len(p.tasks) for p in self.phases)

    @property
    def completed_tasks(self) -> int:
        return sum(
            1
            for p in self.phases
            for t in p.tasks
            if t.status == TaskStatus.COMPLETED
        )

    @property
    def progress(self) -> float:
        total = self.total_tasks
        return self.completed_tasks / total if total > 0 else 0.0


@dataclass
class ExecutionPhase:
    name: str
    tasks: list[AgentTask] = field(default_factory=list)
    parallel: bool = False


class ExecutionPlanner:
    """Planeja a execução de tarefas com fases, dependências e paralelismo."""

    def create_plan(self, name: str, classification: dict[str, Any]) -> ExecutionPlan:
        plan = ExecutionPlan(id=str(uuid.uuid4()), name=name)
        input_type = classification.get("type", "general")
        complexity = classification.get("complexity", "low")

        if input_type == "architecture":
            plan.phases = self._architecture_plan(classification, complexity)
        elif input_type == "implementation":
            plan.phases = self._implementation_plan(classification, complexity)
        elif input_type == "review":
            plan.phases = self._review_plan(classification)
        else:
            plan.phases = self._general_plan(classification)

        return plan

    def _architecture_plan(
        self, ctx: dict[str, Any], complexity: str
    ) -> list[ExecutionPhase]:
        phases = [
            ExecutionPhase(
                name="Analysis",
                tasks=[
                    self._task("Analyze requirements", AgentRole.PLANNER, ctx, Priority.HIGH),
                    self._task("Retrieve existing patterns", AgentRole.KNOWLEDGE, ctx, Priority.MEDIUM),
                ],
                parallel=True,
            ),
            ExecutionPhase(
                name="Design",
                tasks=[
                    self._task("Design architecture", AgentRole.ARCHITECT, ctx, Priority.CRITICAL),
                ],
            ),
            ExecutionPhase(
                name="Validation",
                tasks=[
                    self._task("Security review", AgentRole.SECURITY, ctx, Priority.HIGH),
                    self._task("Architecture review", AgentRole.REVIEWER, ctx, Priority.HIGH),
                ],
                parallel=True,
            ),
            ExecutionPhase(
                name="Documentation",
                tasks=[
                    self._task("Generate ADR", AgentRole.DOCUMENTATION, ctx, Priority.MEDIUM),
                    self._task("Generate diagrams", AgentRole.ARCHITECT, ctx, Priority.MEDIUM),
                ],
                parallel=True,
            ),
        ]
        return phases

    def _implementation_plan(
        self, ctx: dict[str, Any], complexity: str
    ) -> list[ExecutionPhase]:
        phases = [
            ExecutionPhase(
                name="Planning",
                tasks=[
                    self._task("Decompose into subtasks", AgentRole.PLANNER, ctx, Priority.HIGH),
                ],
            ),
            ExecutionPhase(
                name="Implementation",
                tasks=[
                    self._task("Generate code", AgentRole.DEVELOPER, ctx, Priority.CRITICAL),
                ],
            ),
            ExecutionPhase(
                name="Quality",
                tasks=[
                    self._task("Code review", AgentRole.REVIEWER, ctx, Priority.HIGH),
                    self._task("Security analysis", AgentRole.SECURITY, ctx, Priority.HIGH),
                ],
                parallel=True,
            ),
        ]
        if complexity == "high":
            phases.append(
                ExecutionPhase(
                    name="Documentation",
                    tasks=[
                        self._task("Generate documentation", AgentRole.DOCUMENTATION, ctx, Priority.MEDIUM),
                    ],
                )
            )
        return phases

    def _review_plan(self, ctx: dict[str, Any]) -> list[ExecutionPhase]:
        return [
            ExecutionPhase(
                name="Review",
                tasks=[
                    self._task("Code review", AgentRole.REVIEWER, ctx, Priority.HIGH),
                    self._task("Security scan", AgentRole.SECURITY, ctx, Priority.HIGH),
                ],
                parallel=True,
            ),
        ]

    def _general_plan(self, ctx: dict[str, Any]) -> list[ExecutionPhase]:
        return [
            ExecutionPhase(
                name="Analysis",
                tasks=[
                    self._task("Analyze request", AgentRole.PLANNER, ctx, Priority.MEDIUM),
                ],
            ),
        ]

    def _task(
        self, description: str, role: AgentRole, ctx: dict[str, Any], priority: Priority
    ) -> AgentTask:
        return AgentTask(
            id=str(uuid.uuid4()),
            description=description,
            assigned_to=role,
            context={**ctx, "priority": priority.value},
        )
