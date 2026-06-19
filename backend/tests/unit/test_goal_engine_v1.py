from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import uuid4

from prepos.domain.goal.adaptive_capacity_v1 import compute_adaptive_capacity_v1
from prepos.domain.goal.forecast_explanations_v1 import explain_forecast_v1
from prepos.domain.scoring.readiness_forecast_v1 import ReadinessForecastInputs, compute_readiness_forecast_v1
from prepos.domain.study_plan.plan_generator_v1 import DEFAULT_DAILY_MINUTES, PlanGeneratorInputs, generate_daily_plan
from prepos.domain.twin.entities import TwinRecommendation
from prepos.domain.twin.value_objects import RecommendationType


def test_forecast_formula() -> None:
    result = compute_readiness_forecast_v1(
        ReadinessForecastInputs(
            current_readiness=Decimal("71.5"),
            total_estimated_gain=Decimal("10"),
            target_readiness_score=Decimal("85"),
            target_date=date(2026, 9, 1),
            current_time=datetime(2026, 6, 18, tzinfo=UTC),
        )
    )

    assert result.days_remaining == 75
    assert result.projected_readiness == Decimal("81.50")
    assert result.gap_to_goal == Decimal("3.50")
    assert result.on_track is False


def test_gap_calculation_when_on_track() -> None:
    result = compute_readiness_forecast_v1(
        ReadinessForecastInputs(
            current_readiness=Decimal("80"),
            total_estimated_gain=Decimal("10"),
            target_readiness_score=Decimal("85"),
            target_date=date(2026, 9, 1),
            current_time=datetime(2026, 6, 18, tzinfo=UTC),
        )
    )

    assert result.projected_readiness >= Decimal("85")
    assert result.gap_to_goal == Decimal("0.00")
    assert result.on_track is True


def test_on_track_detection() -> None:
    below = compute_readiness_forecast_v1(
        ReadinessForecastInputs(
            current_readiness=Decimal("60"),
            total_estimated_gain=Decimal("5"),
            target_readiness_score=Decimal("85"),
            target_date=date(2026, 7, 1),
            current_time=datetime(2026, 6, 18, tzinfo=UTC),
        )
    )
    assert below.on_track is False

    above = compute_readiness_forecast_v1(
        ReadinessForecastInputs(
            current_readiness=Decimal("90"),
            total_estimated_gain=Decimal("2"),
            target_readiness_score=Decimal("85"),
            target_date=date(2026, 7, 1),
            current_time=datetime(2026, 6, 18, tzinfo=UTC),
        )
    )
    assert above.on_track is True


def test_adaptive_capacity_scaling() -> None:
    assert compute_adaptive_capacity_v1(
        base_capacity_minutes=120,
        gap_to_goal=Decimal("25"),
        on_track=False,
    ) == 180
    assert compute_adaptive_capacity_v1(
        base_capacity_minutes=120,
        gap_to_goal=Decimal("15"),
        on_track=False,
    ) == 150
    assert compute_adaptive_capacity_v1(
        base_capacity_minutes=120,
        gap_to_goal=Decimal("0"),
        on_track=True,
    ) == 120


def test_adaptive_capacity_clamped() -> None:
    assert compute_adaptive_capacity_v1(
        base_capacity_minutes=250,
        gap_to_goal=Decimal("30"),
        on_track=False,
    ) == 300
    assert compute_adaptive_capacity_v1(
        base_capacity_minutes=30,
        gap_to_goal=Decimal("0"),
        on_track=True,
    ) == 30


def test_study_plan_capacity_increase() -> None:
    now = datetime(2026, 6, 18, tzinfo=UTC)
    recommendations = tuple(
        TwinRecommendation(
            concept_id=f"concept-{index}",
            recommendation_type=RecommendationType.WEAKNESS_RECOVERY.value,
            recommendation_score=Decimal("80"),
            importance_score=Decimal("80"),
            weakness_score=Decimal("70"),
            retention_score=Decimal("50"),
            readiness_gain=Decimal("5"),
            explanation="test",
        )
        for index in range(8)
    )
    default_plan = generate_daily_plan(
        PlanGeneratorInputs(
            tenant_id=uuid4(),
            student_id=uuid4(),
            exam_id="neet",
            recommendations=recommendations,
            revision_queue=(),
            readiness_snapshot=None,
            generated_at=now,
            default_daily_minutes=DEFAULT_DAILY_MINUTES,
        )
    )
    expanded_plan = generate_daily_plan(
        PlanGeneratorInputs(
            tenant_id=uuid4(),
            student_id=uuid4(),
            exam_id="neet",
            recommendations=recommendations,
            revision_queue=(),
            readiness_snapshot=None,
            generated_at=now,
            default_daily_minutes=180,
        )
    )

    assert sum(item.estimated_minutes for item in expanded_plan) > sum(
        item.estimated_minutes for item in default_plan
    )


def test_forecast_explanation_projected() -> None:
    explanation = explain_forecast_v1(
        projected_readiness=Decimal("81.2"),
        target_readiness_score=Decimal("85"),
        on_track=False,
        gap_to_goal=Decimal("3.8"),
        base_capacity_minutes=120,
        adaptive_capacity_minutes=120,
    )
    assert explanation == "You are projected to reach 81.2 readiness before the exam."


def test_forecast_explanation_capacity_increase() -> None:
    explanation = explain_forecast_v1(
        projected_readiness=Decimal("70"),
        target_readiness_score=Decimal("85"),
        on_track=False,
        gap_to_goal=Decimal("15"),
        base_capacity_minutes=120,
        adaptive_capacity_minutes=150,
    )
    assert explanation == "Increase study time by 30 minutes/day to stay on track."


def test_forecast_explanation_exceeds_target() -> None:
    explanation = explain_forecast_v1(
        projected_readiness=Decimal("90"),
        target_readiness_score=Decimal("85"),
        on_track=True,
        gap_to_goal=Decimal("0"),
        base_capacity_minutes=120,
        adaptive_capacity_minutes=120,
    )
    assert explanation == "Current trajectory exceeds your target."
