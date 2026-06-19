from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from prepos.domain.scoring.common import round_score
from prepos.domain.study_plan.entities import StudyPlanExecutionRecord
from prepos.domain.study_plan.value_objects import ExecutionStatus

BEHAVIOR_METRICS_V1 = "behavior_metrics_v1"


@dataclass(frozen=True, slots=True)
class ConceptBehaviorStats:
    completion_rate: Decimal
    skip_rate: Decimal
    average_minutes_variance: Decimal


@dataclass(frozen=True, slots=True)
class StudyBehaviorMetrics:
    completion_rate: Decimal
    skip_rate: Decimal
    average_minutes_variance: Decimal
    by_concept: dict[str, ConceptBehaviorStats]


def _zero_stats() -> ConceptBehaviorStats:
    return ConceptBehaviorStats(
        completion_rate=Decimal("0"),
        skip_rate=Decimal("0"),
        average_minutes_variance=Decimal("0"),
    )


def compute_concept_behavior_stats(
    records: tuple[StudyPlanExecutionRecord, ...],
) -> ConceptBehaviorStats:
    if not records:
        return _zero_stats()

    completed = sum(1 for record in records if record.status == ExecutionStatus.COMPLETED)
    skipped = sum(1 for record in records if record.status == ExecutionStatus.SKIPPED)
    total = completed + skipped
    if total == 0:
        return _zero_stats()

    completion_rate = Decimal(completed) / Decimal(total)
    skip_rate = Decimal(skipped) / Decimal(total)

    variance_samples: list[Decimal] = []
    for record in records:
        if record.status != ExecutionStatus.COMPLETED:
            continue
        if record.planned_minutes <= 0:
            continue
        delta = abs(Decimal(record.actual_minutes) - Decimal(record.planned_minutes))
        variance_samples.append(delta / Decimal(record.planned_minutes))

    average_minutes_variance = Decimal("0")
    if variance_samples:
        average_minutes_variance = sum(variance_samples, start=Decimal("0")) / Decimal(len(variance_samples))

    return ConceptBehaviorStats(
        completion_rate=round_score(completion_rate, places=4),
        skip_rate=round_score(skip_rate, places=4),
        average_minutes_variance=round_score(average_minutes_variance, places=4),
    )


def compute_study_behavior_metrics(
    records: tuple[StudyPlanExecutionRecord, ...],
) -> StudyBehaviorMetrics:
    if not records:
        return StudyBehaviorMetrics(
            completion_rate=Decimal("0"),
            skip_rate=Decimal("0"),
            average_minutes_variance=Decimal("0"),
            by_concept={},
        )

    aggregate = compute_concept_behavior_stats(records)
    by_concept: dict[str, ConceptBehaviorStats] = {}
    grouped: dict[str, list[StudyPlanExecutionRecord]] = {}
    for record in records:
        grouped.setdefault(record.concept_id, []).append(record)

    for concept_id, concept_records in grouped.items():
        by_concept[concept_id] = compute_concept_behavior_stats(tuple(concept_records))

    return StudyBehaviorMetrics(
        completion_rate=aggregate.completion_rate,
        skip_rate=aggregate.skip_rate,
        average_minutes_variance=aggregate.average_minutes_variance,
        by_concept=by_concept,
    )
