from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from prepos.application.planning.planning_models import PlanningScoreBreakdown
from prepos.application.recommendations.impact_scoring import (
    current_affairs_score_for_concept,
    forecast_gain_score,
    normalize_score,
    pyq_frequency_score,
)
from prepos.application.recommendations.recommendation_engine import format_concept_name

ADAPTIVE_PLANNING_V1 = "adaptive_planning_v1"

WEAKNESS_WEIGHT = 0.35
RECOMMENDATION_IMPACT_WEIGHT = 0.25
PYQ_FREQUENCY_WEIGHT = 0.15
FORECAST_RISK_WEIGHT = 0.10
CURRENT_AFFAIRS_WEIGHT = 0.10
MEMORY_SUCCESS_WEIGHT = 0.05

DEFAULT_DAILY_MINUTES = 120
REVISION_SPACING_DAYS = 2
MINUTES_BY_ACTIVITY = {
    "WEAKNESS_RECOVERY": 45,
    "HIGH_IMPORTANCE_STUDY": 40,
    "READINESS_BOOST": 35,
    "REVISION": 25,
}


@dataclass(frozen=True, slots=True)
class PlanningCandidateInput:
    concept_id: str
    weakness_score: float
    recommendation_impact: float
    pyq_frequency: float
    forecast_risk: float
    current_affairs: float
    memory_success: float
    readiness_gain: float
    importance_score: float
    pyq_count: int = 0
    previously_effective: bool = False


@dataclass(frozen=True, slots=True)
class ScheduledPlanItem:
    concept_id: str
    concept_name: str
    activity_type: str
    priority_score: float
    estimated_minutes: int
    estimated_readiness_gain: float
    confidence: str
    scheduled_date: date
    source_reason: str
    score_breakdown: PlanningScoreBreakdown


def compute_planning_priority(inputs: PlanningCandidateInput) -> PlanningScoreBreakdown:
    weakness = normalize_score(inputs.weakness_score)
    recommendation = normalize_score(inputs.recommendation_impact * 10.0)
    pyq = normalize_score(inputs.pyq_frequency)
    forecast = normalize_score(inputs.forecast_risk)
    current_affairs = normalize_score(inputs.current_affairs)
    memory = normalize_score(inputs.memory_success)

    if inputs.previously_effective:
        memory = min(100.0, memory + 15.0)

    priority = (
        weakness * WEAKNESS_WEIGHT
        + recommendation * RECOMMENDATION_IMPACT_WEIGHT
        + pyq * PYQ_FREQUENCY_WEIGHT
        + forecast * FORECAST_RISK_WEIGHT
        + current_affairs * CURRENT_AFFAIRS_WEIGHT
        + memory * MEMORY_SUCCESS_WEIGHT
    )
    priority = round(min(100.0, priority), 2)

    reason_codes: list[str] = []
    if weakness >= 50.0:
        reason_codes.append("unresolved_weakness")
    if recommendation >= 50.0:
        reason_codes.append("high_recommendation_impact")
    if pyq >= 40.0:
        reason_codes.append("pyq_frequency")
    if forecast >= 40.0:
        reason_codes.append("forecast_risk")
    if current_affairs >= 50.0:
        reason_codes.append("current_affairs")
    if memory >= 40.0 or inputs.previously_effective:
        reason_codes.append("memory_success")

    return PlanningScoreBreakdown(
        weakness_score=round(weakness, 2),
        recommendation_impact_score=round(recommendation, 2),
        pyq_frequency_score=round(pyq, 2),
        forecast_risk_score=round(forecast, 2),
        current_affairs_score=round(current_affairs, 2),
        memory_success_score=round(memory, 2),
        priority_score=priority,
        reason_codes=reason_codes,
    )


def estimate_plan_minutes(*, priority_score: float, activity_type: str) -> int:
    base = MINUTES_BY_ACTIVITY.get(activity_type, 30)
    if priority_score >= 80.0:
        return base + 10
    if priority_score >= 60.0:
        return base
    return max(20, base - 5)


def estimate_plan_gain(*, priority_score: float, weakness_score: float) -> float:
    return round(min(10.0, (priority_score / 100.0 * 4.0) + (weakness_score / 100.0 * 1.5)), 2)


def plan_confidence(*, priority_score: float, reason_count: int) -> str:
    if priority_score >= 75.0 and reason_count >= 2:
        return "high"
    if priority_score >= 50.0:
        return "medium"
    return "low"


def choose_activity_type(*, weakness_score: float, previously_effective: bool) -> str:
    if weakness_score >= 70.0:
        return "WEAKNESS_RECOVERY"
    if previously_effective:
        return "READINESS_BOOST"
    if weakness_score >= 45.0:
        return "HIGH_IMPORTANCE_STUDY"
    return "REVISION"


