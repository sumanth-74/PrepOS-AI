from __future__ import annotations

from prepos.application.copilot.handlers.student_pyq import map_pyq_to_copilot_response
from prepos.application.knowledge.dto import KnowledgeAskResponse

MENTOR_PYQ_INTENTS: frozenset[str] = frozenset(
    {
        "show_pyqs",
        "pyq_trends",
        "topic_importance",
        "exam_probability",
        "pyq_revision",
        "high_frequency_weak_concepts",
    }
)


def map_mentor_pyq_to_copilot_response(
    *,
    intent: str,
    knowledge: KnowledgeAskResponse,
    student_context_used: bool,
) -> object:
    from prepos.application.copilot.dto import CopilotQueryResponse

    response = map_pyq_to_copilot_response(intent=intent, knowledge=knowledge)
    assert isinstance(response, CopilotQueryResponse)
    return CopilotQueryResponse(
        intent=response.intent,
        answer=response.answer,
        citations=response.citations,
        confidence=response.confidence,
        sources=response.sources,
        student_context_used=student_context_used,
    )
