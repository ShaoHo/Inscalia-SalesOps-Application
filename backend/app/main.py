from enum import Enum

from fastapi import Body, FastAPI, HTTPException
from jsonschema import Draft7Validator
from pydantic import BaseModel, ConfigDict, Field

from app.config import settings

app = FastAPI(title=settings.app_name)

INTENT_JSON_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "SalesOpsIntent",
    "type": "object",
    "required": ["intent_id", "raw_text", "filters", "actions"],
    "properties": {
        "intent_id": {"type": "string"},
        "raw_text": {"type": "string"},
        "language": {"type": "string"},
        "filters": {
            "type": "object",
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
    model_config = ConfigDict(extra="allow")

    industries: list[str] | None = None
    regions: list[str] | None = None
    company_size: str | None = None
    keywords: list[str] | None = None
    roles: list[str] | None = None


class SalesOpsIntent(BaseModel):
    model_config = ConfigDict(extra="allow")

    intent_id: str
    raw_text: str
    language: str | None = None
    filters: IntentFilters
    actions: list[IntentAction] = Field(default_factory=list)


def validate_intent_schema(payload: dict) -> None:
    validator = Draft7Validator(INTENT_JSON_SCHEMA)
    errors = [
        {"path": list(error.path), "message": error.message}
        for error in validator.iter_errors(payload)
    ]
    if errors:
        raise HTTPException(
            status_code=422,
            detail={"message": "Intent JSON does not match schema.", "errors": errors},
        )


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/intents", response_model=SalesOpsIntent, tags=["intents"])
async def create_intent(payload: dict = Body(...)) -> SalesOpsIntent:
    validate_intent_schema(payload)
    return SalesOpsIntent.model_validate(payload)
