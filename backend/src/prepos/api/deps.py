from __future__ import annotations

from typing import Annotated
from uuid import UUID, uuid4

import structlog
from fastapi import Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from prepos.application.auth.ports import (
    AuditLogRepositoryPort,
    RefreshTokenRepositoryPort,
    TenantRepositoryPort,
    UserRepositoryPort,
)
from prepos.application.auth.use_cases import (
    GetCurrentUserUseCase,
    LoginUseCase,
    LogoutUseCase,
    RefreshTokenUseCase,
    RegisterUseCase,
)
from prepos.application.copilot.analytics_service import CopilotAnalyticsService
from prepos.application.copilot.health_service import CopilotHealthService
from prepos.application.copilot.service import CopilotService
from prepos.application.goal.forecast_service import ForecastService
from prepos.application.goal.milestone_service import MilestoneService
from prepos.application.goal.service import GoalService
from prepos.application.forecasting.forecast_service import GoalForecastingService
from prepos.application.memory.memory_service import CoachingMemoryService
from prepos.application.knowledge.knowledge_agent_service import KnowledgeAgentService
from prepos.application.knowledge.services import (
    KnowledgeAdminService,
    KnowledgeIngestionService,
    KnowledgeSearchService,
)
from prepos.application.learning_graph.activity_service import LearningGraphActivityService
from prepos.application.learning_graph.read_services import LearningGraphReadService
from prepos.application.learning_graph.services import LearningGraphService
from prepos.application.mentor.mentor_case_read_service import MentorCaseReadService, MentorQueueReadService
from prepos.application.planning.planning_service import AdaptivePlanningService
from prepos.application.pyq.pyq_service import PyqService
from prepos.application.recommendations.outcomes.outcome_analytics import OutcomeAnalyticsService
from prepos.application.recommendations.outcomes.outcome_service import RecommendationOutcomeService
from prepos.application.recommendations.recommendation_service import LearningRecommendationService
from prepos.application.revision_queue.read_service import RevisionQueueReadService
from prepos.application.scoring.forecast_probability_service import ForecastProbabilityService
from prepos.application.study_plan.execution_tracker import StudyPlanExecutionTracker
from prepos.application.study_plan.service import StudyPlanService
from prepos.application.twin.rebuild_factory import build_mentor_case_service
from prepos.application.twin.services import TwinRecommendationService
from prepos.application.twin.snapshot_read_service import TwinSnapshotReadService
from prepos.application.twin.twin_read_service import TwinReadService
from prepos.core.config import Settings, get_settings
from prepos.core.database import get_db_session
from prepos.core.exceptions import AuthenticationError
from prepos.core.security import decode_token
from prepos.core.tenancy import RoleName, TenantContext
from prepos.events.outbox.publisher import OutboxPublisher
from prepos.infrastructure.cache.learning_graph_cache import NoOpLearningGraphCache
from prepos.infrastructure.db.repositories.auth_repository import (
    SqlAlchemyAuditLogRepository,
    SqlAlchemyRefreshTokenRepository,
    SqlAlchemyTenantRepository,
    SqlAlchemyUserRepository,
)
from prepos.infrastructure.db.repositories.copilot_analytics_repository import (
    SqlAlchemyCopilotAnalyticsRepository,
)
from prepos.infrastructure.db.repositories.exam_repository import SqlAlchemyExamCatalogUnitOfWork
from prepos.infrastructure.db.repositories.goal_repository import SqlAlchemyGoalRepository
from prepos.infrastructure.db.repositories.intervention_history_repository import (
    SqlAlchemyInterventionHistoryRepository,
)
from prepos.infrastructure.db.repositories.knowledge_repository import SqlAlchemyKnowledgeRepository
from prepos.infrastructure.db.repositories.pyq_repository import SqlAlchemyPyqRepository
from prepos.infrastructure.db.repositories.learning_graph_repository import (
    SqlAlchemyLearningGraphReadRepository,
    SqlAlchemyLearningGraphRepository,
)
from prepos.infrastructure.db.repositories.mentor_case_repository import SqlAlchemyMentorCaseRepository
from prepos.infrastructure.db.repositories.mentor_effectiveness_learning_repository import (
    SqlAlchemyMentorEffectivenessLearningRepository,
)
from prepos.infrastructure.db.repositories.revision_queue_repository import SqlAlchemyRevisionQueueRepository
from prepos.infrastructure.db.repositories.student_repository import SqlAlchemyStudentUnitOfWork
from prepos.infrastructure.db.repositories.study_plan_execution_repository import (
    SqlAlchemyStudyPlanExecutionRepository,
)
from prepos.infrastructure.db.repositories.study_plan_repository import SqlAlchemyStudyPlanRepository
from prepos.infrastructure.db.repositories.twin_repository import SqlAlchemyTwinRecommendationRepository
from prepos.infrastructure.db.repositories.twin_snapshot_repository import (
    SqlAlchemyTwinProjectionRepository,
    SqlAlchemyTwinSnapshotRepository,
)
from prepos.infrastructure.knowledge.embedding_provider import build_embedding_provider
from prepos.infrastructure.knowledge.llm_provider import build_llm_provider
from prepos.infrastructure.knowledge.local_storage import LocalKnowledgeStorage


def get_request_id(request: Request) -> str:
    header = request.headers.get("x-request-id")
    return header or str(uuid4())


