import pytest

pytest.importorskip("httpx")

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_create_intent_valid_payload(monkeypatch) -> None:
    def fake_parse_intent(raw_text: str, language: str | None, intent_id: str) -> dict:
        return {
            "intent_id": intent_id,
            "raw_text": raw_text,
            "language": language,
            "filters": {
                "industries": ["SaaS"],
                "regions": ["APAC"],
                "company_size": "SMB",
                "keywords": ["CRM"],
                "roles": ["CTO"],
            },
            "actions": ["search_companies", "find_contacts"],
        }

    monkeypatch.setattr(
        "apps.api.services.llm_intent_parser.parse_intent",
        fake_parse_intent,
    )

    response = client.post(
        "/intents",
        json={"raw_text": "Find SaaS companies in APAC.", "language": "en"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["intent"]["raw_text"] == "Find SaaS companies in APAC."
    assert body["intent"]["actions"] == ["search_companies", "find_contacts"]
    assert len(body["tasks"]) == 2
    assert len(body["celery_tasks"]) == 2


def test_create_intent_invalid_payload(monkeypatch) -> None:
    def fake_parse_intent(raw_text: str, language: str | None, intent_id: str) -> dict:
        return {
            "intent_id": intent_id,
            "raw_text": raw_text,
            "filters": {},
            "actions": ["invalid_action"],
        }

    monkeypatch.setattr(
        "apps.api.services.llm_intent_parser.parse_intent",
        fake_parse_intent,
    )

    response = client.post(
        "/intents",
        json={"raw_text": "Missing required fields.", "language": "en"},
    )

    assert response.status_code == 422
    body = response.json()
    assert body["detail"]["message"] == "Intent JSON does not match schema."
