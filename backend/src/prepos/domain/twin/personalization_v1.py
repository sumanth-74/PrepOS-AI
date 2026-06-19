from __future__ import annotations

from dataclasses import dataclass

from prepos.domain.twin.behavior_profile_types_v1 import LearningStyle, RiskProfile

PERSONALIZATION_V1 = "personalization_v1"


@dataclass(frozen=True, slots=True)
class PersonalizationGuidance:
    session_length_hint: str
    intervention_priority: str
    study_plan_adjustment: str


def build_personalization_guidance_v1(
    *,
    learning_style: LearningStyle,
    risk_profile: RiskProfile,
) -> PersonalizationGuidance:
    if learning_style == LearningStyle.SHORT_BURST_LEARNER:
        session_length_hint = "Prefer shorter daily sessions with focused bursts."
    elif learning_style == LearningStyle.DEEP_FOCUS_LEARNER:
        session_length_hint = "Prefer longer uninterrupted study blocks."
    elif learning_style == LearningStyle.CONSISTENT_LEARNER:
        session_length_hint = "Maintain steady daily session cadence."
    elif learning_style == LearningStyle.RECOVERY_DRIVEN:
        session_length_hint = "Prioritize weakness recovery sessions in daily plans."
    else:
        session_length_hint = "Use a balanced mix of session lengths."

    if risk_profile == RiskProfile.HIGH_RISK:
        intervention_priority = "Prioritize high-urgency interventions immediately."
    elif risk_profile == RiskProfile.MEDIUM_RISK:
        intervention_priority = "Reinforce planned interventions before adding new topics."
    else:
        intervention_priority = "Continue current intervention cadence."

    if learning_style == LearningStyle.RECOVERY_DRIVEN:
        study_plan_adjustment = "Increase weakness remediation items in weekly plans."
    elif risk_profile == RiskProfile.HIGH_RISK:
        study_plan_adjustment = "Reduce weekly load and focus on overdue revisions."
    elif learning_style == LearningStyle.SHORT_BURST_LEARNER:
        study_plan_adjustment = "Split daily plan into shorter session blocks."
    elif learning_style == LearningStyle.DEEP_FOCUS_LEARNER:
        study_plan_adjustment = "Consolidate daily items into fewer longer sessions."
    else:
        study_plan_adjustment = "Keep existing study plan structure."

    return PersonalizationGuidance(
        session_length_hint=session_length_hint,
        intervention_priority=intervention_priority,
        study_plan_adjustment=study_plan_adjustment,
    )
