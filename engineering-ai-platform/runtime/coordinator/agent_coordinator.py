"""Agent Coordinator — coordenação avançada de agentes."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from core.contracts.agent import AgentRole, AgentTask, TaskStatus


class CoordinationStrategy(str, Enum):
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    PIPELINE = "pipeline"
    CONSENSUS = "consensus"


@dataclass
class AgentSlot:
    role: AgentRole
    agent_id: str
    busy: bool = False
    current_task: str = ""
    tasks_completed: int = 0
    last_active: datetime | None = None


@dataclass
class CoordinationPlan:
    id: str
    strategy: CoordinationStrategy
    tasks: list[AgentTask]
    agent_assignments: dict[str, AgentRole] = field(default_factory=dict)
    dependencies: dict[str, list[str]] = field(default_factory=dict)


@dataclass
class CoordinationResult:
    plan_id: str
    success: bool
    results: dict[str, Any] = field(default_factory=dict)
    errors: dict[str, str] = field(default_factory=dict)
    duration_ms: float = 0


class AgentCoordinator:
    """Coordena a execução de tarefas entre múltiplos agentes."""

    def __init__(self) -> None:
        self._agents: dict[str, AgentSlot] = {}
        self._plans: dict[str, CoordinationPlan] = {}
        self._plan_counter = 0
        self._task_handlers: dict[AgentRole, Any] = {}

    def register_agent(self, agent_id: str, role: AgentRole) -> AgentSlot:
        slot = AgentSlot(role=role, agent_id=agent_id)
        self._agents[agent_id] = slot
        return slot

    def unregister_agent(self, agent_id: str) -> None:
        self._agents.pop(agent_id, None)

    def register_handler(self, role: AgentRole, handler: Any) -> None:
        self._task_handlers[role] = handler

    def create_plan(
        self,
        strategy: CoordinationStrategy,
        tasks: list[AgentTask],
        dependencies: dict[str, list[str]] | None = None,
    ) -> CoordinationPlan:
        self._plan_counter += 1
        assignments = self._auto_assign(tasks)
        plan = CoordinationPlan(
            id=f"CP-{self._plan_counter:06d}",
            strategy=strategy,
            tasks=tasks,
            agent_assignments=assignments,
            dependencies=dependencies or {},
        )
        self._plans[plan.id] = plan
        return plan

    async def execute_plan(self, plan: CoordinationPlan) -> CoordinationResult:
        start = datetime.now()

        if plan.strategy == CoordinationStrategy.SEQUENTIAL:
            return await self._execute_sequential(plan, start)
        elif plan.strategy == CoordinationStrategy.PARALLEL:
            return await self._execute_parallel(plan, start)
        elif plan.strategy == CoordinationStrategy.PIPELINE:
            return await self._execute_pipeline(plan, start)
        else:
            return await self._execute_sequential(plan, start)

    async def _execute_sequential(
        self, plan: CoordinationPlan, start: datetime
    ) -> CoordinationResult:
        results: dict[str, Any] = {}
        errors: dict[str, str] = {}

        for task in plan.tasks:
            deps = plan.dependencies.get(task.id, [])
            for dep_id in deps:
                if dep_id in errors:
                    errors[task.id] = f"Dependency {dep_id} failed"
                    break
            else:
                try:
                    result = await self._execute_task(task, plan, results)
                    results[task.id] = result
                except Exception as exc:
                    errors[task.id] = str(exc)

        return CoordinationResult(
            plan_id=plan.id,
            success=len(errors) == 0,
            results=results,
            errors=errors,
            duration_ms=(datetime.now() - start).total_seconds() * 1000,
        )

    async def _execute_parallel(
        self, plan: CoordinationPlan, start: datetime
    ) -> CoordinationResult:
        async def run_task(task: AgentTask) -> tuple[str, Any, str]:
            try:
                result = await self._execute_task(task, plan, {})
                return task.id, result, ""
            except Exception as exc:
                return task.id, None, str(exc)

        task_results = await asyncio.gather(*[run_task(t) for t in plan.tasks])
        results: dict[str, Any] = {}
        errors: dict[str, str] = {}
        for task_id, result, error in task_results:
            if error:
                errors[task_id] = error
            else:
                results[task_id] = result

        return CoordinationResult(
            plan_id=plan.id,
            success=len(errors) == 0,
            results=results,
            errors=errors,
            duration_ms=(datetime.now() - start).total_seconds() * 1000,
        )

    async def _execute_pipeline(
        self, plan: CoordinationPlan, start: datetime
    ) -> CoordinationResult:
        results: dict[str, Any] = {}
        errors: dict[str, str] = {}
        pipeline_data: Any = None

        for task in plan.tasks:
            try:
                if pipeline_data is not None:
                    task.context = task.context or {}
                    task.context["pipeline_input"] = pipeline_data
                result = await self._execute_task(task, plan, results)
                results[task.id] = result
                pipeline_data = result
            except Exception as exc:
                errors[task.id] = str(exc)
                break

        return CoordinationResult(
            plan_id=plan.id,
            success=len(errors) == 0,
            results=results,
            errors=errors,
            duration_ms=(datetime.now() - start).total_seconds() * 1000,
        )

    async def _execute_task(
        self, task: AgentTask, plan: CoordinationPlan, prior_results: dict[str, Any]
    ) -> Any:
        role = plan.agent_assignments.get(task.id)
        if not role:
            raise ValueError(f"No agent assigned to task {task.id}")

        handler = self._task_handlers.get(role)
        if handler and hasattr(handler, "execute"):
            return await handler.execute(task)

        task.status = TaskStatus.COMPLETED
        return {"task_id": task.id, "status": "completed_by_coordinator"}

    def _auto_assign(self, tasks: list[AgentTask]) -> dict[str, AgentRole]:
        assignments: dict[str, AgentRole] = {}
        available = {slot.role: slot for slot in self._agents.values() if not slot.busy}

        for task in tasks:
            role = self._infer_role(task)
            assignments[task.id] = role

        return assignments

    @staticmethod
    def _infer_role(task: AgentTask) -> AgentRole:
        title = task.description.lower()
        if any(kw in title for kw in ("design", "architect", "adr")):
            return AgentRole.ARCHITECT
        if any(kw in title for kw in ("review", "inspect")):
            return AgentRole.REVIEWER
        if any(kw in title for kw in ("security", "vulnerability", "audit")):
            return AgentRole.SECURITY
        if any(kw in title for kw in ("plan", "decompose", "roadmap")):
            return AgentRole.PLANNER
        return AgentRole.DEVELOPER

    def available_agents(self) -> list[AgentSlot]:
        return [s for s in self._agents.values() if not s.busy]

    def get_plan(self, plan_id: str) -> CoordinationPlan | None:
        return self._plans.get(plan_id)

    @property
    def agent_count(self) -> int:
        return len(self._agents)
