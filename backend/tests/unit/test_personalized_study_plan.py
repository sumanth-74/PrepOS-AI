from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from prepos.domain.learning_graph.entities import ConceptProgressNode, LearningGraphReadinessSnapshot
from prepos.domain.learning_graph.policies import NodeStatus
from prepos.domain.study_plan.plan_generator_v1 import (
    PlanGeneratorInputs,
    session_minutes_for_activity,
)
from prepos.domain.study_plan.value_objects import ActivityType
from prepos.domain.twin.behavior_profile_types_v1 import LearningStyle
from prepos.domain.twin.entities import TwinRecommendation
from prepos.domain.twin.value_objects import RecommendationType


def _recommendation(*, concept_id: str, recommendation_type: RecommendationType) -> TwinRecommendation:
    return TwinRecommendation(
        concept_id=concept_id,
        recommendation_type=recommendation_type.value,
        recommendation_score=Decimal("80"),
        importance_score=Decimal("70"),
        weakness_score=Decimal("75"),
        retention_score=Decimal("50"),
        readiness_gain=Decimal("4"),
        explanation="test",
    )


def test_short_burst_session_length() -> None:
    minutes = session_minutes_for_activity(
        ActivityType.REVISION,
        learning_style=LearningStyle.SHORT_BURST_LEARNER,
    )
    assert 15 <= minutes <= 20


def test_deep_focus_session_length() -> None:
    minutes = session_minutes_for_activity(
        ActivityType.HIGH_IMPORTANCE_STUDY,
        learning_style=LearningStyle.DEEP_FOCUS_LEARNER,
    )
    assert 45 <= minutes <= 60


def test_recovery_driven_allocates_more_weakness_recovery_time() -> None:
    default_minutes = session_minutes_for_activity(ActivityType.WEAKNESS_RECOVERY)
    recovery_minutes = session_minutes_for_activity(
        ActivityType.WEAKNESS_RECOVERY,
        learning_style=LearningStyle.RECOVERY_DRIVEN,
    )
    assert recovery_minutes == int(Decimal(default_minutes) * Decimal("1.30"))


def test_generate_study_plan_uses_learning_style_session_lengths() -> None:
    from prepos.domain.study_plan.plan_generator_v1 import generate_study_plan_v1

    now = datetime(2026, 6, 18, tzinfo=UTC)
    plan = generate_study_plan_v1(
        PlanGeneratorInputs(
            tenant_id=UUID("00000000-0000-0000-0000-000000000010"),
            student_id=UUID("00000000-0000-0000-0000-000000000020"),
            exam_id="neet",
            recommendations=(
                _recommendation(
                    concept_id="concept-a",
                    recommendation_type=RecommendationType.WEAKNESS_RECOVERY,
                ),
            ),
            revision_queue=(),
            readiness_snapshot=LearningGraphReadinessSnapshot(
                average_mastery=Decimal("60"),
                average_retention=Decimal("60"),
                average_confidence=Decimal("60"),
                rated_node_count=1,
                total_node_count=1,
            ),
            generated_at=now,
            learning_style=LearningStyle.SHORT_BURST_LEARNER,
        )
    )
    assert plan.daily_plan[0].estimated_minutes == 18
