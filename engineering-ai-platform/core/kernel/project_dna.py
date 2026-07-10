"""Project DNA — identidade técnica do projeto.

Cada projeto possui um arquivo de identidade que o Kernel usa
para adaptar decisões automaticamente.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class ProjectDNA:
    name: str
    language: str
    framework: str
    architecture: str
    database: str | None = None
    cache: str | None = None
    frontend: str | None = None
    cloud: str | None = None
    security: str | None = None
    style: str = "enterprise"
    documentation: str = "exhaustive"
    testing_coverage: int = 80
    deployment: str = "docker"
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_yaml(cls, path: Path) -> ProjectDNA:
        with open(path) as f:
            data = yaml.safe_load(f)

        project = data.get("project", {})
        testing = data.get("testing", {})

        return cls(
            name=project.get("name", "unnamed"),
            language=data.get("language", "python"),
            framework=data.get("framework", ""),
            architecture=data.get("architecture", "clean architecture"),
            database=data.get("database"),
            cache=data.get("cache"),
            frontend=data.get("frontend"),
            cloud=data.get("cloud"),
            security=data.get("security"),
            style=data.get("style", "enterprise"),
            documentation=data.get("documentation", "exhaustive"),
            testing_coverage=testing.get("coverage", 80),
            deployment=data.get("deployment", "docker"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "project": {"name": self.name},
            "language": self.language,
            "framework": self.framework,
            "architecture": self.architecture,
            "database": self.database,
            "cache": self.cache,
            "frontend": self.frontend,
            "cloud": self.cloud,
            "security": self.security,
            "style": self.style,
            "documentation": self.documentation,
            "testing": {"coverage": self.testing_coverage},
            "deployment": self.deployment,
        }

    def to_yaml(self, path: Path) -> None:
        with open(path, "w") as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False, allow_unicode=True)
