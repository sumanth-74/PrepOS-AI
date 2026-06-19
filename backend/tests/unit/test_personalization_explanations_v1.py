from __future__ import annotations

from decimal import Decimal

from prepos.domain.study_plan.value_objects import ActivityType
from prepos.domain.twin.behavior_profile_types_v1 import LearningStyle
from prepos.domain.twin.personalization_explanations_v1 import (
    explain_personalization_summary_v1,
    explain_personalized_score_v1,
)
from prepos.domain.twin.personalized_scoring_v1 import PersonalizedScore


def test_explain_personalized_score_weakness_recovery() -> None:
    explanation = explain_personalized_score_v1(
        activity_type=ActivityType.WEAKNESS_RECOVERY,
        personalized_score=PersonalizedScore(
            base_score=Decimal("70"),
            personalization_multiplier=Decimal("1.30"),
            personalized_score=Decimal("91.00"),
            explanation="",
        ),
    )
    assert explanation == (
        "Weakness recovery activities have produced the highest gains historically."
    )


def test_explain_personalized_score_revision() -> None:
    explanation = explain_personalized_score_v1(
        activity_type=ActivityType.REVISION,
        personalized_score=PersonalizedScore(
            base_score=Decimal("70"),
            personalization_multiplier=Decimal("1.20"),
            personalized_score=Decimal("84.00"),
            explanation="",
        ),
    )
    assert explanation == "Short revision sessions align with your study behavior."


def test_explain_personalization_summary_recovery_driven() -> None:
    explanation = explain_personalization_summary_v1(
        learning_style=LearningStyle.RECOVERY_DRIVEN,
        best_activity_type=ActivityType.WEAKNESS_RECOVERY,
    )
    assert explanation == (
        "Study plans now emphasize weakness remediation because it has shown stronger outcomes."
    )
