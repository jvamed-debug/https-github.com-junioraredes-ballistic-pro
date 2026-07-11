"""CLI Config — gerenciamento de configuração da plataforma."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any


@dataclass
class PlatformConfig:
    project_name: str = ""
    language: str = "python"
    framework: str = ""
    architecture: str = "clean_architecture"
    default_provider: str = "openai"
    default_model: str = "gpt-4"
    autonomy_level: str = "semi_autonomous"
    api_host: str = "localhost"
    api_port: int = 8000
    log_level: str = "INFO"
    providers: dict[str, dict[str, str]] = field(default_factory=dict)
    plugins: list[str] = field(default_factory=list)


class ConfigManager:
    """Gerencia configuração da plataforma com persistência em arquivo."""

    CONFIG_FILE = ".eap.json"

    def __init__(self, base_dir: str = ".") -> None:
        self._base_dir = Path(base_dir)
        self._config = PlatformConfig()
        self._loaded = False

    def load(self) -> PlatformConfig:
        config_path = self._base_dir / self.CONFIG_FILE
        if config_path.exists():
            with open(config_path) as f:
                data = json.load(f)
            self._config = self._from_dict(data)
            self._loaded = True
        return self._config

    def save(self) -> None:
        config_path = self._base_dir / self.CONFIG_FILE
        with open(config_path, "w") as f:
            json.dump(asdict(self._config), f, indent=2)

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self._config, key, default)

    def set(self, key: str, value: Any) -> bool:
        if hasattr(self._config, key):
            setattr(self._config, key, value)
            return True
        return False

    def set_provider(self, name: str, api_key: str = "", base_url: str = "") -> None:
        self._config.providers[name] = {"api_key": api_key, "base_url": base_url}

    def get_provider(self, name: str) -> dict[str, str]:
        return self._config.providers.get(name, {})

    @property
    def config(self) -> PlatformConfig:
        return self._config

    @property
    def is_initialized(self) -> bool:
        return (self._base_dir / self.CONFIG_FILE).exists()

    def reset(self) -> None:
        self._config = PlatformConfig()

    @staticmethod
    def _from_dict(data: dict[str, Any]) -> PlatformConfig:
        valid_fields = {f.name for f in PlatformConfig.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in valid_fields}
        return PlatformConfig(**filtered)
