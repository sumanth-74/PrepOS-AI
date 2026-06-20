from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from prepos.application.learning_graph.dto import LearningGraphWeaknessesResponse, WeaknessItemResponse
from prepos.application.mentor.mentor_dto import MentorCaseResponse
from prepos.application.twin.twin_dto import TwinDashboardResponse


@dataclass(frozen=True, slots=True)
class WeakConceptMetadata:
    concept_id: str
    weakness_score: Decimal
    mastery_score: Decimal


@dataclass(frozen=True, slots=True)
class MentorKnowledgeContext:
    concept_ids: tuple[str, ...]
    weak_concepts: tuple[WeakConceptMetadata, ...]
    retrieval_hints: tuple[str, ...]
    student_context_summary: str
    student_context_used: bool


class MentorKnowledgeContextBuilder:
    _MAX_WEAK_CONCEPTS = 5
    _MAX_DRIVERS = 3

    def build(
        self,
        *,
        student_id: UUID,
        case_id: UUID | None,
        dashboard: TwinDashboardResponse,
        weaknesses: LearningGraphWeaknessesResponse,
        mentor_case: MentorCaseResponse | None = None,
    ) -> MentorKnowledgeContext:
        del case_id
        weak_concepts = self._select_weak_concepts(weaknesses.weaknesses)
        concept_ids = tuple(item.concept_id for item in weak_concepts)
        retrieval_hints = self._build_retrieval_hints(
            concept_ids=concept_ids,
            dashboard=dashboard,
            mentor_case=mentor_case,
        )
        student_context_summary = self._build_student_context_summary(
            student_id=student_id,
            dashboard=dashboard,
            weak_concepts=weak_concepts,
            mentor_case=mentor_case,
        )
        student_context_used = bool(
            concept_ids
            or dashboard.readiness_score is not None
            or dashboard.largest_negative_driver
            or mentor_case is not None
        )
        return MentorKnowledgeContext(
            concept_ids=concept_ids,
            weak_concepts=weak_concepts,
            retrieval_hints=retrieval_hints,
            student_context_summary=student_context_summary,
            student_context_used=student_context_used,
        )

    def _select_weak_concepts(
        self,
        weaknesses: list[WeaknessItemResponse],
    ) -> tuple[WeakConceptMetadata, ...]:
        ranked = sorted(weaknesses, key=lambda item: item.weakness_score, reverse=True)
        return tuple(
            WeakConceptMetadata(
                concept_id=item.concept_id,
                weakness_score=item.weakness_score,
                mastery_score=item.mastery_score,
            )
            for item in ranked[: self._MAX_WEAK_CONCEPTS]
        )

    def _build_retrieval_hints(
        self,
        *,
        concept_ids: tuple[str, ...],
        dashboard: TwinDashboardResponse,
        mentor_case: MentorCaseResponse | None,
    ) -> tuple[str, ...]:
        hints: list[str] = []
        if concept_ids:
            hints.extend(concept_ids)
        if dashboard.largest_negative_driver:
            hints.append(dashboard.largest_negative_driver.replace("_", " "))
        for driver in dashboard.top_negative_drivers[: self._MAX_DRIVERS]:
            normalized = driver.replace("_", " ")
            if normalized not in hints:
                hints.append(normalized)
        if mentor_case is not None:
            hints.append(mentor_case.mentor_action_type.replace("_", " "))
            hints.append(mentor_case.escalation_level.replace("_", " "))
        return tuple(hints)

    def _build_student_context_summary(
        self,
        *,
        student_id: UUID,
        dashboard: TwinDashboardResponse,
        weak_concepts: tuple[WeakConceptMetadata, ...],
        mentor_case: MentorCaseResponse | None,
    ) -> str:
        lines = [f"Student ID: {student_id}"]
        if dashboard.readiness_score is not None:
            lines.append(f"Readiness score: {dashboard.readiness_score}")
        if dashboard.largest_negative_driver:
            lines.append(
                f"Primary negative driver: {dashboard.largest_negative_driver.replace('_', ' ')}"
            )
        elif dashboard.top_negative_drivers:
            drivers = ", ".join(driver.replace("_", " ") for driver in dashboard.top_negative_drivers[:3])
            lines.append(f"Negative drivers: {drivers}")
        if dashboard.due_revision_count > 0:
            lines.append(f"Due revisions: {dashboard.due_revision_count}")
        if weak_concepts:
            lines.append("Weakest concepts:")
            for item in weak_concepts:
                lines.append(
                    f"- {item.concept_id} "
                    f"(weakness={item.weakness_score}, mastery={item.mastery_score})"
                )
        if mentor_case is not None:
            lines.append(
                "Active mentor case: "
                f"{mentor_case.status} / {mentor_case.mentor_action_type} "
                f"(priority={mentor_case.priority})"
            )
        return "\n".join(lines)
