"""Task Runner — executa tarefas através do sistema multi-agent."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from core.contracts.agent import AgentContext, AgentRole, AgentTask, TaskStatus

logger = logging.getLogger(__name__)


class TaskRunner:
    """Executa tarefas de forma sequencial ou paralela."""

    def __init__(self, max_concurrent: int = 5) -> None:
        self._max_concurrent = max_concurrent
        self._semaphore = asyncio.Semaphore(max_concurrent)

    async def run_sequential(
        self,
        tasks: list[AgentTask],
        agents: dict[AgentRole, Any],
        context: AgentContext,
    ) -> list[AgentTask]:
        results = []
        for task in tasks:
            agent = agents.get(task.assigned_to)
            if agent is None:
                task.status = TaskStatus.FAILED
                task.error = f"No agent for role {task.assigned_to.value}"
            else:
                task = await agent.execute(task, context)
            results.append(task)
        return results

    async def run_parallel(
        self,
        tasks: list[AgentTask],
        agents: dict[AgentRole, Any],
        context: AgentContext,
    ) -> list[AgentTask]:
        async def _run_one(task: AgentTask) -> AgentTask:
            async with self._semaphore:
                agent = agents.get(task.assigned_to)
                if agent is None:
                    task.status = TaskStatus.FAILED
                    task.error = f"No agent for role {task.assigned_to.value}"
                    return task
                return await agent.execute(task, context)

        return list(await asyncio.gather(*[_run_one(t) for t in tasks]))
