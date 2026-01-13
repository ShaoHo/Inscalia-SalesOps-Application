from __future__ import annotations

from enum import Enum
from typing import Any

from jsonschema import Draft7Validator
from pydantic import BaseModel, ConfigDict, Field


INTENT_JSON_SCHEMA: dict[str, Any] = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "SalesOpsIntent",
    "type": "object",
    "additionalProperties": False,
    "required": ["intent_id", "raw_text", "filters", "actions"],
    "properties": {
        "intent_id": {"type": "string"},
        "raw_text": {"type": "string"},
        "language": {"type": "string"},
        "filters": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "industries": {"type": "array", "items": {"type": "string"}},
                "regions": {"type": "array", "items": {"type": "string"}},
                "company_size": {"type": "string"},
                "keywords": {"type": "array", "items": {"type": "string"}},
                "roles": {"type": "array", "items": {"type": "string"}},
            },
        },
        "actions": {
            "type": "array",
            "items": {
                "type": "string",
                "enum": [
                    "search_companies",
                    "find_contacts",
                    "collect_news",
                    "generate_emails",
                    "schedule_emails",
                    "update_pipeline",
                ],
            },
        },
    },
}


class IntentAction(str, Enum):
    search_companies = "search_companies"
    find_contacts = "find_contacts"
    collect_news = "collect_news"
    generate_emails = "generate_emails"
    schedule_emails = "schedule_emails"
    update_pipeline = "update_pipeline"


class IntentFilters(BaseModel):
    model_config = ConfigDict(extra="forbid")

    industries: list[str] | None = None
    regions: list[str] | None = None
    company_size: str | None = None
    keywords: list[str] | None = None
    roles: list[str] | None = None


class SalesOpsIntent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    intent_id: str = Field(..., min_length=1)
    raw_text: str = Field(..., min_length=1)
    language: str | None = None
    filters: IntentFilters
    actions: list[IntentAction] = Field(default_factory=list)


class IntentValidationError(ValueError):
    def __init__(self, errors: list[dict[str, Any]]) -> None:
        message = "Intent JSON does not match schema."
        super().__init__(message)
        self.errors = errors


def validate_intent_schema(payload: dict[str, Any]) -> SalesOpsIntent:
    validator = Draft7Validator(INTENT_JSON_SCHEMA)
    errors = [
        {"path": list(error.path), "message": error.message}
        for error in validator.iter_errors(payload)
    ]
    if errors:
        raise IntentValidationError(errors)
    return SalesOpsIntent.model_validate(payload)
