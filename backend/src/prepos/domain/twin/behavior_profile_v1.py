from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from prepos.domain.scoring.common import clamp, round_score
from prepos.domain.study_plan.entities import StudyPlanExecutionRecord
from prepos.domain.study_plan.value_objects import ActivityType, ExecutionStatus
from prepos.domain.twin.behavior_profile_types_v1 import LearningStyle, RiskProfile
from prepos.domain.twin.intervention_history_entities import StudentInterventionHistoryEntry
from prepos.domain.twin.intervention_types_v1 import TwinInterventionType

_SHORT_BURST_THRESHOLD = Decimal("25")
_DEEP_FOCUS_THRESHOLD = Decimal("45")
_CONSISTENT_THRESHOLD = Decimal("80")
_HIGH_RISK_THRESHOLD = Decimal("40")
_MEDIUM_RISK_THRESHOLD = Decimal("70")
_WEAKNESS_REMEDIATION = TwinInterventionType.WEAKNESS_REMEDIATION.value


@dataclass(frozen=True, slots=True)
class BehaviorProfileInputs:
    executions: tuple[StudyPlanExecutionRecord, ...]
    intervention_outcomes: tuple[StudentInterventionHistoryEntry, ...]
    effectiveness_by_type: dict[str, Decimal]


@dataclass(frozen=True, slots=True)
class BehaviorProfile:
    consistency_score: Decimal
    discipline_score: Decimal
    revision_adherence_score: Decimal
    weakness_recovery_score: Decimal
    engagement_score: Decimal
    learning_style: LearningStyle
    risk_profile: RiskProfile


def compute_consistency_score_v1(
    *,
    completed_sessions: int,
    planned_sessions: int,
) -> Decimal:
    if planned_sessions <= 0:
        return Decimal("0")
    raw = (Decimal(completed_sessions) / Decimal(planned_sessions)) * Decimal("100")
    return round_score(clamp(raw, Decimal("0"), Decimal("100")))


def compute_discipline_score_v1(*, skip_rate: Decimal) -> Decimal:
    raw = Decimal("100") - skip_rate * Decimal("100")
    return round_score(clamp(raw, Decimal("0"), Decimal("100")))


def compute_revision_adherence_score_v1(
    executions: tuple[StudyPlanExecutionRecord, ...],
) -> Decimal:
    revision_records = tuple(
        record for record in executions if record.activity_type == ActivityType.REVISION
    )
    if not revision_records:
        return Decimal("0")
    assigned = len(revision_records)
    completed = sum(
        1 for record in revision_records if record.status == ExecutionStatus.COMPLETED
    )
    raw = (Decimal(completed) / Decimal(assigned)) * Decimal("100")
    return round_score(clamp(raw, Decimal("0"), Decimal("100")))


def compute_weakness_recovery_score_v1(
    outcomes: tuple[StudentInterventionHistoryEntry, ...],
) -> Decimal:
    weakness_deltas = [
        outcome.readiness_delta
        for outcome in outcomes
        if outcome.intervention_type == _WEAKNESS_REMEDIATION
    ]
    if not weakness_deltas:
        return Decimal("0")
    average = sum(weakness_deltas, start=Decimal("0")) / Decimal(len(weakness_deltas))
    return round_score(clamp(average, Decimal("0"), Decimal("100")))


def compute_engagement_score_v1(
    executions: tuple[StudyPlanExecutionRecord, ...],
) -> Decimal:
    completed = [
        record
        for record in executions
        if record.status == ExecutionStatus.COMPLETED and record.planned_minutes > 0
    ]
    if not completed:
        return Decimal("0")
    actual_minutes = sum(record.actual_minutes for record in completed)
    planned_minutes = sum(record.planned_minutes for record in completed)
    if planned_minutes <= 0:
        return Decimal("0")
    raw = (Decimal(actual_minutes) / Decimal(planned_minutes)) * Decimal("100")
    return round_score(clamp(raw, Decimal("0"), Decimal("100")))