def build_source_reason(breakdown: PlanningScoreBreakdown) -> str:
    labels = {
        "unresolved_weakness": "unresolved weakness",
        "high_recommendation_impact": "high recommendation impact",
        "pyq_frequency": "PYQ frequency",
        "forecast_risk": "forecast risk",
        "current_affairs": "current affairs relevance",
        "memory_success": "prior successful intervention",
    }
    parts = [labels[code] for code in breakdown.reason_codes if code in labels]
    return ", ".join(parts) if parts else "balanced planning priority"


def generate_weekly_schedule(
    *,
    candidates: list[PlanningCandidateInput],
    start_date: date,
    daily_minutes: int,
) -> tuple[list[ScheduledPlanItem], list[ScheduledPlanItem], list[ScheduledPlanItem]]:
    scored: list[tuple[PlanningCandidateInput, PlanningScoreBreakdown]] = []
    for candidate in candidates:
        scored.append((candidate, compute_planning_priority(candidate)))
    scored.sort(key=lambda item: (-item[1].priority_score, item[0].concept_id))

    today_items: list[ScheduledPlanItem] = []
    week_items: list[ScheduledPlanItem] = []
    next_week_draft: list[ScheduledPlanItem] = []
    scheduled_concepts: set[str] = set()
    revision_dates: dict[str, date] = {}

    week_end = start_date + timedelta(days=6)
    next_week_end = start_date + timedelta(days=13)

    def _schedule_for_day(
        target_date: date,
        budget: int,
        bucket: list[ScheduledPlanItem],
        *,
        allow_duplicates: bool = False,
    ) -> None:
        remaining = budget
        for candidate, breakdown in scored:
            if remaining <= 0:
                break
            if candidate.concept_id in scheduled_concepts and not allow_duplicates:
                continue
            last_revision = revision_dates.get(candidate.concept_id)
            if last_revision is not None and (target_date - last_revision).days < REVISION_SPACING_DAYS:
                continue
            activity_type = choose_activity_type(
                weakness_score=candidate.weakness_score,
                previously_effective=candidate.previously_effective,
            )
            minutes = estimate_plan_minutes(priority_score=breakdown.priority_score, activity_type=activity_type)
            if minutes > remaining:
                continue
            gain = estimate_plan_gain(
                priority_score=breakdown.priority_score,
                weakness_score=candidate.weakness_score,
            )
            item = ScheduledPlanItem(
                concept_id=candidate.concept_id,
                concept_name=format_concept_name(candidate.concept_id),
                activity_type=activity_type,
                priority_score=breakdown.priority_score,
                estimated_minutes=minutes,
                estimated_readiness_gain=gain,
                confidence=plan_confidence(
                    priority_score=breakdown.priority_score,
                    reason_count=len(breakdown.reason_codes),
                ),
                scheduled_date=target_date,
                source_reason=build_source_reason(breakdown),
                score_breakdown=breakdown,
            )
            bucket.append(item)
            scheduled_concepts.add(candidate.concept_id)
            revision_dates[candidate.concept_id] = target_date
            remaining -= minutes

    _schedule_for_day(start_date, daily_minutes, today_items)
    day = start_date
    while day <= week_end:
        if day != start_date:
            _schedule_for_day(day, daily_minutes, week_items)
        day += timedelta(days=1)

    day = week_end + timedelta(days=1)
    while day <= next_week_end:
        _schedule_for_day(day, daily_minutes, next_week_draft, allow_duplicates=True)
        day += timedelta(days=1)

    return today_items, week_items, next_week_draft


def build_candidate_from_signals(
    *,
    concept_id: str,
    weakness_score: float | None,
    impact_score: float | None,
    pyq_frequency: float | None,
    pyq_count: int,
    readiness_gain: float | None,
    gap_to_goal: float | None,
    importance_score: float | None,
    memory_effectiveness: float | None,
) -> PlanningCandidateInput:
    forecast = forecast_gain_score(
        readiness_gain=readiness_gain,
        gap_to_goal=gap_to_goal,
        importance_score=importance_score,
    )
    pyq = pyq_frequency_score(frequency_score=pyq_frequency or 0.0, pyq_count=pyq_count)
    memory = normalize_score((memory_effectiveness or 0.0) * 33.33)
    previously_effective = (memory_effectiveness or 0.0) >= 1.0
    return PlanningCandidateInput(
        concept_id=concept_id,
        weakness_score=normalize_score(weakness_score),
        recommendation_impact=float(impact_score or 0.0),
        pyq_frequency=pyq,
        forecast_risk=forecast,
        current_affairs=current_affairs_score_for_concept(concept_id),
        memory_success=memory,
        readiness_gain=float(readiness_gain or 0.0),
        importance_score=normalize_score(importance_score),
        pyq_count=pyq_count,
        previously_effective=previously_effective,
    )
