from __future__ import annotations

from prepos.application.planning.adaptive_planning_engine import PlanningCandidateInput, compute_planning_priority
from prepos.application.planning.planning_analytics import PlanningAnalyticsService
from prepos.application.planning.planning_explainer import explain_planning_decision


def test_explain_planning_decision_includes_weights() -> None:
    breakdown = compute_planning_priority(
        PlanningCandidateInput(
            concept_id="upsc.polity_federalism",
            weakness_score=80.0,
            recommendation_impact=8.0,
            pyq_frequency=70.0,
            forecast_risk=60.0,
            current_affairs=100.0,
            memory_success=50.0,
            readiness_gain=3.0,
            importance_score=85.0,
            previously_effective=True,
        )
    )
    lines = explain_planning_decision(breakdown=breakdown, source_reason="unresolved weakness")
    assert any("Priority score" in line for line in lines)
    assert any("memory" in line.lower() for line in lines)


def test_planning_analytics_completion_rate() -> None:
    assert PlanningAnalyticsService.completion_rate(completed=3, total=10) == 0.3
    assert PlanningAnalyticsService.completion_rate(completed=0, total=0) == 0.0
