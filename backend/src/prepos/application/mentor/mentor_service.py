from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from prepos.application.mentor.mentor_effectiveness_learning_ports import (
    MentorEffectivenessLearningRepositoryPort,
)
from prepos.application.twin.projection_ports import TwinProjectionRepositoryPort
from prepos.domain.mentor.coaching_recommendations_v1 import (
    CoachingRecommendation,
    generate_coaching_recommendations_v1,
)
from prepos.domain.mentor.escalation_v1 import EscalationSignal, build_escalation_signal_v1
from prepos.domain.mentor.events import (
    EscalationUpdated,
    MentorActionUpdated,
    MentorInsightUpdated,
    MentorSummaryUpdated,
)
from prepos.domain.mentor.mentor_actions_v1 import (
    MentorAction,
    MentorActionInputs,
    build_mentor_action_v1,
    select_mentor_action_type_v1,
)
from prepos.domain.mentor.mentor_insights_v1 import MentorInsight, generate_mentor_insights_v1
from prepos.domain.mentor.mentor_payload_v1 import (
    build_mentor_payload_section,
    extract_mentor_inputs_from_projection,
    serialize_escalation,
    serialize_mentor_action,
)
from prepos.domain.mentor.mentor_summary_v1 import MentorSummary, build_mentor_summary_v1
from prepos.events.outbox.publisher import OutboxPublisher


@dataclass(frozen=True, slots=True)
class MentorSnapshot:
    summary: MentorSummary
    insights: tuple[MentorInsight, ...]
    recommendations: tuple[CoachingRecommendation, ...]
    mentor_payload: dict[str, object]


@dataclass(frozen=True, slots=True)
class MentorActionSnapshot:
    action: MentorAction
    escalation: EscalationSignal
    mentor_payload_patch: dict[str, object]


