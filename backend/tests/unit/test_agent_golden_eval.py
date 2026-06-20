from __future__ import annotations

from prepos.application.agents.planner_agent import PlannerAgent

STUDENT_QUESTIONS = (
    "How can I improve my readiness?",
    "What should I study next for UPSC?",
    "Can I improve readiness by 10 points before prelims?",
    "Which weak concepts matter most?",
    "Explain federalism for prelims",
    "Show my adaptive study plan",
    "What does my forecast look like?",
    "Which PYQ topics should I revise?",
    "Summarize recent current affairs for GS2",
    "What is my readiness score?",
)

MENTOR_QUESTIONS = (
    "What should I do with this student?",
    "Which intervention improves readiness fastest?",
    "Is this student on track for prelims?",
    "Summarize student coaching memory",
    "Which concepts need mentor focus?",
    "Show intervention recommendations",
    "What is the student's forecast risk?",
    "Which PYQ gaps should we address?",
    "Should I escalate this student to cohort review?",
    "What planning adherence issues exist?",
)

ADMIN_QUESTIONS = (
    "What should management focus on next month?",
    "Show institution executive summary",
    "Which cohorts are at risk?",
    "What is intervention ROI this quarter?",
    "Which mentors need coaching support?",
)


def _student_question(index: int) -> str:
    base = STUDENT_QUESTIONS[index % len(STUDENT_QUESTIONS)]
    return f"{base} (scenario {index})"


def _mentor_question(index: int) -> str:
    base = MENTOR_QUESTIONS[index % len(MENTOR_QUESTIONS)]
    return f"{base} (scenario {index})"


def _admin_question(index: int) -> str:
    base = ADMIN_QUESTIONS[index % len(ADMIN_QUESTIONS)]
    return f"{base} (scenario {index})"


def test_golden_planner_outputs_for_one_hundred_student_scenarios() -> None:
    planner = PlannerAgent()
    for index in range(100):
        question = _student_question(index)
        first = planner.plan(objective=question, persona="student")
        second = planner.plan(objective=question, persona="student")
        assert [step.agent_type for step in first.steps] == [step.agent_type for step in second.steps]
        assert first.steps


def test_golden_planner_outputs_for_one_hundred_mentor_scenarios() -> None:
    planner = PlannerAgent()
    for index in range(100):
        question = _mentor_question(index)
        first = planner.plan(objective=question, persona="mentor")
        second = planner.plan(objective=question, persona="mentor")
        assert [step.agent_type for step in first.steps] == [step.agent_type for step in second.steps]
        assert first.steps


def test_golden_planner_outputs_for_fifty_institution_scenarios() -> None:
    planner = PlannerAgent()
    for index in range(50):
        question = _admin_question(index)
        first = planner.plan(objective=question, persona="admin")
        second = planner.plan(objective=question, persona="admin")
        assert [step.agent_type for step in first.steps] == [step.agent_type for step in second.steps]
        assert first.steps
