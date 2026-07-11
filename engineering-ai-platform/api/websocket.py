"""WebSocket Manager — streaming bidirecional para execuções em tempo real."""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class WSEventType(str, Enum):
    CONNECTED = "connected"
    TASK_STARTED = "task_started"
    TASK_PROGRESS = "task_progress"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    AGENT_MESSAGE = "agent_message"
    STREAM_TOKEN = "stream_token"
    HEARTBEAT = "heartbeat"
    ERROR = "error"


@dataclass
class WSEvent:
    event_type: WSEventType
    data: dict[str, Any] = field(default_factory=dict)
    channel: str = "default"
    timestamp: datetime = field(default_factory=datetime.now)

    def to_json(self) -> str:
        return json.dumps({
            "event": self.event_type.value,
            "data": self.data,
            "channel": self.channel,
            "timestamp": self.timestamp.isoformat(),
        })


@dataclass
class WSConnection:
    connection_id: str
    channels: set[str] = field(default_factory=lambda: {"default"})
    connected_at: datetime = field(default_factory=datetime.now)
    messages_sent: int = 0


class WebSocketManager:
    """Gerencia conexões WebSocket e distribuição de eventos."""

    def __init__(self) -> None:
        self._connections: dict[str, WSConnection] = {}
        self._channel_subscribers: dict[str, set[str]] = {}
        self._event_log: list[WSEvent] = []
        self._counter = 0

    def connect(self, connection_id: str | None = None) -> WSConnection:
        self._counter += 1
        cid = connection_id or f"ws-{self._counter:06d}"
        conn = WSConnection(connection_id=cid)
        self._connections[cid] = conn
        self._subscribe_to_channel(cid, "default")
        return conn

    def disconnect(self, connection_id: str) -> None:
        conn = self._connections.pop(connection_id, None)
        if conn:
            for channel in conn.channels:
                subs = self._channel_subscribers.get(channel)
                if subs:
                    subs.discard(connection_id)

    def subscribe(self, connection_id: str, channel: str) -> bool:
        conn = self._connections.get(connection_id)
        if not conn:
            return False
        conn.channels.add(channel)
        self._subscribe_to_channel(connection_id, channel)
        return True

    def unsubscribe(self, connection_id: str, channel: str) -> bool:
        conn = self._connections.get(connection_id)
        if not conn:
            return False
        conn.channels.discard(channel)
        subs = self._channel_subscribers.get(channel)
        if subs:
            subs.discard(connection_id)
        return True

    def create_event(self, event_type: WSEventType, data: dict[str, Any] | None = None,
                     channel: str = "default") -> WSEvent:
        event = WSEvent(event_type=event_type, data=data or {}, channel=channel)
        self._event_log.append(event)
        return event

    def get_recipients(self, channel: str) -> list[str]:
        return list(self._channel_subscribers.get(channel, set()))

    def broadcast(self, event: WSEvent) -> list[str]:
        recipients = self.get_recipients(event.channel)
        for cid in recipients:
            conn = self._connections.get(cid)
            if conn:
                conn.messages_sent += 1
        return recipients

    def _subscribe_to_channel(self, connection_id: str, channel: str) -> None:
        if channel not in self._channel_subscribers:
            self._channel_subscribers[channel] = set()
        self._channel_subscribers[channel].add(connection_id)

    @property
    def connection_count(self) -> int:
        return len(self._connections)

    @property
    def channels(self) -> list[str]:
        return list(self._channel_subscribers.keys())

    def get_event_log(self, channel: str | None = None, limit: int = 100) -> list[WSEvent]:
        events = self._event_log
        if channel:
            events = [e for e in events if e.channel == channel]
        return events[-limit:]
