"""Tests for Release 0.5 — Runtime modules."""

from __future__ import annotations

import asyncio
import sys
import os
import unittest
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from core.contracts.agent import AgentRole, AgentTask, TaskStatus
from core.workflow.definition import WorkflowBuilder, StepType
from runtime.workflow_engine.engine import WorkflowEngine, WorkflowStatus
from runtime.scheduler.scheduler import Scheduler, ScheduleType
from runtime.coordinator.agent_coordinator import (
    AgentCoordinator,
    CoordinationStrategy,
)


class TestWorkflowEngine(unittest.TestCase):
    def test_execute_simple_workflow(self) -> None:
        engine = WorkflowEngine()

        async def agent_handler(step, ctx):
            return {"processed": step.id}

        engine.register_handler(StepType.AGENT, agent_handler)

        wf = (
            WorkflowBuilder("Test")
            .add_agent_step("Step 1", AgentRole.DEVELOPER)
            .build()
        )

        run = asyncio.get_event_loop().run_until_complete(engine.execute(wf))
        assert run.success
        assert len(run.step_results) == 1

    def test_gate_blocks_on_false(self) -> None:
        engine = WorkflowEngine()
        wf = (
            WorkflowBuilder("Gate Test")
            .add_gate("Approval Gate")
            .build()
        )
        gate_id = wf.steps[0].id

        run = asyncio.get_event_loop().run_until_complete(
            engine.execute(wf, context={gate_id: False})
        )
        assert not run.success

    def test_gate_passes_on_true(self) -> None:
        engine = WorkflowEngine()
        wf = (
            WorkflowBuilder("Gate Test")
            .add_gate("Approval Gate")
            .build()
        )
        gate_id = wf.steps[0].id

        run = asyncio.get_event_loop().run_until_complete(
            engine.execute(wf, context={gate_id: True})
        )
        assert run.success

    def test_list_runs(self) -> None:
        engine = WorkflowEngine()

        async def noop(step, ctx):
            return {}

        engine.register_handler(StepType.AGENT, noop)
        wf = WorkflowBuilder("Test").add_agent_step("Step", AgentRole.DEVELOPER).build()
        asyncio.get_event_loop().run_until_complete(engine.execute(wf))
        assert len(engine.list_runs()) == 1


class TestScheduler(unittest.TestCase):
    def test_schedule_once(self) -> None:
        scheduler = Scheduler()
        job = scheduler.schedule_once(
            "Test Job", "noop", run_at=datetime.now() + timedelta(hours=1)
        )
        assert job.schedule_type == ScheduleType.ONCE
        assert scheduler.pending_count() == 1

    def test_cancel_job(self) -> None:
        scheduler = Scheduler()
        job = scheduler.schedule_once(
            "Test", "noop", run_at=datetime.now() + timedelta(hours=1)
        )
        assert scheduler.cancel(job.id)
        assert scheduler.pending_count() == 0

    def test_tick_executes_due_jobs(self) -> None:
        scheduler = Scheduler()
        executed = []

        async def callback(job):
            executed.append(job.id)

        scheduler.register_callback("test_cb", callback)
        scheduler.schedule_once(
            "Due Job", "test_cb", run_at=datetime.now() - timedelta(seconds=1)
        )

        asyncio.get_event_loop().run_until_complete(scheduler.tick())
        assert len(executed) == 1

    def test_schedule_interval(self) -> None:
        scheduler = Scheduler()
        job = scheduler.schedule_interval("Periodic", "noop", interval_seconds=60, max_runs=5)
        assert job.schedule_type == ScheduleType.INTERVAL
        assert job.max_runs == 5


class TestAgentCoordinator(unittest.TestCase):
    def test_register_agents(self) -> None:
        coord = AgentCoordinator()
        coord.register_agent("agent-1", AgentRole.DEVELOPER)
        coord.register_agent("agent-2", AgentRole.ARCHITECT)
        assert coord.agent_count == 2

    def test_create_plan(self) -> None:
        coord = AgentCoordinator()
        coord.register_agent("dev-1", AgentRole.DEVELOPER)
        tasks = [
            AgentTask(id="T1", description="Design API", assigned_to=AgentRole.ARCHITECT),
            AgentTask(id="T2", description="Implement handler", assigned_to=AgentRole.DEVELOPER),
        ]
        plan = coord.create_plan(CoordinationStrategy.SEQUENTIAL, tasks)
        assert len(plan.tasks) == 2
        assert plan.strategy == CoordinationStrategy.SEQUENTIAL

    def test_execute_sequential_plan(self) -> None:
        coord = AgentCoordinator()
        coord.register_agent("dev-1", AgentRole.DEVELOPER)
        tasks = [
            AgentTask(id="T1", description="Implement feature", assigned_to=AgentRole.DEVELOPER),
        ]
        plan = coord.create_plan(CoordinationStrategy.SEQUENTIAL, tasks)
        result = asyncio.get_event_loop().run_until_complete(coord.execute_plan(plan))
        assert result.success

    def test_available_agents(self) -> None:
        coord = AgentCoordinator()
        coord.register_agent("dev-1", AgentRole.DEVELOPER)
        assert len(coord.available_agents()) == 1


if __name__ == "__main__":
    unittest.main()
