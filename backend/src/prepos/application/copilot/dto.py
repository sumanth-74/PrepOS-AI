from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

CopilotPersona = Literal["student", "mentor", "admin"]


class CopilotQueryRequest(BaseModel):
    persona: CopilotPersona
    question: str = Field(min_length=1, max_length=2000)
    student_id: UUID | None = None
    case_id: UUID | None = None
    exam_id: str | None = None
    session_id: UUID | None = None
    agent_mode: bool = False


class CopilotSourceResponse(BaseModel):
    label: str
    reference: str


class CopilotCitationResponse(BaseModel):
    chunk_id: UUID
    source_title: str


class CopilotRecommendationResponse(BaseModel):
    concept_id: str
    concept_name: str
    impact_score: float
    reason_codes: list[str] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)
    estimated_readiness_gain: float
    confidence: str
    explanation: str | None = None


class CopilotCardResponse(BaseModel):
    card_type: str
    title: str
    summary: str
    explanation: str | None = None
    data: dict[str, object] = Field(default_factory=dict)
    expanded: bool = False


class CopilotQueryResponse(BaseModel):
    intent: str
    answer: str
    sources: list[CopilotSourceResponse] = Field(default_factory=list)
    citations: list[CopilotCitationResponse] = Field(default_factory=list)
    recommendations: list[CopilotRecommendationResponse] = Field(default_factory=list)
    cards: list[CopilotCardResponse] = Field(default_factory=list)
    confidence: str | None = None
    student_context_used: bool | None = None
    session_id: UUID | None = None
    trace_id: UUID | None = None
    execution_id: UUID | None = None
    explanation: str | None = None
