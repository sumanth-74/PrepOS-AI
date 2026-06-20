from __future__ import annotations

import pytest

from prepos.application.agents.planner_agent import PlannerAgent


@pytest.mark.parametrize(
    ("persona", "objective", "expected_tools"),
    [
        (
            "student",
            "How can I improve my readiness before prelims?",
            ["forecasting_agent", "student_success_agent"],
        ),
        (
            "student",
            "Explain federalism for UPSC",
            ["knowledge_agent"],
        ),
        (
            "mentor",
            "What should I do with this student?",
            ["mentor_coach_agent", "student_success_agent"],
        ),
        (
            "admin",
            "What should management focus on next month?",
            ["institution_strategy_agent"],
        ),
    ],
)
def test_planner_agent_decomposes_objectives(
    persona: str,
    objective: str,
    expected_tools: list[str],
) -> None:
    planner = PlannerAgent()
    first = planner.plan(objective=objective, persona=persona)
    second = planner.plan(objective=objective, persona=persona)

    first_tools = [step.agent_type for step in first.steps]
    second_tools = [step.agent_type for step in second.steps]
    assert first_tools == second_tools
    for tool in expected_tools:
        assert tool in first_tools


def test_planner_agent_uses_default_toolset_when_no_keywords_match() -> None:
    planner = PlannerAgent()
    plan = planner.plan(objective="hello there", persona="student")
    tools = [step.agent_type for step in plan.steps]
    assert "memory_agent" in tools
    assert "forecasting_agent" in tools
