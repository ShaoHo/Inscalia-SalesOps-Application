import pytest

from apps.api.services.intent_validator import IntentValidationError, validate_intent_schema


def test_validate_intent_schema_accepts_valid_payload() -> None:
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

    intent = validate_intent_schema(payload)

    assert intent.intent_id == "intent-123"
    assert intent.actions[0].value == "search_companies"


def test_validate_intent_schema_rejects_extra_fields() -> None:
    payload = {
        "intent_id": "intent-123",
        "raw_text": "Find SaaS companies in APAC.",
        "filters": {},
        "actions": ["search_companies"],
        "unexpected": "nope",
    }

    with pytest.raises(IntentValidationError) as exc:
        validate_intent_schema(payload)

    assert exc.value.errors
