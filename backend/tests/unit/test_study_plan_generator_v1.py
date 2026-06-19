from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from prepos.domain.learning_graph.entities import ConceptProgressNode, LearningGraphReadinessSnapshot
from prepos.domain.learning_graph.policies import NodeStatus
from prepos.domain.revision_queue.entities import RevisionQueueItem
from prepos.domain.revision_queue.value_objects import RevisionQueueStatus
from prepos.domain.study_plan.plan_generator_v1 import (
    DEFAULT_DAILY_MINUTES,
    PlanGeneratorInputs,
    generate_daily_plan,
    generate_study_plan_v1,
)
from prepos.domain.study_plan.value_objects import ActivityType
from prepos.domain.twin.entities import TwinRecommendation
from prepos.domain.twin.value_objects import RecommendationType


def _node(*, concept_id: str, importance: Decimal = Decimal("80")) -> ConceptProgressNode:
    now = datetime(2026, 6, 18, tzinfo=UTC)
    return ConceptProgressNode(
        id=uuid4(),
        tenant_id=uuid4(),
        student_id=uuid4(),
        exam_id="neet",
        catalog_version="v1",
        concept_id=concept_id,
        subject_id="subject-a",
        topic_id="topic-a",
        mastery_score=Decimal("40"),
        mastery_nonmcq_score=Decimal("0"),
        retention_score=Decimal("100"),
        retention_stability_s=Decimal("30"),
        retention_last_review_at=now,
        retention_last_grade=2,
        confidence_score=Decimal("60"),
        importance_score=importance,
        overconfidence_flag=False,
        mcq_attempt_count=1,
        mcq_correct_count=0,
        nonmcq_attempt_count=0,
        revision_count=1,
        study_minutes=0,
        node_state=NodeStatus.RATED,
        mastery_version="mastery_v1",
        mastery_nonmcq_version="mastery_nonmcq_v1",
        retention_version="retention_v1",
        confidence_version="confidence_v1",
        importance_version="importance_copy_v1",
        first_seen_at=now,
        last_activity_at=now,
        row_version=1,
    )


def _recommendation(
    *,
    concept_id: str,
    recommendation_type: RecommendationType,
    readiness_gain: Decimal,
    score: Decimal = Decimal("80"),
) -> TwinRecommendation:
    return TwinRecommendation(
        concept_id=concept_id,
        recommendation_type=recommendation_type.value,
        recommendation_score=score,
        importance_score=Decimal("80"),
        weakness_score=Decimal("70"),
        retention_score=Decimal("50"),
        readiness_gain=readiness_gain,
        explanation="test",
    )


def _queue_item(*, concept_id: str) -> RevisionQueueItem:
    now = datetime(2026, 6, 18, tzinfo=UTC)
    return RevisionQueueItem(
        id=uuid4(),
        tenant_id=uuid4(),
        student_id=uuid4(),
        exam_id="neet",
        concept_id=concept_id,
        next_review_at=now - timedelta(days=1),
        retention_score=Decimal("40"),
        importance_score=Decimal("70"),
        weakness_score=Decimal("60"),
        priority_score=Decimal("75"),
        status=RevisionQueueStatus.DUE,
        created_at=now,
        updated_at=now,
    )


def test_daily_plan_respects_capacity() -> None:
    now = datetime(2026, 6, 18, tzinfo=UTC)
    recommendations = tuple(
        _recommendation(
            concept_id=f"concept-{index}",
            recommendation_type=RecommendationType.WEAKNESS_RECOVERY,
            readiness_gain=Decimal(str(5 - index)),
        )
        for index in range(6)
    )
    inputs = PlanGeneratorInputs(
        tenant_id=uuid4(),
        student_id=uuid4(),
        exam_id="neet",
        recommendations=recommendations,
        revision_queue=(),
        readiness_snapshot=None,
        generated_at=now,
    )

    daily = generate_daily_plan(inputs)
    total_minutes = sum(item.estimated_minutes for item in daily)

    assert total_minutes <= DEFAULT_DAILY_MINUTES
    assert len(daily) >= 1


def test_daily_plan_prioritizes_higher_readiness_gain_when_adaptive_equal() -> None:
    now = datetime(2026, 6, 18, tzinfo=UTC)
    inputs = PlanGeneratorInputs(
        tenant_id=uuid4(),
        student_id=uuid4(),
        exam_id="neet",
        recommendations=(
            _recommendation(
                concept_id="boost",
                recommendation_type=RecommendationType.READINESS_BOOST,
                readiness_gain=Decimal("9"),
            ),
            _recommendation(
                concept_id="revision",
                recommendation_type=RecommendationType.REVISION_DUE,
                readiness_gain=Decimal("4"),
            ),
        ),
        revision_queue=(),
        readiness_snapshot=None,
        generated_at=now,
    )

    daily = generate_study_plan_v1(inputs).daily_plan

    assert daily[0].concept_id == "boost"
    assert daily[0].readiness_gain == Decimal("9")


def test_weekly_plan_accumulates_readiness_gain() -> None:
    now = datetime(2026, 6, 18, tzinfo=UTC)
    plan = generate_study_plan_v1(
        PlanGeneratorInputs(
            tenant_id=uuid4(),
            student_id=uuid4(),
            exam_id="neet",
            recommendations=(
                _recommendation(
                    concept_id="weak",
                    recommendation_type=RecommendationType.WEAKNESS_RECOVERY,
                    readiness_gain=Decimal("3"),
                ),
            ),
            revision_queue=(),
            readiness_snapshot=LearningGraphReadinessSnapshot(
                average_mastery=Decimal("50"),
                average_retention=Decimal("50"),
                average_confidence=Decimal("50"),
                rated_node_count=1,
                total_node_count=1,
            ),
            generated_at=now,
        )
    )

    assert plan.weekly_plan[0].target_sessions == 2
    assert plan.weekly_plan[0].readiness_gain == Decimal("6.00")
    assert plan.total_estimated_gain == Decimal("6.00")


def test_revision_queue_supplements_missing_recommendations() -> None:
    now = datetime(2026, 6, 18, tzinfo=UTC)
    plan = generate_study_plan_v1(
        PlanGeneratorInputs(
            tenant_id=uuid4(),
            student_id=uuid4(),
            exam_id="neet",
            recommendations=(),
            revision_queue=(_queue_item(concept_id="queue-only"),),
            readiness_snapshot=None,
            generated_at=now,
            default_daily_minutes=120,
        )
    )

    assert plan.daily_plan[0].concept_id == "queue-only"
    assert plan.daily_plan[0].activity_type == ActivityType.REVISION