class MentorService:
    def __init__(
        self,
        *,
        projection_repo: TwinProjectionRepositoryPort,
        outbox: OutboxPublisher,
        learning_repo: MentorEffectivenessLearningRepositoryPort | None = None,
    ) -> None:
        self._projection_repo = projection_repo
        self._outbox = outbox
        self._learning_repo = learning_repo

    async def compute_mentor(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
    ) -> MentorSnapshot | None:
        twin = await self._projection_repo.get_projection(tenant_id, student_id, exam_id)
        if twin is None:
            return None

        inputs = extract_mentor_inputs_from_projection(
            readiness_score=twin.readiness_score,
            due_revision_count=twin.due_revision_count,
            high_risk_concept_count=twin.high_risk_concept_count,
            largest_negative_driver=twin.largest_negative_driver,
            twin_payload=twin.twin_payload,
        )
        insights = generate_mentor_insights_v1(inputs)
        summary = build_mentor_summary_v1(inputs=inputs, insights=insights)
        recommendations = generate_coaching_recommendations_v1(inputs)
        action_snapshot = await self._build_action_snapshot(
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
            inputs=inputs,
            summary=summary,
            insights=insights,
        )
        mentor_payload = build_mentor_payload_section(
            summary=summary,
            insights=insights,
            recommendations=recommendations,
            mentor_action=action_snapshot.action,
            escalation=action_snapshot.escalation,
        )
        return MentorSnapshot(
            summary=summary,
            insights=insights,
            recommendations=recommendations,
            mentor_payload=mentor_payload,
        )

    async def compute_mentor_action(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
    ) -> MentorActionSnapshot | None:
        twin = await self._projection_repo.get_projection(tenant_id, student_id, exam_id)
        if twin is None:
            return None

        inputs = extract_mentor_inputs_from_projection(
            readiness_score=twin.readiness_score,
            due_revision_count=twin.due_revision_count,
            high_risk_concept_count=twin.high_risk_concept_count,
            largest_negative_driver=twin.largest_negative_driver,
            twin_payload=twin.twin_payload,
        )
        insights = generate_mentor_insights_v1(inputs)
        summary = build_mentor_summary_v1(inputs=inputs, insights=insights)
        return await self._build_action_snapshot(
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
            inputs=inputs,
            summary=summary,
            insights=insights,
        )

    async def _build_action_snapshot(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        inputs: object,
        summary: MentorSummary,
        insights: tuple[MentorInsight, ...],
    ) -> MentorActionSnapshot:
        from prepos.domain.mentor.mentor_insights_v1 import MentorInsightInputs

        assert isinstance(inputs, MentorInsightInputs)
        action_inputs = MentorActionInputs(
            summary=summary,
            insights=insights,
            signals=inputs,
        )
        action_type = select_mentor_action_type_v1(action_inputs)
        effectiveness_score = None
        if self._learning_repo is not None:
            effectiveness = await self._learning_repo.get_action_effectiveness(
                tenant_id,
                action_type.value,
            )
            if effectiveness is not None:
                effectiveness_score = effectiveness.effectiveness_score
        action = build_mentor_action_v1(
            action_inputs,
            action_effectiveness_score=effectiveness_score,
        )
        escalation = build_escalation_signal_v1(inputs)
        return MentorActionSnapshot(
            action=action,
            escalation=escalation,
            mentor_payload_patch={
                "mentor_action": serialize_mentor_action(action),
                "escalation": serialize_escalation(escalation),
            },
        )

    async def publish_mentor_insight_updated(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        correlation_id: str,
        causation_id: str | None,
        current_time: datetime | None = None,
    ) -> MentorSnapshot | None:
        snapshot = await self.compute_mentor(
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
        )
        if snapshot is None:
            return None

        top_insight = snapshot.insights[0] if snapshot.insights else None
        await self._outbox.enqueue_mentor_insight_updated(
            MentorInsightUpdated(
                tenant_id=tenant_id,
                student_id=student_id,
                exam_id=exam_id,
                insight_count=len(snapshot.insights),
                top_insight_type=top_insight.insight_type.value if top_insight else None,
                top_insight_priority=top_insight.priority.value if top_insight else None,
                correlation_id=correlation_id,
                causation_id=causation_id,
                occurred_at=current_time or datetime.now(UTC),
            )
        )
        return snapshot

    async def publish_mentor_summary_updated(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        correlation_id: str,
        causation_id: str | None,
        current_time: datetime | None = None,
    ) -> MentorSnapshot | None:
        snapshot = await self.compute_mentor(
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
        )
        if snapshot is None:
            return None

        await self._outbox.enqueue_mentor_summary_updated(
            MentorSummaryUpdated(
                tenant_id=tenant_id,
                student_id=student_id,
                exam_id=exam_id,
                mentor_status=snapshot.summary.overall_status,
                top_mentor_message=snapshot.summary.key_message,
                insight_count=len(snapshot.insights),
                recommendation_count=len(snapshot.recommendations),
                correlation_id=correlation_id,
                causation_id=causation_id,
                occurred_at=current_time or datetime.now(UTC),
            )
        )
        return snapshot

    async def publish_mentor_action_updated(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        correlation_id: str,
        causation_id: str | None,
        current_time: datetime | None = None,
    ) -> MentorActionSnapshot | None:
        snapshot = await self.compute_mentor_action(
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
        )
        if snapshot is None:
            return None

        await self._outbox.enqueue_mentor_action_updated(
            MentorActionUpdated(
                tenant_id=tenant_id,
                student_id=student_id,
                exam_id=exam_id,
                action_type=snapshot.action.action_type,
                priority_score=float(snapshot.action.priority_score),
                urgency=snapshot.action.urgency.value,
                expected_impact=float(snapshot.action.expected_impact),
                explanation=snapshot.action.explanation,
                correlation_id=correlation_id,
                causation_id=causation_id,
                occurred_at=current_time or datetime.now(UTC),
            )
        )
        return snapshot

    async def publish_escalation_updated(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        correlation_id: str,
        causation_id: str | None,
        current_time: datetime | None = None,
    ) -> MentorActionSnapshot | None:
        snapshot = await self.compute_mentor_action(
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
        )
        if snapshot is None:
            return None

        await self._outbox.enqueue_escalation_updated(
            EscalationUpdated(
                tenant_id=tenant_id,
                student_id=student_id,
                exam_id=exam_id,
                escalation_level=snapshot.escalation.level,
                reason=snapshot.escalation.reason,
                correlation_id=correlation_id,
                causation_id=causation_id,
                occurred_at=current_time or datetime.now(UTC),
            )
        )
        return snapshot
