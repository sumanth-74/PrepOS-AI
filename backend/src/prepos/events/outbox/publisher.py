from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from prepos.domain.events.envelope import DomainEventEnvelope
from prepos.infrastructure.db.repositories.event_repository import OutboxRepository


class OutboxPublisher:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = OutboxRepository(session)

    async def enqueue(self, envelope: DomainEventEnvelope) -> None:
        await self._repo.enqueue(envelope)

    async def enqueue_student_registered(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        correlation_id: str,
    ) -> None:
        now = datetime.now(UTC)
        envelope = DomainEventEnvelope(
            event_id=uuid4(),
            event_version=1,
            event_type="StudentRegistered",
            occurred_at=now,
            recorded_at=now,
            tenant_id=tenant_id,
            correlation_id=correlation_id,
            causation_id=None,
            producer="auth_service",
            payload={"user_id": str(user_id), "tenant_id": str(tenant_id)},
            metadata={"user_id": str(user_id)},
        )
        await self.enqueue(envelope)

    async def enqueue_student_onboarding_completed(self, event: object) -> None:
        from prepos.domain.student.events import StudentOnboardingCompleted

        assert isinstance(event, StudentOnboardingCompleted)
        now = datetime.now(UTC)
        envelope = DomainEventEnvelope(
            event_id=uuid4(),
            event_version=1,
            event_type=event.event_type,
            occurred_at=event.occurred_at,
            recorded_at=now,
            tenant_id=event.tenant_id,
            correlation_id=event.correlation_id,
            causation_id=event.causation_id,
            producer="student_onboarding_service",
            payload=event.to_payload(),
            metadata={
                "student_id": str(event.student_id),
                "exam_id": event.exam_id,
            },
        )
        await self.enqueue(envelope)

    async def enqueue_study_plan_updated(self, event: object) -> None:
        from prepos.domain.study_plan.events import StudyPlanUpdated

        assert isinstance(event, StudyPlanUpdated)
        now = datetime.now(UTC)
        envelope = DomainEventEnvelope(
            event_id=uuid4(),
            event_version=1,
            event_type=event.event_type,
            occurred_at=event.occurred_at,
            recorded_at=now,
            tenant_id=event.tenant_id,
            correlation_id=event.correlation_id,
            causation_id=event.causation_id,
            producer="study_plan_service",
            payload=event.to_payload(),
            metadata={
                "student_id": str(event.student_id),
                "exam_id": event.exam_id,
            },
        )
        await self.enqueue(envelope)

    async def enqueue_study_plan_item_completed(self, event: object) -> None:
        from prepos.domain.study_plan.events import StudyPlanItemCompleted

        assert isinstance(event, StudyPlanItemCompleted)
        now = datetime.now(UTC)
        envelope = DomainEventEnvelope(
            event_id=uuid4(),
            event_version=1,
            event_type=event.event_type,
            occurred_at=event.occurred_at,
            recorded_at=now,
            tenant_id=event.tenant_id,
            correlation_id=event.correlation_id,
            causation_id=event.causation_id,
            producer="study_plan_execution_service",
            payload=event.to_payload(),
            metadata={
                "student_id": str(event.student_id),
                "exam_id": event.exam_id,
                "concept_id": event.concept_id,
            },
        )
        await self.enqueue(envelope)

    async def enqueue_study_plan_item_skipped(self, event: object) -> None:
        from prepos.domain.study_plan.events import StudyPlanItemSkipped

        assert isinstance(event, StudyPlanItemSkipped)
        now = datetime.now(UTC)
        envelope = DomainEventEnvelope(
            event_id=uuid4(),
            event_version=1,
            event_type=event.event_type,
            occurred_at=event.occurred_at,
            recorded_at=now,
            tenant_id=event.tenant_id,
            correlation_id=event.correlation_id,
            causation_id=event.causation_id,
            producer="study_plan_execution_service",
            payload=event.to_payload(),
            metadata={
                "student_id": str(event.student_id),
                "exam_id": event.exam_id,
                "concept_id": event.concept_id,
            },
        )
        await self.enqueue(envelope)

    async def enqueue_study_behavior_updated(self, event: object) -> None:
        from prepos.domain.study_plan.events import StudyBehaviorUpdated

        assert isinstance(event, StudyBehaviorUpdated)
        now = datetime.now(UTC)
        envelope = DomainEventEnvelope(
            event_id=uuid4(),
            event_version=1,
            event_type=event.event_type,
            occurred_at=event.occurred_at,
            recorded_at=now,
            tenant_id=event.tenant_id,
            correlation_id=event.correlation_id,
            causation_id=event.causation_id,
            producer="study_plan_execution_tracker",
            payload=event.to_payload(),
            metadata={
                "student_id": str(event.student_id),
                "exam_id": event.exam_id,
            },
        )
        await self.enqueue(envelope)

    async def enqueue_goal_updated(self, event: object) -> None:
        from prepos.domain.goal.events import GoalUpdated

        assert isinstance(event, GoalUpdated)
        now = datetime.now(UTC)
        envelope = DomainEventEnvelope(
            event_id=uuid4(),
            event_version=1,
            event_type=event.event_type,
            occurred_at=event.occurred_at,
            recorded_at=now,
            tenant_id=event.tenant_id,
            correlation_id=event.correlation_id,
            causation_id=event.causation_id,
            producer="goal_service",
            payload=event.to_payload(),
            metadata={
                "student_id": str(event.student_id),
                "exam_id": event.exam_id,
            },
        )
        await self.enqueue(envelope)

    async def enqueue_forecast_updated(self, event: object) -> None:
        from prepos.domain.goal.events import ForecastUpdated

        assert isinstance(event, ForecastUpdated)
        now = datetime.now(UTC)
        envelope = DomainEventEnvelope(
            event_id=uuid4(),
            event_version=1,
            event_type=event.event_type,
            occurred_at=event.occurred_at,
            recorded_at=now,
            tenant_id=event.tenant_id,
            correlation_id=event.correlation_id,
            causation_id=event.causation_id,
            producer="forecast_service",
            payload=event.to_payload(),
            metadata={
                "student_id": str(event.student_id),
                "exam_id": event.exam_id,
            },
        )
        await self.enqueue(envelope)

    async def enqueue_predicted_score_updated(self, event: object) -> None:
        from prepos.domain.scoring.events import PredictedScoreUpdated

        assert isinstance(event, PredictedScoreUpdated)
        now = datetime.now(UTC)
        envelope = DomainEventEnvelope(
            event_id=uuid4(),
            event_version=1,
            event_type=event.event_type,
            occurred_at=event.occurred_at,
            recorded_at=now,
            tenant_id=event.tenant_id,
            correlation_id=event.correlation_id,
            causation_id=event.causation_id,
            producer="predicted_score_service",
            payload=event.to_payload(),
            metadata={
                "student_id": str(event.student_id),
                "exam_id": event.exam_id,
            },
        )
        await self.enqueue(envelope)

    async def enqueue_milestone_updated(self, event: object) -> None:
        from prepos.domain.goal.events import MilestoneUpdated

        assert isinstance(event, MilestoneUpdated)
        now = datetime.now(UTC)
        envelope = DomainEventEnvelope(
            event_id=uuid4(),
            event_version=1,
            event_type=event.event_type,
            occurred_at=event.occurred_at,
            recorded_at=now,
            tenant_id=event.tenant_id,
            correlation_id=event.correlation_id,
            causation_id=event.causation_id,
            producer="milestone_service",
            payload=event.to_payload(),
            metadata={
                "student_id": str(event.student_id),
                "exam_id": event.exam_id,
            },
        )
        await self.enqueue(envelope)

    async def enqueue_forecast_probability_updated(self, event: object) -> None:
        from prepos.domain.scoring.events import ForecastProbabilityUpdated

        assert isinstance(event, ForecastProbabilityUpdated)
        now = datetime.now(UTC)
        envelope = DomainEventEnvelope(
            event_id=uuid4(),
            event_version=1,
            event_type=event.event_type,
            occurred_at=event.occurred_at,
            recorded_at=now,
            tenant_id=event.tenant_id,
            correlation_id=event.correlation_id,
            causation_id=event.causation_id,
            producer="forecast_probability_service",
            payload=event.to_payload(),
            metadata={
                "student_id": str(event.student_id),
                "exam_id": event.exam_id,
            },
        )
        await self.enqueue(envelope)

    async def enqueue_twin_decision_updated(self, event: object) -> None:
        from prepos.domain.twin.events import TwinDecisionUpdated

        assert isinstance(event, TwinDecisionUpdated)
        now = datetime.now(UTC)
        envelope = DomainEventEnvelope(
            event_id=uuid4(),
            event_version=1,
            event_type=event.event_type,
            occurred_at=event.occurred_at,
            recorded_at=now,
            tenant_id=event.tenant_id,
            correlation_id=event.correlation_id,
            causation_id=event.causation_id,
            producer="twin_decision_service",
            payload=event.to_payload(),
            metadata={
                "student_id": str(event.student_id),
                "exam_id": event.exam_id,
            },
        )
        await self.enqueue(envelope)

    async def enqueue_twin_intervention_updated(self, event: object) -> None:
        from prepos.domain.twin.events import TwinInterventionUpdated

        assert isinstance(event, TwinInterventionUpdated)
        now = datetime.now(UTC)
        envelope = DomainEventEnvelope(
            event_id=uuid4(),
            event_version=1,
            event_type=event.event_type,
            occurred_at=event.occurred_at,
            recorded_at=now,
            tenant_id=event.tenant_id,
            correlation_id=event.correlation_id,
            causation_id=event.causation_id,
            producer="twin_intervention_service",
            payload=event.to_payload(),
            metadata={
                "student_id": str(event.student_id),
                "exam_id": event.exam_id,
            },
        )
        await self.enqueue(envelope)

    async def enqueue_intervention_outcome_calculated(self, event: object) -> None:
        from prepos.domain.twin.events import InterventionOutcomeCalculated

        assert isinstance(event, InterventionOutcomeCalculated)
        now = datetime.now(UTC)
        envelope = DomainEventEnvelope(
            event_id=uuid4(),
            event_version=1,
            event_type=event.event_type,
            occurred_at=event.occurred_at,
            recorded_at=now,
            tenant_id=event.tenant_id,
            correlation_id=event.correlation_id,
            causation_id=event.causation_id,
            producer="intervention_outcome_service",
            payload=event.to_payload(),
            metadata={
                "student_id": str(event.student_id),
                "exam_id": event.exam_id,
            },
        )
        await self.enqueue(envelope)

    async def enqueue_intervention_optimization_updated(self, event: object) -> None:
        from prepos.domain.twin.events import InterventionOptimizationUpdated

        assert isinstance(event, InterventionOptimizationUpdated)
        now = datetime.now(UTC)
        envelope = DomainEventEnvelope(
            event_id=uuid4(),
            event_version=1,
            event_type=event.event_type,
            occurred_at=event.occurred_at,
            recorded_at=now,
            tenant_id=event.tenant_id,
            correlation_id=event.correlation_id,
            causation_id=event.causation_id,
            producer="intervention_optimization_service",
            payload=event.to_payload(),
            metadata={
                "student_id": str(event.student_id),
                "exam_id": event.exam_id,
            },
        )
        await self.enqueue(envelope)

    async def enqueue_behavior_profile_updated(self, event: object) -> None:
        from prepos.domain.twin.events import BehaviorProfileUpdated

        assert isinstance(event, BehaviorProfileUpdated)
        now = datetime.now(UTC)
        envelope = DomainEventEnvelope(
            event_id=uuid4(),
            event_version=1,
            event_type=event.event_type,
            occurred_at=event.occurred_at,
            recorded_at=now,
            tenant_id=event.tenant_id,
            correlation_id=event.correlation_id,
            causation_id=event.causation_id,
            producer="behavior_profile_service",
            payload=event.to_payload(),
            metadata={
                "student_id": str(event.student_id),
                "exam_id": event.exam_id,
            },
        )
        await self.enqueue(envelope)

    async def enqueue_personalization_updated(self, event: object) -> None:
        from prepos.domain.twin.events import PersonalizationUpdated

        assert isinstance(event, PersonalizationUpdated)
        now = datetime.now(UTC)
        envelope = DomainEventEnvelope(
            event_id=uuid4(),
            event_version=1,
            event_type=event.event_type,
            occurred_at=event.occurred_at,
            recorded_at=now,
            tenant_id=event.tenant_id,
            correlation_id=event.correlation_id,
            causation_id=event.causation_id,
            producer="personalization_service",
            payload=event.to_payload(),
            metadata={
                "student_id": str(event.student_id),
                "exam_id": event.exam_id,
            },
        )
        await self.enqueue(envelope)

    async def enqueue_mentor_insight_updated(self, event: object) -> None:
        from prepos.domain.mentor.events import MentorInsightUpdated

        assert isinstance(event, MentorInsightUpdated)
        now = datetime.now(UTC)
        envelope = DomainEventEnvelope(
            event_id=uuid4(),
            event_version=1,
            event_type=event.event_type,
            occurred_at=event.occurred_at,
            recorded_at=now,
            tenant_id=event.tenant_id,
            correlation_id=event.correlation_id,
            causation_id=event.causation_id,
            producer="mentor_service",
            payload=event.to_payload(),
            metadata={
                "student_id": str(event.student_id),
                "exam_id": event.exam_id,
            },
        )
        await self.enqueue(envelope)

    async def enqueue_mentor_summary_updated(self, event: object) -> None:
        from prepos.domain.mentor.events import MentorSummaryUpdated

        assert isinstance(event, MentorSummaryUpdated)
        now = datetime.now(UTC)
        envelope = DomainEventEnvelope(
            event_id=uuid4(),
            event_version=1,
            event_type=event.event_type,
            occurred_at=event.occurred_at,
            recorded_at=now,
            tenant_id=event.tenant_id,
            correlation_id=event.correlation_id,
            causation_id=event.causation_id,
            producer="mentor_service",
            payload=event.to_payload(),
            metadata={
                "student_id": str(event.student_id),
                "exam_id": event.exam_id,
            },
        )
        await self.enqueue(envelope)

    async def enqueue_mentor_action_updated(self, event: object) -> None:
        from prepos.domain.mentor.events import MentorActionUpdated

        assert isinstance(event, MentorActionUpdated)
        now = datetime.now(UTC)
        envelope = DomainEventEnvelope(
            event_id=uuid4(),
            event_version=1,
            event_type=event.event_type,
            occurred_at=event.occurred_at,
            recorded_at=now,
            tenant_id=event.tenant_id,
            correlation_id=event.correlation_id,
            causation_id=event.causation_id,
            producer="mentor_service",
            payload=event.to_payload(),
            metadata={
                "student_id": str(event.student_id),
                "exam_id": event.exam_id,
            },
        )
        await self.enqueue(envelope)

    async def enqueue_escalation_updated(self, event: object) -> None:
        from prepos.domain.mentor.events import EscalationUpdated

        assert isinstance(event, EscalationUpdated)
        now = datetime.now(UTC)
        envelope = DomainEventEnvelope(
            event_id=uuid4(),
            event_version=1,
            event_type=event.event_type,
            occurred_at=event.occurred_at,
            recorded_at=now,
            tenant_id=event.tenant_id,
            correlation_id=event.correlation_id,
            causation_id=event.causation_id,
            producer="mentor_service",
            payload=event.to_payload(),
            metadata={
                "student_id": str(event.student_id),
                "exam_id": event.exam_id,
            },
        )
        await self.enqueue(envelope)

    async def enqueue_mentor_case_created(self, event: object) -> None:
        from prepos.domain.mentor.events import MentorCaseCreated

        assert isinstance(event, MentorCaseCreated)
        now = datetime.now(UTC)
        envelope = DomainEventEnvelope(
            event_id=uuid4(),
            event_version=1,
            event_type=event.event_type,
            occurred_at=event.occurred_at,
            recorded_at=now,
            tenant_id=event.tenant_id,
            correlation_id=event.correlation_id,
            causation_id=event.causation_id,
            producer="mentor_case_service",
            payload=event.to_payload(),
            metadata={
                "student_id": str(event.student_id),
                "exam_id": event.exam_id,
                "case_id": str(event.case_id),
            },
        )
        await self.enqueue(envelope)

    async def enqueue_mentor_case_updated(self, event: object) -> None:
        from prepos.domain.mentor.events import MentorCaseUpdated

        assert isinstance(event, MentorCaseUpdated)
        now = datetime.now(UTC)
        envelope = DomainEventEnvelope(
            event_id=uuid4(),
            event_version=1,
            event_type=event.event_type,
            occurred_at=event.occurred_at,
            recorded_at=now,
            tenant_id=event.tenant_id,
            correlation_id=event.correlation_id,
            causation_id=event.causation_id,
            producer="mentor_case_service",
            payload=event.to_payload(),
            metadata={
                "student_id": str(event.student_id),
                "exam_id": event.exam_id,
                "case_id": str(event.case_id),
            },
        )
        await self.enqueue(envelope)

    async def enqueue_mentor_case_resolved(self, event: object) -> None:
        from prepos.domain.mentor.events import MentorCaseResolved

        assert isinstance(event, MentorCaseResolved)
        now = datetime.now(UTC)
        envelope = DomainEventEnvelope(
            event_id=uuid4(),
            event_version=1,
            event_type=event.event_type,
            occurred_at=event.occurred_at,
            recorded_at=now,
            tenant_id=event.tenant_id,
            correlation_id=event.correlation_id,
            causation_id=event.causation_id,
            producer="mentor_case_service",
            payload=event.to_payload(),
            metadata={
                "student_id": str(event.student_id),
                "exam_id": event.exam_id,
                "case_id": str(event.case_id),
            },
        )
        await self.enqueue(envelope)

    async def enqueue_mentor_effectiveness_updated(self, event: object) -> None:
        from prepos.domain.mentor.events import MentorEffectivenessUpdated

        assert isinstance(event, MentorEffectivenessUpdated)
        now = datetime.now(UTC)
        envelope = DomainEventEnvelope(
            event_id=uuid4(),
            event_version=1,
            event_type=event.event_type,
            occurred_at=event.occurred_at,
            recorded_at=now,
            tenant_id=event.tenant_id,
            correlation_id=event.correlation_id,
            causation_id=event.causation_id,
            producer="mentor_effectiveness_learning_service",
            payload=event.to_payload(),
            metadata={
                "student_id": str(event.student_id),
                "exam_id": event.exam_id,
            },
        )
        await self.enqueue(envelope)

    async def enqueue_assessment_completed(self, event: object) -> None:
        from prepos.domain.learning_graph.events import AssessmentCompleted

        assert isinstance(event, AssessmentCompleted)
        now = datetime.now(UTC)
        envelope = DomainEventEnvelope(
            event_id=uuid4(),
            event_version=1,
            event_type=event.event_type,
            occurred_at=event.occurred_at,
            recorded_at=now,
            tenant_id=event.tenant_id,
            correlation_id=event.correlation_id,
            causation_id=event.causation_id,
            producer="learning_graph_activity_service",
            payload=event.to_payload(),
            metadata={
                "student_id": str(event.student_id),
                "concept_id": event.concept_id,
            },
        )
        await self.enqueue(envelope)

    async def enqueue_revision_completed(self, event: object) -> None:
        from prepos.domain.learning_graph.events import RevisionCompleted

        assert isinstance(event, RevisionCompleted)
        now = datetime.now(UTC)
        envelope = DomainEventEnvelope(
            event_id=uuid4(),
            event_version=1,
            event_type=event.event_type,
            occurred_at=event.occurred_at,
            recorded_at=now,
            tenant_id=event.tenant_id,
            correlation_id=event.correlation_id,
            causation_id=event.causation_id,
            producer="learning_graph_activity_service",
            payload=event.to_payload(),
            metadata={
                "student_id": str(event.student_id),
                "concept_id": event.concept_id,
            },
        )
        await self.enqueue(envelope)

    async def enqueue_study_session_logged(self, event: object) -> None:
        from prepos.domain.learning_graph.events import StudySessionLogged

        assert isinstance(event, StudySessionLogged)
        now = datetime.now(UTC)
        envelope = DomainEventEnvelope(
            event_id=uuid4(),
            event_version=1,
            event_type=event.event_type,
            occurred_at=event.occurred_at,
            recorded_at=now,
            tenant_id=event.tenant_id,
            correlation_id=event.correlation_id,
            causation_id=event.causation_id,
            producer="learning_graph_activity_service",
            payload=event.to_payload(),
            metadata={
                "student_id": str(event.student_id),
                "concept_id": event.concept_id,
            },
        )
        await self.enqueue(envelope)

    async def enqueue_pyq_data_changed(self, event: object) -> None:
        from prepos.domain.learning_graph.events import PYQDataChanged

        assert isinstance(event, PYQDataChanged)
        now = datetime.now(UTC)
        envelope = DomainEventEnvelope(
            event_id=uuid4(),
            event_version=1,
            event_type=event.event_type,
            occurred_at=event.occurred_at,
            recorded_at=now,
            tenant_id=event.tenant_id,
            correlation_id=event.correlation_id,
            causation_id=event.causation_id,
            producer="learning_graph_activity_service",
            payload=event.to_payload(),
            metadata={
                "student_id": str(event.student_id),
                "concept_id": event.concept_id,
            },
        )
        await self.enqueue(envelope)

    async def enqueue_learning_graph_updated(self, event: object) -> None:
        from prepos.domain.learning_graph.events import LearningGraphUpdated

        assert isinstance(event, LearningGraphUpdated)
        now = datetime.now(UTC)
        envelope = DomainEventEnvelope(
            event_id=uuid4(),
            event_version=1,
            event_type=event.event_type,
            occurred_at=event.occurred_at,
            recorded_at=now,
            tenant_id=event.tenant_id,
            correlation_id=event.correlation_id,
            causation_id=event.causation_id,
            producer="learning_graph_service",
            payload=event.to_payload(),
            metadata={
                "student_id": str(event.student_id),
                "concept_id": event.concept_id,
            },
        )
        await self.enqueue(envelope)

    async def enqueue_domain_catalog_updated(self, event: object) -> None:
        from prepos.domain.exam.events import DomainCatalogUpdated

        assert isinstance(event, DomainCatalogUpdated)
        now = datetime.now(UTC)
        envelope = DomainEventEnvelope(
            event_id=uuid4(),
            event_version=1,
            event_type=event.event_type,
            occurred_at=event.occurred_at,
            recorded_at=now,
            tenant_id=None,
            correlation_id=event.correlation_id,
            causation_id=event.causation_id,
            producer="exam_catalog_service",
            payload=event.to_payload(),
            metadata={"scope": "platform", "exam_id": event.exam_id},
        )
        await self.enqueue(envelope)

    async def enqueue_revision_queue_updated(self, event: object) -> None:
        from prepos.domain.revision_queue.events import RevisionQueueUpdated

        assert isinstance(event, RevisionQueueUpdated)
        now = datetime.now(UTC)
        envelope = DomainEventEnvelope(
            event_id=uuid4(),
            event_version=1,
            event_type=event.event_type,
            occurred_at=event.occurred_at,
            recorded_at=now,
            tenant_id=event.tenant_id,
            correlation_id=event.correlation_id,
            causation_id=event.causation_id,
            producer="revision_queue_projector",
            payload=event.to_payload(),
            metadata={
                "student_id": str(event.student_id),
                "concept_id": event.concept_id,
            },
        )
        await self.enqueue(envelope)

    async def enqueue_twin_snapshot_updated(self, event: object) -> None:
        """Deprecated: prefer TwinUpdated for new consumers."""
        from prepos.domain.twin.snapshot_events import TwinSnapshotUpdated

        assert isinstance(event, TwinSnapshotUpdated)
        now = datetime.now(UTC)
        envelope = DomainEventEnvelope(
            event_id=uuid4(),
            event_version=1,
            event_type=event.event_type,
            occurred_at=event.occurred_at,
            recorded_at=now,
            tenant_id=event.tenant_id,
            correlation_id=event.correlation_id,
            causation_id=event.causation_id,
            producer="twin_projection_builder",
            payload=event.to_payload(),
            metadata={
                "student_id": str(event.student_id),
                "exam_id": event.exam_id,
                "deprecated": True,
            },
        )
        await self.enqueue(envelope)

    async def enqueue_twin_updated(self, event: object) -> None:
        from prepos.domain.twin.twin_events import TwinUpdated

        assert isinstance(event, TwinUpdated)
        now = datetime.now(UTC)
        envelope = DomainEventEnvelope(
            event_id=uuid4(),
            event_version=1,
            event_type=event.event_type,
            occurred_at=event.occurred_at,
            recorded_at=now,
            tenant_id=event.tenant_id,
            correlation_id=event.correlation_id,
            causation_id=event.causation_id,
            producer="twin_projection_builder",
            payload=event.to_payload(),
            metadata={
                "student_id": str(event.student_id),
                "exam_id": event.exam_id,
                "profile_version": event.profile_version,
            },
        )
        await self.enqueue(envelope)

    async def enqueue_twin_recommendations_updated(self, event: object) -> None:
        from prepos.domain.twin.events import TwinRecommendationsUpdated

        assert isinstance(event, TwinRecommendationsUpdated)
        now = datetime.now(UTC)
        envelope = DomainEventEnvelope(
            event_id=uuid4(),
            event_version=1,
            event_type=event.event_type,
            occurred_at=event.occurred_at,
            recorded_at=now,
            tenant_id=event.tenant_id,
            correlation_id=event.correlation_id,
            causation_id=event.causation_id,
            producer="twin_recommendation_service",
            payload=event.to_payload(),
            metadata={
                "student_id": str(event.student_id),
                "exam_id": event.exam_id,
            },
        )
        await self.enqueue(envelope)
