from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from prepos.domain.learning_graph.policies import NodeStatus
from prepos.domain.scoring.common import clamp, round_score

RETENTION_V1 = "retention_v1"

# Recall grade integers persisted on student_concept_progress.retention_last_grade.
RECALL_GRADE_FORGOT = 0
RECALL_GRADE_HARD = 1
RECALL_GRADE_GOOD = 2
RECALL_GRADE_EASY = 3

# Stability initialization from mastery (LG §8.2 / S5.1).
# | mastery_score | retention_stability_s (days) |
# |--------------|------------------------------|
# | >= 80        | 30                           |
# | >= 60        | 14                           |
# | >= 40        | 7                            |
# | otherwise    | 3                            |
_STABILITY_TIER_HIGH = Decimal("30")
_STABILITY_TIER_MID = Decimal("14")
_STABILITY_TIER_LOW = Decimal("7")
_STABILITY_TIER_MIN = Decimal("3")

# Grade multipliers applied on RevisionCompleted when recomputing stability.
_GRADE_STABILITY_MULTIPLIERS: dict[int, Decimal] = {
    RECALL_GRADE_FORGOT: Decimal("0.5"),
    RECALL_GRADE_HARD: Decimal("1.1"),
    RECALL_GRADE_GOOD: Decimal("1.5"),
    RECALL_GRADE_EASY: Decimal("2.0"),
}


@dataclass(frozen=True, slots=True)
class RetentionInputs:
    """Inputs for retention materialization (read path) and scoring."""

    mastery_score: Decimal
    retention_stability_s: Decimal | None
    retention_last_review_at: datetime | None
    retention_last_grade: int | None
    current_time: datetime
    node_state: str = NodeStatus.UNRATED


@dataclass(frozen=True, slots=True)
class RetentionResult:
    value: Decimal | None
    stability_s: Decimal | None
    next_review_at: datetime | None
    unrated: bool
    version: str = RETENTION_V1


def recall_grade_to_int(recall_grade: str) -> int:
    mapping = {
        "forgot": RECALL_GRADE_FORGOT,
        "hard": RECALL_GRADE_HARD,
        "good": RECALL_GRADE_GOOD,
        "easy": RECALL_GRADE_EASY,
    }
    return mapping.get(recall_grade.lower(), RECALL_GRADE_GOOD)


def initialize_stability_from_mastery(mastery_score: Decimal) -> Decimal:
    """Initialize retention_stability_s (days) from mastery when a node is first reviewed."""
    mastery = clamp(mastery_score, Decimal("0"), Decimal("100"))
    if mastery >= Decimal("80"):
        return _STABILITY_TIER_HIGH
    if mastery >= Decimal("60"):
        return _STABILITY_TIER_MID
    if mastery >= Decimal("40"):
        return _STABILITY_TIER_LOW
    return _STABILITY_TIER_MIN


def compute_elapsed_days(*, last_review_at: datetime, current_time: datetime) -> Decimal:
    review_at = last_review_at.astimezone(UTC) if last_review_at.tzinfo else last_review_at.replace(tzinfo=UTC)
    now = current_time.astimezone(UTC) if current_time.tzinfo else current_time.replace(tzinfo=UTC)
    delta_seconds = Decimal(str((now - review_at).total_seconds()))
    return clamp(delta_seconds / Decimal("86400"), Decimal("0"), Decimal("3650"))


def compute_retention_score_from_state(
    *,
    stability_s: Decimal,
    last_review_at: datetime,
    current_time: datetime,
) -> Decimal:
    """
    Exponential decay (LG §8.2 / S5.1):

        retention = 100 × exp(-elapsed_days / stability_s)

    Immediately after review (elapsed_days = 0): retention = 100.
    """
    elapsed_days = compute_elapsed_days(last_review_at=last_review_at, current_time=current_time)
    stability = max(stability_s, Decimal("0.0001"))
    retention_unit = (-(elapsed_days / stability)).exp()
    value = Decimal("100") * retention_unit
    return round_score(clamp(value, Decimal("0"), Decimal("100")))


def compute_next_review_at(*, last_review_at: datetime, stability_s: Decimal) -> datetime:
    """Schedule next review at last_review_at + stability_s days."""
    review_at = last_review_at.astimezone(UTC) if last_review_at.tzinfo else last_review_at.replace(tzinfo=UTC)
    return review_at + timedelta(days=float(stability_s))


def recompute_stability_after_review(
    *,
    mastery_score: Decimal,
    prior_stability_s: Decimal | None,
    recall_grade: int,
) -> Decimal:
    """RevisionCompleted owns stability updates."""
    if prior_stability_s is None or recall_grade == RECALL_GRADE_FORGOT:
        base = initialize_stability_from_mastery(mastery_score)
    else:
        base = prior_stability_s

    multiplier = _GRADE_STABILITY_MULTIPLIERS.get(recall_grade, Decimal("1.5"))
    updated = base * multiplier
    return clamp(updated, Decimal("1"), Decimal("365")).quantize(Decimal("0.0001"))


def compute_retention_v1(inputs: RetentionInputs) -> RetentionResult:
    """Materialize retention score and next_review_at from persisted state."""
    if inputs.node_state == NodeStatus.UNRATED:
        return RetentionResult(
            value=None,
            stability_s=None,
            next_review_at=None,
            unrated=True,
        )

    if inputs.retention_last_review_at is None or inputs.retention_stability_s is None:
        return RetentionResult(
            value=None,
            stability_s=inputs.retention_stability_s,
            next_review_at=None,
            unrated=False,
        )

    value = compute_retention_score_from_state(
        stability_s=inputs.retention_stability_s,
        last_review_at=inputs.retention_last_review_at,
        current_time=inputs.current_time,
    )
    next_review_at = compute_next_review_at(
        last_review_at=inputs.retention_last_review_at,
        stability_s=inputs.retention_stability_s,
    )
    return RetentionResult(
        value=value,
        stability_s=inputs.retention_stability_s,
        next_review_at=next_review_at,
        unrated=False,
    )


def apply_revision_retention_update(
    *,
    mastery_score: Decimal,
    prior_stability_s: Decimal | None,
    recall_grade: str,
    current_time: datetime,
) -> tuple[Decimal, Decimal, datetime, datetime, int]:
    """
    Persisted state written by RevisionCompleted.

    Returns:
        retention_stability_s, retention_score (100 at review time), last_review_at,
        last_event_at, retention_last_grade
    """
    grade = recall_grade_to_int(recall_grade)
    stability_s = recompute_stability_after_review(
        mastery_score=mastery_score,
        prior_stability_s=prior_stability_s,
        recall_grade=grade,
    )
    return (
        stability_s,
        Decimal("100"),
        current_time,
        current_time,
        grade,
    )
