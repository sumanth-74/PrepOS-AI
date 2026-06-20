from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

MemoryType = Literal[
    "recommendation_history",
    "recommendation_outcomes",
    "coaching_notes",
    "learning_preferences",
    "progress_milestones",
    "weakness_trends",
    "mentor_interventions",
    "goal_changes",
]

SUPPORTED_MEMORY_TYPES: frozenset[str] = frozenset(
    {
        "recommendation_history",
        "recommendation_outcomes",
        "coaching_notes",
        "learning_preferences",
        "progress_milestones",
        "weakness_trends",
        "mentor_interventions",
        "goal_changes",
    }
)


class MemoryRecordResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    user_id: UUID
    persona: str
    memory_type: str
    memory_key: str
    memory_value: dict[str, object]
    created_at: datetime
    updated_at: datetime


class MemoryListResponse(BaseModel):
    memories: list[MemoryRecordResponse]
    total: int


class TimelineEventResponse(BaseModel):
    event_type: str
    occurred_at: datetime
    concept_id: str | None = None
    concept_name: str | None = None
    summary: str
    details: dict[str, object] = Field(default_factory=dict)


class LearningTimelineResponse(BaseModel):
    events: list[TimelineEventResponse]
    total: int


class MilestoneListResponse(BaseModel):
    milestones: list[MemoryRecordResponse]
    total: int


class MemoryRebuildResponse(BaseModel):
    status: str
    memories_created: int
    milestones_detected: int


class MemoryAdminResponse(BaseModel):
    total_memories: int
    memory_growth_last_30_days: int
    top_memory_types: list[dict[str, object]]
    milestone_count: int
    last_rebuild_at: str | None = None
