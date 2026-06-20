from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

# Documented deterministic weights (must sum to 1.0).
WEAKNESS_WEIGHT = 0.40
PYQ_FREQUENCY_WEIGHT = 0.30
FORECAST_GAIN_WEIGHT = 0.20
CURRENT_AFFAIRS_WEIGHT = 0.10

IMPACT_SCORE_MAX = 10.0

# Concepts linked to current affairs keyword mapping (domain/knowledge/concept_mapping.py).
CURRENT_AFFAIRS_RELEVANT_CONCEPTS: frozenset[str] = frozenset(
    {
        "polity_federalism",
        "polity_basic_structure",
        "polity_article_356",
        "economy_union_budget",
        "economy_economic_survey",
        "economy_gst",
        "environment_climate_change",
        "governance_welfare_schemes",
    }
)


@dataclass(frozen=True, slots=True)
class ImpactInputs:
    weakness_score: float
    pyq_frequency_score: float
    forecast_gain_score: float
    current_affairs_score: float


@dataclass(frozen=True, slots=True)
class ImpactBreakdown:
    weakness_score: float
    pyq_frequency_score: float
    forecast_gain_score: float
    current_affairs_score: float
    impact_score: float
    reason_codes: tuple[str, ...]


def normalize_score(value: Decimal | float | None, *, default: float = 0.0) -> float:
    if value is None:
        return default
    numeric = float(value)
    return max(0.0, min(100.0, numeric))


def pyq_frequency_score(*, frequency_score: float, pyq_count: int) -> float:
    base = normalize_score(frequency_score)
    if pyq_count >= 10:
        return min(100.0, base + 10.0)
    if pyq_count >= 5:
        return min(100.0, base + 5.0)
    return base


def forecast_gain_score(
    *,
    readiness_gain: Decimal | float | None,
    gap_to_goal: Decimal | float | None,
    importance_score: Decimal | float | None,
) -> float:
    gain = normalize_score(readiness_gain)
    gap = normalize_score(gap_to_goal)
    importance = normalize_score(importance_score)
    blended = (gain * 0.50) + (gap * 0.30) + (importance * 0.20)
    return round(blended, 2)


def current_affairs_score_for_concept(concept_id: str) -> float:
    normalized = concept_id.strip().lower()
    for marker in CURRENT_AFFAIRS_RELEVANT_CONCEPTS:
        if marker in normalized or normalized.endswith(marker):
            return 100.0
    return 0.0


def compute_impact(inputs: ImpactInputs) -> ImpactBreakdown:
    weighted = (
        inputs.weakness_score * WEAKNESS_WEIGHT
        + inputs.pyq_frequency_score * PYQ_FREQUENCY_WEIGHT
        + inputs.forecast_gain_score * FORECAST_GAIN_WEIGHT
        + inputs.current_affairs_score * CURRENT_AFFAIRS_WEIGHT
    )
    impact_score = round(min(IMPACT_SCORE_MAX, weighted / 10.0), 2)

    reason_codes: list[str] = []
    if inputs.weakness_score >= 50.0:
        reason_codes.append("weakness")
    if inputs.pyq_frequency_score >= 40.0:
        reason_codes.append("high_pyq_frequency")
    if inputs.forecast_gain_score >= 40.0:
        reason_codes.append("forecast_impact")
    if inputs.current_affairs_score >= 50.0:
        reason_codes.append("current_affairs_relevant")

    return ImpactBreakdown(
        weakness_score=round(inputs.weakness_score, 2),
        pyq_frequency_score=round(inputs.pyq_frequency_score, 2),
        forecast_gain_score=round(inputs.forecast_gain_score, 2),
        current_affairs_score=round(inputs.current_affairs_score, 2),
        impact_score=impact_score,
        reason_codes=tuple(reason_codes),
    )


def estimate_readiness_gain(*, impact_score: float, weakness_score: float) -> float:
    return round(min(10.0, (impact_score * 0.35) + (weakness_score / 100.0 * 1.5)), 2)


def recommendation_confidence(*, impact_score: float, reason_count: int) -> str:
    if impact_score >= 7.0 and reason_count >= 2:
        return "high"
    if impact_score >= 5.0:
        return "medium"
    return "low"


def human_reasons(
    *,
    reason_codes: tuple[str, ...],
    pyq_count: int = 0,
    current_affairs_label: str | None = None,
) -> list[str]:
    mapping = {
        "weakness": "Weakness score high",
        "high_pyq_frequency": f"Appeared in {pyq_count} PYQs" if pyq_count else "High PYQ frequency",
        "forecast_impact": "High forecast impact on readiness",
        "current_affairs_relevant": current_affairs_label or "Linked to current affairs",
    }
    return [mapping[code] for code in reason_codes if code in mapping]
