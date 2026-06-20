from __future__ import annotations

from dataclasses import dataclass, field

from prepos.application.memory.memory_models import MemoryRecordResponse, TimelineEventResponse


@dataclass(frozen=True, slots=True)
class MemoryContext:
    recent_memories: list[MemoryRecordResponse] = field(default_factory=list)
    milestones: list[MemoryRecordResponse] = field(default_factory=list)
    outcome_summaries: list[MemoryRecordResponse] = field(default_factory=list)
    intervention_summaries: list[MemoryRecordResponse] = field(default_factory=list)
    weakness_trends: list[MemoryRecordResponse] = field(default_factory=list)
    context_lines: list[str] = field(default_factory=list)


STUDENT_RECENT_LIMIT = 20
STUDENT_MILESTONE_LIMIT = 5
STUDENT_OUTCOME_LIMIT = 5
MENTOR_RECENT_LIMIT = 50


class MemoryContextBuilder:
    def build_student_context(self, *, memories: list[MemoryRecordResponse]) -> MemoryContext:
        recent = memories[:STUDENT_RECENT_LIMIT]
        milestones = _top_by_type(memories, "progress_milestones", STUDENT_MILESTONE_LIMIT)
        outcomes = _top_outcomes(memories, STUDENT_OUTCOME_LIMIT)
        context_lines = _build_student_lines(recent=recent, milestones=milestones, outcomes=outcomes)
        return MemoryContext(
            recent_memories=recent,
            milestones=milestones,
            outcome_summaries=outcomes,
            context_lines=context_lines,
        )

    def build_mentor_context(self, *, memories: list[MemoryRecordResponse]) -> MemoryContext:
        recent = memories[:MENTOR_RECENT_LIMIT]
        milestones = _top_by_type(memories, "progress_milestones", STUDENT_MILESTONE_LIMIT)
        outcomes = _top_outcomes(memories, STUDENT_OUTCOME_LIMIT)
        interventions = _top_by_type(memories, "mentor_interventions", 10)
        weakness_trends = _top_by_type(memories, "weakness_trends", 10)
        context_lines = _build_mentor_lines(
            interventions=interventions,
            outcomes=outcomes,
            weakness_trends=weakness_trends,
            milestones=milestones,
        )
        return MemoryContext(
            recent_memories=recent,
            milestones=milestones,
            outcome_summaries=outcomes,
            intervention_summaries=interventions,
            weakness_trends=weakness_trends,
            context_lines=context_lines,
        )


def append_memory_context_to_answer(answer: str, context: MemoryContext) -> str:
    if not context.context_lines:
        return answer
    memory_block = "\n".join(f"- {line}" for line in context.context_lines[:5])
    return f"{answer}\n\nCoaching memory context:\n{memory_block}"


def _top_by_type(
    memories: list[MemoryRecordResponse],
    memory_type: str,
    limit: int,
) -> list[MemoryRecordResponse]:
    filtered = [item for item in memories if item.memory_type == memory_type]
    return filtered[:limit]


def _top_outcomes(memories: list[MemoryRecordResponse], limit: int) -> list[MemoryRecordResponse]:
    outcomes = [item for item in memories if item.memory_type == "recommendation_outcomes"]
    outcomes.sort(
        key=lambda item: float(item.memory_value.get("effectiveness_score", 0)),
        reverse=True,
    )
    return outcomes[:limit]


def _build_student_lines(
    *,
    recent: list[MemoryRecordResponse],
    milestones: list[MemoryRecordResponse],
    outcomes: list[MemoryRecordResponse],
) -> list[str]:
    lines: list[str] = []
    for outcome in outcomes:
        concept = str(outcome.memory_value.get("concept_name") or outcome.memory_value.get("concept_id"))
        actual_gain = float(outcome.memory_value.get("actual_gain", 0))
        effectiveness = float(outcome.memory_value.get("effectiveness_score", 0))
        lines.append(f"{concept} previously improved readiness by +{actual_gain:.1f} (effectiveness {effectiveness:.2f})")
    for milestone in milestones[:3]:
        lines.append(str(milestone.memory_value.get("summary") or milestone.memory_key))
    for item in recent:
        if item.memory_type != "recommendation_history":
            continue
        concept = str(item.memory_value.get("concept_name") or item.memory_value.get("concept_id"))
        shown_at = item.memory_value.get("shown_at")
        if shown_at:
            lines.append(f"{concept} was previously recommended on {shown_at}")
        if len(lines) >= 5:
            break
    return lines


def _build_mentor_lines(
    *,
    interventions: list[MemoryRecordResponse],
    outcomes: list[MemoryRecordResponse],
    weakness_trends: list[MemoryRecordResponse],
    milestones: list[MemoryRecordResponse],
) -> list[str]:
    lines: list[str] = []
    for intervention in interventions:
        if intervention.memory_value.get("status") != "successful":
            continue
        concept = str(intervention.memory_value.get("concept_name") or intervention.memory_value.get("concept_id"))
        effectiveness = float(intervention.memory_value.get("effectiveness_score", 0))
        lines.append(f"{concept} coaching previously produced {effectiveness:.1f}× expected gain")
    for outcome in outcomes[:3]:
        concept = str(outcome.memory_value.get("concept_name") or outcome.memory_value.get("concept_id"))
        actual_gain = float(outcome.memory_value.get("actual_gain", 0))
        lines.append(f"{concept} intervention outcome: +{actual_gain:.1f} readiness")
    stagnant = [item for item in weakness_trends if float(item.memory_value.get("delta", 0)) <= 0]
    for trend in stagnant[:3]:
        concept = str(trend.memory_value.get("concept_name") or trend.memory_value.get("concept_id"))
        lines.append(f"{concept} remains stagnant (weakness trend {trend.memory_value.get('delta')})")
    for milestone in milestones[:2]:
        lines.append(str(milestone.memory_value.get("summary") or milestone.memory_key))
    return lines


def memories_to_timeline(memories: list[MemoryRecordResponse]) -> list[TimelineEventResponse]:
    events: list[TimelineEventResponse] = []
    for memory in memories:
        value = memory.memory_value
        concept_id = value.get("concept_id")
        concept_name = value.get("concept_name")
        if memory.memory_type == "recommendation_history":
            summary = f"Recommended {concept_name or concept_id}"
        elif memory.memory_type == "recommendation_outcomes":
            summary = (
                f"Outcome for {concept_name or concept_id}: "
                f"+{float(value.get('actual_gain', 0)):.1f} readiness"
            )
        elif memory.memory_type == "progress_milestones":
            summary = str(value.get("summary") or "Progress milestone reached")
        elif memory.memory_type == "mentor_interventions":
            summary = f"Intervention on {concept_name or concept_id} ({value.get('status')})"
        elif memory.memory_type == "goal_changes":
            summary = "Goal trajectory updated"
        else:
            summary = f"{memory.memory_type.replace('_', ' ').title()} recorded"
        events.append(
            TimelineEventResponse(
                event_type=memory.memory_type,
                occurred_at=memory.updated_at,
                concept_id=str(concept_id) if concept_id else None,
                concept_name=str(concept_name) if concept_name else None,
                summary=summary,
                details=value,
            )
        )
    events.sort(key=lambda item: item.occurred_at, reverse=True)
    return events
