"""Tests for Release 0.7 — API (auth, websocket, routes, middleware)."""

from __future__ import annotations

import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from api.auth import AuthManager
from api.websocket import WebSocketManager, WSEventType
from api.middleware import RequestLogger, CORSConfig, ErrorHandler
from api.routes.agents import AgentRoutes
from api.routes.projects import ProjectRoutes
from api.routes.workflows import WorkflowRoutes
from api.app import EAPApplication


class TestAuthManager(unittest.TestCase):
    def test_create_and_validate_key(self) -> None:
        mgr = AuthManager()
        raw_key, api_key = mgr.create_api_key("test", "user@test.com", scopes=["read", "write"])
        assert api_key.name == "test"
        validated = mgr.validate_key(raw_key)
        assert validated is not None
        assert validated.key_id == api_key.key_id

    def test_invalid_key(self) -> None:
        mgr = AuthManager()
        assert mgr.validate_key("invalid_key") is None

    def test_scope_check(self) -> None:
        mgr = AuthManager()
        _, api_key = mgr.create_api_key("test", "owner", scopes=["read"])
        assert mgr.check_scope(api_key, "read") is True
        assert mgr.check_scope(api_key, "write") is False

    def test_wildcard_scope(self) -> None:
        mgr = AuthManager()
        _, api_key = mgr.create_api_key("admin", "owner", scopes=["*"])
        assert mgr.check_scope(api_key, "anything") is True

    def test_rate_limiting(self) -> None:
        mgr = AuthManager()
        _, api_key = mgr.create_api_key("test", "owner", rate_limit=3)
        assert mgr.check_rate_limit(api_key.key_id, limit=3) is True
        assert mgr.check_rate_limit(api_key.key_id, limit=3) is True
        assert mgr.check_rate_limit(api_key.key_id, limit=3) is True
        assert mgr.check_rate_limit(api_key.key_id, limit=3) is False

    def test_revoke_key(self) -> None:
        mgr = AuthManager()
        raw_key, api_key = mgr.create_api_key("test", "owner")
        mgr.revoke_key(api_key.key_id)
        assert mgr.validate_key(raw_key) is None


class TestWebSocketManager(unittest.TestCase):
    def test_connect_disconnect(self) -> None:
        ws = WebSocketManager()
        conn = ws.connect("ws-1")
        assert ws.connection_count == 1
        ws.disconnect("ws-1")
        assert ws.connection_count == 0

    def test_subscribe_channel(self) -> None:
        ws = WebSocketManager()
        ws.connect("ws-1")
        ws.subscribe("ws-1", "tasks")
        assert "tasks" in ws.channels

    def test_broadcast(self) -> None:
        ws = WebSocketManager()
        ws.connect("ws-1")
        ws.connect("ws-2")
        event = ws.create_event(WSEventType.TASK_STARTED, {"task_id": "T1"})
        recipients = ws.broadcast(event)
        assert len(recipients) == 2

    def test_event_log(self) -> None:
        ws = WebSocketManager()
        ws.create_event(WSEventType.CONNECTED, {"client": "ws-1"})
        ws.create_event(WSEventType.HEARTBEAT)
        log = ws.get_event_log()
        assert len(log) == 2

    def test_event_to_json(self) -> None:
        ws = WebSocketManager()
        event = ws.create_event(WSEventType.STREAM_TOKEN, {"token": "hello"})
        json_str = event.to_json()
        assert '"stream_token"' in json_str


class TestMiddleware(unittest.TestCase):
    def test_request_logger(self) -> None:
        logger = RequestLogger()
        logger.log("GET", "/api/agents", 200, 15.5)
        logger.log("POST", "/api/projects", 201, 22.0)
        assert logger.total_requests == 2
        entries = logger.get_entries(limit=1)
        assert len(entries) == 1

    def test_cors_config(self) -> None:
        cors = CORSConfig()
        assert cors.is_origin_allowed("anything") is True
        cors2 = CORSConfig(allow_origins=["https://example.com"])
        assert cors2.is_origin_allowed("https://example.com") is True
        assert cors2.is_origin_allowed("https://evil.com") is False

    def test_error_handler(self) -> None:
        err = ErrorHandler.not_found("Project")
        assert err["error"]["code"] == 404
        err = ErrorHandler.unauthorized()
        assert err["error"]["code"] == 401
        err = ErrorHandler.rate_limited()
        assert err["error"]["code"] == 429


class TestAgentRoutes(unittest.TestCase):
    def test_list_agents(self) -> None:
        routes = AgentRoutes()
        result = routes.list_agents()
        assert result.success is True
        assert len(result.data) == 8

    def test_get_agent(self) -> None:
        routes = AgentRoutes()
        result = routes.get_agent("architect")
        assert result.success is True
        assert result.data["role"] == "architect"

    def test_get_unknown_agent(self) -> None:
        routes = AgentRoutes()
        result = routes.get_agent("nonexistent")
        assert result.success is False


class TestProjectRoutes(unittest.TestCase):
    def test_create_and_get(self) -> None:
        routes = ProjectRoutes()
        result = routes.create_project("Test Project", language="python")
        assert result.success is True
        project_id = result.data["id"]
        get_result = routes.get_project(project_id)
        assert get_result.success is True

    def test_list_projects(self) -> None:
        routes = ProjectRoutes()
        routes.create_project("P1")
        routes.create_project("P2")
        result = routes.list_projects()
        assert len(result.data) == 2

    def test_delete_project(self) -> None:
        routes = ProjectRoutes()
        result = routes.create_project("To Delete")
        pid = result.data["id"]
        del_result = routes.delete_project(pid)
        assert del_result.success is True


class TestWorkflowRoutes(unittest.TestCase):
    def test_create_and_start(self) -> None:
        routes = WorkflowRoutes()
        result = routes.create_workflow("Test WF", steps_total=3)
        wf_id = result.data["id"]
        start = routes.start_workflow(wf_id)
        assert start.data["status"] == "running"

    def test_complete_steps(self) -> None:
        routes = WorkflowRoutes()
        result = routes.create_workflow("WF", steps_total=2)
        wf_id = result.data["id"]
        routes.start_workflow(wf_id)
        routes.complete_step(wf_id)
        step2 = routes.complete_step(wf_id)
        assert step2.data["status"] == "completed"

    def test_cancel_workflow(self) -> None:
        routes = WorkflowRoutes()
        result = routes.create_workflow("WF")
        wf_id = result.data["id"]
        cancel = routes.cancel_workflow(wf_id)
        assert cancel.data["status"] == "cancelled"


class TestEAPApplication(unittest.TestCase):
    def test_health_check(self) -> None:
        app = EAPApplication()
        health = app.health_check()
        assert health["status"] == "healthy"
        assert "version" in health

    def test_registered_routes(self) -> None:
        app = EAPApplication()
        routes = app.registered_routes
        assert len(routes) >= 5

    def test_handle_unknown_route(self) -> None:
        app = EAPApplication()
        result = app.handle_request("GET", "/api/v1/nonexistent")
        assert result["error"]["code"] == 404


if __name__ == "__main__":
    unittest.main()
