"""Auth & Rate Limiting — autenticação e controle de taxa da API."""

from __future__ import annotations

import hashlib
import secrets
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class AuthMethod(str, Enum):
    API_KEY = "api_key"
    BEARER_TOKEN = "bearer_token"


@dataclass
class APIKey:
    key_id: str
    key_hash: str
    name: str
    owner: str
    scopes: list[str] = field(default_factory=list)
    rate_limit: int = 60
    active: bool = True
    created_at: float = field(default_factory=time.time)


@dataclass
class RateLimitEntry:
    key_id: str
    window_start: float
    request_count: int = 0


class AuthManager:
    """Gerencia autenticação por API key e rate limiting."""

    def __init__(self) -> None:
        self._keys: dict[str, APIKey] = {}
        self._rate_limits: dict[str, RateLimitEntry] = {}
        self._window_seconds = 60

    def create_api_key(self, name: str, owner: str, scopes: list[str] | None = None,
                       rate_limit: int = 60) -> tuple[str, APIKey]:
        raw_key = secrets.token_urlsafe(32)
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        key_id = f"eap_{secrets.token_hex(8)}"

        api_key = APIKey(
            key_id=key_id,
            key_hash=key_hash,
            name=name,
            owner=owner,
            scopes=scopes or ["read"],
            rate_limit=rate_limit,
        )
        self._keys[key_id] = api_key
        return raw_key, api_key

    def validate_key(self, raw_key: str) -> APIKey | None:
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        for api_key in self._keys.values():
            if api_key.key_hash == key_hash and api_key.active:
                return api_key
        return None

    def check_scope(self, api_key: APIKey, required_scope: str) -> bool:
        if "*" in api_key.scopes:
            return True
        return required_scope in api_key.scopes

    def check_rate_limit(self, key_id: str, limit: int = 60) -> bool:
        now = time.time()
        entry = self._rate_limits.get(key_id)

        if entry is None or (now - entry.window_start) >= self._window_seconds:
            self._rate_limits[key_id] = RateLimitEntry(
                key_id=key_id, window_start=now, request_count=1
            )
            return True

        if entry.request_count >= limit:
            return False

        entry.request_count += 1
        return True

    def revoke_key(self, key_id: str) -> bool:
        api_key = self._keys.get(key_id)
        if api_key:
            api_key.active = False
            return True
        return False

    def list_keys(self, owner: str | None = None) -> list[APIKey]:
        keys = list(self._keys.values())
        if owner:
            keys = [k for k in keys if k.owner == owner]
        return keys
