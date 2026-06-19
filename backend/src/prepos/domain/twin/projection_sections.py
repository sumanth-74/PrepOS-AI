from __future__ import annotations

from enum import StrEnum


class TwinProjectionSection(StrEnum):
    READINESS = "readiness"
    RECOMMENDATIONS = "recommendations"
    QUEUE = "queue"
    STUDY_PLAN = "study_plan"
    FORECAST = "forecast"
    PREDICTED_SCORE = "predicted_score"
    MILESTONES = "milestones"
    FORECAST_PROBABILITY = "forecast_probability"
    DECISION = "decision"
    INTERVENTION = "intervention"
    INTERVENTION_OUTCOME = "intervention_outcome"
    BEHAVIOR_PROFILE = "behavior_profile"
    PERSONALIZATION = "personalization"
    MENTOR = "mentor"
    MENTOR_ACTION = "mentor_action"
    MENTOR_CASE = "mentor_case"
    MENTOR_EFFECTIVENESS = "mentor_effectiveness"
