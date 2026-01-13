import sqlite3
from datetime import datetime, timezone

from apps.api.services.intent_validator import SalesOpsIntent
from apps.api.services.orchestrator import map_tasks_to_celery, plan_tasks_for_intent
from audit_log import AuditLogStore
from orchestrator.planner import TaskPlanner


def test_plan_tasks_for_intent_produces_celery_mapping() -> None:
    intent = SalesOpsIntent.model_validate(
        {
            "intent_id": "intent-1",
            "raw_text": "Find SaaS companies in APAC.",
            "language": "en",
            "filters": {"regions": ["APAC"]},
            "actions": ["search_companies", "collect_news"],
        }
    )
    planner = TaskPlanner(
        id_generator=lambda task_type: f"id-{task_type}",
        clock=lambda: datetime(2024, 1, 1, tzinfo=timezone.utc),
        audit_log_store=AuditLogStore(lambda: sqlite3.connect(":memory:")),
    )

    tasks = plan_tasks_for_intent(intent, planner=planner)
    celery_tasks = map_tasks_to_celery(tasks)

    assert [task.task_type for task in tasks] == ["search_companies", "collect_news"]
    assert celery_tasks == [
        {
            "task_id": "id-search_companies",
            "task_type": "search_companies",
            "celery_task": "workers.tasks.company_search",
        },
        {
            "task_id": "id-collect_news",
            "task_type": "collect_news",
            "celery_task": "workers.tasks.news_collector",
        },
    ]
