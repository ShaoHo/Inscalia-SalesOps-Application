from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any, Callable
from uuid import uuid4

import redis

from app.config import settings
from audit_log import AuditLogStore, get_default_audit_log_store
from workers.celery_app import celery_app


RedisClient = redis.Redis
AUDIT_LOG_STORE: AuditLogStore | None = None


def get_redis_client() -> RedisClient:
    return redis.Redis.from_url(settings.redis_url, decode_responses=True)


def get_audit_log_store() -> AuditLogStore:
    return AUDIT_LOG_STORE or get_default_audit_log_store()


def build_idempotency_key(
    intent_id: str,
    task_type: str,
    entity_id: str | None,
    version: str | None = None,
) -> str:
    parts = [intent_id, task_type, entity_id or "none"]
    if version:
        parts.append(version)
    return ":".join(parts)


def run_idempotent_task(
    task_type: str,
    intent_id: str,
    entity_id: str | None,
    payload: dict[str, Any],
    version: str | None,
    handler: Callable[[dict[str, Any]], dict[str, Any]],
) -> dict[str, Any]:
    client = get_redis_client()
    idempotency_key = build_idempotency_key(intent_id, task_type, entity_id, version)
    lock_key = f"lock:{idempotency_key}"
    result_key = f"result:{idempotency_key}"
    audit_log_store = get_audit_log_store()

    existing = client.get(result_key)
    if existing:
        result = json.loads(existing)
        audit_log_store.append(
            f"worker.{task_type}",
            {
                "intent_id": intent_id,
                "entity_id": entity_id,
                "payload": payload,
                "version": version,
                "cached": True,
            },
            result,
        )
        return result

    lock_token = str(uuid4())
    acquired = client.set(lock_key, lock_token, nx=True, ex=300)
    if not acquired:
        existing = client.get(result_key)
        if existing:
            result = json.loads(existing)
            audit_log_store.append(
                f"worker.{task_type}",
                {
                    "intent_id": intent_id,
                    "entity_id": entity_id,
                    "payload": payload,
                    "version": version,
                    "cached": True,
                },
                result,
            )
            return result
        result = {
            "status": "locked",
            "task_type": task_type,
            "idempotency_key": idempotency_key,
        }
        audit_log_store.append(
            f"worker.{task_type}",
            {
                "intent_id": intent_id,
                "entity_id": entity_id,
                "payload": payload,
                "version": version,
                "locked": True,
            },
            result,
        )
        return result

    try:
        result = handler(payload)
        response = {
            "status": "success",
            "task_type": task_type,
            "idempotency_key": idempotency_key,
            "result": result,
        }
        client.set(result_key, json.dumps(response), ex=86400)
        audit_log_store.append(
            f"worker.{task_type}",
            {
                "intent_id": intent_id,
                "entity_id": entity_id,
                "payload": payload,
                "version": version,
            },
            response,
        )
        return response
    except Exception as exc:  # noqa: BLE001
        failure_response = {
            "status": "failed",
            "task_type": task_type,
            "idempotency_key": idempotency_key,
            "error": str(exc),
        }
        audit_log_store.append(
            f"worker.{task_type}",
            {
                "intent_id": intent_id,
                "entity_id": entity_id,
                "payload": payload,
                "version": version,
                "error": str(exc),
            },
            failure_response,
        )
        raise
    finally:
        if client.get(lock_key) == lock_token:
            client.delete(lock_key)


@celery_app.task
def heartbeat() -> str:
    return f"heartbeat:{datetime.utcnow().isoformat()}"


def search_companies_with_playwright(payload: dict[str, Any]) -> list[dict[str, Any]]:
    query = payload.get("query", "target accounts")
    return [{"name": f"{query} Holdings", "source": "playwright"}]


def search_companies_with_selenium(payload: dict[str, Any]) -> list[dict[str, Any]]:
    industry = payload.get("industry", "SaaS")
    return [{"name": f"{industry} Labs", "source": "selenium"}]


def find_contacts_with_mailscout(payload: dict[str, Any]) -> list[dict[str, Any]]:
    domain = payload.get("domain", "example.com")
    return [
        {
            "name": "Taylor Prospect",
            "email": f"taylor@{domain}",
            "source": "mailscout",
        }
    ]


def find_contacts_with_theharvester(payload: dict[str, Any]) -> list[dict[str, Any]]:
    domain = payload.get("domain", "example.com")
    return [
        {
            "name": "Jordan Lead",
            "email": f"jordan@{domain}",
            "source": "theharvester",
        }
    ]


def collect_news_with_newsapi(payload: dict[str, Any]) -> list[dict[str, Any]]:
    topic = payload.get("topic", "sales")
    return [
        {
            "title": f"{topic.title()} market update",
            "url": "https://news.example.com/story",
            "source": "newsapi",
        }
    ]


def parse_articles_with_newspaper(articles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "title": article["title"],
            "summary": f"Summary for {article['title']}",
            "source": "newspaper3k",
        }
        for article in articles
    ]


