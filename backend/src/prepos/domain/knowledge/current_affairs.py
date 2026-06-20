from __future__ import annotations

import math
from datetime import UTC, datetime
from enum import StrEnum


class CurrentAffairsSourceType(StrEnum):
    CURRENT_AFFAIRS = "current_affairs"
    PIB = "pib"
    PRS = "prs"
    GOVERNMENT_SCHEME = "government_scheme"
    BUDGET = "budget"
    ECONOMIC_SURVEY = "economic_survey"


CURRENT_AFFAIRS_SOURCE_TYPES: frozenset[str] = frozenset(
    member.value for member in CurrentAffairsSourceType
)

AUTHORITY_BOOST_MULTIPLIERS: dict[str, float] = {
    CurrentAffairsSourceType.PIB.value: 1.25,
    CurrentAffairsSourceType.PRS.value: 1.20,
    CurrentAffairsSourceType.GOVERNMENT_SCHEME.value: 1.15,
    CurrentAffairsSourceType.BUDGET.value: 1.18,
    CurrentAffairsSourceType.ECONOMIC_SURVEY.value: 1.18,
    CurrentAffairsSourceType.CURRENT_AFFAIRS.value: 1.10,
}

DEFAULT_AUTHORITY_MULTIPLIER = 1.0


def authority_boost_multiplier(source_authority: str | None, source_type: str | None = None) -> float:
    if source_authority:
        normalized = source_authority.strip().lower()
        if normalized in AUTHORITY_BOOST_MULTIPLIERS:
            return AUTHORITY_BOOST_MULTIPLIERS[normalized]
    if source_type:
        normalized_type = source_type.strip().lower()
        return AUTHORITY_BOOST_MULTIPLIERS.get(normalized_type, DEFAULT_AUTHORITY_MULTIPLIER)
    return DEFAULT_AUTHORITY_MULTIPLIER


def recency_boost_multiplier(
    published_at: datetime | None,
    *,
    reference_time: datetime | None = None,
    half_life_days: int = 30,
    max_boost: float = 0.5,
) -> float:
    if published_at is None:
        return 1.0
    now = reference_time or datetime.now(UTC)
    published = published_at if published_at.tzinfo else published_at.replace(tzinfo=UTC)
    age_days = max(0.0, (now - published).total_seconds() / 86400.0)
    boost = max_boost * math.exp(-age_days / max(half_life_days, 1))
    return 1.0 + boost


def apply_ranking_boosts(
    *,
    base_score: float,
    published_at: datetime | None,
    source_authority: str | None,
    source_type: str | None,
    prefer_recency: bool,
    reference_time: datetime | None = None,
) -> float:
    score = base_score
    if prefer_recency:
        score *= recency_boost_multiplier(published_at, reference_time=reference_time)
    score *= authority_boost_multiplier(source_authority, source_type)
    return score


def is_current_affairs_source_type(source_type: str) -> bool:
    return source_type.strip().lower() in CURRENT_AFFAIRS_SOURCE_TYPES
