from __future__ import annotations

from prepos.application.copilot.dto import (
    CopilotCitationResponse,
    CopilotQueryResponse,
    CopilotSourceResponse,
)
from prepos.application.knowledge.confidence import INSUFFICIENT_EVIDENCE_ANSWER
from prepos.application.knowledge.dto import KnowledgeAskResponse

STUDENT_PYQ_INTENTS: frozenset[str] = frozenset(
    {
        "show_pyqs",
        "pyq_trends",
        "topic_importance",
        "exam_probability",
    }
)


def map_pyq_to_copilot_response(
    *,
    intent: str,
    knowledge: KnowledgeAskResponse,
) -> CopilotQueryResponse:
    confidence = knowledge.confidence
    if confidence == "low":
        return CopilotQueryResponse(
            intent=intent,
            answer=INSUFFICIENT_EVIDENCE_ANSWER,
            citations=[],
            confidence=confidence,
            sources=[
                CopilotSourceResponse(
                    label="PYQ Knowledge Agent",
                    reference="POST /pyq/search",
                )
            ],
        )

    citations = [
        CopilotCitationResponse(
            chunk_id=item.chunk_id,
            source_title=item.source_title,
        )
        for item in knowledge.citations
    ]
    sources = [
        CopilotSourceResponse(label=item.source_title, reference=f"chunk:{item.chunk_id}")
        for item in citations
    ]
    sources.append(CopilotSourceResponse(label="PYQ Knowledge Agent", reference="POST /pyq/search"))

    return CopilotQueryResponse(
        intent=intent,
        answer=knowledge.answer,
        citations=citations,
        confidence=confidence,
        sources=sources,
    )
