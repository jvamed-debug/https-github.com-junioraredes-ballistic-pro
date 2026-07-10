"""Engineering Engine — motor principal de engenharia.

Pipeline:
Entrada → Classificação → Contextualização → Recuperação →
Planejamento → Arquitetura → Implementação → Validação →
Documentação → Knowledge Capture → Entrega
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from core.contracts.agent import AgentContext, AgentTask, TaskStatus


class PipelineStage(str, Enum):
    INPUT = "input"
    CLASSIFICATION = "classification"
    CONTEXTUALIZATION = "contextualization"
    RETRIEVAL = "retrieval"
    PLANNING = "planning"
    ARCHITECTURE = "architecture"
    IMPLEMENTATION = "implementation"
    VALIDATION = "validation"
    DOCUMENTATION = "documentation"
    KNOWLEDGE_CAPTURE = "knowledge_capture"
    DELIVERY = "delivery"


@dataclass
class PipelineExecution:
    id: str
    stages_completed: list[PipelineStage] = field(default_factory=list)
    current_stage: PipelineStage = PipelineStage.INPUT
    artifacts: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)


class EngineeringEngine:
    """Motor de engenharia que coordena o pipeline de processamento."""

    def __init__(self) -> None:
        self._executions: dict[str, PipelineExecution] = {}

    def create_execution(self) -> PipelineExecution:
        execution = PipelineExecution(id=str(uuid.uuid4()))
        self._executions[execution.id] = execution
        return execution

    def get_execution(self, execution_id: str) -> PipelineExecution | None:
        return self._executions.get(execution_id)

    async def classify_input(self, raw_input: str, context: AgentContext) -> dict[str, Any]:
        return {
            "input": raw_input,
            "type": self._detect_input_type(raw_input),
            "domains": self._detect_domains(raw_input),
            "complexity": self._estimate_complexity(raw_input),
        }

    async def plan_tasks(
        self, classification: dict[str, Any], context: AgentContext
    ) -> list[AgentTask]:
        tasks: list[AgentTask] = []
        input_type = classification.get("type", "general")

        from core.contracts.agent import AgentRole

        if input_type == "architecture":
            tasks.append(self._create_task("Design architecture", AgentRole.ARCHITECT, classification))
            tasks.append(self._create_task("Security review", AgentRole.SECURITY, classification))
            tasks.append(self._create_task("Generate documentation", AgentRole.DOCUMENTATION, classification))
        elif input_type == "implementation":
            tasks.append(self._create_task("Plan implementation", AgentRole.PLANNER, classification))
            tasks.append(self._create_task("Generate code", AgentRole.DEVELOPER, classification))
            tasks.append(self._create_task("Review code", AgentRole.REVIEWER, classification))
        elif input_type == "review":
            tasks.append(self._create_task("Code review", AgentRole.REVIEWER, classification))
            tasks.append(self._create_task("Security analysis", AgentRole.SECURITY, classification))
        else:
            tasks.append(self._create_task("Analyze request", AgentRole.PLANNER, classification))

        return tasks

    def _create_task(
        self, description: str, role: "AgentRole", context: dict[str, Any]
    ) -> AgentTask:
        return AgentTask(
            id=str(uuid.uuid4()),
            description=description,
            assigned_to=role,
            context=context,
        )

    def _detect_input_type(self, raw_input: str) -> str:
        lower = raw_input.lower()
        if any(w in lower for w in ["arquitetura", "architecture", "design", "projetar"]):
            return "architecture"
        if any(w in lower for w in ["implementar", "código", "code", "develop"]):
            return "implementation"
        if any(w in lower for w in ["revisar", "review", "analisar"]):
            return "review"
        return "general"

    def _detect_domains(self, raw_input: str) -> list[str]:
        domain_keywords = {
            "backend": ["api", "backend", "server", "fastapi", "django"],
            "frontend": ["frontend", "react", "nextjs", "ui", "interface"],
            "database": ["banco", "database", "postgres", "sql", "mongodb"],
            "infrastructure": ["docker", "kubernetes", "infra", "deploy", "aws"],
            "security": ["segurança", "security", "auth", "oauth", "encryption"],
        }
        lower = raw_input.lower()
        return [
            domain
            for domain, keywords in domain_keywords.items()
            if any(kw in lower for kw in keywords)
        ]

    def _estimate_complexity(self, raw_input: str) -> str:
        word_count = len(raw_input.split())
        if word_count < 20:
            return "low"
        if word_count < 100:
            return "medium"
        return "high"
