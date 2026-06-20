from __future__ import annotations

from prepos.application.copilot.dto import CopilotQueryResponse, CopilotSourceResponse
from prepos.application.memory.memory_context import memories_to_timeline
from prepos.application.memory.memory_models import MemoryRecordResponse
from prepos.application.memory.memory_service import CoachingMemoryService

STUDENT_MEMORY_INTENTS: frozenset[str] = frozenset(
    {
        "learning_history",
        "progress_timeline",
        "past_recommendations",
        "milestones",
    }
)

STUDENT_MEMORY_INJECTION_INTENTS: frozenset[str] = frozenset(
    {
        "study_next",
        "weekly_focus",
        "progress_summary",
        "recommendation_progress",
        "learning_progress",
    }
)

STUDENT_MEMORY_INTROS: dict[str, str] = {
    "learning_history": "Your recent learning history from structured coaching memory:",
    "progress_timeline": "Your learning progress timeline:",
    "past_recommendations": "Past recommendations stored in your coaching memory:",
    "milestones": "Milestones you have achieved:",
}


def map_student_memory_to_copilot_response(
    *,
    intent: str,
    memories: list[MemoryRecordResponse],
    intro: str | None = None,
) -> CopilotQueryResponse:
    resolved_intro = intro or STUDENT_MEMORY_INTROS.get(intent, "Your coaching memory:")
    lines = [resolved_intro, ""]
    if not memories:
        lines.append("No coaching memories recorded yet. Complete recommendations to build your history.")
    else:
        if intent == "progress_timeline":
            for event in memories_to_timeline(memories)[:10]:
                lines.append(f"- {event.occurred_at.date()}: {event.summary}")
        elif intent == "milestones":
            for item in memories[:10]:
                summary = item.memory_value.get("summary") or item.memory_key
                lines.append(f"- {summary}")
        elif intent == "past_recommendations":
            for item in memories[:10]:
                if item.memory_type != "recommendation_history":
                    continue
                concept = item.memory_value.get("concept_name") or item.memory_value.get("concept_id")
                lines.append(f"- {concept} recommended (impact {item.memory_value.get('impact_score')})")
        else:
            for item in memories[:10]:
                concept = item.memory_value.get("concept_name") or item.memory_value.get("concept_id") or item.memory_type
                lines.append(f"- [{item.memory_type}] {concept}")

    return CopilotQueryResponse(
        intent=intent,
        answer="\n".join(lines),
        confidence="high" if memories else "low",
        sources=[
            CopilotSourceResponse(label="Coaching memory", reference="GET /memory/student"),
            CopilotSourceResponse(label="Learning timeline", reference="GET /memory/student/timeline"),
        ],
    )


async def build_student_memory_response(
    *,
    intent: str,
    memory_service: CoachingMemoryService,
    tenant_id,
    user_id,
) -> CopilotQueryResponse:
    if intent == "milestones":
        milestones = await memory_service.get_milestones(tenant_id=tenant_id, user_id=user_id)
        return map_student_memory_to_copilot_response(intent=intent, memories=milestones.milestones)
    if intent == "past_recommendations":
        memories = await memory_service.list_memories(
            tenant_id=tenant_id,
            user_id=user_id,
            persona="student",
            memory_type="recommendation_history",
            limit=20,
        )
        return map_student_memory_to_copilot_response(intent=intent, memories=memories.memories)
    if intent == "progress_timeline":
        memories = await memory_service.list_memories(
            tenant_id=tenant_id,
            user_id=user_id,
            persona="student",
            limit=50,
        )
        return map_student_memory_to_copilot_response(intent=intent, memories=memories.memories)

    memories = await memory_service.list_memories(
        tenant_id=tenant_id,
        user_id=user_id,
        persona="student",
        limit=20,
    )
    return map_student_memory_to_copilot_response(intent=intent, memories=memories.memories)
