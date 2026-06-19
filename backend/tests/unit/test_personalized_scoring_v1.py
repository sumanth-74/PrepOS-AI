from __future__ import annotations

from decimal import Decimal

from datetime import UTC, datetime
from uuid import UUID

from prepos.domain.study_plan.value_objects import ActivityType
from prepos.domain.twin.behavior_profile_types_v1 import LearningStyle, RiskProfile
from prepos.domain.twin.personalized_scoring_v1 import (
    build_effectiveness_by_activity,
    compute_personalization_multiplier,
    compute_personalized_score_v1,
    historical_effectiveness_multiplier,
    learning_style_multiplier,
    risk_score_adjustment,
    select_best_activity_type,
)
from prepos.domain.twin.intervention_history_entities import StudentInterventionHistoryEntry


def test_learning_style_multiplier_short_burst_revision() -> None:
    multiplier = learning_style_multiplier(
        learning_style=LearningStyle.SHORT_BURST_LEARNER,
        activity_type=ActivityType.REVISION,
    )
    assert multiplier == Decimal("1.20")


def test_learning_style_multiplier_recovery_driven_weakness() -> None:
    multiplier = learning_style_multiplier(
        learning_style=LearningStyle.RECOVERY_DRIVEN,
        activity_type=ActivityType.WEAKNESS_RECOVERY,
    )
    assert multiplier == Decimal("1.30")


def test_historical_effectiveness_multiplier_example() -> None:
    assert historical_effectiveness_multiplier(historical_effectiveness=Decimal("60")) == Decimal("1.30")


def test_risk_score_adjustments() -> None:
    assert risk_score_adjustment(risk_profile=RiskProfile.HIGH_RISK) == Decimal("15")
    assert risk_score_adjustment(risk_profile=RiskProfile.MEDIUM_RISK) == Decimal("5")
    assert risk_score_adjustment(risk_profile=RiskProfile.LOW_RISK) == Decimal("0")


def test_personalized_score_formula() -> None:
    result = compute_personalized_score_v1(
        base_score=Decimal("70"),
        learning_style=LearningStyle.RECOVERY_DRIVEN,
        risk_profile=RiskProfile.MEDIUM_RISK,
        activity_type=ActivityType.WEAKNESS_RECOVERY,
        historical_effectiveness=Decimal("60"),
    )
    assert result.personalization_multiplier == Decimal("1.69")
    assert result.personalized_score == Decimal("100.00")


def test_build_effectiveness_by_activity_averages_by_mapped_activity() -> None:
    outcomes = (
        StudentInterventionHistoryEntry(
            id=UUID("00000000-0000-0000-0000-000000000001"),
            tenant_id=UUID("00000000-0000-0000-0000-000000000010"),
            student_id=UUID("00000000-0000-0000-0000-000000000020"),
            exam_id="neet",
            intervention_type="WEAKNESS_REMEDIATION",
            effectiveness_score=Decimal("60"),
            readiness_delta=Decimal("1"),
            predicted_score_delta=Decimal("1"),
            completion_delta=Decimal("0.1"),
            outcome_status="EFFECTIVE",
            created_at=datetime.now(UTC),
        ),
        StudentInterventionHistoryEntry(
            id=UUID("00000000-0000-0000-0000-000000000002"),
            tenant_id=UUID("00000000-0000-0000-0000-000000000010"),
            student_id=UUID("00000000-0000-0000-0000-000000000020"),
            exam_id="neet",
            intervention_type="REVISION_SPRINT",
            effectiveness_score=Decimal("40"),
            readiness_delta=Decimal("1"),
            predicted_score_delta=Decimal("1"),
            completion_delta=Decimal("0.1"),
            outcome_status="EFFECTIVE",
            created_at=datetime.now(UTC),
        ),
    )
    effectiveness = build_effectiveness_by_activity(outcomes)
    assert effectiveness["WEAKNESS_RECOVERY"] == Decimal("60.00")
    assert effectiveness["REVISION"] == Decimal("40.00")


def test_select_best_activity_type_prefers_highest_effectiveness() -> None:
    activity, effectiveness, multiplier = select_best_activity_type(
        learning_style=LearningStyle.BALANCED,
        effectiveness_by_activity={
            "WEAKNESS_RECOVERY": Decimal("72.4"),
            "REVISION": Decimal("40"),
        },
    )
    assert activity == ActivityType.WEAKNESS_RECOVERY
    assert effectiveness == Decimal("72.4")
    assert multiplier == Decimal("1.362")


def test_combined_multiplier_uses_style_and_history() -> None:
    multiplier = compute_personalization_multiplier(
        learning_style=LearningStyle.SHORT_BURST_LEARNER,
        activity_type=ActivityType.REVISION,
        historical_effectiveness=Decimal("60"),
    )
    assert multiplier == Decimal("1.5600")
