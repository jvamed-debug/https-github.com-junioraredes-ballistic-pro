"""Workflow Routes — endpoints REST para gerenciamento de workflows."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class WorkflowInfo:
    id: str
    name: str
    status: str = "created"
    steps_total: int = 0
    steps_completed: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowRouteResponse:
    success: bool
    data: Any = None
    error: str = ""


class WorkflowRoutes:
    """Handlers para endpoints de workflows."""

    def __init__(self) -> None:
        self._workflows: dict[str, WorkflowInfo] = {}
        self._counter = 0

    def create_workflow(self, name: str, steps_total: int = 0,
                        metadata: dict[str, Any] | None = None) -> WorkflowRouteResponse:
        self._counter += 1
        wf_id = f"WF-{self._counter:06d}"
        wf = WorkflowInfo(
            id=wf_id, name=name, steps_total=steps_total,
            metadata=metadata or {},
        )
        self._workflows[wf_id] = wf
        return WorkflowRouteResponse(success=True, data={
            "id": wf.id, "name": wf.name, "status": wf.status,
        })

    def get_workflow(self, workflow_id: str) -> WorkflowRouteResponse:
        wf = self._workflows.get(workflow_id)
        if not wf:
            return WorkflowRouteResponse(success=False, error=f"Workflow '{workflow_id}' not found")
        return WorkflowRouteResponse(success=True, data=vars(wf))

    def list_workflows(self, status: str | None = None) -> WorkflowRouteResponse:
        workflows = list(self._workflows.values())
        if status:
            workflows = [w for w in workflows if w.status == status]
        return WorkflowRouteResponse(
            success=True,
            data=[{"id": w.id, "name": w.name, "status": w.status} for w in workflows],
        )

    def start_workflow(self, workflow_id: str) -> WorkflowRouteResponse:
        wf = self._workflows.get(workflow_id)
        if not wf:
            return WorkflowRouteResponse(success=False, error=f"Workflow '{workflow_id}' not found")
        wf.status = "running"
        return WorkflowRouteResponse(success=True, data={"id": wf.id, "status": wf.status})

    def complete_step(self, workflow_id: str) -> WorkflowRouteResponse:
        wf = self._workflows.get(workflow_id)
        if not wf:
            return WorkflowRouteResponse(success=False, error=f"Workflow '{workflow_id}' not found")
        wf.steps_completed += 1
        if wf.steps_total > 0 and wf.steps_completed >= wf.steps_total:
            wf.status = "completed"
        return WorkflowRouteResponse(success=True, data={
            "id": wf.id, "steps_completed": wf.steps_completed, "status": wf.status,
        })

    def cancel_workflow(self, workflow_id: str) -> WorkflowRouteResponse:
        wf = self._workflows.get(workflow_id)
        if not wf:
            return WorkflowRouteResponse(success=False, error=f"Workflow '{workflow_id}' not found")
        wf.status = "cancelled"
        return WorkflowRouteResponse(success=True, data={"id": wf.id, "status": wf.status})
