"""Tests for Release 0.2 — Kernel modules."""

from __future__ import annotations

import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from core.contracts.agent import AgentRole
from core.kernel.planner import ExecutionPlanner
from core.kernel.validator import Validator
from core.kernel.review_engine import ReviewEngine
from core.workflow.definition import WorkflowBuilder, StepType


class TestExecutionPlanner(unittest.TestCase):
    def test_create_general_plan(self) -> None:
        planner = ExecutionPlanner()
        plan = planner.create_plan("Test Plan", {"type": "general"})
        assert plan.name == "Test Plan"
        assert len(plan.phases) >= 1

    def test_architecture_plan(self) -> None:
        planner = ExecutionPlanner()
        plan = planner.create_plan("Arch Plan", {"type": "architecture"})
        assert len(plan.phases) >= 2

    def test_implementation_plan(self) -> None:
        planner = ExecutionPlanner()
        plan = planner.create_plan("Impl Plan", {"type": "implementation"})
        assert any("implementation" in p.name.lower() for p in plan.phases)

    def test_progress_tracking(self) -> None:
        planner = ExecutionPlanner()
        plan = planner.create_plan("Test", {"type": "general"})
        assert plan.progress == 0.0
        assert plan.total_tasks >= 1


class TestValidator(unittest.TestCase):
    def test_validate_safe_code(self) -> None:
        validator = Validator()
        result = validator.validate_code("def hello():\n    return 'world'")
        assert result.valid

    def test_validate_dangerous_code(self) -> None:
        validator = Validator()
        result = validator.validate_code("eval(user_input)")
        assert len(result.warnings) > 0

    def test_validate_architecture_with_components(self) -> None:
        validator = Validator()
        arch = {"components": ["api", "service"], "patterns": ["repo"], "security": True}
        result = validator.validate_architecture(arch)
        assert result.valid

    def test_validate_architecture_missing_components(self) -> None:
        validator = Validator()
        result = validator.validate_architecture({})
        assert not result.valid

    def test_validate_artifact(self) -> None:
        validator = Validator()
        result = validator.validate({"id": "A1", "type": "service", "version": "1.0"})
        assert result.valid


class TestReviewEngine(unittest.TestCase):
    def test_code_review(self) -> None:
        engine = ReviewEngine()
        report = engine.review(
            {"id": "C1", "content": 'def foo():\n    """Doc."""\n    return 42\n', "tests": True},
            "code",
        )
        assert 0 <= report.score <= 10

    def test_architecture_review(self) -> None:
        engine = ReviewEngine()
        report = engine.review(
            {"id": "A1", "components": ["api"], "security": True},
            "architecture",
        )
        assert report.score >= 0

    def test_score_max_when_no_findings(self) -> None:
        engine = ReviewEngine()
        report = engine.review({"id": "X1"}, "unknown_type")
        assert report.score == 10.0


class TestWorkflowBuilder(unittest.TestCase):
    def test_build_agent_workflow(self) -> None:
        wf = (
            WorkflowBuilder("Test Workflow")
            .add_agent_step("Design", AgentRole.ARCHITECT)
            .add_agent_step("Implement", AgentRole.DEVELOPER)
            .build()
        )
        assert wf.name == "Test Workflow"
        assert len(wf.steps) == 2

    def test_build_with_gate(self) -> None:
        wf = (
            WorkflowBuilder("Gate Workflow")
            .add_agent_step("Code", AgentRole.DEVELOPER)
            .add_gate("Approval")
            .build()
        )
        assert wf.steps[1].step_type == StepType.GATE

    def test_validation_step(self) -> None:
        wf = (
            WorkflowBuilder("Validation Workflow")
            .add_validation_step("Check quality")
            .build()
        )
        assert wf.steps[0].step_type == StepType.VALIDATION


if __name__ == "__main__":
    unittest.main()
