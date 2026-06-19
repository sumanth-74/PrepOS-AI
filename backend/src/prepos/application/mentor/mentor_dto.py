from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MentorQueueItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    student_id: UUID
    mentor_action: str
    priority_score: Decimal
    escalation_level: str
    case_id: UUID
    case_status: str
    opened_at: datetime


class MentorQueueResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: list[MentorQueueItemResponse] = Field(default_factory=list)


class MentorDashboardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    open_cases: int = 0
    critical_cases: int = 0
    average_resolution_time_hours: Decimal = Decimal("0")
    mentor_effectiveness_score: Decimal = Decimal("0")
    best_action: str | None = None
    best_action_effectiveness: Decimal = Decimal("0")
    average_action_effectiveness: Decimal = Decimal("0")


class MentorCaseNoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    note_id: UUID
    mentor_id: UUID
    note: str
    created_at: datetime


class MentorCaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    case_id: UUID
    student_id: UUID
    exam_id: str
    status: str
    priority: str
    mentor_action_type: str
    escalation_level: str
    mentor_action_priority: Decimal
    opened_at: datetime
    resolved_at: datetime | None = None
    resolution_reason: str | None = None
    notes: list[MentorCaseNoteResponse] = Field(default_factory=list)


class AddCaseNoteRequest(BaseModel):
    note: str = Field(min_length=1, max_length=4000)


class ResolveCaseRequest(BaseModel):
    resolution_reason: str
