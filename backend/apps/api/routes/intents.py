from __future__ import annotations

from typing import Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from apps.api.services.intent_validator import IntentValidationError, SalesOpsIntent, validate_intent_schema
from apps.api.services import llm_intent_parser
from apps.api.services.orchestrator import map_tasks_to_celery, plan_tasks_for_intent

router = APIRouter(prefix="/intents", tags=["intents"])


class IntentRequest(BaseModel):
    raw_text: str = Field(..., min_length=1)
    language: str | None = None
    intent_id: str | None = None


class IntentResponse(BaseModel):
    intent: SalesOpsIntent
    tasks: list[dict[str, Any]]
    celery_tasks: list[dict[str, str]]


@router.post("", response_model=IntentResponse)
async def create_intent(payload: IntentRequest) -> IntentResponse:
    intent_id = payload.intent_id or str(uuid4())
    intent_payload = llm_intent_parser.parse_intent(payload.raw_text, payload.language, intent_id)
    try:
        intent = validate_intent_schema(intent_payload)
    except IntentValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail={"message": str(exc), "errors": exc.errors},
        ) from exc

    tasks = plan_tasks_for_intent(intent)
    return IntentResponse(
        intent=intent,
        tasks=[task.to_dict() for task in tasks],
        celery_tasks=map_tasks_to_celery(tasks),
    )
