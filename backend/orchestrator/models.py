from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class TaskStatus(str, Enum):
    queued = "queued"
    running = "running"
    success = "success"
    failed = "failed"
    retrying = "retrying"
    deadletter = "deadletter"


@dataclass(frozen=True)
class Task:
    task_id: str
    intent_id: str
    task_type: str
    status: TaskStatus
    retry_count: int
    idempotency_key: str
    payload: dict[str, Any]
    created_at: datetime

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "intent_id": self.intent_id,
            "task_type": self.task_type,
            "status": self.status.value,
            "retry_count": self.retry_count,
            "idempotency_key": self.idempotency_key,
            "payload": self.payload,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "Task":
        created_at = payload["created_at"]
        if isinstance(created_at, str):
            created_at_dt = datetime.fromisoformat(created_at)
        else:
            created_at_dt = created_at
        if created_at_dt.tzinfo is None:
            created_at_dt = created_at_dt.replace(tzinfo=timezone.utc)
        return cls(
            task_id=payload["task_id"],
            intent_id=payload["intent_id"],
            task_type=payload["task_type"],
            status=TaskStatus(payload["status"]),
            retry_count=payload.get("retry_count", 0),
            idempotency_key=payload["idempotency_key"],
            payload=payload.get("payload", {}),
            created_at=created_at_dt,
        )
