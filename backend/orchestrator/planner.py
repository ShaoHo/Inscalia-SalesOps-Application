from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from orchestrator.models import Task, TaskStatus

IdGenerator = Callable[[str], str]
Clock = Callable[[], datetime]


def default_id_generator(_: str) -> str:
    return str(uuid4())


def default_clock() -> datetime:
    return datetime.now(timezone.utc)


def build_idempotency_key(intent_id: str, task_type: str, entity_id: str | None) -> str:
    entity_token = entity_id or "none"
    return f"{intent_id}:{task_type}:{entity_token}"


class TaskPlanner:
    def __init__(
        self,
        id_generator: IdGenerator | None = None,
        clock: Clock | None = None,
    ) -> None:
        self._id_generator = id_generator or default_id_generator
        self._clock = clock or default_clock

    def plan_tasks(
        self,
        intent_id: str,
        task_types: Iterable[str],
        *,
        entity_id: str | None = None,
        payloads: Mapping[str, dict[str, Any]] | None = None,
    ) -> list[Task]:
        payload_map = payloads or {}
        created_at = self._clock()
        tasks: list[Task] = []
        for task_type in task_types:
            payload = dict(payload_map.get(task_type, {}))
            task = Task(
                task_id=self._id_generator(task_type),
                intent_id=intent_id,
                task_type=task_type,
                status=TaskStatus.queued,
                retry_count=0,
                idempotency_key=build_idempotency_key(
                    intent_id=intent_id,
                    task_type=task_type,
                    entity_id=entity_id,
                ),
                payload=payload,
                created_at=created_at,
            )
            tasks.append(task)
        return tasks
