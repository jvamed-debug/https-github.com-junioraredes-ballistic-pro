"""Workflow Engine — motor de execução de workflows."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Awaitable

from core.workflow.definition import (
    StepType,
    WorkflowDefinition,
    WorkflowStep,
)


class WorkflowStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


@dataclass
class StepResult:
    step_id: str
    status: WorkflowStatus
    output: Any = None
    error: str = ""
    duration_ms: float = 0


@dataclass
class WorkflowRun:
    id: str
    workflow_id: str
    status: WorkflowStatus = WorkflowStatus.PENDING
    started_at: datetime | None = None
    finished_at: datetime | None = None
    step_results: list[StepResult] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)

    @property
    def duration_ms(self) -> float:
        if self.started_at and self.finished_at:
            return (self.finished_at - self.started_at).total_seconds() * 1000
        return 0

    @property
    def success(self) -> bool:
        return self.status == WorkflowStatus.COMPLETED


StepHandler = Callable[[WorkflowStep, dict[str, Any]], Awaitable[Any]]


class WorkflowEngine:
    """Motor de execução de workflows definidos via WorkflowDefinition."""

    def __init__(self) -> None:
        self._handlers: dict[StepType, StepHandler] = {}
        self._runs: dict[str, WorkflowRun] = {}
        self._run_counter = 0

    def register_handler(self, step_type: StepType, handler: StepHandler) -> None:
        self._handlers[step_type] = handler

    async def execute(
        self, workflow: WorkflowDefinition, context: dict[str, Any] | None = None
    ) -> WorkflowRun:
        self._run_counter += 1
        run = WorkflowRun(
            id=f"WR-{self._run_counter:06d}",
            workflow_id=workflow.id,
            status=WorkflowStatus.RUNNING,
            started_at=datetime.now(),
            context=dict(context or {}),
        )
        self._runs[run.id] = run

        try:
            for step in workflow.steps:
                result = await self._execute_step(step, run.context)
                run.step_results.append(result)
                if result.status == WorkflowStatus.FAILED:
                    if step.on_failure == "stop":
                        run.status = WorkflowStatus.FAILED
                        break
                run.context[step.id] = result.output
            else:
                run.status = WorkflowStatus.COMPLETED
        except Exception as exc:
            run.status = WorkflowStatus.FAILED
            run.step_results.append(StepResult(
                step_id="engine-error", status=WorkflowStatus.FAILED, error=str(exc)
            ))

        run.finished_at = datetime.now()
        return run

    async def _execute_step(self, step: WorkflowStep, context: dict[str, Any]) -> StepResult:
        start = datetime.now()

        if step.step_type == StepType.GATE:
            return self._execute_gate(step, context, start)

        if step.step_type == StepType.CONDITIONAL:
            return self._execute_conditional(step, context, start)

        handler = self._handlers.get(step.step_type)
        if not handler:
            return StepResult(
                step_id=step.id,
                status=WorkflowStatus.FAILED,
                error=f"No handler for step type: {step.step_type.value}",
                duration_ms=self._elapsed(start),
            )

        try:
            output = await handler(step, context)
            return StepResult(
                step_id=step.id,
                status=WorkflowStatus.COMPLETED,
                output=output,
                duration_ms=self._elapsed(start),
            )
        except Exception as exc:
            return StepResult(
                step_id=step.id,
                status=WorkflowStatus.FAILED,
                error=str(exc),
                duration_ms=self._elapsed(start),
            )

    def _execute_gate(
        self, step: WorkflowStep, context: dict[str, Any], start: datetime
    ) -> StepResult:
        gate_key = step.config.get("gate_key", step.id)
        approved = context.get(gate_key, False)
        return StepResult(
            step_id=step.id,
            status=WorkflowStatus.COMPLETED if approved else WorkflowStatus.FAILED,
            output={"approved": approved},
            duration_ms=self._elapsed(start),
        )

    def _execute_conditional(
        self, step: WorkflowStep, context: dict[str, Any], start: datetime
    ) -> StepResult:
        condition_met = bool(context.get(step.config.get("condition_key", ""), False))
        return StepResult(
            step_id=step.id,
            status=WorkflowStatus.COMPLETED,
            output={"condition_met": condition_met},
            duration_ms=self._elapsed(start),
        )

    def get_run(self, run_id: str) -> WorkflowRun | None:
        return self._runs.get(run_id)

    def list_runs(self, workflow_id: str | None = None) -> list[WorkflowRun]:
        runs = list(self._runs.values())
        if workflow_id:
            runs = [r for r in runs if r.workflow_id == workflow_id]
        return runs

    @staticmethod
    def _elapsed(start: datetime) -> float:
        return (datetime.now() - start).total_seconds() * 1000
