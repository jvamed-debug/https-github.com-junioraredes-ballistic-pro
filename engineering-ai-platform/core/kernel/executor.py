"""Executor — execução coordenada de planos com agentes."""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any

from core.contracts.agent import AgentContext, AgentInterface, AgentRole, AgentTask, TaskStatus
from core.kernel.planner import ExecutionPlan, ExecutionPhase
from core.kernel.validator import ValidationResult, Validator

logger = logging.getLogger(__name__)


@dataclass
class ExecutionReport:
    plan_id: str
    plan_name: str
    total_tasks: int
    completed: int
    failed: int
    skipped: int
    duration_seconds: float
    phase_results: list[PhaseResult] = field(default_factory=list)
    validation: ValidationResult | None = None

    @property
    def success(self) -> bool:
        return self.failed == 0


@dataclass
class PhaseResult:
    name: str
    tasks: list[AgentTask]
    duration_seconds: float

    @property
    def all_succeeded(self) -> bool:
        return all(t.status == TaskStatus.COMPLETED for t in self.tasks)


class Executor:
    """Executa planos de engenharia coordenando agentes e validação."""

    def __init__(
        self,
        agents: dict[AgentRole, AgentInterface],
        validator: Validator | None = None,
        max_parallel: int = 5,
    ) -> None:
        self._agents = agents
        self._validator = validator or Validator()
        self._semaphore = asyncio.Semaphore(max_parallel)

    async def execute_plan(
        self, plan: ExecutionPlan, context: AgentContext
    ) -> ExecutionReport:
        start = time.monotonic()
        phase_results: list[PhaseResult] = []
        completed = 0
        failed = 0
        skipped = 0

        for phase in plan.phases:
            phase_start = time.monotonic()

            if phase.parallel:
                tasks = await self._run_parallel(phase.tasks, context)
            else:
                tasks = await self._run_sequential(phase.tasks, context)

            phase_results.append(PhaseResult(
                name=phase.name,
                tasks=tasks,
                duration_seconds=time.monotonic() - phase_start,
            ))

            for task in tasks:
                if task.status == TaskStatus.COMPLETED:
                    completed += 1
                elif task.status == TaskStatus.FAILED:
                    failed += 1
                else:
                    skipped += 1

            if any(t.status == TaskStatus.FAILED for t in tasks):
                logger.warning("Phase '%s' had failures, continuing...", phase.name)

        duration = time.monotonic() - start

        return ExecutionReport(
            plan_id=plan.id,
            plan_name=plan.name,
            total_tasks=plan.total_tasks,
            completed=completed,
            failed=failed,
            skipped=skipped,
            duration_seconds=duration,
            phase_results=phase_results,
        )

    async def _run_sequential(
        self, tasks: list[AgentTask], context: AgentContext
    ) -> list[AgentTask]:
        results = []
        for task in tasks:
            result = await self._execute_task(task, context)
            results.append(result)
        return results

    async def _run_parallel(
        self, tasks: list[AgentTask], context: AgentContext
    ) -> list[AgentTask]:
        async def _bounded(task: AgentTask) -> AgentTask:
            async with self._semaphore:
                return await self._execute_task(task, context)

        return list(await asyncio.gather(*[_bounded(t) for t in tasks]))

    async def _execute_task(self, task: AgentTask, context: AgentContext) -> AgentTask:
        agent = self._agents.get(task.assigned_to)
        if agent is None:
            task.status = TaskStatus.FAILED
            task.error = f"No agent for role: {task.assigned_to.value}"
            logger.error("No agent for role %s", task.assigned_to.value)
            return task

        try:
            return await agent.execute(task, context)
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            logger.exception("Task '%s' failed", task.description)
            return task
