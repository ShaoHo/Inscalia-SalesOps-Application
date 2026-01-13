from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_create_intent_valid_payload() -> None:
    payload = {
        "intent_id": "intent-123",
        "raw_text": "Find SaaS companies in APAC.",
        "language": "en",
        "filters": {
            "industries": ["SaaS"],
            "regions": ["APAC"],
            "company_size": "SMB",
            "keywords": ["CRM"],
            "roles": ["CTO"],
        },
        "actions": ["search_companies", "find_contacts"],
    }

    response = client.post("/intents", json=payload)

    assert response.status_code == 200
    assert response.json() == payload


def test_create_intent_invalid_payload() -> None:
    payload = {
        "raw_text": "Missing required fields.",
        "filters": {},
        "actions": ["invalid_action"],
    }

    response = client.post("/intents", json=payload)

    assert response.status_code == 422
    body = response.json()
    assert body["detail"]["message"] == "Intent JSON does not match schema."
