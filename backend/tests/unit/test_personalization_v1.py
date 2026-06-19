from __future__ import annotations

from prepos.domain.twin.behavior_profile_types_v1 import LearningStyle, RiskProfile
from prepos.domain.twin.personalization_v1 import build_personalization_guidance_v1


def test_short_burst_personalization() -> None:
    guidance = build_personalization_guidance_v1(
        learning_style=LearningStyle.SHORT_BURST_LEARNER,
        risk_profile=RiskProfile.LOW_RISK,
    )
    assert "shorter daily sessions" in guidance.session_length_hint
    assert "Split daily plan" in guidance.study_plan_adjustment


def test_high_risk_personalization() -> None:
    guidance = build_personalization_guidance_v1(
        learning_style=LearningStyle.BALANCED,
        risk_profile=RiskProfile.HIGH_RISK,
    )
    assert "high-urgency interventions" in guidance.intervention_priority
    assert "Reduce weekly load" in guidance.study_plan_adjustment


def test_recovery_driven_personalization() -> None:
    guidance = build_personalization_guidance_v1(
        learning_style=LearningStyle.RECOVERY_DRIVEN,
        risk_profile=RiskProfile.MEDIUM_RISK,
    )
    assert "weakness recovery" in guidance.session_length_hint.lower()
    assert "weakness remediation" in guidance.study_plan_adjustment.lower()
