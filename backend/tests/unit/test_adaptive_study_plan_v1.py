from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from prepos.domain.study_plan.adaptive_priority_v1 import compute_adaptive_priority_v1
from prepos.domain.study_plan.behavior_metrics_v1 import (
    ConceptBehaviorStats,
    StudyBehaviorMetrics,
    compute_study_behavior_metrics,
)
from prepos.domain.study_plan.entities import StudyPlanExecutionRecord
from prepos.domain.study_plan.plan_adjustment_explanations_v1 import explain_plan_adjustment_v1
from prepos.domain.study_plan.plan_generator_v1 import PlanGeneratorInputs, generate_study_plan_v1
from prepos.domain.study_plan.value_objects import ActivityType, ExecutionStatus
from prepos.domain.twin.entities import TwinRecommendation
from prepos.domain.twin.value_objects import RecommendationType


def test_adaptive_priority_formula() -> None:
    result = compute_adaptive_priority_v1(
        priority_score=Decimal("80"),
        completion_rate=Decimal("0.50"),
        skip_rate=Decimal("0.20"),
    )
    expected = Decimal("80") * Decimal("1.20") * Decimal("0.875")
    assert result == Decimal("84.00")
    assert expected == Decimal("84.00")


def test_completion_lowers_urgency() -> None:
    baseline = compute_adaptive_priority_v1(
        priority_score=Decimal("80"),
        completion_rate=Decimal("0"),
        skip_rate=Decimal("0"),
    )
    with_completion = compute_adaptive_priority_v1(
        priority_score=Decimal("80"),
        completion_rate=Decimal("1"),
        skip_rate=Decimal("0"),
    )
    assert with_completion < baseline
    assert with_completion == Decimal("60.00")


def test_skipping_increases_urgency() -> None:
    baseline = compute_adaptive_priority_v1(
        priority_score=Decimal("80"),
        completion_rate=Decimal("0"),
        skip_rate=Decimal("0"),
    )
    with_skips = compute_adaptive_priority_v1(
        priority_score=Decimal("80"),
        completion_rate=Decimal("0"),
        skip_rate=Decimal("0.50"),
    )
    assert with_skips > baseline
    assert with_skips == Decimal("100.00")


def _execution(
    *,
    concept_id: str,
    status: ExecutionStatus,
    planned: int = 20,
    actual: int = 20,
) -> StudyPlanExecutionRecord:
    now = datetime(2026, 6, 18, tzinfo=UTC)
    return StudyPlanExecutionRecord(
        id=uuid4(),
        tenant_id=uuid4(),
        student_id=uuid4(),
        exam_id="neet",
        concept_id=concept_id,
        activity_type=ActivityType.REVISION,
        planned_minutes=planned,
        actual_minutes=actual,
        status=status,
        completed_at=now,
    )


def test_execution_metrics_aggregate() -> None:
    records = (
        _execution(concept_id="a", status=ExecutionStatus.COMPLETED, planned=20, actual=30),
        _execution(concept_id="a", status=ExecutionStatus.SKIPPED),
        _execution(concept_id="b", status=ExecutionStatus.COMPLETED),
    )
    metrics = compute_study_behavior_metrics(records)

    assert metrics.completion_rate == Decimal("0.6667")
    assert metrics.skip_rate == Decimal("0.3333")
    assert metrics.by_concept["a"].skip_rate == Decimal("0.5000")
    assert metrics.average_minutes_variance == Decimal("0.2500")


def test_explain_skipped_sessions() -> None:
    behavior = ConceptBehaviorStats(
        completion_rate=Decimal("0"),
        skip_rate=Decimal("1"),
        average_minutes_variance=Decimal("0"),
    )
    explanation = explain_plan_adjustment_v1(
        priority_score=Decimal("70"),
        adaptive_priority=Decimal("87.50"),
        readiness_gain=Decimal("3"),
        behavior=behavior,
    )
    assert explanation == "Moved higher because previous sessions were skipped."


def test_explain_consistent_completion() -> None:
    behavior = ConceptBehaviorStats(
        completion_rate=Decimal("1"),
        skip_rate=Decimal("0"),
        average_minutes_variance=Decimal("0"),
    )
    explanation = explain_plan_adjustment_v1(
        priority_score=Decimal("80"),
        adaptive_priority=Decimal("60"),
        readiness_gain=Decimal("3"),
        behavior=behavior,
    )
    assert explanation == "Priority reduced because you consistently complete revisions."


def test_plan_reorders_after_skip_history() -> None:
    now = datetime(2026, 6, 18, tzinfo=UTC)
    skipped_metrics = StudyBehaviorMetrics(
        completion_rate=Decimal("0"),
        skip_rate=Decimal("1"),
        average_minutes_variance=Decimal("0"),
        by_concept={
            "often-skipped": ConceptBehaviorStats(
                completion_rate=Decimal("0"),
                skip_rate=Decimal("1"),
                average_minutes_variance=Decimal("0"),
            ),
        },
    )
    plan = generate_study_plan_v1(
        PlanGeneratorInputs(
            tenant_id=uuid4(),
            student_id=uuid4(),
            exam_id="neet",
            recommendations=(
                TwinRecommendation(
                    concept_id="stable",
                    recommendation_type=RecommendationType.WEAKNESS_RECOVERY.value,
                    recommendation_score=Decimal("80"),
                    importance_score=Decimal("80"),
                    weakness_score=Decimal("70"),
                    retention_score=Decimal("50"),
                    readiness_gain=Decimal("8"),
                    explanation="test",
                ),
                TwinRecommendation(
                    concept_id="often-skipped",
                    recommendation_type=RecommendationType.WEAKNESS_RECOVERY.value,
                    recommendation_score=Decimal("80"),
                    importance_score=Decimal("80"),
                    weakness_score=Decimal("70"),
                    retention_score=Decimal("50"),
                    readiness_gain=Decimal("4"),
                    explanation="test",
                ),
            ),
            revision_queue=(),
            readiness_snapshot=None,
            behavior_metrics=skipped_metrics,
            generated_at=now,
        )
    )

    assert plan.daily_plan[0].concept_id == "often-skipped"
    assert plan.daily_plan[0].adaptive_priority > Decimal("80")