def _average_completed_session_minutes(
    executions: tuple[StudyPlanExecutionRecord, ...],
) -> Decimal | None:
    completed = [
        record
        for record in executions
        if record.status == ExecutionStatus.COMPLETED and record.actual_minutes > 0
    ]
    if not completed:
        return None
    total = sum(record.actual_minutes for record in completed)
    return Decimal(total) / Decimal(len(completed))


def _weakness_outperforms_others(effectiveness_by_type: dict[str, Decimal]) -> bool:
    weakness_score = effectiveness_by_type.get(_WEAKNESS_REMEDIATION)
    if weakness_score is None:
        return False
    other_scores = [
        score
        for intervention_type, score in effectiveness_by_type.items()
        if intervention_type != _WEAKNESS_REMEDIATION
    ]
    if not other_scores:
        return weakness_score > Decimal("0")
    average_other = sum(other_scores, start=Decimal("0")) / Decimal(len(other_scores))
    return weakness_score > average_other


def classify_learning_style_v1(
    *,
    consistency_score: Decimal,
    average_session_minutes: Decimal | None,
    effectiveness_by_type: dict[str, Decimal],
) -> LearningStyle:
    if _weakness_outperforms_others(effectiveness_by_type):
        return LearningStyle.RECOVERY_DRIVEN
    if consistency_score > _CONSISTENT_THRESHOLD:
        return LearningStyle.CONSISTENT_LEARNER
    if average_session_minutes is not None and average_session_minutes < _SHORT_BURST_THRESHOLD:
        return LearningStyle.SHORT_BURST_LEARNER
    if average_session_minutes is not None and average_session_minutes > _DEEP_FOCUS_THRESHOLD:
        return LearningStyle.DEEP_FOCUS_LEARNER
    return LearningStyle.BALANCED


def classify_risk_profile_v1(*, consistency_score: Decimal) -> RiskProfile:
    if consistency_score < _HIGH_RISK_THRESHOLD:
        return RiskProfile.HIGH_RISK
    if consistency_score < _MEDIUM_RISK_THRESHOLD:
        return RiskProfile.MEDIUM_RISK
    return RiskProfile.LOW_RISK


def build_behavior_profile_v1(inputs: BehaviorProfileInputs) -> BehaviorProfile:
    executions = inputs.executions
    planned_sessions = len(executions)
    completed_sessions = sum(
        1 for record in executions if record.status == ExecutionStatus.COMPLETED
    )
    skipped_sessions = sum(
        1 for record in executions if record.status == ExecutionStatus.SKIPPED
    )
    total_sessions = completed_sessions + skipped_sessions
    skip_rate = (
        Decimal(skipped_sessions) / Decimal(total_sessions)
        if total_sessions > 0
        else Decimal("0")
    )

    consistency_score = compute_consistency_score_v1(
        completed_sessions=completed_sessions,
        planned_sessions=planned_sessions,
    )
    discipline_score = compute_discipline_score_v1(skip_rate=skip_rate)
    revision_adherence_score = compute_revision_adherence_score_v1(executions)
    weakness_recovery_score = compute_weakness_recovery_score_v1(inputs.intervention_outcomes)
    engagement_score = compute_engagement_score_v1(executions)
    average_session_minutes = _average_completed_session_minutes(executions)
    learning_style = classify_learning_style_v1(
        consistency_score=consistency_score,
        average_session_minutes=average_session_minutes,
        effectiveness_by_type=inputs.effectiveness_by_type,
    )
    risk_profile = classify_risk_profile_v1(consistency_score=consistency_score)

    return BehaviorProfile(
        consistency_score=consistency_score,
        discipline_score=discipline_score,
        revision_adherence_score=revision_adherence_score,
        weakness_recovery_score=weakness_recovery_score,
        engagement_score=engagement_score,
        learning_style=learning_style,
        risk_profile=risk_profile,
    )
