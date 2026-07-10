"""Review Engine — motor de revisão automatizada de artefatos."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ReviewCategory(str, Enum):
    CORRECTNESS = "correctness"
    SECURITY = "security"
    PERFORMANCE = "performance"
    MAINTAINABILITY = "maintainability"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    ARCHITECTURE = "architecture"


class ReviewSeverity(str, Enum):
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"
    SUGGESTION = "suggestion"


@dataclass(frozen=True)
class ReviewFinding:
    category: ReviewCategory
    severity: ReviewSeverity
    title: str
    description: str
    location: str | None = None
    suggestion: str | None = None
    evidence_level: str = "E1"


@dataclass
class ReviewReport:
    artifact_id: str
    artifact_type: str
    findings: list[ReviewFinding] = field(default_factory=list)
    score: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def critical_findings(self) -> list[ReviewFinding]:
        return [f for f in self.findings if f.severity == ReviewSeverity.CRITICAL]

    @property
    def passed(self) -> bool:
        return len(self.critical_findings) == 0

    @property
    def findings_by_category(self) -> dict[str, list[ReviewFinding]]:
        result: dict[str, list[ReviewFinding]] = {}
        for finding in self.findings:
            result.setdefault(finding.category.value, []).append(finding)
        return result


class ReviewChecklist:
    """Checklist de revisão configurável por tipo de artefato."""

    def __init__(self, name: str) -> None:
        self.name = name
        self._checks: list[dict[str, Any]] = []

    def add_check(
        self,
        category: ReviewCategory,
        description: str,
        check_fn: Any,
        severity: ReviewSeverity = ReviewSeverity.MAJOR,
    ) -> None:
        self._checks.append({
            "category": category,
            "description": description,
            "check_fn": check_fn,
            "severity": severity,
        })

    def run(self, artifact: dict[str, Any]) -> list[ReviewFinding]:
        findings: list[ReviewFinding] = []
        for check in self._checks:
            result = check["check_fn"](artifact)
            if result:
                findings.append(ReviewFinding(
                    category=check["category"],
                    severity=check["severity"],
                    title=check["description"],
                    description=result,
                ))
        return findings


class ReviewEngine:
    """Motor de revisão que aplica checklists e gera relatórios."""

    def __init__(self) -> None:
        self._checklists: dict[str, ReviewChecklist] = {}
        self._register_defaults()

    def register_checklist(self, artifact_type: str, checklist: ReviewChecklist) -> None:
        self._checklists[artifact_type] = checklist

    def review(self, artifact: dict[str, Any], artifact_type: str) -> ReviewReport:
        findings: list[ReviewFinding] = []

        checklist = self._checklists.get(artifact_type)
        if checklist:
            findings.extend(checklist.run(artifact))

        score = self._calculate_score(findings)

        return ReviewReport(
            artifact_id=artifact.get("id", "unknown"),
            artifact_type=artifact_type,
            findings=findings,
            score=score,
        )

    def _calculate_score(self, findings: list[ReviewFinding]) -> float:
        if not findings:
            return 10.0
        penalties = {
            ReviewSeverity.CRITICAL: 3.0,
            ReviewSeverity.MAJOR: 1.5,
            ReviewSeverity.MINOR: 0.5,
            ReviewSeverity.SUGGESTION: 0.1,
        }
        total_penalty = sum(penalties.get(f.severity, 0) for f in findings)
        return max(0.0, 10.0 - total_penalty)

    def _register_defaults(self) -> None:
        code_checklist = ReviewChecklist("code")
        code_checklist.add_check(
            ReviewCategory.CORRECTNESS,
            "Code must not be empty",
            lambda a: "Empty code artifact" if not a.get("content") else None,
            ReviewSeverity.CRITICAL,
        )
        code_checklist.add_check(
            ReviewCategory.DOCUMENTATION,
            "Code should have docstrings",
            lambda a: "Missing docstrings" if a.get("content") and "def " in a.get("content", "") and '"""' not in a.get("content", "") else None,
            ReviewSeverity.MINOR,
        )
        code_checklist.add_check(
            ReviewCategory.TESTING,
            "Code should have associated tests",
            lambda a: "No tests referenced" if not a.get("tests") else None,
            ReviewSeverity.MAJOR,
        )
        self.register_checklist("code", code_checklist)

        arch_checklist = ReviewChecklist("architecture")
        arch_checklist.add_check(
            ReviewCategory.ARCHITECTURE,
            "Architecture must define components",
            lambda a: "No components defined" if not a.get("components") else None,
            ReviewSeverity.CRITICAL,
        )
        arch_checklist.add_check(
            ReviewCategory.SECURITY,
            "Architecture should address security",
            lambda a: "No security considerations" if not a.get("security") else None,
            ReviewSeverity.MAJOR,
        )
        self.register_checklist("architecture", arch_checklist)