def generate_email_with_template(payload: dict[str, Any]) -> dict[str, Any]:
    recipient = payload.get("recipient", "Prospect")
    company = payload.get("company", "your company")
    return {
        "subject": f"Idea for {recipient}",
        "body": f"Hi {recipient}, I noticed {company} could benefit from SalesOps.",
        "channel": "email",
    }


def _parse_start_at(value: str | datetime | None, *, now: datetime) -> datetime:
    if value is None:
        return now
    if isinstance(value, datetime):
        start_at = value
    else:
        start_at = datetime.fromisoformat(value)
    if start_at.tzinfo is None:
        start_at = start_at.replace(tzinfo=timezone.utc)
    return start_at


def build_schedule_plan(payload: dict[str, Any]) -> dict[str, Any]:
    cadence_days = int(payload.get("cadence_days", 7))
    steps = list(payload.get("steps", []))
    contact_replied = bool(payload.get("contact_replied", False))
    completed_steps = int(payload.get("completed_steps", 0))
    start_at = _parse_start_at(payload.get("start_at"), now=datetime.now(timezone.utc))

    scheduled_steps: list[dict[str, Any]] = []
    for index, step in enumerate(steps, start=1):
        step_payload = dict(step)
        step_payload.setdefault("step_number", index)
        send_at = start_at + timedelta(days=cadence_days * (index - 1))
        if contact_replied and index > completed_steps:
            step_payload["status"] = "paused"
            step_payload["next_send_at"] = None
        else:
            step_payload["status"] = "scheduled"
            step_payload["next_send_at"] = send_at.isoformat()
        scheduled_steps.append(step_payload)

    overall_status = (
        "paused"
        if contact_replied and len(steps) > completed_steps
        else "scheduled"
    )
    return {
        "cadence_days": cadence_days,
        "status": overall_status,
        "steps": scheduled_steps,
    }


def score_pipeline_bant(payload: dict[str, Any]) -> dict[str, Any]:
    bant = payload.get("bant", {"budget": 3, "authority": 3, "need": 3, "timing": 3})
    score = sum(bant.values())
    return {"bant": bant, "score": score, "qualified": score >= 10}


def _company_search(payload: dict[str, Any]) -> dict[str, Any]:
    companies = search_companies_with_playwright(payload)
    companies.extend(search_companies_with_selenium(payload))
    return {"companies": companies}


def _contact_finder(payload: dict[str, Any]) -> dict[str, Any]:
    contacts = find_contacts_with_mailscout(payload)
    contacts.extend(find_contacts_with_theharvester(payload))
    return {"contacts": contacts}


def _news_collector(payload: dict[str, Any]) -> dict[str, Any]:
    articles = collect_news_with_newsapi(payload)
    summaries = parse_articles_with_newspaper(articles)
    return {"articles": articles, "summaries": summaries}


def _email_generator(payload: dict[str, Any]) -> dict[str, Any]:
    return {"email": generate_email_with_template(payload)}


def _scheduler(payload: dict[str, Any]) -> dict[str, Any]:
    return {"schedule": build_schedule_plan(payload)}


def _pipeline_bant(payload: dict[str, Any]) -> dict[str, Any]:
    return {"assessment": score_pipeline_bant(payload)}


@celery_app.task
def company_search(
    intent_id: str,
    entity_id: str | None,
    payload: dict[str, Any] | None = None,
    version: str | None = None,
) -> dict[str, Any]:
    return run_idempotent_task(
        "company_search",
        intent_id,
        entity_id,
        payload or {},
        version,
        _company_search,
    )


@celery_app.task
def contact_finder(
    intent_id: str,
    entity_id: str | None,
    payload: dict[str, Any] | None = None,
    version: str | None = None,
) -> dict[str, Any]:
    return run_idempotent_task(
        "contact_finder",
        intent_id,
        entity_id,
        payload or {},
        version,
        _contact_finder,
    )


@celery_app.task
def news_collector(
    intent_id: str,
    entity_id: str | None,
    payload: dict[str, Any] | None = None,
    version: str | None = None,
) -> dict[str, Any]:
    return run_idempotent_task(
        "news_collector",
        intent_id,
        entity_id,
        payload or {},
        version,
        _news_collector,
    )


@celery_app.task
def email_generator(
    intent_id: str,
    entity_id: str | None,
    payload: dict[str, Any] | None = None,
    version: str | None = None,
) -> dict[str, Any]:
    return run_idempotent_task(
        "email_generator",
        intent_id,
        entity_id,
        payload or {},
        version,
        _email_generator,
    )


@celery_app.task
def scheduler(
    intent_id: str,
    entity_id: str | None,
    payload: dict[str, Any] | None = None,
    version: str | None = None,
) -> dict[str, Any]:
    return run_idempotent_task(
        "scheduler",
        intent_id,
        entity_id,
        payload or {},
        version,
        _scheduler,
    )


@celery_app.task
def pipeline_bant(
    intent_id: str,
    entity_id: str | None,
    payload: dict[str, Any] | None = None,
    version: str | None = None,
) -> dict[str, Any]:
    return run_idempotent_task(
        "pipeline_bant",
        intent_id,
        entity_id,
        payload or {},
        version,
        _pipeline_bant,
    )
