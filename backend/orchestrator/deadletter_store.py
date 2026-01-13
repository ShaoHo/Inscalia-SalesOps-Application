from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable

from audit_log import default_connection_factory
from orchestrator.models import Task

Clock = Callable[[], datetime]
ConnectionFactory = Callable[[], Any]


def default_clock() -> datetime:
    return datetime.now(timezone.utc)


def _is_sqlite_connection(connection: Any) -> bool:
    return isinstance(connection, sqlite3.Connection)


def initialize_deadletter_table(connection: Any) -> None:
    if _is_sqlite_connection(connection):
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS deadletter_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_json TEXT NOT NULL,
                reason TEXT NOT NULL,
                deadlettered_at TEXT NOT NULL
            )
            """
        )
    else:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS deadletter_tasks (
                id BIGSERIAL PRIMARY KEY,
                task_json JSONB NOT NULL,
                reason TEXT NOT NULL,
                deadlettered_at TIMESTAMPTZ NOT NULL
            )
            """
        )


@dataclass(frozen=True)
class DeadLetterItem:
    id: int
    task: Task
    reason: str
    deadlettered_at: datetime


class DeadLetterStore:
    def __init__(
        self,
        connection_factory: ConnectionFactory,
        *,
        clock: Clock | None = None,
        close_connection: bool = True,
    ) -> None:
        self._connection_factory = connection_factory
        self._clock = clock or default_clock
        self._close_connection = close_connection

    def append(self, task: Task, reason: str) -> DeadLetterItem:
        deadlettered_at = self._clock()
        task_json = json.dumps(task.to_dict(), sort_keys=True)
        connection = self._connection_factory()
        try:
            initialize_deadletter_table(connection)
            if _is_sqlite_connection(connection):
                cursor = connection.execute(
                    """
                    INSERT INTO deadletter_tasks (task_json, reason, deadlettered_at)
                    VALUES (?, ?, ?)
                    """,
                    (task_json, reason, deadlettered_at.isoformat()),
                )
                item_id = int(cursor.lastrowid)
            else:
                cursor = connection.execute(
                    """
                    INSERT INTO deadletter_tasks (task_json, reason, deadlettered_at)
                    VALUES (%s, %s, %s)
                    RETURNING id
                    """,
                    (task_json, reason, deadlettered_at),
                )
                row = cursor.fetchone()
                item_id = int(row[0]) if row else 0
            connection.commit()
        finally:
            if self._close_connection:
                connection.close()
        return DeadLetterItem(
            id=item_id,
            task=task,
            reason=reason,
            deadlettered_at=deadlettered_at,
        )

    def list(self, *, limit: int = 50) -> list[DeadLetterItem]:
        connection = self._connection_factory()
        try:
            initialize_deadletter_table(connection)
            if _is_sqlite_connection(connection):
                rows = connection.execute(
                    """
                    SELECT id, task_json, reason, deadlettered_at
                    FROM deadletter_tasks
                    ORDER BY id DESC
                    LIMIT ?
                    """,
                    (limit,),
                ).fetchall()
            else:
                rows = connection.execute(
                    """
                    SELECT id, task_json, reason, deadlettered_at
                    FROM deadletter_tasks
                    ORDER BY id DESC
                    LIMIT %s
                    """,
                    (limit,),
                ).fetchall()
        finally:
            if self._close_connection:
                connection.close()
        items: list[DeadLetterItem] = []
        for item_id, task_payload, reason, deadlettered_at in rows:
            if isinstance(task_payload, str):
                task_data = json.loads(task_payload)
            else:
                task_data = task_payload
            if isinstance(deadlettered_at, str):
                deadlettered_dt = datetime.fromisoformat(deadlettered_at)
            else:
                deadlettered_dt = deadlettered_at
            items.append(
                DeadLetterItem(
                    id=int(item_id),
                    task=Task.from_dict(task_data),
                    reason=reason,
                    deadlettered_at=deadlettered_dt,
                )
            )
        return items


_DEFAULT_STORE: DeadLetterStore | None = None


def get_default_deadletter_store() -> DeadLetterStore:
    global _DEFAULT_STORE
    if _DEFAULT_STORE is None:
        _DEFAULT_STORE = DeadLetterStore(default_connection_factory())
    return _DEFAULT_STORE
