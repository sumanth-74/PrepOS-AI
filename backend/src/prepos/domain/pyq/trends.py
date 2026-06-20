from __future__ import annotations

import math
from dataclasses import dataclass

from prepos.domain.knowledge.pyq import TREND_CEIL, TREND_FLOOR, TREND_RECENT_YEARS


@dataclass(frozen=True, slots=True)
class PyqQuestionYearHit:
    concept_id: str
    year: int
    confidence_score: float


@dataclass(frozen=True, slots=True)
class ConceptPyqAggregate:
    concept_id: str
    pyq_count: int
    first_appearance_year: int | None
    last_appearance_year: int | None
    frequency_score: float
    trend_score: float


def compute_concept_statistics(
    *,
    hits: list[PyqQuestionYearHit],
    reference_year: int,
) -> list[ConceptPyqAggregate]:
    by_concept: dict[str, list[PyqQuestionYearHit]] = {}
    for hit in hits:
        by_concept.setdefault(hit.concept_id, []).append(hit)

    raw_counts: dict[str, float] = {}
    aggregates: dict[str, ConceptPyqAggregate] = {}
    for concept_id, concept_hits in by_concept.items():
        years = sorted({item.year for item in concept_hits})
        pyq_count = len(years)
        raw_counts[concept_id] = sum(item.confidence_score for item in concept_hits)
        recent_cutoff = reference_year - TREND_RECENT_YEARS + 1
        prior_start = reference_year - 2 * TREND_RECENT_YEARS + 1
        prior_end = reference_year - TREND_RECENT_YEARS
        hits_recent = sum(
            item.confidence_score for item in concept_hits if item.year >= recent_cutoff
        )
        hits_prior = sum(
            item.confidence_score
            for item in concept_hits
            if prior_start <= item.year <= prior_end
        )
        trend_ratio = (hits_recent + 1.0) / (hits_prior + 1.0)
        trend_norm = _clamp(
            100.0 * (trend_ratio - TREND_FLOOR) / max(TREND_CEIL - TREND_FLOOR, 0.01),
            0.0,
            100.0,
        )
        aggregates[concept_id] = ConceptPyqAggregate(
            concept_id=concept_id,
            pyq_count=pyq_count,
            first_appearance_year=years[0] if years else None,
            last_appearance_year=years[-1] if years else None,
            frequency_score=0.0,
            trend_score=round(trend_norm, 2),
        )

    max_raw = max(raw_counts.values(), default=0.0)
    results: list[ConceptPyqAggregate] = []
    for concept_id, aggregate in aggregates.items():
        raw = raw_counts.get(concept_id, 0.0)
        frequency = 0.0
        if max_raw > 0 and raw > 0:
            frequency = round(100.0 * math.log1p(raw) / math.log1p(max_raw), 2)
        results.append(
            ConceptPyqAggregate(
                concept_id=concept_id,
                pyq_count=aggregate.pyq_count,
                first_appearance_year=aggregate.first_appearance_year,
                last_appearance_year=aggregate.last_appearance_year,
                frequency_score=frequency,
                trend_score=aggregate.trend_score,
            )
        )
    results.sort(key=lambda item: (item.frequency_score, item.pyq_count), reverse=True)
    return results


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))