async def get_session(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> AsyncSession:
    return session


def get_tenant_repo(session: Annotated[AsyncSession, Depends(get_session)]) -> TenantRepositoryPort:
    return SqlAlchemyTenantRepository(session)


def get_user_repo(session: Annotated[AsyncSession, Depends(get_session)]) -> UserRepositoryPort:
    return SqlAlchemyUserRepository(session)


def get_refresh_repo(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> RefreshTokenRepositoryPort:
    return SqlAlchemyRefreshTokenRepository(session)


def get_audit_repo(session: Annotated[AsyncSession, Depends(get_session)]) -> AuditLogRepositoryPort:
    return SqlAlchemyAuditLogRepository(session)


def get_outbox(session: Annotated[AsyncSession, Depends(get_session)]) -> OutboxPublisher:
    return OutboxPublisher(session)


def get_exam_uow(session: Annotated[AsyncSession, Depends(get_session)]) -> SqlAlchemyExamCatalogUnitOfWork:
    return SqlAlchemyExamCatalogUnitOfWork(session)


def get_student_uow(session: Annotated[AsyncSession, Depends(get_session)]) -> SqlAlchemyStudentUnitOfWork:
    return SqlAlchemyStudentUnitOfWork(session)


def get_learning_graph_repo(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> SqlAlchemyLearningGraphRepository:
    return SqlAlchemyLearningGraphRepository(session)


def get_learning_graph_read_repo(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> SqlAlchemyLearningGraphReadRepository:
    return SqlAlchemyLearningGraphReadRepository(session)


def get_learning_graph_service(
    settings: Annotated[Settings, Depends(get_settings)],
    session: Annotated[AsyncSession, Depends(get_session)],
    exam_uow: Annotated[SqlAlchemyExamCatalogUnitOfWork, Depends(get_exam_uow)],
    outbox: Annotated[OutboxPublisher, Depends(get_outbox)],
) -> LearningGraphService:
    return LearningGraphService(
        repo=SqlAlchemyLearningGraphRepository(session),
        exam_uow=exam_uow,
        outbox=outbox,
        cache=NoOpLearningGraphCache(),
        max_retries=settings.lg_optimistic_lock_max_retries,
    )


def get_learning_graph_activity_service(
    session: Annotated[AsyncSession, Depends(get_session)],
    outbox: Annotated[OutboxPublisher, Depends(get_outbox)],
) -> LearningGraphActivityService:
    return LearningGraphActivityService(outbox=outbox)


def get_learning_graph_read_service(
    read_repo: Annotated[SqlAlchemyLearningGraphReadRepository, Depends(get_learning_graph_read_repo)],
    write_repo: Annotated[SqlAlchemyLearningGraphRepository, Depends(get_learning_graph_repo)],
) -> LearningGraphReadService:
    return LearningGraphReadService(
        read_repo=read_repo,
        write_repo=write_repo,
        cache=NoOpLearningGraphCache(),
    )


def get_twin_recommendation_service(
    read_service: Annotated[LearningGraphReadService, Depends(get_learning_graph_read_service)],
    session: Annotated[AsyncSession, Depends(get_session)],
    outbox: Annotated[OutboxPublisher, Depends(get_outbox)],
) -> TwinRecommendationService:
    return TwinRecommendationService(
        learning_graph_read_service=read_service,
        recommendation_repo=SqlAlchemyTwinRecommendationRepository(session),
        outbox=outbox,
    )


def get_revision_queue_read_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> RevisionQueueReadService:
    return RevisionQueueReadService(
        queue_repo=SqlAlchemyRevisionQueueRepository(session),
    )


def get_twin_snapshot_read_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TwinSnapshotReadService:
    return TwinSnapshotReadService(
        snapshot_repo=SqlAlchemyTwinSnapshotRepository(session),
    )


def get_twin_read_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TwinReadService:
    return TwinReadService(
        projection_repo=SqlAlchemyTwinProjectionRepository(session),
    )


def get_mentor_queue_read_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> MentorQueueReadService:
    return MentorQueueReadService(
        case_repo=SqlAlchemyMentorCaseRepository(session),
    )


def get_mentor_case_read_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> MentorCaseReadService:
    history_repo = SqlAlchemyInterventionHistoryRepository(session)
    return MentorCaseReadService(
        case_repo=SqlAlchemyMentorCaseRepository(session),
        learning_repo=SqlAlchemyMentorEffectivenessLearningRepository(
            session=session,
            history_repo=history_repo,
        ),
    )


def get_mentor_case_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> MentorCaseService:
    return build_mentor_case_service(session=session)


def get_study_plan_service(
    read_service: Annotated[LearningGraphReadService, Depends(get_learning_graph_read_service)],
    session: Annotated[AsyncSession, Depends(get_session)],
    outbox: Annotated[OutboxPublisher, Depends(get_outbox)],
) -> StudyPlanService:
    execution_repo = SqlAlchemyStudyPlanExecutionRepository(session)
    forecast_service = ForecastService(
        read_service=read_service,
        goal_repo=SqlAlchemyGoalRepository(session),
        study_plan_repo=SqlAlchemyStudyPlanRepository(session),
        outbox=outbox,
    )
    return StudyPlanService(
        read_service=read_service,
        recommendation_repo=SqlAlchemyTwinRecommendationRepository(session),
        queue_repo=SqlAlchemyRevisionQueueRepository(session),
        study_plan_repo=SqlAlchemyStudyPlanRepository(session),
        execution_repo=execution_repo,
        execution_tracker=StudyPlanExecutionTracker(
            execution_repo=execution_repo,
            outbox=outbox,
        ),
        forecast_service=forecast_service,
        outbox=outbox,
    )


def get_goal_service(
    session: Annotated[AsyncSession, Depends(get_session)],
    read_service: Annotated[LearningGraphReadService, Depends(get_learning_graph_read_service)],
    outbox: Annotated[OutboxPublisher, Depends(get_outbox)],
) -> GoalService:
    milestone_service = MilestoneService(
        read_service=read_service,
        goal_repo=SqlAlchemyGoalRepository(session),
        outbox=outbox,
    )
    forecast_probability_service = ForecastProbabilityService(
        read_service=read_service,
        goal_repo=SqlAlchemyGoalRepository(session),
        study_plan_repo=SqlAlchemyStudyPlanRepository(session),
        outbox=outbox,
    )
    return GoalService(
        goal_repo=SqlAlchemyGoalRepository(session),
        milestone_service=milestone_service,
        forecast_probability_service=forecast_probability_service,
        outbox=outbox,
    )


def get_copilot_analytics_repo(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> SqlAlchemyCopilotAnalyticsRepository:
    return SqlAlchemyCopilotAnalyticsRepository(session)


def get_copilot_analytics_service(
    repo: Annotated[SqlAlchemyCopilotAnalyticsRepository, Depends(get_copilot_analytics_repo)],
) -> CopilotAnalyticsService:
    return CopilotAnalyticsService(repo=repo)


def get_copilot_health_service() -> CopilotHealthService:
    return CopilotHealthService()


def get_knowledge_repo(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> SqlAlchemyKnowledgeRepository:
    return SqlAlchemyKnowledgeRepository(session)


def get_knowledge_search_service(
    settings: Annotated[Settings, Depends(get_settings)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> KnowledgeSearchService:
    return KnowledgeSearchService(
        settings=settings,
        repository=SqlAlchemyKnowledgeRepository(session),
        embedding_provider=build_embedding_provider(settings),
    )


def get_knowledge_admin_service(
    settings: Annotated[Settings, Depends(get_settings)],
    session: Annotated[AsyncSession, Depends(get_session)],
    knowledge_security: Annotated[object, Depends(get_knowledge_security_service)],
) -> KnowledgeAdminService:
    from prepos.tasks.knowledge_tasks import embed_source_chunks

    ingestion_service = KnowledgeIngestionService(
        settings=settings,
        repository=SqlAlchemyKnowledgeRepository(session),
        storage=LocalKnowledgeStorage(settings),
        embed_task=embed_source_chunks,
        knowledge_security_service=knowledge_security,
    )
    return KnowledgeAdminService(
        repository=SqlAlchemyKnowledgeRepository(session),
        ingestion_service=ingestion_service,
    )


def get_knowledge_agent_service(
    settings: Annotated[Settings, Depends(get_settings)],
    search_service: Annotated[KnowledgeSearchService, Depends(get_knowledge_search_service)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> KnowledgeAgentService:
    from prepos.application.knowledge.evaluation_service import KnowledgeEvaluationService
    from prepos.infrastructure.db.repositories.rag_quality_repository import SqlAlchemyRagQualityRepository

    evaluation_service = KnowledgeEvaluationService(repository=SqlAlchemyRagQualityRepository(session))
    return KnowledgeAgentService(
        settings=settings,
        search_service=search_service,
        llm_provider=build_llm_provider(settings),
        evaluation_service=evaluation_service,
    )


def get_rag_quality_repo(
    session: Annotated[AsyncSession, Depends(get_session)],
):
    from prepos.infrastructure.db.repositories.rag_quality_repository import SqlAlchemyRagQualityRepository

    return SqlAlchemyRagQualityRepository(session)


def get_rag_quality_service(
    repo: Annotated[object, Depends(get_rag_quality_repo)],
):
    from prepos.application.knowledge.rag_quality_service import RagQualityService

    return RagQualityService(repository=repo)


def get_current_affairs_analytics_repo(
    session: Annotated[AsyncSession, Depends(get_session)],
):
    from prepos.infrastructure.db.repositories.current_affairs_analytics_repository import (
        SqlAlchemyCurrentAffairsAnalyticsRepository,
    )

    return SqlAlchemyCurrentAffairsAnalyticsRepository(session)


def get_current_affairs_analytics_service(
    repo: Annotated[object, Depends(get_current_affairs_analytics_repo)],
):
    from prepos.application.knowledge.current_affairs_analytics_service import (
        CurrentAffairsAnalyticsService,
    )

    return CurrentAffairsAnalyticsService(repo=repo)


def get_current_affairs_service(
    settings: Annotated[Settings, Depends(get_settings)],
    session: Annotated[AsyncSession, Depends(get_session)],
    search_service: Annotated[KnowledgeSearchService, Depends(get_knowledge_search_service)],
):
    from prepos.application.knowledge.current_affairs_service import (
        CurrentAffairsIngestionService,
        CurrentAffairsService,
    )
    from prepos.tasks.knowledge_tasks import embed_source_chunks

    repo = SqlAlchemyKnowledgeRepository(session)
    ingestion = KnowledgeIngestionService(
        settings=settings,
        repository=repo,
        storage=LocalKnowledgeStorage(settings),
        embed_task=embed_source_chunks,
    )
    ca_ingestion = CurrentAffairsIngestionService(repository=repo, ingestion_service=ingestion)
    return CurrentAffairsService(
        repository=repo,
        ingestion_service=ca_ingestion,
        search_service=search_service,
    )


def get_pyq_repo(
    session: Annotated[AsyncSession, Depends(get_session)],
):
    from prepos.infrastructure.db.repositories.pyq_repository import SqlAlchemyPyqRepository

    return SqlAlchemyPyqRepository(session)


def get_pyq_analytics_repo(
    session: Annotated[AsyncSession, Depends(get_session)],
):
    from prepos.infrastructure.db.repositories.pyq_analytics_repository import (
        SqlAlchemyPyqAnalyticsRepository,
    )

    return SqlAlchemyPyqAnalyticsRepository(session)


def get_pyq_analytics_service(
    repo: Annotated[object, Depends(get_pyq_analytics_repo)],
):
    from prepos.application.pyq.pyq_analytics_service import PyqAnalyticsService

    return PyqAnalyticsService(repo=repo)


def get_pyq_service(
    settings: Annotated[Settings, Depends(get_settings)],
    session: Annotated[AsyncSession, Depends(get_session)],
    search_service: Annotated[KnowledgeSearchService, Depends(get_knowledge_search_service)],
):
    from prepos.application.pyq.pyq_ingestion_service import PYQIngestionService
    from prepos.application.pyq.pyq_service import PyqService
    from prepos.tasks.knowledge_tasks import embed_source_chunks

    knowledge_repo = SqlAlchemyKnowledgeRepository(session)
    pyq_repo = SqlAlchemyPyqRepository(session)
    ingestion = PYQIngestionService(
        settings=settings,
        repository=pyq_repo,
        knowledge_repository=knowledge_repo,
        storage=LocalKnowledgeStorage(settings),
        embed_task=embed_source_chunks,
    )
    return PyqService(
        repository=pyq_repo,
        knowledge_repository=knowledge_repo,
        ingestion_service=ingestion,
        search_service=search_service,
    )


def get_recommendation_analytics_repo(
    session: Annotated[AsyncSession, Depends(get_session)],
):
    from prepos.infrastructure.db.repositories.recommendation_analytics_repository import (
        SqlAlchemyRecommendationAnalyticsRepository,
    )

    return SqlAlchemyRecommendationAnalyticsRepository(session)


def get_recommendation_analytics_service(
    repo: Annotated[object, Depends(get_recommendation_analytics_repo)],
):
    from prepos.application.recommendations.recommendation_analytics_service import (
        RecommendationAnalyticsService,
    )

    return RecommendationAnalyticsService(repository=repo)


def get_recommendation_outcome_repo(
    session: Annotated[AsyncSession, Depends(get_session)],
):
    from prepos.infrastructure.db.repositories.recommendation_outcome_repository import (
        SqlAlchemyRecommendationOutcomeRepository,
    )

    return SqlAlchemyRecommendationOutcomeRepository(session)


def get_recommendation_outcome_service(
    outcome_repo: Annotated[object, Depends(get_recommendation_outcome_repo)],
    analytics_repo: Annotated[object, Depends(get_recommendation_analytics_repo)],
    twin_read_service: Annotated[TwinReadService, Depends(get_twin_read_service)],
    learning_graph_read_service: Annotated[LearningGraphReadService, Depends(get_learning_graph_read_service)],
):
    from prepos.application.recommendations.outcomes.outcome_service import RecommendationOutcomeService

    return RecommendationOutcomeService(
        outcome_repository=outcome_repo,
        analytics_repository=analytics_repo,
        twin_read_service=twin_read_service,
        learning_graph_read_service=learning_graph_read_service,
    )


def get_outcome_analytics_service(
    outcome_repo: Annotated[object, Depends(get_recommendation_outcome_repo)],
):
    from prepos.application.recommendations.outcomes.outcome_analytics import OutcomeAnalyticsService

    return OutcomeAnalyticsService(repository=outcome_repo)


def get_memory_repo(
    session: Annotated[AsyncSession, Depends(get_session)],
):
    from prepos.infrastructure.db.repositories.memory_repository import SqlAlchemyMemoryRepository

    return SqlAlchemyMemoryRepository(session)


def get_coaching_memory_service(
    memory_repo: Annotated[object, Depends(get_memory_repo)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    from prepos.application.memory.memory_service import CoachingMemoryService

    return CoachingMemoryService(repository=memory_repo, session=session)


def get_learning_timeline_service(
    memory_service: Annotated[CoachingMemoryService, Depends(get_coaching_memory_service)],
):
    from prepos.application.memory.memory_service import LearningTimelineService

    return LearningTimelineService(memory_service=memory_service)


def get_planning_repo(
    session: Annotated[AsyncSession, Depends(get_session)],
):
    from prepos.infrastructure.db.repositories.planning_repository import SqlAlchemyPlanningRepository

    return SqlAlchemyPlanningRepository(session)


def get_learning_recommendation_service(
    twin_read_service: Annotated[TwinReadService, Depends(get_twin_read_service)],
    learning_graph_read_service: Annotated[LearningGraphReadService, Depends(get_learning_graph_read_service)],
    goal_service: Annotated[GoalService, Depends(get_goal_service)],
    study_plan_service: Annotated[StudyPlanService, Depends(get_study_plan_service)],
    twin_recommendation_service: Annotated[TwinRecommendationService, Depends(get_twin_recommendation_service)],
    session: Annotated[AsyncSession, Depends(get_session)],
    analytics_repo: Annotated[object, Depends(get_recommendation_analytics_repo)],
) -> LearningRecommendationService:
    return LearningRecommendationService(
        twin_read_service=twin_read_service,
        learning_graph_read_service=learning_graph_read_service,
        goal_service=goal_service,
        study_plan_service=study_plan_service,
        twin_recommendation_service=twin_recommendation_service,
        pyq_repository=SqlAlchemyPyqRepository(session),
        analytics_repository=analytics_repo,
    )


def get_adaptive_planning_service(
    planning_repo: Annotated[object, Depends(get_planning_repo)],
    twin_read_service: Annotated[TwinReadService, Depends(get_twin_read_service)],
    learning_graph_read_service: Annotated[LearningGraphReadService, Depends(get_learning_graph_read_service)],
    goal_service: Annotated[GoalService, Depends(get_goal_service)],
    recommendation_service: Annotated[LearningRecommendationService, Depends(get_learning_recommendation_service)],
    memory_service: Annotated[CoachingMemoryService, Depends(get_coaching_memory_service)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    from prepos.application.planning.planning_service import AdaptivePlanningService
    from prepos.infrastructure.db.repositories.pyq_repository import SqlAlchemyPyqRepository

    return AdaptivePlanningService(
        repository=planning_repo,
        twin_read_service=twin_read_service,
        learning_graph_read_service=learning_graph_read_service,
        goal_service=goal_service,
        recommendation_service=recommendation_service,
        memory_service=memory_service,
        pyq_repository=SqlAlchemyPyqRepository(session),
    )


def get_forecasting_repo(
    session: Annotated[AsyncSession, Depends(get_session)],
):
    from prepos.infrastructure.db.repositories.forecasting_repository import SqlAlchemyForecastingRepository

    return SqlAlchemyForecastingRepository(session)


def get_goal_forecasting_service(
    forecasting_repo: Annotated[object, Depends(get_forecasting_repo)],
    twin_read_service: Annotated[TwinReadService, Depends(get_twin_read_service)],
    planning_service: Annotated[AdaptivePlanningService, Depends(get_adaptive_planning_service)],
    recommendation_service: Annotated[LearningRecommendationService, Depends(get_learning_recommendation_service)],
    memory_service: Annotated[CoachingMemoryService, Depends(get_coaching_memory_service)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> GoalForecastingService:
    return GoalForecastingService(
        repository=forecasting_repo,
        goal_repository=SqlAlchemyGoalRepository(session),
        twin_read_service=twin_read_service,
        planning_service=planning_service,
        recommendation_service=recommendation_service,
        memory_service=memory_service,
    )


def get_intervention_repo(
    session: Annotated[AsyncSession, Depends(get_session)],
):
    from prepos.infrastructure.db.repositories.intervention_repository import SqlAlchemyInterventionRepository

    return SqlAlchemyInterventionRepository(session)


def get_mentor_intervention_service(
    intervention_repo: Annotated[object, Depends(get_intervention_repo)],
    twin_read_service: Annotated[TwinReadService, Depends(get_twin_read_service)],
    recommendation_service: Annotated[LearningRecommendationService, Depends(get_learning_recommendation_service)],
    memory_service: Annotated[CoachingMemoryService, Depends(get_coaching_memory_service)],
    planning_service: Annotated[AdaptivePlanningService, Depends(get_adaptive_planning_service)],
    forecasting_service: Annotated[GoalForecastingService, Depends(get_goal_forecasting_service)],
):
    from prepos.application.interventions.intervention_service import MentorInterventionService

    return MentorInterventionService(
        repository=intervention_repo,
        twin_read_service=twin_read_service,
        recommendation_service=recommendation_service,
        memory_service=memory_service,
        planning_service=planning_service,
        forecasting_service=forecasting_service,
    )


def get_cohort_repo(
    session: Annotated[AsyncSession, Depends(get_session)],
):
    from prepos.infrastructure.db.repositories.cohort_repository import SqlAlchemyCohortRepository

    return SqlAlchemyCohortRepository(session)


def get_cohort_intelligence_service(
    cohort_repo: Annotated[object, Depends(get_cohort_repo)],
):
    from prepos.application.cohort.cohort_service import CohortIntelligenceService

    return CohortIntelligenceService(repository=cohort_repo)


def get_institution_repo(
    session: Annotated[AsyncSession, Depends(get_session)],
):
    from prepos.infrastructure.db.repositories.institution_repository import SqlAlchemyInstitutionRepository

    return SqlAlchemyInstitutionRepository(session)


def get_institution_intelligence_service(
    institution_repo: Annotated[object, Depends(get_institution_repo)],
):
    from prepos.application.institution.institution_service import InstitutionIntelligenceService

    return InstitutionIntelligenceService(repository=institution_repo)


def get_institution_outcome_repo(
    session: Annotated[AsyncSession, Depends(get_session)],
):
    from prepos.infrastructure.db.repositories.institution_outcome_repository import (
        SqlAlchemyInstitutionOutcomeRepository,
    )

    return SqlAlchemyInstitutionOutcomeRepository(session)


def get_institution_outcome_service(
    outcome_repo: Annotated[object, Depends(get_institution_outcome_repo)],
):
    from prepos.application.institution_outcomes.outcome_service import InstitutionOutcomeService

    return InstitutionOutcomeService(repository=outcome_repo)


def get_agent_repo(
    session: Annotated[AsyncSession, Depends(get_session)],
):
    from prepos.infrastructure.db.repositories.agent_repository import SqlAlchemyAgentRepository

    return SqlAlchemyAgentRepository(session)


def get_agent_analytics_service(
    agent_repo: Annotated[object, Depends(get_agent_repo)],
):
    from prepos.application.agents.agent_analytics import AgentAnalyticsService

    return AgentAnalyticsService(repository=agent_repo)


def get_agentops_repo(
    session: Annotated[AsyncSession, Depends(get_session)],
):
    from prepos.infrastructure.db.repositories.agentops_repository import SqlAlchemyAgentOpsRepository

    return SqlAlchemyAgentOpsRepository(session)


def get_agent_trace_service(
    agentops_repo: Annotated[object, Depends(get_agentops_repo)],
):
    from prepos.application.agentops.trace_service import AgentTraceService

    return AgentTraceService(repository=agentops_repo)


def get_agent_evaluation_service(
    agentops_repo: Annotated[object, Depends(get_agentops_repo)],
):
    from prepos.application.agentops.evaluation_service import AgentEvaluationService

    return AgentEvaluationService(repository=agentops_repo)


def get_agent_feedback_service(
    agentops_repo: Annotated[object, Depends(get_agentops_repo)],
):
    from prepos.application.agentops.feedback_service import AgentFeedbackService

    return AgentFeedbackService(repository=agentops_repo)


def get_agent_cost_service(
    agentops_repo: Annotated[object, Depends(get_agentops_repo)],
):
    from prepos.application.agentops.cost_service import AgentCostService

    return AgentCostService(repository=agentops_repo)


def get_agent_approval_service(
    agentops_repo: Annotated[object, Depends(get_agentops_repo)],
):
    from prepos.application.agentops.approval_service import AgentApprovalService

    return AgentApprovalService(repository=agentops_repo)


def get_agent_health_service(
    agentops_repo: Annotated[object, Depends(get_agentops_repo)],
):
    from prepos.application.agentops.health_service import AgentHealthService

    return AgentHealthService(repository=agentops_repo)


def get_agent_orchestrator(
    session: Annotated[AsyncSession, Depends(get_session)],
    recommendation_service: Annotated[LearningRecommendationService, Depends(get_learning_recommendation_service)],
    planning_service: Annotated[AdaptivePlanningService, Depends(get_adaptive_planning_service)],
    forecasting_service: Annotated[GoalForecastingService, Depends(get_goal_forecasting_service)],
    knowledge_agent_service: Annotated[KnowledgeAgentService, Depends(get_knowledge_agent_service)],
    memory_service: Annotated[CoachingMemoryService, Depends(get_coaching_memory_service)],
    pyq_service: Annotated[object, Depends(get_pyq_service)],
    twin_read_service: Annotated[TwinReadService, Depends(get_twin_read_service)],
    current_affairs_service: Annotated[object, Depends(get_current_affairs_service)],
    outcome_service: Annotated[RecommendationOutcomeService, Depends(get_recommendation_outcome_service)],
    trace_service: Annotated[object, Depends(get_agent_trace_service)],
):
    from prepos.application.agents.agent_memory_context import AgentMemoryContextBuilder
    from prepos.application.agents.learning_loop_service import AgentLearningLoopService
    from prepos.application.agents.orchestrator import AgentOrchestrator
    from prepos.application.agents.registry import build_tool_registry
    from prepos.application.cohort.cohort_service import CohortIntelligenceService
    from prepos.application.institution.institution_service import InstitutionIntelligenceService
    from prepos.application.institution_outcomes.outcome_service import InstitutionOutcomeService
    from prepos.application.interventions.intervention_service import MentorInterventionService
    from prepos.application.knowledge.current_affairs_service import CurrentAffairsService
    from prepos.application.pyq.pyq_service import PyqService
    from prepos.infrastructure.db.repositories.agent_repository import SqlAlchemyAgentRepository
    from prepos.infrastructure.db.repositories.cohort_repository import SqlAlchemyCohortRepository
    from prepos.infrastructure.db.repositories.institution_outcome_repository import (
        SqlAlchemyInstitutionOutcomeRepository,
    )
    from prepos.infrastructure.db.repositories.institution_repository import SqlAlchemyInstitutionRepository
    from prepos.infrastructure.db.repositories.intervention_repository import SqlAlchemyInterventionRepository

    assert isinstance(pyq_service, PyqService)
    assert isinstance(current_affairs_service, CurrentAffairsService)
    intervention_service = MentorInterventionService(
        repository=SqlAlchemyInterventionRepository(session),
        twin_read_service=twin_read_service,
        recommendation_service=recommendation_service,
        memory_service=memory_service,
        planning_service=planning_service,
        forecasting_service=forecasting_service,
    )
    tool_registry = build_tool_registry(
        recommendation_service=recommendation_service,
        planning_service=planning_service,
        forecasting_service=forecasting_service,
        knowledge_service=knowledge_agent_service,
        memory_service=memory_service,
        pyq_service=pyq_service,
        current_affairs_service=current_affairs_service,
        intervention_service=intervention_service,
        cohort_service=CohortIntelligenceService(repository=SqlAlchemyCohortRepository(session)),
        institution_service=InstitutionIntelligenceService(repository=SqlAlchemyInstitutionRepository(session)),
        institution_outcome_service=InstitutionOutcomeService(
            repository=SqlAlchemyInstitutionOutcomeRepository(session)
        ),
        twin_read_service=twin_read_service,
    )
    return AgentOrchestrator(
        repository=SqlAlchemyAgentRepository(session),
        tool_registry=tool_registry,
        memory_builder=AgentMemoryContextBuilder(memory_service=memory_service),
        learning_loop=AgentLearningLoopService(
            repository=SqlAlchemyAgentRepository(session),
            outcome_service=outcome_service,
        ),
        trace_service=trace_service,
    )


def get_copilot_service(
    session: Annotated[AsyncSession, Depends(get_session)],
    student_uow: Annotated[SqlAlchemyStudentUnitOfWork, Depends(get_student_uow)],
    twin_read_service: Annotated[TwinReadService, Depends(get_twin_read_service)],
    twin_recommendation_service: Annotated[TwinRecommendationService, Depends(get_twin_recommendation_service)],
    learning_graph_read_service: Annotated[LearningGraphReadService, Depends(get_learning_graph_read_service)],
    goal_service: Annotated[GoalService, Depends(get_goal_service)],
    study_plan_service: Annotated[StudyPlanService, Depends(get_study_plan_service)],
    mentor_case_read_service: Annotated[MentorCaseReadService, Depends(get_mentor_case_read_service)],
    health_service: Annotated[CopilotHealthService, Depends(get_copilot_health_service)],
    analytics_service: Annotated[CopilotAnalyticsService, Depends(get_copilot_analytics_service)],
    knowledge_agent_service: Annotated[KnowledgeAgentService, Depends(get_knowledge_agent_service)],
    pyq_service: Annotated[object, Depends(get_pyq_service)],
    recommendation_service: Annotated[LearningRecommendationService, Depends(get_learning_recommendation_service)],
    outcome_service: Annotated[RecommendationOutcomeService, Depends(get_recommendation_outcome_service)],
    outcome_analytics_service: Annotated[OutcomeAnalyticsService, Depends(get_outcome_analytics_service)],
    memory_service: Annotated[CoachingMemoryService, Depends(get_coaching_memory_service)],
    planning_service: Annotated[AdaptivePlanningService, Depends(get_adaptive_planning_service)],
    forecasting_service: Annotated[GoalForecastingService, Depends(get_goal_forecasting_service)],
    agent_orchestrator: Annotated[object, Depends(get_agent_orchestrator)],
    prompt_security_service: Annotated[object, Depends(get_prompt_security_service)],
    evaluation_platform_service: Annotated[object, Depends(get_evaluation_platform_service)],
    recommendation_validation_service: Annotated[object, Depends(get_recommendation_validation_service)],
) -> CopilotService:
    from prepos.application.agents.orchestrator import AgentOrchestrator
    from prepos.application.pyq.pyq_service import PyqService
    from prepos.application.recommendations.outcomes.outcome_service import RecommendationOutcomeService
    from prepos.application.planning.planning_service import AdaptivePlanningService
    from prepos.application.interventions.intervention_service import MentorInterventionService
    from prepos.application.cohort.cohort_service import CohortIntelligenceService
    from prepos.application.institution.institution_service import InstitutionIntelligenceService
    from prepos.application.institution_outcomes.outcome_service import InstitutionOutcomeService
    from prepos.infrastructure.db.repositories.intervention_repository import SqlAlchemyInterventionRepository
    from prepos.infrastructure.db.repositories.cohort_repository import SqlAlchemyCohortRepository
    from prepos.infrastructure.db.repositories.institution_repository import SqlAlchemyInstitutionRepository
    from prepos.infrastructure.db.repositories.institution_outcome_repository import (
        SqlAlchemyInstitutionOutcomeRepository,
    )

    assert isinstance(pyq_service, PyqService)
    assert isinstance(recommendation_service, LearningRecommendationService)
    assert isinstance(outcome_service, RecommendationOutcomeService)
    assert isinstance(outcome_analytics_service, OutcomeAnalyticsService)
    assert isinstance(memory_service, CoachingMemoryService)
    assert isinstance(planning_service, AdaptivePlanningService)
    assert isinstance(forecasting_service, GoalForecastingService)
    assert isinstance(agent_orchestrator, AgentOrchestrator)
    intervention_service = MentorInterventionService(
        repository=SqlAlchemyInterventionRepository(session),
        twin_read_service=twin_read_service,
        recommendation_service=recommendation_service,
        memory_service=memory_service,
        planning_service=planning_service,
        forecasting_service=forecasting_service,
    )
    cohort_service = CohortIntelligenceService(repository=SqlAlchemyCohortRepository(session))
    institution_service = InstitutionIntelligenceService(repository=SqlAlchemyInstitutionRepository(session))
    institution_outcome_service = InstitutionOutcomeService(
        repository=SqlAlchemyInstitutionOutcomeRepository(session)
    )
    return CopilotService(
        session=session,
        student_uow=student_uow,
        twin_read_service=twin_read_service,
        twin_recommendation_service=twin_recommendation_service,
        learning_graph_read_service=learning_graph_read_service,
        goal_service=goal_service,
        study_plan_service=study_plan_service,
        mentor_case_read_service=mentor_case_read_service,
        health_service=health_service,
        analytics_service=analytics_service,
        knowledge_agent_service=knowledge_agent_service,
        pyq_service=pyq_service,
        recommendation_service=recommendation_service,
        outcome_service=outcome_service,
        outcome_analytics_service=outcome_analytics_service,
        memory_service=memory_service,
        planning_service=planning_service,
        forecasting_service=forecasting_service,
        intervention_service=intervention_service,
        cohort_service=cohort_service,
        institution_service=institution_service,
        institution_outcome_service=institution_outcome_service,
        agent_orchestrator=agent_orchestrator,
        prompt_security_service=prompt_security_service,
        evaluation_platform_service=evaluation_platform_service,
        recommendation_validation_service=recommendation_validation_service,
    )


def get_register_use_case(
    settings: Annotated[Settings, Depends(get_settings)],
    tenant_repo: Annotated[TenantRepositoryPort, Depends(get_tenant_repo)],
    user_repo: Annotated[UserRepositoryPort, Depends(get_user_repo)],
    refresh_repo: Annotated[RefreshTokenRepositoryPort, Depends(get_refresh_repo)],
    audit_repo: Annotated[AuditLogRepositoryPort, Depends(get_audit_repo)],
    outbox: Annotated[OutboxPublisher, Depends(get_outbox)],
) -> RegisterUseCase:
    return RegisterUseCase(
        settings=settings,
        tenant_repo=tenant_repo,
        user_repo=user_repo,
        refresh_repo=refresh_repo,
        audit_repo=audit_repo,
        outbox=outbox,
    )


def get_login_use_case(
    settings: Annotated[Settings, Depends(get_settings)],
    tenant_repo: Annotated[TenantRepositoryPort, Depends(get_tenant_repo)],
    user_repo: Annotated[UserRepositoryPort, Depends(get_user_repo)],
    refresh_repo: Annotated[RefreshTokenRepositoryPort, Depends(get_refresh_repo)],
    audit_repo: Annotated[AuditLogRepositoryPort, Depends(get_audit_repo)],
) -> LoginUseCase:
    return LoginUseCase(
        settings=settings,
        tenant_repo=tenant_repo,
        user_repo=user_repo,
        refresh_repo=refresh_repo,
        audit_repo=audit_repo,
    )


def get_refresh_use_case(
    settings: Annotated[Settings, Depends(get_settings)],
    user_repo: Annotated[UserRepositoryPort, Depends(get_user_repo)],
    refresh_repo: Annotated[RefreshTokenRepositoryPort, Depends(get_refresh_repo)],
) -> RefreshTokenUseCase:
    return RefreshTokenUseCase(settings=settings, user_repo=user_repo, refresh_repo=refresh_repo)


def get_logout_use_case(
    settings: Annotated[Settings, Depends(get_settings)],
    refresh_repo: Annotated[RefreshTokenRepositoryPort, Depends(get_refresh_repo)],
    audit_repo: Annotated[AuditLogRepositoryPort, Depends(get_audit_repo)],
) -> LogoutUseCase:
    return LogoutUseCase(settings=settings, refresh_repo=refresh_repo, audit_repo=audit_repo)


def get_current_user_use_case(
    user_repo: Annotated[UserRepositoryPort, Depends(get_user_repo)],
) -> GetCurrentUserUseCase:
    return GetCurrentUserUseCase(user_repo=user_repo)


async def get_current_context(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
    authorization: Annotated[str | None, Header()] = None,
) -> TenantContext:
    token: str | None = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
    if token is None:
        token = request.cookies.get("access_token")
    if not token:
        raise AuthenticationError("Missing access token.")

    payload = decode_token(settings, token)
    if payload.get("type") != "access":
        raise AuthenticationError("Invalid access token.")

    roles_raw = payload.get("roles", [])
    roles: frozenset[RoleName] = frozenset()
    if isinstance(roles_raw, list):
        parsed: set[RoleName] = set()
        for item in roles_raw:
            try:
                parsed.add(RoleName(str(item)))
            except ValueError:
                continue
        roles = frozenset(parsed)
    request_id = get_request_id(request)
    structlog.contextvars.bind_contextvars(
        request_id=request_id,
        tenant_id=str(payload["tenant_id"]),
        user_id=str(payload["sub"]),
    )
    return TenantContext(
        tenant_id=UUID(str(payload["tenant_id"])),
        user_id=UUID(str(payload["sub"])),
        roles=roles,
        request_id=request_id,
        correlation_id=request_id,
    )


def get_platform_maturity_repo(
    session: Annotated[AsyncSession, Depends(get_session)],
):
    from prepos.infrastructure.db.repositories.platform_maturity_repository import (
        SqlAlchemyPlatformMaturityRepository,
    )

    return SqlAlchemyPlatformMaturityRepository(session)


def get_prompt_security_service(
    repo: Annotated[object, Depends(get_platform_maturity_repo)],
):
    from prepos.application.security.prompt_security_service import PromptSecurityService

    return PromptSecurityService(repository=repo)


def get_knowledge_security_service(
    repo: Annotated[object, Depends(get_platform_maturity_repo)],
):
    from prepos.application.security.knowledge_security_service import KnowledgeSecurityService

    return KnowledgeSecurityService(repository=repo)


def get_tenant_audit_service(
    repo: Annotated[object, Depends(get_platform_maturity_repo)],
):
    from prepos.application.security.tenant_audit_service import TenantAuditService

    return TenantAuditService(repository=repo)


def get_job_reliability_service(
    repo: Annotated[object, Depends(get_platform_maturity_repo)],
):
    from prepos.application.platform.job_reliability_service import JobReliabilityService

    return JobReliabilityService(repository=repo)


def get_forecast_accuracy_service(
    repo: Annotated[object, Depends(get_platform_maturity_repo)],
):
    from prepos.application.platform.forecast_accuracy_service import ForecastAccuracyService

    return ForecastAccuracyService(repository=repo)


def get_recommendation_validation_service(
    repo: Annotated[object, Depends(get_platform_maturity_repo)],
):
    from prepos.application.platform.recommendation_validation_service import (
        RecommendationValidationService,
    )

    return RecommendationValidationService(repository=repo)


def get_evaluation_platform_service(
    repo: Annotated[object, Depends(get_platform_maturity_repo)],
):
    from prepos.application.platform.evaluation_platform_service import EvaluationPlatformService

    return EvaluationPlatformService(repository=repo)


def get_disaster_recovery_service(
    settings: Annotated[Settings, Depends(get_settings)],
    repo: Annotated[object, Depends(get_platform_maturity_repo)],
):
    from prepos.application.platform.disaster_recovery_service import DisasterRecoveryService

    return DisasterRecoveryService(repository=repo, settings=settings)


def get_product_analytics_service(
    session: Annotated[AsyncSession, Depends(get_session)],
    repo: Annotated[object, Depends(get_platform_maturity_repo)],
):
    from prepos.application.platform.product_analytics_service import ProductAnalyticsService

    return ProductAnalyticsService(repository=repo, session=session)


def get_monitoring_service(
    repo: Annotated[object, Depends(get_platform_maturity_repo)],
):
    from prepos.application.platform.monitoring_service import MonitoringService

    return MonitoringService(repository=repo)


def get_outcome_measurement_service(
    repo: Annotated[object, Depends(get_platform_maturity_repo)],
):
    from prepos.application.platform.monitoring_service import OutcomeMeasurementService

    return OutcomeMeasurementService(repository=repo)


def get_platform_readiness_service(
    repo: Annotated[object, Depends(get_platform_maturity_repo)],
    prompt_security: Annotated[object, Depends(get_prompt_security_service)],
    tenant_audit: Annotated[object, Depends(get_tenant_audit_service)],
    knowledge_security: Annotated[object, Depends(get_knowledge_security_service)],
    forecast_accuracy: Annotated[object, Depends(get_forecast_accuracy_service)],
    recommendation_validation: Annotated[object, Depends(get_recommendation_validation_service)],
    disaster_recovery: Annotated[object, Depends(get_disaster_recovery_service)],
):
    from prepos.application.platform.platform_readiness_service import PlatformReadinessService

    return PlatformReadinessService(
        repository=repo,
        prompt_security=prompt_security,
        tenant_audit=tenant_audit,
        knowledge_security=knowledge_security,
        forecast_accuracy=forecast_accuracy,
        recommendation_validation=recommendation_validation,
        disaster_recovery=disaster_recovery,
    )


def get_event_bus(
    settings: Annotated[Settings, Depends(get_settings)],
    repo: Annotated[object, Depends(get_platform_maturity_repo)],
):
    from prepos.domain_events.redis_streams_bus import RedisStreamsEventBus

    return RedisStreamsEventBus(settings=settings, repository=repo)
