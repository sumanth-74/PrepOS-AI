from __future__ import annotations

from enum import StrEnum

BEHAVIOR_PROFILE_V1 = "behavior_profile_v1"


class LearningStyle(StrEnum):
    SHORT_BURST_LEARNER = "SHORT_BURST_LEARNER"
    DEEP_FOCUS_LEARNER = "DEEP_FOCUS_LEARNER"
    CONSISTENT_LEARNER = "CONSISTENT_LEARNER"
    RECOVERY_DRIVEN = "RECOVERY_DRIVEN"
    BALANCED = "BALANCED"


class RiskProfile(StrEnum):
    HIGH_RISK = "HIGH_RISK"
    MEDIUM_RISK = "MEDIUM_RISK"
    LOW_RISK = "LOW_RISK"
