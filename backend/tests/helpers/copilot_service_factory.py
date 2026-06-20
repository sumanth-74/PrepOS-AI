from __future__ import annotations

from unittest.mock import AsyncMock


def build_copilot_service_kwargs(**overrides: object) -> dict[str, object]:
    defaults: dict[str, object] = {
        "session": AsyncMock(),
        "student_uow": AsyncMock(),
        "twin_read_service": AsyncMock(),
        "twin_recommendation_service": AsyncMock(),
        "learning_graph_read_service": AsyncMock(),
        "goal_service": AsyncMock(),
        "study_plan_service": AsyncMock(),
        "mentor_case_read_service": AsyncMock(),
        "health_service": AsyncMock(),
        "analytics_service": AsyncMock(),
        "knowledge_agent_service": AsyncMock(),
        "pyq_service": AsyncMock(),
        "recommendation_service": AsyncMock(),
        "outcome_service": AsyncMock(),
        "outcome_analytics_service": AsyncMock(),
        "memory_service": AsyncMock(),
        "planning_service": AsyncMock(),
        "forecasting_service": AsyncMock(),
        "intervention_service": AsyncMock(),
        "cohort_service": AsyncMock(),
        "institution_service": AsyncMock(),
        "institution_outcome_service": AsyncMock(),
        "agent_orchestrator": AsyncMock(),
    }
    defaults.update(overrides)
    return defaults
