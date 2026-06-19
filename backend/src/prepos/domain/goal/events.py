from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from prepos.domain.goal.milestones_v1 import MilestoneStatus


@dataclass(frozen=True, slots=True)
class GoalUpdated:
    tenant_id: UUID
    student_id: UUID
    exam_id: str
    target_readiness_score: Decimal
    target_date: date
    daily_capacity_minutes: int
    correlation_id: str
    causation_id: str | None
    occurred_at: datetime

    @property
    def event_type(self) -> str:
        return "GoalUpdated"

    def to_payload(self) -> dict[str, object]:
        return {
            "tenant_id": str(self.tenant_id),
            "student_id": str(self.student_id),
            "exam_id": self.exam_id,
            "target_readiness_score": float(self.target_readiness_score),
            "target_date": self.target_date.isoformat(),
            "daily_capacity_minutes": self.daily_capacity_minutes,
        }


@dataclass(frozen=True, slots=True)
class ForecastUpdated:
    tenant_id: UUID
    student_id: UUID
    exam_id: str
    target_readiness_score: Decimal
    target_date: date
    current_readiness: Decimal
    projected_readiness: Decimal
    gap_to_goal: Decimal
    on_track: bool
    days_remaining: int
    adaptive_capacity_minutes: int
    explanation: str
    correlation_id: str
    causation_id: str | None
    occurred_at: datetime

    @property
    def event_type(self) -> str:
        return "ForecastUpdated"

    def to_payload(self) -> dict[str, object]:
        return {
            "tenant_id": str(self.tenant_id),
            "student_id": str(self.student_id),
            "exam_id": self.exam_id,
            "target_readiness_score": float(self.target_readiness_score),
            "target_date": self.target_date.isoformat(),
            "current_readiness": float(self.current_readiness),
            "projected_readiness": float(self.projected_readiness),
            "gap_to_goal": float(self.gap_to_goal),
            "on_track": self.on_track,
            "days_remaining": self.days_remaining,
            "adaptive_capacity_minutes": self.adaptive_capacity_minutes,
            "explanation": self.explanation,
        }


@dataclass(frozen=True, slots=True)
class MilestoneUpdated:
    tenant_id: UUID
    student_id: UUID
    exam_id: str
    required_gain: Decimal
    expected_daily_progress: Decimal
    expected_weekly_progress: Decimal
    milestones: tuple[dict[str, Any], ...]
    milestone_status: MilestoneStatus
    current_gap: Decimal
    next_milestone_date: date | None
    next_milestone_target: Decimal | None
    explanation: str
    correlation_id: str
    causation_id: str | None
    occurred_at: datetime

    @property
    def event_type(self) -> str:
        return "MilestoneUpdated"

    def to_payload(self) -> dict[str, object]:
        return {
            "tenant_id": str(self.tenant_id),
            "student_id": str(self.student_id),
            "exam_id": self.exam_id,
            "required_gain": float(self.required_gain),
            "expected_daily_progress": float(self.expected_daily_progress),
            "expected_weekly_progress": float(self.expected_weekly_progress),
            "milestones": list(self.milestones),
            "milestone_status": self.milestone_status.value,
            "current_gap": float(self.current_gap),
            "next_milestone_date": (
                self.next_milestone_date.isoformat() if self.next_milestone_date is not None else None
            ),
            "next_milestone_target": (
                float(self.next_milestone_target)
                if self.next_milestone_target is not None
                else None
            ),
            "explanation": self.explanation,
        }
