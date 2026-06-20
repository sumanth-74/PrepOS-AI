from __future__ import annotations

from uuid import uuid4

from prepos.application.copilot.handlers.student_knowledge import map_knowledge_to_copilot_response
from prepos.application.knowledge.confidence import INSUFFICIENT_EVIDENCE_ANSWER
from prepos.application.knowledge.dto import KnowledgeAskCitation, KnowledgeAskResponse


def test_map_knowledge_response_includes_citations_for_high_confidence() -> None:
    chunk_id = uuid4()
    knowledge = KnowledgeAskResponse(
        answer="Federalism divides power between centre and states.",
        citations=[KnowledgeAskCitation(chunk_id=chunk_id, source_title="Polity Notes")],
        confidence="high",
    )

    response = map_knowledge_to_copilot_response(intent="explain_concept", knowledge=knowledge)

    assert response.intent == "explain_concept"
    assert response.answer == knowledge.answer
    assert response.confidence == "high"
    assert len(response.citations) == 1
    assert response.citations[0].source_title == "Polity Notes"
    assert any(source.label == "Polity Notes" for source in response.sources)


def test_map_knowledge_response_uses_fallback_for_low_confidence() -> None:
    knowledge = KnowledgeAskResponse(
        answer="Speculative answer.",
        citations=[KnowledgeAskCitation(chunk_id=uuid4(), source_title="Unused")],
        confidence="low",
    )

    response = map_knowledge_to_copilot_response(intent="what_is", knowledge=knowledge)

    assert response.intent == "what_is"
    assert response.answer == INSUFFICIENT_EVIDENCE_ANSWER
    assert response.confidence == "low"
    assert response.citations == []
