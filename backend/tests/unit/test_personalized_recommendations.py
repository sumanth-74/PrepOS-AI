from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from prepos.domain.learning_graph.entities import ConceptProgressNode, LearningGraphReadinessSnapshot
from prepos.domain.learning_graph.policies import NodeStatus
from prepos.domain.scoring.readiness_v1_1 import READINESS_V1_1, ReadinessResultV1_1
from prepos.domain.study_plan.value_objects import ActivityType
from prepos.domain.twin.behavior_profile_types_v1 import LearningStyle, RiskProfile
from prepos.domain.twin.personalized_scoring_v1 import PersonalizationContext
from prepos.domain.twin.recommendations_v1 import TwinRecommendationInputs, compute_twin_recommendations_v1


def _node(*, concept_id: str, importance: Decimal, mastery: Decimal) -> ConceptProgressNode:
    now = datetime(2026, 6, 18, tzinfo=UTC)
    return ConceptProgressNode(
        id=UUID("00000000-0000-0000-0000-000000000001"),
        tenant_id=UUID("00000000-0000-0000-0000-000000000010"),
        student_id=UUID("00000000-0000-0000-0000-000000000020"),
        exam_id="neet",
        catalog_version="v1",
        concept_id=concept_id,
        subject_id="subject-a",
        topic_id="topic-a",
        mastery_score=mastery,
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


def test_personalized_ranking_prefers_higher_personalized_score() -> None:
    now = datetime(2026, 6, 18, tzinfo=UTC)
    readiness = LearningGraphReadinessSnapshot(
        average_mastery=Decimal("60"),
        average_retention=Decimal("60"),
        average_confidence=Decimal("60"),
        rated_node_count=2,
        total_node_count=2,
    )
    readiness_result = ReadinessResultV1_1(
        overall_score=Decimal("60"),
        knowledge_subscore=Decimal("60"),
        retention_subscore=Decimal("60"),
        confidence_subscore=Decimal("60"),
        coverage_subscore=Decimal("60"),
        rated_node_count=2,
        total_node_count=2,
        unrated=False,
        version=READINESS_V1_1,
    )
    recommendations = compute_twin_recommendations_v1(
        TwinRecommendationInputs(
            nodes=(
                _node(concept_id="concept-a", importance=Decimal("90"), mastery=Decimal("20")),
                _node(concept_id="concept-b", importance=Decimal("50"), mastery=Decimal("20")),
            ),
            weakness_by_concept={
                "concept-a": Decimal("80"),
                "concept-b": Decimal("80"),
            },
            due_concept_ids=frozenset({"concept-b"}),
            readiness_snapshot=readiness,
            readiness_result=readiness_result,
            readiness_drivers=None,
            current_time=now,
            personalization=PersonalizationContext(
                learning_style=LearningStyle.SHORT_BURST_LEARNER,
                risk_profile=RiskProfile.HIGH_RISK,
                effectiveness_by_activity={
                    ActivityType.REVISION.value: Decimal("60"),
                    ActivityType.WEAKNESS_RECOVERY.value: Decimal("20"),
                },
            ),
        )
    )
    assert recommendations[0].concept_id == "concept-b"
