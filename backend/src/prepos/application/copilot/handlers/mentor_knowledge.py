from __future__ import annotations

from prepos.application.copilot.dto import CopilotQueryResponse
from prepos.application.copilot.handlers.student_knowledge import map_knowledge_to_copilot_response
from prepos.application.knowledge.dto import KnowledgeAskResponse

MENTOR_CONTENT_INTENTS: frozenset[str] = frozenset(
    {
        "explain_concept",
        "explain_topic",
        "coaching_guidance",
        "explain_student_weakness",
        "concept_revision_strategy",
    }
)


def map_mentor_knowledge_to_copilot_response(
    *,
    intent: str,
    knowledge: KnowledgeAskResponse,
    student_context_used: bool,
) -> CopilotQueryResponse:
    response = map_knowledge_to_copilot_response(intent=intent, knowledge=knowledge)
    response.student_context_used = student_context_used
    return response
