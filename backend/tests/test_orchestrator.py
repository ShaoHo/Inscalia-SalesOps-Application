import sqlite3
from datetime import datetime, timezone

import pytest

from audit_log import AuditLogStore
from orchestrator import Task, TaskPlanner, TaskStateMachine, TaskStatus
from orchestrator.deadletter_store import DeadLetterStore


def test_task_planning_is_deterministic() -> None:
    fixed_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
    id_generator = lambda task_type: f"id-{task_type}"  # noqa: E731
    connection = sqlite3.connect(":memory:")
    audit_log_store = AuditLogStore(lambda: connection, close_connection=False)
    planner = TaskPlanner(
        id_generator=id_generator,
        clock=lambda: fixed_time,
        audit_log_store=audit_log_store,
    )

    task_types = ["search_companies", "find_contacts"]
    payloads = {"search_companies": {"filters": {"region": "APAC"}}}

    first_plan = planner.plan_tasks(
        "intent-1",
        task_types,
        entity_id="entity-9",
        payloads=payloads,
    )
    second_plan = planner.plan_tasks(
        "intent-1",
        task_types,
        entity_id="entity-9",
        payloads=payloads,
    )

    assert [task.to_dict() for task in first_plan] == [
        task.to_dict() for task in second_plan
    ]


def test_state_machine_transitions_follow_prd() -> None:
    task = Task(
        task_id="task-1",
        intent_id="intent-1",
        task_type="search_companies",
        status=TaskStatus.queued,
        retry_count=0,
        idempotency_key="intent-1:search_companies:none",
        payload={},
        created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
    )
    connection = sqlite3.connect(":memory:")
    audit_log_store = AuditLogStore(lambda: connection, close_connection=False)
    machine = TaskStateMachine(audit_log_store=audit_log_store)

    running = machine.transition(task, TaskStatus.running)
    failed = machine.record_failure(running)
    retrying = machine.schedule_retry(failed, max_retries=2)
    requeued = machine.requeue(retrying)

    assert running.status == TaskStatus.running
    assert failed.status == TaskStatus.failed
    assert retrying.status == TaskStatus.retrying
    assert retrying.retry_count == 1
    assert requeued.status == TaskStatus.queued

    with pytest.raises(ValueError):
        machine.transition(task, TaskStatus.success)


def test_failure_can_deadletter() -> None:
    task = Task(
        task_id="task-2",
        intent_id="intent-1",
        task_type="search_companies",
        status=TaskStatus.failed,
        retry_count=1,
        idempotency_key="intent-1:search_companies:none",
        payload={},
        created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
    )
    connection = sqlite3.connect(":memory:")
    audit_log_store = AuditLogStore(lambda: connection, close_connection=False)
    deadletter_store = DeadLetterStore(lambda: connection, close_connection=False)
    machine = TaskStateMachine(
        audit_log_store=audit_log_store,
        deadletter_store=deadletter_store,
    )

    deadlettered = machine.schedule_retry(task, max_retries=1)

    assert deadlettered.status == TaskStatus.deadletter
    assert deadlettered.retry_count == 2


def test_deadletter_store_records_retry_exhaustion() -> None:
    task = Task(
        task_id="task-3",
        intent_id="intent-2",
        task_type="collect_news",
        status=TaskStatus.failed,
        retry_count=2,
        idempotency_key="intent-2:collect_news:none",
        payload={"topic": "saas"},
        created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
    )
    connection = sqlite3.connect(":memory:")
    audit_log_store = AuditLogStore(lambda: connection, close_connection=False)
    deadletter_store = DeadLetterStore(lambda: connection, close_connection=False)
    machine = TaskStateMachine(
        audit_log_store=audit_log_store,
        deadletter_store=deadletter_store,
    )

    deadlettered = machine.schedule_retry(task, max_retries=2)

    assert deadlettered.status == TaskStatus.deadletter
    items = deadletter_store.list()
    assert len(items) == 1
    assert items[0].task.task_id == "task-3"
    assert items[0].reason == "retry_limit_exhausted"
