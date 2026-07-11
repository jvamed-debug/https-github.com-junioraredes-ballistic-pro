"""Tests for Release 0.6 — Agents (autonomy, protocol, knowledge, documentation)."""

from __future__ import annotations

import sys
import os
import asyncio
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from agents.autonomy import (
    AutonomyLevel, AutonomyManager, AutonomyPolicy, DEFAULT_POLICIES,
)
from agents.protocol import (
    AgentMessage, MessageBus, MessageType, MessagePriority,
)
from core.contracts.agent import AgentRole


class TestAutonomyManager(unittest.TestCase):
    def test_default_policy(self) -> None:
        mgr = AutonomyManager()
        policy = mgr.get_policy("agent-1")
        assert policy.level == AutonomyLevel.SEMI_AUTONOMOUS

    def test_set_level(self) -> None:
        mgr = AutonomyManager()
        mgr.set_level("agent-1", AutonomyLevel.AUTONOMOUS)
        policy = mgr.get_policy("agent-1")
        assert policy.level == AutonomyLevel.AUTONOMOUS

    def test_can_execute_auto_approve(self) -> None:
        mgr = AutonomyManager()
        mgr.set_level("agent-1", AutonomyLevel.SEMI_AUTONOMOUS)
        assert mgr.can_execute("agent-1", "read") is True
        assert mgr.can_execute("agent-1", "deploy") is False

    def test_can_execute_cost_limit(self) -> None:
        mgr = AutonomyManager()
        mgr.set_level("agent-1", AutonomyLevel.SEMI_AUTONOMOUS)
        assert mgr.can_execute("agent-1", "read", estimated_cost=0.5) is True
        assert mgr.can_execute("agent-1", "read", estimated_cost=5.0) is False

    def test_request_and_approve(self) -> None:
        mgr = AutonomyManager()
        req = mgr.request_approval("agent-1", "deploy", "Deploy to prod")
        assert req.approved is None
        assert len(mgr.pending_approvals()) == 1
        mgr.approve(req.id, reviewer="admin")
        assert req.approved is True
        assert len(mgr.pending_approvals()) == 0

    def test_deny_request(self) -> None:
        mgr = AutonomyManager()
        req = mgr.request_approval("agent-1", "delete", "Delete database")
        mgr.deny(req.id)
        assert req.approved is False

    def test_blocked_actions(self) -> None:
        mgr = AutonomyManager()
        policy = AutonomyPolicy(
            level=AutonomyLevel.AUTONOMOUS,
            auto_approve=["*"],
            blocked_actions=["delete_prod"],
        )
        mgr.set_policy("agent-1", policy)
        assert mgr.can_execute("agent-1", "read") is True
        assert mgr.can_execute("agent-1", "delete_prod") is False

    def test_full_autonomous(self) -> None:
        mgr = AutonomyManager()
        mgr.set_level("agent-1", AutonomyLevel.FULL_AUTONOMOUS)
        assert mgr.can_execute("agent-1", "deploy") is True
        assert mgr.can_execute("agent-1", "merge") is True


class TestMessageBus(unittest.TestCase):
    def test_create_message(self) -> None:
        bus = MessageBus()
        msg = bus.create_message(
            sender=AgentRole.ORCHESTRATOR,
            receiver=AgentRole.DEVELOPER,
            message_type=MessageType.REQUEST,
            subject="Generate code",
        )
        assert msg.id == "MSG-000001"
        assert msg.sender == AgentRole.ORCHESTRATOR

    def test_send_to_subscriber(self) -> None:
        bus = MessageBus()
        received = []

        def handler(msg: AgentMessage) -> str:
            received.append(msg)
            return "ok"

        bus.subscribe(AgentRole.DEVELOPER, handler)
        msg = bus.create_message(
            sender=AgentRole.ORCHESTRATOR,
            receiver=AgentRole.DEVELOPER,
            message_type=MessageType.REQUEST,
        )
        results = asyncio.get_event_loop().run_until_complete(bus.send(msg))
        assert len(received) == 1
        assert results == ["ok"]

    def test_broadcast(self) -> None:
        bus = MessageBus()
        received_by: list[str] = []

        def dev_handler(msg: AgentMessage) -> None:
            received_by.append("dev")

        def sec_handler(msg: AgentMessage) -> None:
            received_by.append("sec")

        bus.subscribe(AgentRole.DEVELOPER, dev_handler)
        bus.subscribe(AgentRole.SECURITY, sec_handler)

        msg = bus.create_message(
            sender=AgentRole.ORCHESTRATOR,
            receiver=None,
            message_type=MessageType.BROADCAST,
            subject="System update",
        )
        asyncio.get_event_loop().run_until_complete(bus.send(msg))
        assert "dev" in received_by
        assert "sec" in received_by

    def test_message_log(self) -> None:
        bus = MessageBus()
        msg = bus.create_message(
            sender=AgentRole.ARCHITECT,
            receiver=AgentRole.DEVELOPER,
            message_type=MessageType.DELEGATE,
        )
        asyncio.get_event_loop().run_until_complete(bus.send(msg))
        log = bus.get_log()
        assert len(log) == 1
        assert bus.message_count == 1

    def test_unsubscribe(self) -> None:
        bus = MessageBus()
        bus.subscribe(AgentRole.DEVELOPER, lambda m: None)
        assert bus.subscriber_count == 1
        bus.unsubscribe(AgentRole.DEVELOPER)
        assert bus.subscriber_count == 0


class TestDefaultPolicies(unittest.TestCase):
    def test_all_levels_defined(self) -> None:
        for level in AutonomyLevel:
            assert level in DEFAULT_POLICIES

    def test_supervised_blocks_all(self) -> None:
        policy = DEFAULT_POLICIES[AutonomyLevel.SUPERVISED]
        assert "*" in policy.requires_approval
        assert len(policy.auto_approve) == 0


if __name__ == "__main__":
    unittest.main()
