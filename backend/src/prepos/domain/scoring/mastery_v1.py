from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from prepos.domain.scoring.common import (
    clamp,
    recency_weight,
    redistribute_weights,
    round_score,
    shrink,
    weighted_blend,
)
from prepos.domain.scoring.config import DEFAULT_SCORING_CONFIG, ScoringConfig

MASTERY_V1 = "mastery_v1"


class McqDifficulty(StrEnum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


@dataclass(frozen=True, slots=True)
class McqAttemptEvidence:
    correct: bool
    difficulty: McqDifficulty = McqDifficulty.MEDIUM
    age_days: Decimal = Decimal("0")


@dataclass(frozen=True, slots=True)
class RecencyWeightedEvidence:
    """Normalized [0, 1] value with recency weight already applied upstream, or raw score 0-1."""

    value_unit: Decimal
    age_days: Decimal = Decimal("0")


@dataclass(frozen=True, slots=True)
class MasteryEvidenceCounters:
    """Pre-normalized component values in [0, 1] plus evidence counts."""

    mcq_component: Decimal = Decimal("0")
    n_mcq: int = 0
    mains_component: Decimal = Decimal("0")
    n_mains: int = 0
    revision_component: Decimal = Decimal("0")
    n_rev: int = 0
    study_component: Decimal = Decimal("0")
    n_study: int = 0


@dataclass(frozen=True, slots=True)
class MasteryResult:
    value: Decimal
    version: str
    raw_unit: Decimal
    shrunk_unit: Decimal
    n_total: int
    unrated: bool
    active_components: tuple[str, ...]
    redistributed_weights: dict[str, Decimal]


def difficulty_multiplier(difficulty: McqDifficulty, config: ScoringConfig) -> Decimal:
    if difficulty == McqDifficulty.EASY:
        return config.MCQ_DIFFICULTY_EASY
    if difficulty == McqDifficulty.HARD:
        return config.MCQ_DIFFICULTY_HARD
    return config.MCQ_DIFFICULTY_MEDIUM


def compute_mcq_component(
    attempts: tuple[McqAttemptEvidence, ...],
    *,
    config: ScoringConfig = DEFAULT_SCORING_CONFIG,
) -> tuple[Decimal, int]:
    """Difficulty- and recency-weighted MCQ accuracy (spec §2.3.1)."""
    if not attempts:
        return Decimal("0"), 0

    weighted_correct = Decimal("0")
    weighted_total = Decimal("0")
    for attempt in attempts:
        difficulty = difficulty_multiplier(attempt.difficulty, config)
        recency = recency_weight(attempt.age_days, config.MASTERY_RECENCY_HALFLIFE_DAYS)
        weight = difficulty * recency
        weighted_total += weight
        if attempt.correct:
            weighted_correct += weight

    if weighted_total == 0:
        return Decimal("0"), len(attempts)

    mcq_raw = weighted_correct / weighted_total
    return clamp(mcq_raw, Decimal("0"), Decimal("1")), len(attempts)


def compute_recency_weighted_component(
    evidences: tuple[RecencyWeightedEvidence, ...],
    *,
    config: ScoringConfig = DEFAULT_SCORING_CONFIG,
) -> tuple[Decimal, int]:
    """Recency-weighted mean for Mains or Revision components (spec §2.3.1)."""
    if not evidences:
        return Decimal("0"), 0

    weighted_sum = Decimal("0")
    weight_total = Decimal("0")
    for evidence in evidences:
        recency = recency_weight(evidence.age_days, config.MASTERY_RECENCY_HALFLIFE_DAYS)
        weighted_sum += evidence.value_unit * recency
        weight_total += recency

    if weight_total == 0:
        return Decimal("0"), len(evidences)

    return clamp(weighted_sum / weight_total, Decimal("0"), Decimal("1")), len(evidences)


def compute_study_component(
    study_minutes: Decimal,
    *,
    config: ScoringConfig = DEFAULT_SCORING_CONFIG,
) -> Decimal:
    """Saturating study engagement signal (spec §2.3.1)."""
    if study_minutes <= 0:
        return Decimal("0")
    saturation = config.MASTERY_STUDY_SATURATION_MINUTES
    return clamp(Decimal("1") - (-(study_minutes / saturation)).exp(), Decimal("0"), Decimal("1"))


def build_mastery_evidence(
    *,
    mcq_attempts: tuple[McqAttemptEvidence, ...] = (),
    mains_evidences: tuple[RecencyWeightedEvidence, ...] = (),
    revision_evidences: tuple[RecencyWeightedEvidence, ...] = (),
    study_minutes: Decimal = Decimal("0"),
    n_study_sessions: int = 0,
    config: ScoringConfig = DEFAULT_SCORING_CONFIG,
) -> MasteryEvidenceCounters:
    """Derive normalized components and counters from raw evidence."""
    mcq_component, n_mcq = compute_mcq_component(mcq_attempts, config=config)
    mains_component, n_mains = compute_recency_weighted_component(mains_evidences, config=config)
    revision_component, n_rev = compute_recency_weighted_component(revision_evidences, config=config)
    study_component = compute_study_component(study_minutes, config=config)
    n_study = n_study_sessions if study_minutes > 0 else 0

    return MasteryEvidenceCounters(
        mcq_component=mcq_component,
        n_mcq=n_mcq,
        mains_component=mains_component,
        n_mains=n_mains,
        revision_component=revision_component,
        n_rev=n_rev,
        study_component=study_component,
        n_study=n_study,
    )


def compute_mastery_v1(
    evidence: MasteryEvidenceCounters,
    *,
    config: ScoringConfig = DEFAULT_SCORING_CONFIG,
) -> MasteryResult:
    """Full mastery formula with weight redistribution and shrinkage (spec §2.5)."""
    component_values = {
        "mcq": clamp(evidence.mcq_component, Decimal("0"), Decimal("1")),
        "mains": clamp(evidence.mains_component, Decimal("0"), Decimal("1")),
        "revision": clamp(evidence.revision_component, Decimal("0"), Decimal("1")),
        "study": clamp(evidence.study_component, Decimal("0"), Decimal("1")),
    }
    component_counts = {
        "mcq": evidence.n_mcq,
        "mains": evidence.n_mains,
        "revision": evidence.n_rev,
        "study": evidence.n_study,
    }
    base_weights = {
        "mcq": config.MASTERY_W_MCQ,
        "mains": config.MASTERY_W_MAINS,
        "revision": config.MASTERY_W_REVISION,
        "study": config.MASTERY_W_STUDY,
    }

    redistributed = redistribute_weights(base_weights, component_counts)
    n_total = sum(component_counts.values())

    if not redistributed:
        return MasteryResult(
            value=Decimal("0"),
            version=MASTERY_V1,
            raw_unit=Decimal("0"),
            shrunk_unit=Decimal("0"),
            n_total=0,
            unrated=True,
            active_components=(),
            redistributed_weights={},
        )

    raw_unit = weighted_blend(component_values, redistributed)
    shrunk_unit = shrink(raw_unit, n_total, config.MASTERY_K_CONF, config.MASTERY_PRIOR)
    mastery = round_score(Decimal("100") * shrunk_unit)

    return MasteryResult(
        value=mastery,
        version=MASTERY_V1,
        raw_unit=raw_unit,
        shrunk_unit=shrunk_unit,
        n_total=n_total,
        unrated=False,
        active_components=tuple(redistributed),
        redistributed_weights=redistributed,
    )
