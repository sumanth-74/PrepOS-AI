from __future__ import annotations

from prepos.domain.study_plan.value_objects import ActivityType
from prepos.domain.twin.behavior_profile_types_v1 import LearningStyle
from prepos.domain.twin.personalized_scoring_v1 import PersonalizedScore

PERSONALIZATION_EXPLANATIONS_V1 = "personalization_explanations_v1"


def explain_personalized_score_v1(
    *,
    activity_type: ActivityType,
    personalized_score: PersonalizedScore,
) -> str:
    if activity_type == ActivityType.WEAKNESS_RECOVERY:
        return "Weakness recovery activities have produced the highest gains historically."
    if activity_type == ActivityType.REVISION:
        return "Short revision sessions align with your study behavior."
    return "Personalized ranking reflects your learning style and historical outcomes."


def explain_personalization_summary_v1(
    *,
    learning_style: LearningStyle,
    best_activity_type: ActivityType,
) -> str:
    if learning_style == LearningStyle.RECOVERY_DRIVEN:
        return (
            "Study plans now emphasize weakness remediation because it has shown stronger outcomes."
        )
    if learning_style == LearningStyle.SHORT_BURST_LEARNER and best_activity_type == ActivityType.REVISION:
        return "Short revision sessions align with your study behavior."
    if best_activity_type == ActivityType.WEAKNESS_RECOVERY:
        return "Weakness recovery activities have produced the highest gains historically."
    return "Recommendations and plans are tuned to your behavioral profile."
