from __future__ import annotations

from decimal import Decimal

from prepos.domain.twin.behavior_profile_explanations_v1 import explain_behavior_profile_v1
from prepos.domain.twin.behavior_profile_types_v1 import LearningStyle, RiskProfile


def test_consistent_learner_explanation() -> None:
    explanation = explain_behavior_profile_v1(
        learning_style=LearningStyle.CONSISTENT_LEARNER,
        risk_profile=RiskProfile.LOW_RISK,
        consistency_score=Decimal("85"),
        revision_adherence_score=Decimal("80"),
    )
    assert explanation == "You consistently complete planned sessions."


def test_short_burst_explanation() -> None:
    explanation = explain_behavior_profile_v1(
        learning_style=LearningStyle.SHORT_BURST_LEARNER,
        risk_profile=RiskProfile.MEDIUM_RISK,
        consistency_score=Decimal("60"),
        revision_adherence_score=Decimal("70"),
    )
    assert explanation == "Short study sessions appear most effective."


def test_revision_decline_explanation() -> None:
    explanation = explain_behavior_profile_v1(
        learning_style=LearningStyle.BALANCED,
        risk_profile=RiskProfile.LOW_RISK,
        consistency_score=Decimal("75"),
        revision_adherence_score=Decimal("40"),
    )
    assert explanation == "Revision adherence has declined recently."
