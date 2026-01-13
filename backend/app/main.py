from fastapi import FastAPI
from pydantic import BaseModel

from app.config import settings
from app.schemas import DeadLetterItemRead, DeadLetterTask
from apps.api.routes.intents import router as intents_router
from orchestrator.deadletter_store import get_default_deadletter_store

app = FastAPI(title=settings.app_name)


class MetricsResponse(BaseModel):
    status: str
    service: str


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/metrics", response_model=MetricsResponse, tags=["health"])
async def metrics() -> MetricsResponse:
    return MetricsResponse(status="ok", service=settings.app_name)


app.include_router(intents_router)


@app.get("/deadletter", response_model=list[DeadLetterItemRead], tags=["deadletter"])
async def list_deadletter(limit: int = 50) -> list[DeadLetterItemRead]:
    store = get_default_deadletter_store()
    items = store.list(limit=limit)
    return [
        DeadLetterItemRead(
            id=item.id,
            reason=item.reason,
            deadlettered_at=item.deadlettered_at,
            task=DeadLetterTask(
                task_id=item.task.task_id,
                intent_id=item.task.intent_id,
                task_type=item.task.task_type,
                status=item.task.status.value,
                retry_count=item.task.retry_count,
                idempotency_key=item.task.idempotency_key,
                payload=item.task.payload,
                created_at=item.task.created_at,
            ),
        )
        for item in items
    ]
