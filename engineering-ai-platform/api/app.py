"""API Application — ponto de entrada da REST API."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from api.auth import AuthManager
from api.middleware import RequestLogger, CORSConfig, ErrorHandler
from api.websocket import WebSocketManager
from api.routes.agents import AgentRoutes
from api.routes.projects import ProjectRoutes
from api.routes.workflows import WorkflowRoutes


@dataclass
class APIConfig:
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    cors: CORSConfig = field(default_factory=CORSConfig)
    title: str = "Engineering AI Platform API"
    version: str = "1.0.0"


class EAPApplication:
    """Aplicação principal da API — coordena rotas, auth, middleware e websocket."""

    def __init__(self, config: APIConfig | None = None) -> None:
        self.config = config or APIConfig()
        self.auth = AuthManager()
        self.logger = RequestLogger()
        self.ws_manager = WebSocketManager()
        self.agent_routes = AgentRoutes()
        self.project_routes = ProjectRoutes()
        self.workflow_routes = WorkflowRoutes()
        self._routes: dict[str, Any] = {}
        self._register_routes()

    def _register_routes(self) -> None:
        self._routes = {
            "GET /api/v1/agents": self.agent_routes.list_agents,
            "GET /api/v1/agents/{role}": self.agent_routes.get_agent,
            "GET /api/v1/projects": self.project_routes.list_projects,
            "POST /api/v1/projects": self.project_routes.create_project,
            "GET /api/v1/projects/{id}": self.project_routes.get_project,
            "GET /api/v1/workflows": self.workflow_routes.list_workflows,
            "POST /api/v1/workflows": self.workflow_routes.create_workflow,
            "GET /api/v1/workflows/{id}": self.workflow_routes.get_workflow,
            "POST /api/v1/workflows/{id}/start": self.workflow_routes.start_workflow,
        }

    def handle_request(self, method: str, path: str, body: dict[str, Any] | None = None,
                       api_key: str = "") -> dict[str, Any]:
        if api_key:
            key = self.auth.validate_key(api_key)
            if not key:
                return ErrorHandler.unauthorized()
            if not self.auth.check_rate_limit(key.key_id, key.rate_limit):
                return ErrorHandler.rate_limited()

        route_key = f"{method} {path}"
        handler = self._routes.get(route_key)
        if handler:
            result = handler(**(body or {}))
            return {"success": result.success, "data": result.data, "error": result.error}

        return ErrorHandler.not_found(path)

    @property
    def registered_routes(self) -> list[str]:
        return list(self._routes.keys())

    def health_check(self) -> dict[str, Any]:
        return {
            "status": "healthy",
            "version": self.config.version,
            "connections": self.ws_manager.connection_count,
            "total_requests": self.logger.total_requests,
        }
