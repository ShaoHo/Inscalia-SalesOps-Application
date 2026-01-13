from __future__ import annotations

import sqlite3
from typing import Any

import pytest

from audit_log import AuditLogStore
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

    def keys(self) -> list[str]:
        return list(self.store.keys())


def _attach_redis(monkeypatch: Any, client: InMemoryRedis) -> None:
    monkeypatch.setattr(tasks, "get_redis_client", lambda: client)


@pytest.fixture(autouse=True)
def audit_log_store(monkeypatch: Any) -> AuditLogStore:
    connection = sqlite3.connect(":memory:")
    store = AuditLogStore(lambda: connection, close_connection=False)
    monkeypatch.setattr(tasks, "AUDIT_LOG_STORE", store)
    return store


def test_company_search_task(monkeypatch: Any) -> None:
    client = InMemoryRedis()
    _attach_redis(monkeypatch, client)
    monkeypatch.setattr(
        tasks,
        "search_companies_with_playwright",
        lambda payload: [{"name": "Acme", "source": "playwright"}],
    )
    monkeypatch.setattr(
        tasks,
        "search_companies_with_selenium",
        lambda payload: [{"name": "Beta", "source": "selenium"}],
    )

    result = tasks.company_search(
        intent_id="intent-1",
        entity_id="entity-1",
        payload={"query": "saas"},
        version="v1",
    )

    assert result["status"] == "success"
    assert result["task_type"] == "company_search"
    assert result["result"]["companies"] == [
        {"name": "Acme", "source": "playwright"},
        {"name": "Beta", "source": "selenium"},
    ]


def test_contact_finder_task(monkeypatch: Any) -> None:
    client = InMemoryRedis()
    _attach_redis(monkeypatch, client)
    monkeypatch.setattr(
        tasks,
        "find_contacts_with_mailscout",
        lambda payload: [{"name": "Taylor", "email": "t@acme.com"}],
    )
    monkeypatch.setattr(
        tasks,
        "find_contacts_with_theharvester",
        lambda payload: [{"name": "Jordan", "email": "j@acme.com"}],
    )

    result = tasks.contact_finder(
        intent_id="intent-2",
        entity_id="entity-2",
        payload={"domain": "acme.com"},
    )

    assert result["status"] == "success"
    assert result["task_type"] == "contact_finder"
    assert result["result"]["contacts"][0]["name"] == "Taylor"
    assert result["result"]["contacts"][1]["name"] == "Jordan"


def test_news_collector_task(monkeypatch: Any) -> None:
    client = InMemoryRedis()
    _attach_redis(monkeypatch, client)
    monkeypatch.setattr(
        tasks,
        "collect_news_with_newsapi",
        lambda payload: [{"title": "Update", "url": "https://n.example"}],
    )
    monkeypatch.setattr(
        tasks,
        "parse_articles_with_newspaper",
        lambda articles: [{"title": "Update", "summary": "Summary"}],
    )

    result = tasks.news_collector(
        intent_id="intent-3",
        entity_id="entity-3",
        payload={"topic": "sales"},
        version="v2",
    )

    assert result["status"] == "success"
    assert result["task_type"] == "news_collector"
    assert result["result"]["summaries"][0]["summary"] == "Summary"


def test_email_generator_task(monkeypatch: Any) -> None:
    client = InMemoryRedis()
    _attach_redis(monkeypatch, client)
    monkeypatch.setattr(
        tasks,
        "generate_email_with_template",
        lambda payload: {"subject": "Hi", "body": "Hello"},
    )

    result = tasks.email_generator(
        intent_id="intent-4",
        entity_id="entity-4",
        payload={"recipient": "Alex"},
    )

    assert result["status"] == "success"
    assert result["task_type"] == "email_generator"
    assert result["result"]["email"]["subject"] == "Hi"


def test_scheduler_task(monkeypatch: Any) -> None:
    client = InMemoryRedis()
    _attach_redis(monkeypatch, client)
    monkeypatch.setattr(
        tasks,
        "build_schedule_plan",
        lambda payload: {"next_step": "call", "due_date": "2024-06-01"},
    )

    result = tasks.scheduler(
        intent_id="intent-5",
        entity_id="entity-5",
        payload={"next_step": "call"},
    )

    assert result["status"] == "success"
    assert result["task_type"] == "scheduler"
    assert result["result"]["schedule"]["next_step"] == "call"


def test_pipeline_bant_task(monkeypatch: Any) -> None:
    client = InMemoryRedis()
    _attach_redis(monkeypatch, client)
    monkeypatch.setattr(
        tasks,
        "score_pipeline_bant",
        lambda payload: {"score": 12, "qualified": True},
    )

    result = tasks.pipeline_bant(
        intent_id="intent-6",
        entity_id="entity-6",
        payload={"bant": {"budget": 4, "authority": 4, "need": 4, "timing": 0}},
    )

    assert result["status"] == "success"
    assert result["task_type"] == "pipeline_bant"
    assert result["result"]["assessment"]["qualified"] is True


def test_idempotency_caches_results(monkeypatch: Any) -> None:
    client = InMemoryRedis()
    _attach_redis(monkeypatch, client)
    calls: dict[str, int] = {"count": 0}

    def _handler(payload: dict[str, Any]) -> dict[str, Any]:
        calls["count"] += 1
        return {"companies": [{"name": "Acme"}]}

    monkeypatch.setattr(tasks, "_company_search", _handler)

    first = tasks.company_search(
        intent_id="intent-7",
        entity_id="entity-7",
        payload={"query": "Acme"},
        version="v1",
    )
    second = tasks.company_search(
        intent_id="intent-7",
        entity_id="entity-7",
        payload={"query": "Acme"},
        version="v1",
    )

    assert first == second
    assert calls["count"] == 1


def test_lock_idempotency_returns_locked(monkeypatch: Any) -> None:
    client = InMemoryRedis()
    _attach_redis(monkeypatch, client)
    lock_key = (
        "lock:"
        f"{tasks.build_idempotency_key('intent-8', 'company_search', 'entity-8', 'v1')}"
    )
    client.set(lock_key, "token-1", nx=True)

    result = tasks.company_search(
        intent_id="intent-8",
        entity_id="entity-8",
        payload={"query": "Acme"},
        version="v1",
    )

    assert result["status"] == "locked"
    assert lock_key in client.keys()
