from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from prepos.application.goal.forecast_service import ForecastService
from prepos.application.goal.milestone_service import MilestoneService
from prepos.application.learning_graph.read_services import LearningGraphReadService
from prepos.application.mentor.mentor_case_service import MentorCaseService
from prepos.application.mentor.mentor_effectiveness_learning_service import (
    MentorEffectivenessLearningService,
)
from prepos.application.mentor.mentor_service import MentorService
from prepos.application.scoring.forecast_probability_service import ForecastProbabilityService
from prepos.application.scoring.predicted_score_service import PredictedScoreService
from prepos.application.twin.behavior_profile_service import BehaviorProfileService
from prepos.application.twin.decision_service import TwinDecisionService
from prepos.application.twin.intervention_optimization_service import InterventionOptimizationService
from prepos.application.twin.intervention_outcome_service import InterventionOutcomeService
from prepos.application.twin.intervention_service import TwinInterventionService
from prepos.application.twin.personalization_service import PersonalizationService
from prepos.application.twin.projection_builder import TwinProjectionBuilder
from prepos.application.twin.rebuild_service import TwinRebuildService
from prepos.application.twin.summary_adapters import (
    BehaviorProfileSummaryAdapter,
    DecisionSummaryAdapter,
    ForecastProbabilitySummaryAdapter,
    ForecastSummaryAdapter,
    InterventionOutcomeSummaryAdapter,
    InterventionSummaryAdapter,
    LearningGraphReadinessSummaryAdapter,
    MentorActionSummaryAdapter,
    MentorCaseSummaryAdapter,
    MentorEffectivenessSummaryAdapter,
    MentorSummaryAdapter,
    MilestoneSummaryAdapter,
    PersonalizationSummaryAdapter,
    PredictedScoreSummaryAdapter,
    RevisionQueueSummaryAdapter,
    StudyBehaviorSummaryAdapter,
    StudyPlanSummaryAdapter,
    TwinRecommendationSummaryAdapter,
)
from prepos.domain.twin.projection_sections import TwinProjectionSection
from prepos.events.outbox.publisher import OutboxPublisher
from prepos.infrastructure.db.repositories.goal_repository import SqlAlchemyGoalRepository
from prepos.infrastructure.db.repositories.intervention_history_repository import (
    SqlAlchemyInterventionHistoryRepository,
)
from prepos.infrastructure.db.repositories.mentor_case_repository import SqlAlchemyMentorCaseRepository
from prepos.infrastructure.db.repositories.mentor_effectiveness_learning_repository import (
    SqlAlchemyMentorEffectivenessLearningRepository,
)
from prepos.infrastructure.db.repositories.revision_queue_repository import SqlAlchemyRevisionQueueRepository
from prepos.infrastructure.db.repositories.study_plan_execution_repository import (
    SqlAlchemyStudyPlanExecutionRepository,
)
from prepos.infrastructure.db.repositories.study_plan_repository import SqlAlchemyStudyPlanRepository
from prepos.infrastructure.db.repositories.twin_rebuild_lock_repository import SqlAlchemyTwinRebuildLockRepository
from prepos.infrastructure.db.repositories.twin_repository import SqlAlchemyTwinRecommendationRepository
from prepos.infrastructure.db.repositories.twin_snapshot_repository import SqlAlchemyTwinProjectionRepository


def build_forecast_service(
    *,
    session: AsyncSession,
    read_service: LearningGraphReadService,
) -> ForecastService:
    return ForecastService(
        read_service=read_service,
        goal_repo=SqlAlchemyGoalRepository(session),
        study_plan_repo=SqlAlchemyStudyPlanRepository(session),
        outbox=OutboxPublisher(session),
    )


def build_forecast_probability_service(
    *,
    session: AsyncSession,
    read_service: LearningGraphReadService,
) -> ForecastProbabilityService:
    return ForecastProbabilityService(
        read_service=read_service,
        goal_repo=SqlAlchemyGoalRepository(session),
        study_plan_repo=SqlAlchemyStudyPlanRepository(session),
        outbox=OutboxPublisher(session),
    )


def build_milestone_service(
    *,
    session: AsyncSession,
    read_service: LearningGraphReadService,
) -> MilestoneService:
    return MilestoneService(
        read_service=read_service,
        goal_repo=SqlAlchemyGoalRepository(session),
        outbox=OutboxPublisher(session),
    )


def build_predicted_score_service(
    *,
    session: AsyncSession,
    read_service: LearningGraphReadService,
) -> PredictedScoreService:
    return PredictedScoreService(
        read_service=read_service,
        recommendation_repo=SqlAlchemyTwinRecommendationRepository(session),
        study_plan_repo=SqlAlchemyStudyPlanRepository(session),
        outbox=OutboxPublisher(session),
    )


