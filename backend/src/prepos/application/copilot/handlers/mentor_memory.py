from __future__ import annotations

from prepos.application.copilot.dto import CopilotQueryResponse, CopilotSourceResponse
from prepos.application.copilot.handlers.student_memory import map_student_memory_to_copilot_response
from prepos.application.memory.memory_service import CoachingMemoryService

MENTOR_MEMORY_INTENTS: frozenset[str] = frozenset(
    {
        "intervention_history",
        "coaching_timeline",
        "successful_interventions",
        "failed_interventions",
    }
)

MENTOR_MEMORY_INTROS: dict[str, str] = {
    "intervention_history": "Intervention history for this student:",
    "coaching_timeline": "Coaching timeline for this student:",
    "successful_interventions": "Successful coaching interventions:",
    "failed_interventions": "Interventions that underperformed:",
}


async def build_mentor_memory_response(
    *,
    intent: str,
    memory_service: CoachingMemoryService,
    tenant_id,
    student_user_id,
) -> CopilotQueryResponse:
    if intent in {"successful_interventions", "failed_interventions", "intervention_history"}:
        memories = await memory_service.list_memories(
            tenant_id=tenant_id,
            user_id=student_user_id,
            persona="mentor",
            memory_type="mentor_interventions",
            limit=50,
        )
        if intent == "successful_interventions":
            filtered = [
                item for item in memories.memories if item.memory_value.get("status") == "successful"
            ]
        elif intent == "failed_interventions":
            filtered = [item for item in memories.memories if item.memory_value.get("status") == "failed"]
        else:
            filtered = memories.memories
        response = map_student_memory_to_copilot_response(
            intent=intent,
            memories=filtered,
            intro=MENTOR_MEMORY_INTROS.get(intent),
        )
    else:
        memories = await memory_service.list_memories(
            tenant_id=tenant_id,
            user_id=student_user_id,
            persona="mentor",
            limit=50,
        )
        response = map_student_memory_to_copilot_response(
            intent=intent,
            memories=memories.memories,
            intro=MENTOR_MEMORY_INTROS.get(intent),
        )

    return CopilotQueryResponse(
        intent=response.intent,
        answer=response.answer,
        confidence=response.confidence,
        sources=[
            *response.sources,
            CopilotSourceResponse(label="Mentor coaching memory", reference="GET /memory/mentor/{student_id}"),
        ],
        student_context_used=True,
    )
