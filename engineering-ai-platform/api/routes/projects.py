"""Project Routes — endpoints REST para gerenciamento de projetos."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class ProjectInfo:
    id: str
    name: str
    language: str = "python"
    framework: str = ""
    architecture: str = "clean_architecture"
    status: str = "active"
    created_at: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ProjectRouteResponse:
    success: bool
    data: Any = None
    error: str = ""


class ProjectRoutes:
    """Handlers para endpoints de projetos."""

    def __init__(self) -> None:
        self._projects: dict[str, ProjectInfo] = {}
        self._counter = 0

    def create_project(self, name: str, language: str = "python",
                       framework: str = "", architecture: str = "clean_architecture",
                       metadata: dict[str, Any] | None = None) -> ProjectRouteResponse:
        self._counter += 1
        project_id = f"PRJ-{self._counter:06d}"
        project = ProjectInfo(
            id=project_id, name=name, language=language,
            framework=framework, architecture=architecture,
            metadata=metadata or {},
        )
        self._projects[project_id] = project
        return ProjectRouteResponse(success=True, data={
            "id": project.id, "name": project.name, "status": project.status,
        })

    def get_project(self, project_id: str) -> ProjectRouteResponse:
        project = self._projects.get(project_id)
        if not project:
            return ProjectRouteResponse(success=False, error=f"Project '{project_id}' not found")
        return ProjectRouteResponse(success=True, data=vars(project))

    def list_projects(self, status: str | None = None) -> ProjectRouteResponse:
        projects = list(self._projects.values())
        if status:
            projects = [p for p in projects if p.status == status]
        return ProjectRouteResponse(
            success=True,
            data=[{"id": p.id, "name": p.name, "status": p.status} for p in projects],
        )

    def update_project(self, project_id: str, **kwargs: Any) -> ProjectRouteResponse:
        project = self._projects.get(project_id)
        if not project:
            return ProjectRouteResponse(success=False, error=f"Project '{project_id}' not found")
        for key, value in kwargs.items():
            if hasattr(project, key) and key != "id":
                setattr(project, key, value)
        return ProjectRouteResponse(success=True, data={"id": project.id, "name": project.name})

    def delete_project(self, project_id: str) -> ProjectRouteResponse:
        if project_id not in self._projects:
            return ProjectRouteResponse(success=False, error=f"Project '{project_id}' not found")
        self._projects.pop(project_id)
        return ProjectRouteResponse(success=True, data={"deleted": project_id})
