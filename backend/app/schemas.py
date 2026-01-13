from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AccountCreate(BaseModel):
    name: str = Field(..., min_length=1)
    industry: str | None = None


class AccountRead(AccountCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class ContactCreate(BaseModel):
    account_id: int
    first_name: str = Field(..., min_length=1)
    last_name: str = Field(..., min_length=1)
    title: str | None = None


class ContactRead(ContactCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class EmailCreate(BaseModel):
    contact_id: int
    address: str = Field(..., min_length=3)
    version: int = Field(..., ge=1)


class EmailRead(EmailCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class PipelineCreate(BaseModel):
    account_id: int
    name: str = Field(..., min_length=1)
    stage: str = Field(..., min_length=1)
    amount_cents: int | None = Field(default=None, ge=0)


class PipelineRead(PipelineCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class BantCreate(BaseModel):
    pipeline_id: int
    budget: str = Field(..., min_length=1)
    authority: str = Field(..., min_length=1)
    need: str = Field(..., min_length=1)
    timeline: str = Field(..., min_length=1)


class BantRead(BantCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class TaskCreate(BaseModel):
    account_id: int
    contact_id: int | None = None
    title: str = Field(..., min_length=1)
    status: str = Field(..., min_length=1)
    due_at: datetime | None = None


class TaskRead(TaskCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class ArtifactCreate(BaseModel):
    task_id: int
    name: str = Field(..., min_length=1)
    uri: str = Field(..., min_length=1)


class ArtifactRead(ArtifactCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class AuditLogCreate(BaseModel):
    trigger_source: str = Field(..., min_length=1)
    input_json: str = Field(..., min_length=1)
    output_result: str = Field(..., min_length=1)


class AuditLogRead(AuditLogCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class DeadLetterTask(BaseModel):
    task_id: str
    intent_id: str
    task_type: str
    status: str
    retry_count: int
    idempotency_key: str
    payload: dict[str, object]
    created_at: datetime


class DeadLetterItemRead(BaseModel):
    id: int
    reason: str
    deadlettered_at: datetime
    task: DeadLetterTask
