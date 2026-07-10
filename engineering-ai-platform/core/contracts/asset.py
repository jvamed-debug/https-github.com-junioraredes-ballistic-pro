"""Engineering Asset Model (EAM) — modelo de ativos de engenharia."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class AssetType(str, Enum):
    ARCHITECTURE = "ARCH"
    API = "API"
    COMPONENT = "COMP"
    ADR = "ADR"
    PLAYBOOK = "PLAY"
    RUNBOOK = "RUN"
    TEST = "TEST"
    PIPELINE = "PIPE"
    POLICY = "POL"
    PROMPT = "PROMPT"
    PATTERN = "PAT"
    DIAGRAM = "DIAG"
    METRIC = "MET"
    DATA_MODEL = "DM"


class AssetStatus(str, Enum):
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class EvidenceLevel(str, Enum):
    E0_HYPOTHESIS = "E0"
    E1_PRACTICAL_EXPERIENCE = "E1"
    E2_OFFICIAL_DOCS = "E2"
    E3_TECHNICAL_STANDARD = "E3"
    E4_REPRODUCIBLE_BENCHMARK = "E4"
    E5_PROJECT_VALIDATED = "E5"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class EngineeringAsset:
    id: str
    asset_type: AssetType
    version: str
    author: str
    created: datetime
    updated: datetime
    status: AssetStatus
    owner: str
    title: str
    description: str
    domain: str
    tags: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    project: str | None = None
    risk: RiskLevel = RiskLevel.LOW
    evidence_level: EvidenceLevel = EvidenceLevel.E0_HYPOTHESIS
    quality_score: float | None = None
    reviewed_by: str | None = None
    approved_by: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def asset_code(self) -> str:
        seq = self.id.split("-")[-1] if "-" in self.id else "000000"
        return f"ENG-{self.asset_type.value}-{seq}"
