from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

READINESS_MILESTONE_THRESHOLDS: tuple[int, ...] = (5, 10)
WEAKNESS_RESOLVED_THRESHOLD = 40.0


@dataclass(frozen=True, slots=True)
class MilestoneCandidate:
    memory_key: str
    summary: str
    memory_value: dict[str, object]


def detect_readiness_milestones(
    *,
    previous_readiness: float | None,
    current_readiness: float | None,
    occurred_at: datetime,
) -> list[MilestoneCandidate]:
    if previous_readiness is None or current_readiness is None:
        return []
    delta = current_readiness - previous_readiness
    milestones: list[MilestoneCandidate] = []
    for threshold in READINESS_MILESTONE_THRESHOLDS:
        if delta >= threshold:
            milestones.append(
                MilestoneCandidate(
                    memory_key=f"progress_milestones:readiness_plus_{threshold}:{occurred_at.date().isoformat()}",
                    summary=f"Readiness improved by +{threshold} or more (actual +{delta:.1f})",
                    memory_value={
                        "milestone_type": "readiness_gain",
                        "threshold": threshold,
                        "actual_gain": round(delta, 2),
                        "readiness_before": round(previous_readiness, 2),
                        "readiness_after": round(current_readiness, 2),
                        "occurred_at": occurred_at.isoformat(),
                    },
                )
            )
    return milestones


def detect_weakness_resolved_milestone(
    *,
    concept_id: str,
    weakness_before: float | None,
    weakness_after: float | None,
    occurred_at: datetime,
) -> MilestoneCandidate | None:
    if weakness_before is None or weakness_after is None:
        return None
    if weakness_before >= WEAKNESS_RESOLVED_THRESHOLD and weakness_after < WEAKNESS_RESOLVED_THRESHOLD:
        return MilestoneCandidate(
            memory_key=f"progress_milestones:weakness_resolved:{concept_id}:{occurred_at.date().isoformat()}",
            summary=f"Weak concept resolved for {concept_id}",
            memory_value={
                "milestone_type": "weakness_resolved",
                "concept_id": concept_id,
                "weakness_before": round(weakness_before, 2),
                "weakness_after": round(weakness_after, 2),
                "occurred_at": occurred_at.isoformat(),
            },
        )
    return None


def detect_goal_milestone(
    *,
    on_track: bool | None,
    goal_probability: Decimal | float | None,
    occurred_at: datetime,
) -> MilestoneCandidate | None:
    if on_track is not True:
        return None
    probability = float(goal_probability) if goal_probability is not None else None
    return MilestoneCandidate(
        memory_key=f"progress_milestones:goal_on_track:{occurred_at.date().isoformat()}",
        summary="Goal trajectory on track",
        memory_value={
            "milestone_type": "goal_on_track",
            "goal_probability": probability,
            "occurred_at": occurred_at.isoformat(),
        },
    )


def detect_forecast_milestone(
    *,
    forecast_before: float | None,
    forecast_after: float | None,
    target: float | None,
    occurred_at: datetime,
) -> MilestoneCandidate | None:
    if forecast_before is None or forecast_after is None or target is None:
        return None
    if forecast_before < target <= forecast_after:
        return MilestoneCandidate(
            memory_key=f"progress_milestones:forecast_target:{occurred_at.date().isoformat()}",
            summary=f"Forecast target {target:.1f} reached",
            memory_value={
                "milestone_type": "forecast_target_reached",
                "forecast_before": round(forecast_before, 2),
                "forecast_after": round(forecast_after, 2),
                "target": round(target, 2),
                "occurred_at": occurred_at.isoformat(),
            },
        )
    return None
