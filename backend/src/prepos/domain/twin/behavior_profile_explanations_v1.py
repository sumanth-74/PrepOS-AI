from __future__ import annotations

from decimal import Decimal

from prepos.domain.scoring.common import round_score
from prepos.domain.twin.behavior_profile_types_v1 import LearningStyle, RiskProfile

BEHAVIOR_PROFILE_EXPLANATIONS_V1 = "behavior_profile_explanations_v1"


def explain_behavior_profile_v1(
    *,
    learning_style: LearningStyle,
    risk_profile: RiskProfile,
    consistency_score: Decimal,
    revision_adherence_score: Decimal,
) -> str:
    if learning_style == LearningStyle.CONSISTENT_LEARNER:
        return "You consistently complete planned sessions."
    if learning_style == LearningStyle.SHORT_BURST_LEARNER:
        return "Short study sessions appear most effective."
    if learning_style == LearningStyle.DEEP_FOCUS_LEARNER:
        return "Longer focused study blocks appear most effective."
    if learning_style == LearningStyle.RECOVERY_DRIVEN:
        return "Weakness recovery interventions are outperforming other strategies."
    if revision_adherence_score < Decimal("50"):
        return "Revision adherence has declined recently."
    if risk_profile == RiskProfile.HIGH_RISK:
        return (
            f"Study consistency is low at {round_score(consistency_score):.2f}%; "
            "increasing session completion should improve outcomes."
        )
    return "Your study behavior profile is balanced across session types."
