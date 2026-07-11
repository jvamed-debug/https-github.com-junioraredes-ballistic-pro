"""Agent Communication Protocol — protocolo de comunicação entre agentes."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from core.contracts.agent import AgentRole


class MessageType(str, Enum):
    REQUEST = "request"
    RESPONSE = "response"
    BROADCAST = "broadcast"
    DELEGATE = "delegate"
    NOTIFY = "notify"
    ACK = "ack"


class MessagePriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AgentMessage:
    id: str
    sender: AgentRole
    receiver: AgentRole | None
    message_type: MessageType
    priority: MessagePriority = MessagePriority.NORMAL
    subject: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    correlation_id: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    ttl_seconds: int = 300


MessageHandler = Any


class MessageBus:
    """Barramento de mensagens para comunicação inter-agentes."""

    def __init__(self) -> None:
        self._subscribers: dict[AgentRole, list[MessageHandler]] = {}
        self._message_log: list[AgentMessage] = []
        self._counter = 0

    def subscribe(self, role: AgentRole, handler: MessageHandler) -> None:
        if role not in self._subscribers:
            self._subscribers[role] = []
        self._subscribers[role].append(handler)

    def unsubscribe(self, role: AgentRole) -> None:
        self._subscribers.pop(role, None)

    def create_message(
        self,
        sender: AgentRole,
        receiver: AgentRole | None,
        message_type: MessageType,
        subject: str = "",
        payload: dict[str, Any] | None = None,
        priority: MessagePriority = MessagePriority.NORMAL,
        correlation_id: str = "",
    ) -> AgentMessage:
        self._counter += 1
        return AgentMessage(
            id=f"MSG-{self._counter:06d}",
            sender=sender,
            receiver=receiver,
            message_type=message_type,
            priority=priority,
            subject=subject,
            payload=payload or {},
            correlation_id=correlation_id,
        )

    async def send(self, message: AgentMessage) -> list[Any]:
        self._message_log.append(message)

        if message.message_type == MessageType.BROADCAST:
            return await self._broadcast(message)

        if message.receiver and message.receiver in self._subscribers:
            results = []
            for handler in self._subscribers[message.receiver]:
                if callable(handler):
                    result = handler(message)
                    if hasattr(result, "__await__"):
                        result = await result
                    results.append(result)
            return results

        return []

    async def _broadcast(self, message: AgentMessage) -> list[Any]:
        results = []
        for role, handlers in self._subscribers.items():
            if role == message.sender:
                continue
            for handler in handlers:
                if callable(handler):
                    result = handler(message)
                    if hasattr(result, "__await__"):
                        result = await result
                    results.append(result)
        return results

    def get_log(self, sender: AgentRole | None = None,
                receiver: AgentRole | None = None,
                limit: int = 100) -> list[AgentMessage]:
        messages = self._message_log
        if sender:
            messages = [m for m in messages if m.sender == sender]
        if receiver:
            messages = [m for m in messages if m.receiver == receiver]
        return messages[-limit:]

    @property
    def message_count(self) -> int:
        return len(self._message_log)

    @property
    def subscriber_count(self) -> int:
        return sum(len(handlers) for handlers in self._subscribers.values())
