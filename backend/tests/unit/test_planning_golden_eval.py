from __future__ import annotations

from datetime import date

import pytest

from prepos.application.planning.adaptive_planning_engine import (
    PlanningCandidateInput,
    compute_planning_priority,
    generate_weekly_schedule,
)


def test_golden_planning_for_one_hundred_students() -> None:
    start = date(2026, 1, 1)
    for index in range(100):
        candidates = [
            PlanningCandidateInput(
                concept_id=f"concept_{index}_{offset}",
                weakness_score=40.0 + index * 0.3 + offset,
                recommendation_impact=5.0 + (index % 5),
                pyq_frequency=30.0 + offset * 5,
                forecast_risk=20.0 + (index % 7),
                current_affairs=float((index + offset) % 2 * 100),
                memory_success=float((index % 3) * 33),
                readiness_gain=1.0 + offset * 0.5,
                importance_score=50.0 + index * 0.2,
                previously_effective=index % 4 == 0,
            )
            for offset in range(4)
        ]
        first = generate_weekly_schedule(candidates=candidates, start_date=start, daily_minutes=120)
        second = generate_weekly_schedule(candidates=candidates, start_date=start, daily_minutes=120)
        assert first == second
        today_items, week_items, draft_items = first
        total_minutes_today = sum(item.estimated_minutes for item in today_items)
        assert total_minutes_today <= 120
        if week_items:
            assert all(0 <= item.priority_score <= 100 for item in week_items)
        priorities = [compute_planning_priority(candidate).priority_score for candidate in candidates]
        assert all(0 <= score <= 100 for score in priorities)
