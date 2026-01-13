from datetime import datetime, timezone

import pytest

from orchestrator import Task, TaskPlanner, TaskStateMachine, TaskStatus


def test_task_planning_is_deterministic() -> None:
    fixed_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
    id_generator = lambda task_type: f"id-{task_type}"  # noqa: E731
    planner = TaskPlanner(id_generator=id_generator, clock=lambda: fixed_time)

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
    machine = TaskStateMachine()

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
    machine = TaskStateMachine()

    deadlettered = machine.schedule_retry(task, max_retries=1)

    assert deadlettered.status == TaskStatus.deadletter
    assert deadlettered.retry_count == 2