def build_twin_decision_service(
    *,
    session: AsyncSession,
    read_service: LearningGraphReadService,
) -> TwinDecisionService:
    outbox = OutboxPublisher(session)
    goal_repo = SqlAlchemyGoalRepository(session)
    study_plan_repo = SqlAlchemyStudyPlanRepository(session)
    forecast_probability_service = build_forecast_probability_service(
        session=session,
        read_service=read_service,
    )
    milestone_service = build_milestone_service(session=session, read_service=read_service)
    personalization_service = build_personalization_service(session=session)
    return TwinDecisionService(
        read_service=read_service,
        goal_repo=goal_repo,
        study_plan_repo=study_plan_repo,
        execution_repo=SqlAlchemyStudyPlanExecutionRepository(session),
        queue_repo=SqlAlchemyRevisionQueueRepository(session),
        forecast_probability_service=forecast_probability_service,
        milestone_service=milestone_service,
        outbox=outbox,
        personalization_service=personalization_service,
    )


def build_twin_intervention_service(
    *,
    session: AsyncSession,
    read_service: LearningGraphReadService,
) -> TwinInterventionService:
    decision_service = build_twin_decision_service(session=session, read_service=read_service)
    return TwinInterventionService(
        decision_service=decision_service,
        study_plan_repo=SqlAlchemyStudyPlanRepository(session),
        queue_repo=SqlAlchemyRevisionQueueRepository(session),
        forecast_probability_service=build_forecast_probability_service(
            session=session,
            read_service=read_service,
        ),
        milestone_service=build_milestone_service(session=session, read_service=read_service),
        outbox=OutboxPublisher(session),
        personalization_service=build_personalization_service(session=session),
    )


def build_intervention_outcome_service(
    *,
    session: AsyncSession,
    read_service: LearningGraphReadService,
) -> InterventionOutcomeService:
    return InterventionOutcomeService(
        read_service=read_service,
        predicted_score_service=build_predicted_score_service(session=session, read_service=read_service),
        execution_repo=SqlAlchemyStudyPlanExecutionRepository(session),
        projection_repo=SqlAlchemyTwinProjectionRepository(session),
        history_repo=SqlAlchemyInterventionHistoryRepository(session),
        outbox=OutboxPublisher(session),
    )


def build_intervention_optimization_service(
    *,
    session: AsyncSession,
) -> InterventionOptimizationService:
    return InterventionOptimizationService(
        projection_repo=SqlAlchemyTwinProjectionRepository(session),
        history_repo=SqlAlchemyInterventionHistoryRepository(session),
        outbox=OutboxPublisher(session),
    )


def build_behavior_profile_service(
    *,
    session: AsyncSession,
) -> BehaviorProfileService:
    return BehaviorProfileService(
        execution_repo=SqlAlchemyStudyPlanExecutionRepository(session),
        history_repo=SqlAlchemyInterventionHistoryRepository(session),
        outbox=OutboxPublisher(session),
    )


def build_personalization_service(
    *,
    session: AsyncSession,
) -> PersonalizationService:
    return PersonalizationService(
        behavior_profile_service=build_behavior_profile_service(session=session),
        history_repo=SqlAlchemyInterventionHistoryRepository(session),
        outbox=OutboxPublisher(session),
    )


def build_mentor_case_service(
    *,
    session: AsyncSession,
) -> MentorCaseService:
    return MentorCaseService(
        case_repo=SqlAlchemyMentorCaseRepository(session),
        projection_repo=SqlAlchemyTwinProjectionRepository(session),
        outbox=OutboxPublisher(session),
    )


def build_mentor_effectiveness_learning_service(
    *,
    session: AsyncSession,
) -> MentorEffectivenessLearningService:
    history_repo = SqlAlchemyInterventionHistoryRepository(session)
    return MentorEffectivenessLearningService(
        learning_repo=SqlAlchemyMentorEffectivenessLearningRepository(
            session=session,
            history_repo=history_repo,
        ),
        case_repo=SqlAlchemyMentorCaseRepository(session),
        outbox=OutboxPublisher(session),
    )


def build_mentor_service(
    *,
    session: AsyncSession,
) -> MentorService:
    history_repo = SqlAlchemyInterventionHistoryRepository(session)
    return MentorService(
        projection_repo=SqlAlchemyTwinProjectionRepository(session),
        outbox=OutboxPublisher(session),
        learning_repo=SqlAlchemyMentorEffectivenessLearningRepository(
            session=session,
            history_repo=history_repo,
        ),
    )


