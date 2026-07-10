"""Validator — validação de artefatos, código e decisões de engenharia."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Severity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass(frozen=True)
class ValidationIssue:
    rule: str
    message: str
    severity: Severity
    location: str | None = None
    suggestion: str | None = None


@dataclass
class ValidationResult:
    valid: bool
    issues: list[ValidationIssue] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def errors(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.severity == Severity.ERROR]

    @property
    def warnings(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.severity == Severity.WARNING]


class ValidationRule:
    """Regra de validação individual."""

    def __init__(self, name: str, check: Any, severity: Severity = Severity.ERROR) -> None:
        self.name = name
        self._check = check
        self.severity = severity

    def validate(self, artifact: dict[str, Any]) -> ValidationIssue | None:
        result = self._check(artifact)
        if result is not None:
            return ValidationIssue(
                rule=self.name,
                message=result,
                severity=self.severity,
            )
        return None


class Validator:
    """Motor de validação com regras configuráveis."""

    def __init__(self) -> None:
        self._rules: list[ValidationRule] = []
        self._register_default_rules()

    def add_rule(self, rule: ValidationRule) -> None:
        self._rules.append(rule)

    def validate(self, artifact: dict[str, Any]) -> ValidationResult:
        issues: list[ValidationIssue] = []
        for rule in self._rules:
            issue = rule.validate(artifact)
            if issue is not None:
                issues.append(issue)

        has_errors = any(i.severity == Severity.ERROR for i in issues)
        return ValidationResult(valid=not has_errors, issues=issues)

    def validate_code(self, code: str, language: str = "python") -> ValidationResult:
        issues: list[ValidationIssue] = []

        if not code.strip():
            issues.append(ValidationIssue(
                rule="non_empty",
                message="Code must not be empty",
                severity=Severity.ERROR,
            ))

        dangerous_patterns = {
            "python": ["eval(", "exec(", "__import__('os')", "subprocess.call("],
            "javascript": ["eval(", "innerHTML", "document.write("],
        }
        for pattern in dangerous_patterns.get(language, []):
            if pattern in code:
                issues.append(ValidationIssue(
                    rule="security_pattern",
                    message=f"Potentially dangerous pattern detected: {pattern}",
                    severity=Severity.WARNING,
                    suggestion=f"Review usage of '{pattern}' for security implications",
                ))

        has_errors = any(i.severity == Severity.ERROR for i in issues)
        return ValidationResult(valid=not has_errors, issues=issues)

    def validate_architecture(self, architecture: dict[str, Any]) -> ValidationResult:
        issues: list[ValidationIssue] = []

        if not architecture.get("components"):
            issues.append(ValidationIssue(
                rule="has_components",
                message="Architecture must define components",
                severity=Severity.ERROR,
            ))

        if not architecture.get("patterns"):
            issues.append(ValidationIssue(
                rule="has_patterns",
                message="Architecture should specify design patterns",
                severity=Severity.WARNING,
            ))

        if not architecture.get("security"):
            issues.append(ValidationIssue(
                rule="has_security",
                message="Architecture should include security considerations",
                severity=Severity.WARNING,
            ))

        has_errors = any(i.severity == Severity.ERROR for i in issues)
        return ValidationResult(valid=not has_errors, issues=issues)

    def _register_default_rules(self) -> None:
        self.add_rule(ValidationRule(
            "has_id",
            lambda a: "Artifact must have an 'id'" if not a.get("id") else None,
        ))
        self.add_rule(ValidationRule(
            "has_type",
            lambda a: "Artifact must have a 'type'" if not a.get("type") else None,
        ))
        self.add_rule(ValidationRule(
            "has_version",
            lambda a: "Artifact should have a 'version'" if not a.get("version") else None,
            severity=Severity.WARNING,
        ))
