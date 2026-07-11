"""Audit Log — registro auditável de todas as ações da plataforma."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class AuditAction(str, Enum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXECUTE = "execute"
    LOGIN = "login"
    LOGOUT = "logout"
    APPROVE = "approve"
    DENY = "deny"
    DEPLOY = "deploy"


class AuditSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AuditEntry:
    id: str
    timestamp: datetime
    actor: str
    action: AuditAction
    resource_type: str
    resource_id: str
    tenant_id: str = ""
    severity: AuditSeverity = AuditSeverity.LOW
    details: dict[str, Any] = field(default_factory=dict)
    ip_address: str = ""
    success: bool = True


class AuditLog:
    """Log de auditoria imutável com busca e filtros."""

    def __init__(self, max_entries: int = 100000) -> None:
        self._entries: list[AuditEntry] = []
        self._counter = 0
        self._max_entries = max_entries

    def record(
        self,
        actor: str,
        action: AuditAction,
        resource_type: str,
        resource_id: str,
        tenant_id: str = "",
        severity: AuditSeverity = AuditSeverity.LOW,
        details: dict[str, Any] | None = None,
        ip_address: str = "",
        success: bool = True,
    ) -> AuditEntry:
        self._counter += 1
        entry = AuditEntry(
            id=f"AUD-{self._counter:08d}",
            timestamp=datetime.now(),
            actor=actor,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            tenant_id=tenant_id,
            severity=severity,
            details=details or {},
            ip_address=ip_address,
            success=success,
        )
        self._entries.append(entry)
        if len(self._entries) > self._max_entries:
            self._entries = self._entries[-self._max_entries:]
        return entry

    def query(
        self,
        actor: str | None = None,
        action: AuditAction | None = None,
        resource_type: str | None = None,
        tenant_id: str | None = None,
        severity: AuditSeverity | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 100,
    ) -> list[AuditEntry]:
        results = self._entries
        if actor:
            results = [e for e in results if e.actor == actor]
        if action:
            results = [e for e in results if e.action == action]
        if resource_type:
            results = [e for e in results if e.resource_type == resource_type]
        if tenant_id:
            results = [e for e in results if e.tenant_id == tenant_id]
        if severity:
            results = [e for e in results if e.severity == severity]
        if start_time:
            results = [e for e in results if e.timestamp >= start_time]
        if end_time:
            results = [e for e in results if e.timestamp <= end_time]
        return results[-limit:]

    def get_entry(self, entry_id: str) -> AuditEntry | None:
        for e in self._entries:
            if e.id == entry_id:
                return e
        return None

    def count_by_action(self, action: AuditAction) -> int:
        return sum(1 for e in self._entries if e.action == action)

    def failed_actions(self, limit: int = 50) -> list[AuditEntry]:
        return [e for e in self._entries if not e.success][-limit:]

    def security_events(self, limit: int = 50) -> list[AuditEntry]:
        return [e for e in self._entries
                if e.severity in (AuditSeverity.HIGH, AuditSeverity.CRITICAL)][-limit:]

    @property
    def total_entries(self) -> int:
        return len(self._entries)
