"""Template Engine — motor de templates para geração de artefatos."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Template:
    id: str
    name: str
    category: str
    content: str
    variables: list[str] = field(default_factory=list)
    description: str = ""


class TemplateEngine:
    """Motor de templates para geração de artefatos de engenharia."""

    def __init__(self) -> None:
        self._templates: dict[str, Template] = {}
        self._load_defaults()

    def register(self, template: Template) -> None:
        self._templates[template.id] = template

    def get(self, template_id: str) -> Template | None:
        return self._templates.get(template_id)

    def render(self, template_id: str, variables: dict[str, Any]) -> str:
        template = self._templates.get(template_id)
        if template is None:
            raise KeyError(f"Template '{template_id}' not found")

        content = template.content
        for key, value in variables.items():
            content = content.replace(f"{{{{{key}}}}}", str(value))
        return content

    def by_category(self, category: str) -> list[Template]:
        return [t for t in self._templates.values() if t.category == category]

    def categories(self) -> list[str]:
        return sorted({t.category for t in self._templates.values()})

    @property
    def count(self) -> int:
        return len(self._templates)

    def _load_defaults(self) -> None:
        self.register(Template(
            id="TPL-ADR",
            name="Architecture Decision Record",
            category="documentation",
            variables=["id", "title", "status", "context", "decision", "consequences"],
            content=(
                "# {{id}}: {{title}}\n\n"
                "**Status:** {{status}}\n\n"
                "## Context\n\n{{context}}\n\n"
                "## Decision\n\n{{decision}}\n\n"
                "## Consequences\n\n{{consequences}}\n"
            ),
        ))
        self.register(Template(
            id="TPL-API-ENDPOINT",
            name="API Endpoint",
            category="code",
            variables=["method", "path", "description", "request_body", "response_body"],
            content=(
                "@router.{{method}}(\"{{path}}\")\n"
                "async def handler(request: {{request_body}}) -> {{response_body}}:\n"
                '    """{{description}}"""\n'
                "    ...\n"
            ),
        ))
        self.register(Template(
            id="TPL-SERVICE",
            name="Service Class",
            category="code",
            variables=["name", "description"],
            content=(
                "class {{name}}Service:\n"
                '    """{{description}}"""\n\n'
                "    def __init__(self, repository: {{name}}Repository) -> None:\n"
                "        self._repository = repository\n"
            ),
        ))
        self.register(Template(
            id="TPL-RUNBOOK",
            name="Runbook",
            category="operations",
            variables=["title", "trigger", "steps", "rollback"],
            content=(
                "# Runbook: {{title}}\n\n"
                "## Trigger\n\n{{trigger}}\n\n"
                "## Steps\n\n{{steps}}\n\n"
                "## Rollback\n\n{{rollback}}\n"
            ),
        ))
