from __future__ import annotations

import pytest

from prepos.application.copilot.intent_router import route_intent, suggested_prompts_for_persona


@pytest.mark.parametrize(
    ("question", "expected"),
    [
        ("Explain federalism", "explain_concept"),
        ("Define separation of powers", "define_concept"),
        ("What is the basic structure doctrine?", "what_is"),
        ("Tell me about the Preamble", "explain_topic"),
        ("Describe the Parliament", "explain_topic"),
    ],
)
def test_student_content_intent_routing(question: str, expected: str) -> None:
    assert route_intent(persona="student", question=question) == expected


@pytest.mark.parametrize(
    ("question", "expected"),
    [
        ("Why is my readiness low?", "readiness_low"),
        ("what should I study today", "study_today"),
        ("Show my weakest concepts", "weakest_concepts"),
        ("Why was this recommendation generated?", "recommendation_why"),
        ("Am I on track for my goal?", "goal_on_track"),
        ("What activities should I complete next?", "next_activities"),
        ("What should I study next?", "study_next"),
        ("What gives me the biggest score improvement?", "highest_score_improvement"),
        ("Which weak concepts matter most?", "weak_concepts_priority"),
        ("Which topics are important for UPSC?", "important_topics"),
    ],
)
def test_student_intent_routing(question: str, expected: str) -> None:
    assert route_intent(persona="student", question=question) == expected


@pytest.mark.parametrize(
    ("question", "expected"),
    [
        ("Explain this student's weakest concept", "explain_student_weakness"),
        ("Give coaching guidance for federalism", "coaching_guidance"),
        ("Summarize Article 356 for mentoring", "explain_topic"),
        ("What should this student revise next?", "concept_revision_strategy"),
        ("Explain federalism", "explain_concept"),
    ],
)
def test_mentor_content_intent_routing(question: str, expected: str) -> None:
    assert route_intent(persona="mentor", question=question) == expected


@pytest.mark.parametrize(
    ("question", "expected"),
    [
        ("Summarize this student", "summarize_student"),
        ("Explain escalation reason", "escalation_reason"),
        ("Show top risks", "top_risks"),
        ("Show forecast summary", "forecast_summary"),
        ("Draft coaching note", "draft_coaching_note"),
        ("What should this student focus on?", "student_focus_areas"),
        ("Which intervention improves readiness fastest?", "highest_impact_intervention"),
    ],
)
def test_mentor_intent_routing(question: str, expected: str) -> None:
    assert route_intent(persona="mentor", question=question) == expected


@pytest.mark.parametrize(
    ("question", "expected"),
    [
        ("Platform health", "platform_health"),
        ("Worker status", "worker_status"),
        ("Outbox status", "outbox_status"),
        ("Deployment readiness", "deployment_readiness"),
    ],
)
def test_admin_intent_routing(question: str, expected: str) -> None:
    assert route_intent(persona="admin", question=question) == expected


def test_unknown_intent_returns_unknown() -> None:
    assert route_intent(persona="student", question="Tell me a joke") == "unknown"


def test_suggested_prompts_are_persona_scoped() -> None:
    student_prompts = suggested_prompts_for_persona("student")
    mentor_prompts = suggested_prompts_for_persona("mentor")
    assert "why is my readiness low" in student_prompts
    assert "summarize this student" in mentor_prompts
    assert "why is my readiness low" not in mentor_prompts
