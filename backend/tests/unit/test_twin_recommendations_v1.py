from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from prepos.domain.learning_graph.entities import ConceptProgressNode, LearningGraphReadinessSnapshot
from prepos.domain.learning_graph.policies import NodeStatus
from prepos.domain.twin.recommendations_v1 import (
    TwinRecommendationInputs,
    classify_recommendation_type,
    compute_recommendation_score,
    compute_retention_risk,
    compute_revision_due_bonus,
    compute_twin_recommendations_v1,
    explain_recommendation,
)
from prepos.domain.twin.value_objects import RecommendationType


def _node(
    *,
    concept_id: str,
    mastery: Decimal = Decimal("40"),
    importance: Decimal = Decimal("50"),
    retention_stability: Decimal | None = Decimal("30"),
    review_at: datetime | None = None,
) -> ConceptProgressNode:
    now = datetime(2026, 6, 18, 12, 0, tzinfo=UTC)
    review = review_at or now
    return ConceptProgressNode(
        id=UUID("00000000-0000-0000-0000-000000000001"),
        tenant_id=UUID("00000000-0000-0000-0000-000000000010"),
        student_id=UUID("00000000-0000-0000-0000-000000000020"),
        exam_id="upsc-cse",
        catalog_version="v1",
        concept_id=concept_id,
        subject_id="subject-a",
        topic_id="topic-a",
        mastery_score=mastery,
        mastery_nonmcq_score=Decimal("0"),
        retention_score=Decimal("100"),
        retention_stability_s=retention_stability,
        retention_last_review_at=review,
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
        first_seen_at=review,
        last_activity_at=review,
        row_version=1,
    )


def test_recommendation_score_formula() -> None:
    score = compute_recommendation_score(
        importance_score=Decimal("85"),
        weakness_score=Decimal("78"),
        retention_score=Decimal("40"),
        is_due=True,
    )
    assert score == Decimal("79.40")


def test_retention_risk_calculation() -> None:
    assert compute_retention_risk(Decimal("40")) == Decimal("60")
    assert compute_retention_risk(None) == Decimal("100")


def test_revision_due_bonus() -> None:
    assert compute_revision_due_bonus(is_due=True) == Decimal("100")
    assert compute_revision_due_bonus(is_due=False) == Decimal("0")


def test_recommendation_classification_priority() -> None:
    assert (
        classify_recommendation_type(
            is_due=True,
            weakness_score=Decimal("80"),
            importance_score=Decimal("90"),
            mastery_score=Decimal("30"),
        )
        == RecommendationType.REVISION_DUE
    )
    assert (
        classify_recommendation_type(
            is_due=False,
            weakness_score=Decimal("75"),
            importance_score=Decimal("90"),
            mastery_score=Decimal("30"),
        )
        == RecommendationType.WEAKNESS_RECOVERY
    )
    assert (
        classify_recommendation_type(
            is_due=False,
            weakness_score=Decimal("50"),
            importance_score=Decimal("85"),
            mastery_score=Decimal("40"),
        )
        == RecommendationType.HIGH_IMPORTANCE_GAP
    )
    assert (
        classify_recommendation_type(
            is_due=False,
            weakness_score=Decimal("50"),
            importance_score=Decimal("70"),
            mastery_score=Decimal("60"),
        )
        == RecommendationType.READINESS_BOOST
    )


def test_explanation_generation() -> None:
    explanation = explain_recommendation(
        RecommendationType.REVISION_DUE,
        readiness_gain=Decimal("4.20"),
    )
    assert "4.2 points" in explanation
    assert explain_recommendation(
        RecommendationType.WEAKNESS_RECOVERY,
        readiness_gain=Decimal("3.50"),
    ).startswith("This weak concept has high improvement potential")


def test_ranking_order() -> None:
    now = datetime(2026, 6, 18, 12, 0, tzinfo=UTC)
    high = _node(concept_id="concept-high", importance=Decimal("90"))
    low = _node(concept_id="concept-low", importance=Decimal("50"))
    inputs = TwinRecommendationInputs(
        nodes=(low, high),
        weakness_by_concept={
            "concept-high": Decimal("80"),
            "concept-low": Decimal("40"),
        },
        due_concept_ids=frozenset({"concept-high"}),
        readiness_snapshot=LearningGraphReadinessSnapshot(
            average_mastery=Decimal("50"),
            average_retention=Decimal("70"),
            average_confidence=Decimal("60"),
            rated_node_count=2,
            total_node_count=10,
        ),
        readiness_result=None,
        readiness_drivers=None,
        current_time=now,
    )

    recommendations = compute_twin_recommendations_v1(inputs)

    assert recommendations[0].concept_id == "concept-high"
    assert recommendations[0].readiness_gain >= recommendations[1].readiness_gain


def test_ranking_prefers_readiness_gain_over_recommendation_score() -> None:
    now = datetime(2026, 6, 18, 12, 0, tzinfo=UTC)
    high_score_low_gain = _node(concept_id="aaa", importance=Decimal("90"))
    lower_score_high_gain = _node(concept_id="bbb", importance=Decimal("60"), mastery=Decimal("20"))
    inputs = TwinRecommendationInputs(
        nodes=(high_score_low_gain, lower_score_high_gain),
        weakness_by_concept={
            "aaa": Decimal("30"),
            "bbb": Decimal("95"),
        },
        due_concept_ids=frozenset({"aaa"}),
        readiness_snapshot=LearningGraphReadinessSnapshot(
            average_mastery=Decimal("50"),
            average_retention=Decimal("70"),
            average_confidence=Decimal("60"),
            rated_node_count=2,
            total_node_count=10,
        ),
        readiness_result=None,
        readiness_drivers=None,
        current_time=now,
    )

    recommendations = compute_twin_recommendations_v1(inputs)

    assert recommendations[0].concept_id == "bbb"
    assert recommendations[0].readiness_gain >= recommendations[1].readiness_gain


def test_due_revision_type_when_overdue() -> None:
    now = datetime(2026, 6, 18, 12, 0, tzinfo=UTC)
    overdue = _node(
        concept_id="due-concept",
        review_at=now - timedelta(days=40),
        retention_stability=Decimal("10"),
    )
    recommendations = compute_twin_recommendations_v1(
        TwinRecommendationInputs(
            nodes=(overdue,),
            weakness_by_concept={"due-concept": Decimal("55")},
            due_concept_ids=frozenset({"due-concept"}),
            readiness_snapshot=LearningGraphReadinessSnapshot(
                average_mastery=Decimal("40"),
                average_retention=Decimal("50"),
                average_confidence=Decimal("60"),
                rated_node_count=1,
                total_node_count=5,
            ),
            readiness_result=None,
            readiness_drivers=None,
            current_time=now,
        )
    )

    assert recommendations[0].recommendation_type == RecommendationType.REVISION_DUE.value
    assert recommendations[0].readiness_gain > Decimal("0")