def build_twin_rebuild_service(
    *,
    session: AsyncSession,
    read_service: LearningGraphReadService,
) -> TwinRebuildService:
    queue_repo = SqlAlchemyRevisionQueueRepository(session)
    recommendation_repo = SqlAlchemyTwinRecommendationRepository(session)
    study_plan_repo = SqlAlchemyStudyPlanRepository(session)
    execution_repo = SqlAlchemyStudyPlanExecutionRepository(session)
    projection_repo = SqlAlchemyTwinProjectionRepository(session)
    forecast_service = build_forecast_service(session=session, read_service=read_service)
    predicted_score_service = build_predicted_score_service(session=session, read_service=read_service)
    milestone_service = build_milestone_service(session=session, read_service=read_service)
    forecast_probability_service = build_forecast_probability_service(
        session=session,
        read_service=read_service,
    )
    decision_service = build_twin_decision_service(session=session, read_service=read_service)
    intervention_service = build_twin_intervention_service(session=session, read_service=read_service)
    history_repo = SqlAlchemyInterventionHistoryRepository(session)
    optimization_service = build_intervention_optimization_service(session=session)
    behavior_profile_service = build_behavior_profile_service(session=session)
    personalization_service = build_personalization_service(session=session)
    mentor_service = build_mentor_service(session=session)
    mentor_case_service = build_mentor_case_service(session=session)
    mentor_effectiveness_service = build_mentor_effectiveness_learning_service(session=session)
    builder = TwinProjectionBuilder(
        readiness_port=LearningGraphReadinessSummaryAdapter(read_service=read_service),
        queue_port=RevisionQueueSummaryAdapter(queue_repo=queue_repo),
        recommendation_port=TwinRecommendationSummaryAdapter(recommendation_repo=recommendation_repo),
        study_plan_port=StudyPlanSummaryAdapter(study_plan_repo=study_plan_repo),
        behavior_port=StudyBehaviorSummaryAdapter(execution_repo=execution_repo),
        forecast_port=ForecastSummaryAdapter(forecast_service=forecast_service),
        predicted_score_port=PredictedScoreSummaryAdapter(
            predicted_score_service=predicted_score_service,
        ),
        milestone_port=MilestoneSummaryAdapter(milestone_service=milestone_service),
        forecast_probability_port=ForecastProbabilitySummaryAdapter(
            forecast_probability_service=forecast_probability_service,
        ),
        decision_port=DecisionSummaryAdapter(decision_service=decision_service),
        intervention_port=InterventionSummaryAdapter(intervention_service=intervention_service),
        intervention_outcome_port=InterventionOutcomeSummaryAdapter(
            optimization_service=optimization_service,
            history_repo=history_repo,
        ),
        behavior_profile_port=BehaviorProfileSummaryAdapter(
            behavior_profile_service=behavior_profile_service,
        ),
        personalization_port=PersonalizationSummaryAdapter(
            personalization_service=personalization_service,
        ),
        mentor_port=MentorSummaryAdapter(
            mentor_service=mentor_service,
        ),
        mentor_action_port=MentorActionSummaryAdapter(
            mentor_service=mentor_service,
        ),
        mentor_case_port=MentorCaseSummaryAdapter(
            mentor_case_service=mentor_case_service,
        ),
        mentor_effectiveness_port=MentorEffectivenessSummaryAdapter(
            learning_service=mentor_effectiveness_service,
        ),
        projection_repo=projection_repo,
        outbox=OutboxPublisher(session),
    )
    return TwinRebuildService(
        builder=builder,
        lock_repo=SqlAlchemyTwinRebuildLockRepository(session),
        projection_repo=projection_repo,
    )


async def request_twin_incremental_update(
    *,
    session: AsyncSession,
    read_service: LearningGraphReadService,
    tenant_id: UUID,
    student_id: UUID,
    exam_id: str,
    section: TwinProjectionSection,
    correlation_id: str,
    causation_id: str | None,
    concept_id: str | None = None,
    learning_graph_row_version: int | None = None,
) -> None:
    service = build_twin_rebuild_service(session=session, read_service=read_service)
    await service.request_incremental_update(
        section=section,
        tenant_id=tenant_id,
        student_id=student_id,
        exam_id=exam_id,
        correlation_id=correlation_id,
        causation_id=causation_id,
        concept_id=concept_id,
        learning_graph_row_version=learning_graph_row_version,
    )


async def request_twin_rebuild(
    *,
    session: AsyncSession,
    read_service: LearningGraphReadService,
    tenant_id: UUID,
    student_id: UUID,
    exam_id: str,
    correlation_id: str,
    causation_id: str | None,
) -> None:
    service = build_twin_rebuild_service(session=session, read_service=read_service)
    await service.request_rebuild(
        tenant_id=tenant_id,
        student_id=student_id,
        exam_id=exam_id,
        correlation_id=correlation_id,
        causation_id=causation_id,
    )
