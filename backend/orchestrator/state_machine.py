from __future__ import annotations

from dataclasses import replace
from typing import Iterable

from audit_log import AuditLogStore, get_default_audit_log_store
from orchestrator.deadletter_store import DeadLetterStore, get_default_deadletter_store
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
    def __init__(
        self,
        allowed_transitions: Iterable[tuple[TaskStatus, TaskStatus]] | None = None,
        audit_log_store: AuditLogStore | None = None,
        deadletter_store: DeadLetterStore | None = None,
    ) -> None:
        self._allowed_transitions = set(allowed_transitions or _ALLOWED_TRANSITIONS)
        self._audit_log_store = audit_log_store or get_default_audit_log_store()
        self._deadletter_store = deadletter_store or get_default_deadletter_store()

    def can_transition(self, current: TaskStatus, target: TaskStatus) -> bool:
        return (current, target) in self._allowed_transitions

    def transition(self, task: Task, target: TaskStatus) -> Task:
        if not self.can_transition(task.status, target):
            raise ValueError(f"Invalid transition from {task.status.value} to {target.value}")
        next_task = replace(task, status=target)
        self._audit_log_store.append(
            "orchestrator.transition",
            {"task": task.to_dict(), "target_status": target.value},
            {"task": next_task.to_dict()},
        )
        return next_task

    def record_failure(self, task: Task) -> Task:
        return self.transition(task, TaskStatus.failed)

    def schedule_retry(self, task: Task, *, max_retries: int) -> Task:
        if task.status != TaskStatus.failed:
            raise ValueError("Task must be in failed state to schedule retry.")
        next_task = replace(task, retry_count=task.retry_count + 1)
        if task.retry_count < max_retries:
            return self.transition(next_task, TaskStatus.retrying)
        transitioned = self.transition(next_task, TaskStatus.deadletter)
        self._deadletter_store.append(transitioned, "retry_limit_exhausted")
        return transitioned

    def requeue(self, task: Task) -> Task:
        return self.transition(task, TaskStatus.queued)
