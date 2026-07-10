"""Base Agent — implementação base compartilhada por todos os agentes."""

from __future__ import annotations

import logging
from typing import Any

from core.contracts.agent import (
    AgentCapability,
    AgentContext,
    AgentInterface,
    AgentRole,
    AgentTask,
    TaskStatus,
)
from core.contracts.llm_provider import (
    LLMConfig,
    LLMMessage,
    LLMProviderInterface,
    LLMResponse,
    LLMRole,
)

logger = logging.getLogger(__name__)


class BaseAgent(AgentInterface):
    """Implementação base com funcionalidade compartilhada."""

    def __init__(self, llm: LLMProviderInterface, config: dict[str, Any] | None = None) -> None:
        self._llm = llm
        self._config = config or {}
        self._llm_config = LLMConfig(
            model=self._config.get("model", "default"),
            temperature=self._config.get("temperature", 0.7),
            max_tokens=self._config.get("max_tokens", 4096),
        )

    async def execute(self, task: AgentTask, context: AgentContext) -> AgentTask:
        task.status = TaskStatus.IN_PROGRESS
        try:
            messages = self._build_messages(task, context)
            response = await self._llm.complete(messages, self._llm_config)
            task.result = self._process_response(response, task)
            task.status = TaskStatus.COMPLETED
        except Exception as e:
            logger.exception("Agent %s failed on task %s", self.role.value, task.id)
            task.error = str(e)
            task.status = TaskStatus.FAILED
        return task

    def _build_messages(self, task: AgentTask, context: AgentContext) -> list[LLMMessage]:
        messages = [
            LLMMessage(role=LLMRole.SYSTEM, content=self._system_prompt(context)),
        ]
        for hist in context.conversation_history:
            messages.append(LLMMessage(
                role=LLMRole(hist.get("role", "user")),
                content=hist.get("content", ""),
            ))
        messages.append(LLMMessage(
            role=LLMRole.USER,
            content=self._task_prompt(task),
        ))
        return messages

    def _system_prompt(self, context: AgentContext) -> str:
        dna = context.project_dna
        return (
            f"You are {self.role.value} agent in the Engineering AI Platform.\n"
            f"Project: {dna.get('project', {}).get('name', 'unknown')}\n"
            f"Language: {dna.get('language', 'python')}\n"
            f"Framework: {dna.get('framework', '')}\n"
            f"Architecture: {dna.get('architecture', 'clean architecture')}\n"
        )

    def _task_prompt(self, task: AgentTask) -> str:
        return f"Task: {task.description}\nContext: {task.context}"

    def _process_response(self, response: LLMResponse, task: AgentTask) -> dict[str, Any]:
        return {
            "output": response.content,
            "model": response.model,
            "provider": response.provider,
            "usage": response.usage,
        }
