"""Workflow Definition — definição declarativa de workflows."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from core.contracts.agent import AgentRole


class StepType(str, Enum):
    AGENT = "agent"
    VALIDATION = "validation"
    GATE = "gate"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"


@dataclass
class WorkflowStep:
    id: str
    name: str
    step_type: StepType
    agent_role: AgentRole | None = None
    config: dict[str, Any] = field(default_factory=dict)
    depends_on: list[str] = field(default_factory=list)
    on_failure: str = "stop"


@dataclass
class WorkflowDefinition:
    id: str
    name: str
    description: str
    steps: list[WorkflowStep] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_step(self, step: WorkflowStep) -> None:
        self.steps.append(step)

    def get_step(self, step_id: str) -> WorkflowStep | None:
        return next((s for s in self.steps if s.id == step_id), None)

    @property
    def step_ids(self) -> list[str]:
        return [s.id for s in self.steps]


class WorkflowBuilder:
    """Builder fluente para criar workflows."""

    def __init__(self, name: str, description: str = "") -> None:
        self._definition = WorkflowDefinition(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
        )

    def add_agent_step(
        self,
        name: str,
        role: AgentRole,
        depends_on: list[str] | None = None,
        config: dict[str, Any] | None = None,
    ) -> WorkflowBuilder:
        step = WorkflowStep(
            id=str(uuid.uuid4()),
            name=name,
            step_type=StepType.AGENT,
            agent_role=role,
            depends_on=depends_on or [],
            config=config or {},
        )
        self._definition.add_step(step)
        return self

    def add_validation_step(
        self,
        name: str,
        depends_on: list[str] | None = None,
        config: dict[str, Any] | None = None,
    ) -> WorkflowBuilder:
        step = WorkflowStep(
            id=str(uuid.uuid4()),
            name=name,
            step_type=StepType.VALIDATION,
            depends_on=depends_on or [],
            config=config or {},
        )
        self._definition.add_step(step)
        return self

    def add_gate(
        self,
        name: str,
        depends_on: list[str] | None = None,
        on_failure: str = "stop",
    ) -> WorkflowBuilder:
        step = WorkflowStep(
            id=str(uuid.uuid4()),
            name=name,
            step_type=StepType.GATE,
            depends_on=depends_on or [],
            on_failure=on_failure,
        )
        self._definition.add_step(step)
        return self

    def build(self) -> WorkflowDefinition:
        return self._definition
