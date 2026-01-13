from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from typing import Any

from audit_log import AuditLogStore
from orchestrator import TaskPlanner, TaskStateMachine, TaskStatus
from workers import tasks


class InMemoryRedis:
    def __init__(self) -> None:
        self.store: dict[str, str] = {}

    def get(self, key: str) -> str | None:
        return self.store.get(key)

    def set(self, key: str, value: str, nx: bool = False, ex: int | None = None) -> bool:
        if nx and key in self.store:
            return False
        self.store[key] = value
        return True

    def delete(self, key: str) -> int:
        return 1 if self.store.pop(key, None) is not None else 0


def test_audit_log_append_only() -> None:
    connection = sqlite3.connect(":memory:")
    fixed_time = datetime(2024, 2, 1, tzinfo=timezone.utc)
    store = AuditLogStore(
        lambda: connection,
        clock=lambda: fixed_time,
        close_connection=False,
    )

    store.append(
        "orchestrator.plan_tasks",
        {"intent_id": "intent-1"},
        {"tasks": []},
    )
    first_rows = connection.execute(
        "SELECT id, trigger_source, input_json, output_result, created_at FROM audit_log ORDER BY id"
    ).fetchall()

    store.append(
        "worker.company_search",
        {"intent_id": "intent-1"},
        {"status": "success"},
    )
    second_rows = connection.execute(
        "SELECT id, trigger_source, input_json, output_result, created_at FROM audit_log ORDER BY id"
    ).fetchall()

    assert len(first_rows) == 1
    assert len(second_rows) == 2
    assert second_rows[0] == first_rows[0]
    assert json.loads(second_rows[0][2]) == {"intent_id": "intent-1"}


def test_orchestrator_and_worker_actions_log_entries(monkeypatch: Any) -> None:
    connection = sqlite3.connect(":memory:")
    store = AuditLogStore(lambda: connection, close_connection=False)

    planner = TaskPlanner(audit_log_store=store)
    tasks_list = planner.plan_tasks("intent-9", ["company_search"], entity_id="entity-1")
    machine = TaskStateMachine(audit_log_store=store)
    machine.transition(tasks_list[0], TaskStatus.running)

    client = InMemoryRedis()
    monkeypatch.setattr(tasks, "get_redis_client", lambda: client)
    monkeypatch.setattr(tasks, "AUDIT_LOG_STORE", store)
    monkeypatch.setattr(tasks, "_company_search", lambda payload: {"companies": []})

    tasks.company_search("intent-9", "entity-1", payload={})

    rows = connection.execute(
        "SELECT trigger_source FROM audit_log ORDER BY id"
    ).fetchall()
    sources = {row[0] for row in rows}

    assert "orchestrator.plan_tasks" in sources
    assert "orchestrator.transition" in sources
    assert "worker.company_search" in sources
