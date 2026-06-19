from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class ScoringConfig:
    """Versioned tunable constants for the PrepOS scoring engine (spec §1.6)."""

    version: str = "scoring_v1"

    # Mastery (§2)
    MASTERY_W_MCQ: Decimal = Decimal("0.40")
    MASTERY_W_MAINS: Decimal = Decimal("0.30")
    MASTERY_W_REVISION: Decimal = Decimal("0.20")
    MASTERY_W_STUDY: Decimal = Decimal("0.10")
    MASTERY_PRIOR: Decimal = Decimal("0.0")
    MASTERY_K_CONF: Decimal = Decimal("8")
    MASTERY_RECENCY_HALFLIFE_DAYS: Decimal = Decimal("45")
    MASTERY_STUDY_SATURATION_MINUTES: Decimal = Decimal("120")

    # MasteryNonMCQ (v1.1 §4.2) — reuses MASTERY_* machinery over non-MCQ channels only
    MASTERY_NONMCQ_W_MAINS: Decimal = Decimal("0.30")
    MASTERY_NONMCQ_W_REVISION: Decimal = Decimal("0.20")
    MASTERY_NONMCQ_W_STUDY: Decimal = Decimal("0.10")

    # Retention (§3)
    RET_S_BASE_INTERCEPT: Decimal = Decimal("2.0")
    RET_S_BASE_SLOPE: Decimal = Decimal("0.18")
    RET_REVISION_EF: Decimal = Decimal("1.6")
    RET_FAIL_FACTOR: Decimal = Decimal("0.6")
    RET_S_MIN: Decimal = Decimal("0.5")
    RET_S_MAX: Decimal = Decimal("3650")
    RETENTION_MODEL: str = "stability_exp"

    # Importance (§4)
    IMP_W_PYQ_FREQ: Decimal = Decimal("0.40")
    IMP_W_TREND: Decimal = Decimal("0.25")
    IMP_W_EXAM_REL: Decimal = Decimal("0.25")
    IMP_W_FACULTY: Decimal = Decimal("0.10")
    IMP_TREND_WINDOW: int = 5
    IMP_HALFLIFE_YEARS: Decimal = Decimal("6")

    # Confidence (Assessment §16 / internal engine)
    CONF_W_SELF: Decimal = Decimal("0.50")
    CONF_W_SPEED: Decimal = Decimal("0.25")
    CONF_W_CONSISTENCY: Decimal = Decimal("0.25")
    CONF_PRIOR: Decimal = Decimal("50")
    CONF_K_CONF: Decimal = Decimal("8")

    # Weakness (§5)
    WEAK_W_MASTERY: Decimal = Decimal("0.55")
    WEAK_W_RETENTION: Decimal = Decimal("0.30")
    WEAK_W_ERROR: Decimal = Decimal("0.15")
    WEAK_OVERCONF_BONUS: Decimal = Decimal("10")
    WEAK_OVERCONFIDENCE_GAP: Decimal = Decimal("25")
    WEAK_OVERCONFIDENCE_MASTERY_CEILING: Decimal = Decimal("70")

    # Readiness (§7)
    READINESS_W_KNOWLEDGE: Decimal = Decimal("0.30")
    READINESS_W_RETENTION: Decimal = Decimal("0.25")
    READINESS_W_MCQ: Decimal = Decimal("0.20")
    READINESS_W_WRITING: Decimal = Decimal("0.15")
    READINESS_W_CA: Decimal = Decimal("0.10")
    READINESS_COVERAGE_FLOOR: Decimal = Decimal("0.0")

    # Revision Health (§6)
    REVHEALTH_HALFLIFE_DAYS: Decimal = Decimal("30")

    # MCQ difficulty multipliers (§2.3.1)
    MCQ_DIFFICULTY_EASY: Decimal = Decimal("0.7")
    MCQ_DIFFICULTY_MEDIUM: Decimal = Decimal("1.0")
    MCQ_DIFFICULTY_HARD: Decimal = Decimal("1.3")


DEFAULT_SCORING_CONFIG = ScoringConfig()
