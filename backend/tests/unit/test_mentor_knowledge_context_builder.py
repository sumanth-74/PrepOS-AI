from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

from prepos.application.copilot.mentor_knowledge_context import MentorKnowledgeContextBuilder
from prepos.application.learning_graph.dto import LearningGraphWeaknessesResponse, WeaknessItemResponse
from prepos.application.mentor.mentor_dto import MentorCaseResponse
from prepos.application.twin.twin_dto import TwinDashboardResponse


def test_builds_concept_ids_and_retrieval_hints_from_weaknesses() -> None:
    student_id = uuid4()
    dashboard = TwinDashboardResponse(
        readiness_score=Decimal("42.5"),
        largest_negative_driver="revision_backlog",
        top_negative_drivers=["revision_backlog", "weak_mastery"],
        due_revision_count=3,
    )
    weaknesses = LearningGraphWeaknessesResponse(
        student_id=student_id,
        weaknesses=[
            WeaknessItemResponse(
                concept_id="polity_federalism",
                mastery_score=Decimal("0.35"),
                retention_score=Decimal("0.40"),
                importance_score=Decimal("0.90"),
                weakness_score=Decimal("0.82"),
            ),
            WeaknessItemResponse(
                concept_id="polity_basic_structure",
                mastery_score=Decimal("0.50"),
                retention_score=Decimal("0.55"),
                importance_score=Decimal("0.80"),
                weakness_score=Decimal("0.61"),
            ),
        ],
    )

    context = MentorKnowledgeContextBuilder().build(
        student_id=student_id,
        case_id=None,
        dashboard=dashboard,
        weaknesses=weaknesses,
    )

    assert context.concept_ids == ("polity_federalism", "polity_basic_structure")
    assert "polity_federalism" in context.retrieval_hints
    assert "revision backlog" in context.retrieval_hints
    assert context.student_context_used is True
    assert "polity_federalism" in context.student_context_summary


def test_includes_mentor_case_in_context_and_hints() -> None:
    student_id = uuid4()
    case_id = uuid4()
    dashboard = TwinDashboardResponse(readiness_score=Decimal("55"))
    weaknesses = LearningGraphWeaknessesResponse(student_id=student_id, weaknesses=[])
    mentor_case = MentorCaseResponse(
        case_id=case_id,
        student_id=student_id,
        exam_id="upsc_cse",
        status="open",
        priority="high",
        mentor_action_type="concept_coaching",
        escalation_level="moderate",
        mentor_action_priority=Decimal("0.8"),
        opened_at=__import__("datetime").datetime.now(__import__("datetime").UTC),
    )

    context = MentorKnowledgeContextBuilder().build(
        student_id=student_id,
        case_id=case_id,
        dashboard=dashboard,
        weaknesses=weaknesses,
        mentor_case=mentor_case,
    )

    assert "concept coaching" in context.retrieval_hints
    assert "concept_coaching" in context.student_context_summary or "concept coaching" in context.student_context_summary
    assert context.student_context_used is True
