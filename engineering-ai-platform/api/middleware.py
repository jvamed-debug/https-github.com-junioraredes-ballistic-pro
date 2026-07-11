"""API Middleware — middleware para logging, CORS e error handling."""

from __future__ import annotations

import time
import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class RequestLog:
    method: str
    path: str
    status_code: int
    duration_ms: float
    client_ip: str = ""
    key_id: str = ""
    timestamp: float = field(default_factory=time.time)


class RequestLogger:
    """Registra requisições para auditoria."""

    def __init__(self, max_entries: int = 10000) -> None:
        self._entries: list[RequestLog] = []
        self._max_entries = max_entries

    def log(self, method: str, path: str, status_code: int, duration_ms: float,
            client_ip: str = "", key_id: str = "") -> RequestLog:
        entry = RequestLog(
            method=method, path=path, status_code=status_code,
            duration_ms=duration_ms, client_ip=client_ip, key_id=key_id,
        )
        self._entries.append(entry)
        if len(self._entries) > self._max_entries:
            self._entries = self._entries[-self._max_entries:]
        return entry

    def get_entries(self, limit: int = 100, path: str | None = None) -> list[RequestLog]:
        entries = self._entries
        if path:
            entries = [e for e in entries if e.path == path]
        return entries[-limit:]

    @property
    def total_requests(self) -> int:
        return len(self._entries)


@dataclass
class CORSConfig:
    allow_origins: list[str] = field(default_factory=lambda: ["*"])
    allow_methods: list[str] = field(default_factory=lambda: ["GET", "POST", "PUT", "DELETE"])
    allow_headers: list[str] = field(default_factory=lambda: ["*"])
    max_age: int = 3600

    def is_origin_allowed(self, origin: str) -> bool:
        if "*" in self.allow_origins:
            return True
        return origin in self.allow_origins


class ErrorHandler:
    """Formata erros da API de forma consistente."""

    @staticmethod
    def format_error(status_code: int, message: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
        return {
            "error": {
                "code": status_code,
                "message": message,
                "details": details or {},
            }
        }

    @staticmethod
    def not_found(resource: str) -> dict[str, Any]:
        return ErrorHandler.format_error(404, f"{resource} not found")

    @staticmethod
    def unauthorized(message: str = "Invalid or missing API key") -> dict[str, Any]:
        return ErrorHandler.format_error(401, message)

    @staticmethod
    def rate_limited() -> dict[str, Any]:
        return ErrorHandler.format_error(429, "Rate limit exceeded")

    @staticmethod
    def validation_error(details: dict[str, Any]) -> dict[str, Any]:
        return ErrorHandler.format_error(422, "Validation error", details)
