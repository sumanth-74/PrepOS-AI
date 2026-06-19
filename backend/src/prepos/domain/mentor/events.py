from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from prepos.domain.mentor.mentor_types_v1 import (
    CaseResolutionReason,
    CaseStatus,
    EscalationLevel,
    MentorActionType,
    OverallStatus,
)


@dataclass(frozen=True, slots=True)
class MentorInsightUpdated:
    tenant_id: UUID
    student_id: UUID
    exam_id: str
    insight_count: int
    top_insight_type: str | None
    top_insight_priority: str | None
    correlation_id: str
    causation_id: str | None
    occurred_at: datetime

    @property
    def event_type(self) -> str:
        return "MentorInsightUpdated"

    def to_payload(self) -> dict[str, object]:
        return {
            "tenant_id": str(self.tenant_id),
            "student_id": str(self.student_id),
            "exam_id": self.exam_id,
            "insight_count": self.insight_count,
            "top_insight_type": self.top_insight_type,
            "top_insight_priority": self.top_insight_priority,
        }


@dataclass(frozen=True, slots=True)
class MentorSummaryUpdated:
    tenant_id: UUID
    student_id: UUID
    exam_id: str
    mentor_status: OverallStatus
    top_mentor_message: str
    insight_count: int
    recommendation_count: int
    correlation_id: str
    causation_id: str | None
    occurred_at: datetime

    @property
    def event_type(self) -> str:
        return "MentorSummaryUpdated"

    def to_payload(self) -> dict[str, object]:
        return {
            "tenant_id": str(self.tenant_id),
            "student_id": str(self.student_id),
            "exam_id": self.exam_id,
            "mentor_status": self.mentor_status.value,
            "top_mentor_message": self.top_mentor_message,
            "insight_count": self.insight_count,
            "recommendation_count": self.recommendation_count,
        }


@dataclass(frozen=True, slots=True)
class MentorActionUpdated:
    tenant_id: UUID
    student_id: UUID
    exam_id: str
    action_type: MentorActionType
    priority_score: float
    urgency: str
    expected_impact: float
    explanation: str
    correlation_id: str
    causation_id: str | None
    occurred_at: datetime

    @property
    def event_type(self) -> str:
        return "MentorActionUpdated"

    def to_payload(self) -> dict[str, object]:
        return {
            "tenant_id": str(self.tenant_id),
            "student_id": str(self.student_id),
            "exam_id": self.exam_id,
            "action_type": self.action_type.value,
            "priority_score": self.priority_score,
            "urgency": self.urgency,
            "expected_impact": self.expected_impact,
            "explanation": self.explanation,
        }


@dataclass(frozen=True, slots=True)
class EscalationUpdated:
    tenant_id: UUID
    student_id: UUID
    exam_id: str
    escalation_level: EscalationLevel
    reason: str
    correlation_id: str
    causation_id: str | None
    occurred_at: datetime

    @property
    def event_type(self) -> str:
        return "EscalationUpdated"

    def to_payload(self) -> dict[str, object]:
        return {
            "tenant_id": str(self.tenant_id),
            "student_id": str(self.student_id),
            "exam_id": self.exam_id,
            "escalation_level": self.escalation_level.value,
            "reason": self.reason,
        }


@dataclass(frozen=True, slots=True)
class MentorCaseCreated:
    tenant_id: UUID
    student_id: UUID
    exam_id: str
    case_id: UUID
    mentor_action_type: MentorActionType
    case_status: CaseStatus
    case_priority: str
    escalation_level: EscalationLevel
    priority_score: float
    explanation: str
    correlation_id: str
    causation_id: str | None
    occurred_at: datetime

    @property
    def event_type(self) -> str:
        return "MentorCaseCreated"

    def to_payload(self) -> dict[str, object]:
        return {
            "tenant_id": str(self.tenant_id),
            "student_id": str(self.student_id),
            "exam_id": self.exam_id,
            "case_id": str(self.case_id),
            "mentor_action_type": self.mentor_action_type.value,
            "case_status": self.case_status.value,
            "case_priority": self.case_priority,
            "escalation_level": self.escalation_level.value,
            "priority_score": self.priority_score,
            "explanation": self.explanation,
        }


@dataclass(frozen=True, slots=True)
class MentorCaseUpdated:
    tenant_id: UUID
    student_id: UUID
    exam_id: str
    case_id: UUID
    case_status: CaseStatus
    case_priority: str
    correlation_id: str
    causation_id: str | None
    occurred_at: datetime

    @property
    def event_type(self) -> str:
        return "MentorCaseUpdated"

    def to_payload(self) -> dict[str, object]:
        return {
            "tenant_id": str(self.tenant_id),
            "student_id": str(self.student_id),
            "exam_id": self.exam_id,
            "case_id": str(self.case_id),
            "case_status": self.case_status.value,
            "case_priority": self.case_priority,
        }


@dataclass(frozen=True, slots=True)
class MentorCaseResolved:
    tenant_id: UUID
    student_id: UUID
    exam_id: str
    case_id: UUID
    resolution_reason: CaseResolutionReason
    explanation: str
    correlation_id: str
    causation_id: str | None
    occurred_at: datetime

    @property
    def event_type(self) -> str:
        return "MentorCaseResolved"

    def to_payload(self) -> dict[str, object]:
        return {
            "tenant_id": str(self.tenant_id),
            "student_id": str(self.student_id),
            "exam_id": self.exam_id,
            "case_id": str(self.case_id),
            "resolution_reason": self.resolution_reason.value,
            "explanation": self.explanation,
        }


@dataclass(frozen=True, slots=True)
class MentorEffectivenessUpdated:
    tenant_id: UUID
    student_id: UUID
    exam_id: str
    effectiveness_score: float
    cases_resolved: int
    average_resolution_time_hours: float
    risk_reduction_rate: float
    best_action: str | None
    best_action_effectiveness: float
    average_action_effectiveness: float
    correlation_id: str
    causation_id: str | None
    occurred_at: datetime

    @property
    def event_type(self) -> str:
        return "MentorEffectivenessUpdated"

    def to_payload(self) -> dict[str, object]:
        return {
            "tenant_id": str(self.tenant_id),
            "student_id": str(self.student_id),
            "exam_id": self.exam_id,
            "effectiveness_score": self.effectiveness_score,
            "cases_resolved": self.cases_resolved,
            "average_resolution_time_hours": self.average_resolution_time_hours,
            "risk_reduction_rate": self.risk_reduction_rate,
            "best_action": self.best_action,
            "best_action_effectiveness": self.best_action_effectiveness,
            "average_action_effectiveness": self.average_action_effectiveness,
        }
