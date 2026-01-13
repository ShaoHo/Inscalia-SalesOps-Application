from __future__ import annotations

from dataclasses import replace
from typing import Iterable

from orchestrator.models import Task, TaskStatus

_ALLOWED_TRANSITIONS: set[tuple[TaskStatus, TaskStatus]] = {
    (TaskStatus.queued, TaskStatus.running),
    (TaskStatus.running, TaskStatus.success),
    (TaskStatus.running, TaskStatus.failed),
    (TaskStatus.failed, TaskStatus.retrying),
    (TaskStatus.retrying, TaskStatus.queued),
    (TaskStatus.failed, TaskStatus.deadletter),
}


class TaskStateMachine:
    def __init__(self, allowed_transitions: Iterable[tuple[TaskStatus, TaskStatus]] | None = None) -> None:
        self._allowed_transitions = set(allowed_transitions or _ALLOWED_TRANSITIONS)

    def can_transition(self, current: TaskStatus, target: TaskStatus) -> bool:
        return (current, target) in self._allowed_transitions

    def transition(self, task: Task, target: TaskStatus) -> Task:
        if not self.can_transition(task.status, target):
            raise ValueError(f"Invalid transition from {task.status.value} to {target.value}")
        return replace(task, status=target)

    def record_failure(self, task: Task) -> Task:
        return self.transition(task, TaskStatus.failed)

    def schedule_retry(self, task: Task, *, max_retries: int) -> Task:
        if task.status != TaskStatus.failed:
            raise ValueError("Task must be in failed state to schedule retry.")
        next_status = (
            TaskStatus.retrying if task.retry_count < max_retries else TaskStatus.deadletter
        )
        next_task = replace(task, retry_count=task.retry_count + 1)
        return self.transition(next_task, next_status)

    def requeue(self, task: Task) -> Task:
        return self.transition(task, TaskStatus.queued)
