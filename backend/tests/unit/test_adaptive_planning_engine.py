from __future__ import annotations

from datetime import date

import pytest

from prepos.application.planning.adaptive_planning_engine import (
    PlanningCandidateInput,
    compute_planning_priority,
    generate_weekly_schedule,
)


def test_planning_priority_uses_documented_weights() -> None:
    inputs = PlanningCandidateInput(
        concept_id="upsc.polity_federalism",
        weakness_score=100.0,
        recommendation_impact=10.0,
        pyq_frequency=100.0,
        forecast_risk=100.0,
        current_affairs=100.0,
        memory_success=100.0,
        readiness_gain=5.0,
        importance_score=90.0,
    )
    breakdown = compute_planning_priority(inputs)
    assert breakdown.priority_score == 100.0
    assert "unresolved_weakness" in breakdown.reason_codes


def test_generate_weekly_schedule_is_deterministic() -> None:
    candidates = [
        PlanningCandidateInput(
            concept_id=f"concept_{index}",
            weakness_score=80.0 - index,
            recommendation_impact=8.0,
            pyq_frequency=70.0,
            forecast_risk=60.0,
            current_affairs=50.0,
            memory_success=40.0,
            readiness_gain=3.0,
            importance_score=80.0,
        )
        for index in range(5)
    ]
    start = date(2026, 6, 18)
    first = generate_weekly_schedule(candidates=candidates, start_date=start, daily_minutes=120)
    second = generate_weekly_schedule(candidates=candidates, start_date=start, daily_minutes=120)
    assert first == second
    assert len(first[0]) >= 1
    assert all(item.estimated_minutes <= 120 for item in first[0])


def test_schedule_avoids_duplicate_concepts_in_same_day() -> None:
    candidates = [
        PlanningCandidateInput(
            concept_id="same_concept",
            weakness_score=90.0,
            recommendation_impact=9.0,
            pyq_frequency=80.0,
            forecast_risk=70.0,
            current_affairs=60.0,
            memory_success=50.0,
            readiness_gain=4.0,
            importance_score=85.0,
        )
    ]
    today, week, _draft = generate_weekly_schedule(
        candidates=candidates,
        start_date=date(2026, 6, 18),
        daily_minutes=240,
    )
    concept_ids = [item.concept_id for item in today]
    assert len(concept_ids) == len(set(concept_ids))
