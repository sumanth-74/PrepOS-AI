from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from prepos.domain.mentor.mentor_types_v1 import (
    CASE_CREATING_ACTIONS,
    ActionUrgency,
    CasePriority,
    CaseResolutionReason,
    CaseStatus,
    EscalationLevel,
    MentorActionType,
)

CASE_MANAGEMENT_V1 = "case_management_v1"


@dataclass(frozen=True, slots=True)
class MentorCase:
    case_id: UUID
    student_id: UUID
    exam_id: str
    status: CaseStatus
    priority: CasePriority
    mentor_action_type: MentorActionType
    escalation_level: EscalationLevel
    mentor_action_priority: Decimal
    opened_at: datetime
    resolved_at: datetime | None = None
    resolution_reason: CaseResolutionReason | None = None


@dataclass(frozen=True, slots=True)
class MentorCaseNote:
    id: UUID
    case_id: UUID
    mentor_id: UUID
    note: str
    created_at: datetime


def should_create_case(*, action_type: MentorActionType) -> bool:
    return action_type in CASE_CREATING_ACTIONS


def map_case_priority(
    *,
    urgency: ActionUrgency,
    escalation_level: EscalationLevel,
) -> CasePriority:
    if escalation_level == EscalationLevel.CRITICAL or urgency == ActionUrgency.CRITICAL:
        return CasePriority.CRITICAL
    if escalation_level == EscalationLevel.HIGH or urgency == ActionUrgency.HIGH:
        return CasePriority.HIGH
    if escalation_level in {EscalationLevel.MEDIUM, EscalationLevel.LOW}:
        return CasePriority.MEDIUM
    return CasePriority.LOW


def is_successful_resolution(*, reason: CaseResolutionReason) -> bool:
    return reason != CaseResolutionReason.FALSE_POSITIVE


def is_risk_reduced_resolution(*, reason: CaseResolutionReason) -> bool:
    return reason in {
        CaseResolutionReason.RISK_REDUCED,
        CaseResolutionReason.PLAN_UPDATED,
        CaseResolutionReason.GOAL_ADJUSTED,
    }
