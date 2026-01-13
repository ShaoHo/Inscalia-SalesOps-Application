from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from apps.api.services.audit_log import append_audit_log
from apps.api.services.intent_validator import IntentAction, SalesOpsIntent
from orchestrator.models import Task
from orchestrator.planner import TaskPlanner

ACTION_TO_CELERY_TASK = {
    IntentAction.search_companies: "workers.tasks.company_search",
    IntentAction.find_contacts: "workers.tasks.contact_finder",
    IntentAction.collect_news: "workers.tasks.news_collector",
    IntentAction.generate_emails: "workers.tasks.email_generator",
    IntentAction.schedule_emails: "workers.tasks.scheduler",
    IntentAction.update_pipeline: "workers.tasks.pipeline_bant",
}


def _build_payloads(intent: SalesOpsIntent) -> dict[str, dict[str, Any]]:
    filters_payload = intent.filters.model_dump(exclude_none=True)
    base_payload = {
        "raw_text": intent.raw_text,
        "language": intent.language,
        "filters": filters_payload,
    }
    payloads: dict[str, dict[str, Any]] = {}
    for action in intent.actions:
        payloads[action.value] = dict(base_payload)
    return payloads


def plan_tasks_for_intent(
    intent: SalesOpsIntent,
    *,
    planner: TaskPlanner | None = None,
) -> list[Task]:
    task_planner = planner or TaskPlanner()
    task_types: Iterable[str] = [action.value for action in intent.actions]
    tasks = task_planner.plan_tasks(
        intent.intent_id,
        task_types,
        payloads=_build_payloads(intent),
    )
    append_audit_log(
        "orchestrator.plan_intent",
        {"intent_id": intent.intent_id, "actions": [action.value for action in intent.actions]},
        {"tasks": [task.to_dict() for task in tasks]},
    )
    return tasks


def map_tasks_to_celery(tasks: Iterable[Task]) -> list[dict[str, str]]:
    celery_tasks: list[dict[str, str]] = []
    for task in tasks:
        action = IntentAction(task.task_type)
        celery_tasks.append(
            {
                "task_id": task.task_id,
                "task_type": task.task_type,
                "celery_task": ACTION_TO_CELERY_TASK[action],
            }
        )
    return celery_tasks
