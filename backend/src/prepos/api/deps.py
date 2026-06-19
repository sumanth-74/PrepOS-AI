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
from prepos.application.goal.forecast_service import ForecastService
from prepos.application.goal.milestone_service import MilestoneService
from prepos.application.goal.service import GoalService
from prepos.application.learning_graph.activity_service import LearningGraphActivityService
from prepos.application.learning_graph.read_services import LearningGraphReadService
from prepos.application.learning_graph.services import LearningGraphService
from prepos.application.mentor.mentor_case_read_service import MentorCaseReadService, MentorQueueReadService
from prepos.application.mentor.mentor_case_service import MentorCaseService
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
from prepos.infrastructure.db.repositories.exam_repository import SqlAlchemyExamCatalogUnitOfWork
from prepos.infrastructure.db.repositories.goal_repository import SqlAlchemyGoalRepository
from prepos.infrastructure.db.repositories.intervention_history_repository import (
    SqlAlchemyInterventionHistoryRepository,
)
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
