from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from prepos.domain.study_plan.entities import StudyPlanExecutionRecord
from prepos.domain.study_plan.value_objects import ActivityType, ExecutionStatus
from prepos.domain.twin.behavior_profile_types_v1 import LearningStyle, RiskProfile
from prepos.domain.twin.behavior_profile_v1 import (
    BehaviorProfileInputs,
    build_behavior_profile_v1,
    classify_learning_style_v1,
    classify_risk_profile_v1,
    compute_consistency_score_v1,
    compute_discipline_score_v1,
    compute_engagement_score_v1,
)
from prepos.domain.twin.intervention_history_entities import StudentInterventionHistoryEntry
from prepos.domain.twin.intervention_types_v1 import TwinInterventionType


def _execution(
    *,
    activity_type: ActivityType = ActivityType.HIGH_IMPORTANCE_STUDY,
    status: ExecutionStatus = ExecutionStatus.COMPLETED,
    planned_minutes: int = 30,
    actual_minutes: int = 30,
) -> StudyPlanExecutionRecord:
    return StudyPlanExecutionRecord(
        id=uuid4(),
        tenant_id=uuid4(),
        student_id=uuid4(),
        exam_id="neet",
        concept_id="concept-a",
        activity_type=activity_type,
        planned_minutes=planned_minutes,
        actual_minutes=actual_minutes,
        status=status,
        completed_at=datetime(2026, 6, 18, tzinfo=UTC),
    )


def test_consistency_score_formula() -> None:
    score = compute_consistency_score_v1(completed_sessions=4, planned_sessions=5)
    assert score == Decimal("80.00")


def test_discipline_score_formula() -> None:
    score = compute_discipline_score_v1(skip_rate=Decimal("0.09"))
    assert score == Decimal("91.00")


def test_engagement_score_formula() -> None:
    executions = (
        _execution(planned_minutes=40, actual_minutes=36),
        _execution(planned_minutes=20, actual_minutes=20),
    )
    score = compute_engagement_score_v1(executions)
    assert score == Decimal("93.33")


def test_classify_consistent_learner() -> None:
    style = classify_learning_style_v1(
        consistency_score=Decimal("85"),
        average_session_minutes=Decimal("30"),
        effectiveness_by_type={},
    )
    assert style == LearningStyle.CONSISTENT_LEARNER


def test_classify_short_burst_learner() -> None:
    style = classify_learning_style_v1(
        consistency_score=Decimal("60"),
        average_session_minutes=Decimal("20"),
        effectiveness_by_type={},
    )
    assert style == LearningStyle.SHORT_BURST_LEARNER


def test_classify_recovery_driven() -> None:
    style = classify_learning_style_v1(
        consistency_score=Decimal("60"),
        average_session_minutes=Decimal("30"),
        effectiveness_by_type={
            TwinInterventionType.WEAKNESS_REMEDIATION.value: Decimal("80"),
            TwinInterventionType.REVISION_SPRINT.value: Decimal("40"),
        },
    )
    assert style == LearningStyle.RECOVERY_DRIVEN


def test_classify_risk_profile() -> None:
    assert classify_risk_profile_v1(consistency_score=Decimal("30")) == RiskProfile.HIGH_RISK
    assert classify_risk_profile_v1(consistency_score=Decimal("55")) == RiskProfile.MEDIUM_RISK
    assert classify_risk_profile_v1(consistency_score=Decimal("85")) == RiskProfile.LOW_RISK


def test_build_behavior_profile() -> None:
    now = datetime(2026, 6, 18, tzinfo=UTC)
    outcomes = (
        StudentInterventionHistoryEntry(
            id=uuid4(),
            tenant_id=uuid4(),
            student_id=uuid4(),
            exam_id="neet",
            intervention_type=TwinInterventionType.WEAKNESS_REMEDIATION.value,
            effectiveness_score=Decimal("70"),
            readiness_delta=Decimal("6.2"),
            predicted_score_delta=Decimal("10"),
            completion_delta=Decimal("0.1"),
            outcome_status="EFFECTIVE",
            created_at=now,
        ),
    )
    profile = build_behavior_profile_v1(
        BehaviorProfileInputs(
            executions=(
                _execution(status=ExecutionStatus.COMPLETED),
                _execution(status=ExecutionStatus.COMPLETED),
                _execution(status=ExecutionStatus.SKIPPED),
                _execution(
                    activity_type=ActivityType.REVISION,
                    status=ExecutionStatus.COMPLETED,
                ),
                _execution(
                    activity_type=ActivityType.REVISION,
                    status=ExecutionStatus.SKIPPED,
                ),
            ),
            intervention_outcomes=outcomes,
            effectiveness_by_type={
                TwinInterventionType.WEAKNESS_REMEDIATION.value: Decimal("70"),
            },
        )
    )
    assert profile.consistency_score == Decimal("60.00")
    assert profile.discipline_score == Decimal("60.00")
    assert profile.revision_adherence_score == Decimal("50.00")
    assert profile.weakness_recovery_score == Decimal("6.20")
