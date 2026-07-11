"""Scheduler — agendamento e execução periódica de tarefas."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Awaitable


class ScheduleType(str, Enum):
    ONCE = "once"
    INTERVAL = "interval"
    CRON_LIKE = "cron_like"


class JobStatus(str, Enum):
    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ScheduledJob:
    id: str
    name: str
    schedule_type: ScheduleType
    callback_name: str
    status: JobStatus = JobStatus.SCHEDULED
    interval_seconds: int = 0
    next_run: datetime | None = None
    last_run: datetime | None = None
    run_count: int = 0
    max_runs: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


JobCallback = Callable[[ScheduledJob], Awaitable[Any]]


class Scheduler:
    """Agendador de tarefas com suporte a execução única e periódica."""

    def __init__(self) -> None:
        self._jobs: dict[str, ScheduledJob] = {}
        self._callbacks: dict[str, JobCallback] = {}
        self._counter = 0
        self._running = False
        self._task: asyncio.Task[None] | None = None

    def register_callback(self, name: str, callback: JobCallback) -> None:
        self._callbacks[name] = callback

    def schedule_once(
        self, name: str, callback_name: str, run_at: datetime, metadata: dict[str, Any] | None = None
    ) -> ScheduledJob:
        self._counter += 1
        job = ScheduledJob(
            id=f"JOB-{self._counter:06d}",
            name=name,
            schedule_type=ScheduleType.ONCE,
            callback_name=callback_name,
            next_run=run_at,
            max_runs=1,
            metadata=metadata or {},
        )
        self._jobs[job.id] = job
        return job

    def schedule_interval(
        self,
        name: str,
        callback_name: str,
        interval_seconds: int,
        max_runs: int = 0,
        metadata: dict[str, Any] | None = None,
    ) -> ScheduledJob:
        self._counter += 1
        job = ScheduledJob(
            id=f"JOB-{self._counter:06d}",
            name=name,
            schedule_type=ScheduleType.INTERVAL,
            callback_name=callback_name,
            interval_seconds=interval_seconds,
            next_run=datetime.now() + timedelta(seconds=interval_seconds),
            max_runs=max_runs,
            metadata=metadata or {},
        )
        self._jobs[job.id] = job
        return job

    def cancel(self, job_id: str) -> bool:
        job = self._jobs.get(job_id)
        if job and job.status == JobStatus.SCHEDULED:
            job.status = JobStatus.CANCELLED
            return True
        return False

    def get_job(self, job_id: str) -> ScheduledJob | None:
        return self._jobs.get(job_id)

    def list_jobs(self, status: JobStatus | None = None) -> list[ScheduledJob]:
        jobs = list(self._jobs.values())
        if status:
            jobs = [j for j in jobs if j.status == status]
        return sorted(jobs, key=lambda j: j.next_run or datetime.max)

    def pending_count(self) -> int:
        return sum(1 for j in self._jobs.values() if j.status == JobStatus.SCHEDULED)

    async def tick(self) -> list[ScheduledJob]:
        now = datetime.now()
        executed: list[ScheduledJob] = []

        for job in list(self._jobs.values()):
            if job.status != JobStatus.SCHEDULED:
                continue
            if job.next_run and job.next_run <= now:
                await self._execute_job(job)
                executed.append(job)

        return executed

    async def start(self, poll_interval: float = 1.0) -> None:
        self._running = True
        self._task = asyncio.create_task(self._loop(poll_interval))

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def _loop(self, poll_interval: float) -> None:
        while self._running:
            await self.tick()
            await asyncio.sleep(poll_interval)

    async def _execute_job(self, job: ScheduledJob) -> None:
        callback = self._callbacks.get(job.callback_name)
        if not callback:
            job.status = JobStatus.FAILED
            return

        job.status = JobStatus.RUNNING
        try:
            await callback(job)
            job.run_count += 1
            job.last_run = datetime.now()

            if job.schedule_type == ScheduleType.ONCE:
                job.status = JobStatus.COMPLETED
            elif job.max_runs and job.run_count >= job.max_runs:
                job.status = JobStatus.COMPLETED
            else:
                job.next_run = datetime.now() + timedelta(seconds=job.interval_seconds)
                job.status = JobStatus.SCHEDULED
        except Exception:
            job.status = JobStatus.FAILED
