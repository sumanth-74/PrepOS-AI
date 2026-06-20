from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse

from prepos.api.deps import (
    get_current_context,
    get_learning_recommendation_service,
    get_outcome_analytics_service,
    get_recommendation_analytics_service,
    get_recommendation_outcome_service,
    get_student_uow,
)
from prepos.application.recommendations.outcomes.outcome_analytics import OutcomeAnalyticsService
from prepos.application.recommendations.outcomes.outcome_models import (
    CompleteRecommendationResponse,
    RecommendationEffectivenessResponse,
    RecommendationOutcomeListResponse,
    RecommendationOutcomeResponse,
)
from prepos.application.recommendations.outcomes.outcome_service import RecommendationOutcomeService
from prepos.application.recommendations.recommendation_analytics_service import RecommendationAnalyticsService
from prepos.application.recommendations.recommendation_models import (
    MentorRecommendationsRequest,
    RecommendationExplainResponse,
    RecommendationsResponse,
    StudentRecommendationsRequest,
)
from prepos.application.recommendations.recommendation_service import LearningRecommendationService
from prepos.core.exceptions import ValidationError
from prepos.core.tenancy import RoleName, TenantContext
from prepos.domain.learning_graph.exceptions import NodeNotFoundError
from prepos.infrastructure.db.repositories.student_repository import SqlAlchemyStudentUnitOfWork

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


async def _resolve_student_id(
    *,
    context: TenantContext,
    student_uow: SqlAlchemyStudentUnitOfWork,
    student_id: str | None,
) -> UUID:
    if context.has_role(RoleName.STUDENT):
        student = await student_uow.student_repo.get_by_user_id(context.tenant_id, context.user_id)
        if student is None:
            raise NodeNotFoundError("Student profile not found.")
        return student.id

    context.require_role(RoleName.FACULTY, RoleName.INSTITUTE_ADMIN)
    if student_id is None:
        raise ValidationError("student_id is required for mentor/admin requests.")
    student = await student_uow.student_repo.get_by_id(context.tenant_id, UUID(student_id))
    if student is None:
        raise ValidationError("Student not found.", details={"student_id": student_id})
    return student.id


@router.post("/student", response_model=RecommendationsResponse, summary="Personalized student recommendations")
async def get_student_recommendations(
    request: StudentRecommendationsRequest,
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[LearningRecommendationService, Depends(get_learning_recommendation_service)],
    student_uow: Annotated[SqlAlchemyStudentUnitOfWork, Depends(get_student_uow)],
) -> RecommendationsResponse:
    context.require_role(RoleName.STUDENT)
    student = await student_uow.student_repo.get_by_user_id(context.tenant_id, context.user_id)
    if student is None:
        raise NodeNotFoundError("Student profile not found.", details={"user_id": str(context.user_id)})
    return await service.get_student_recommendations(
        tenant_id=context.tenant_id,
        student_id=student.id,
        exam_id=request.exam_id,
        user_id=context.user_id,
        limit=request.limit,
    )


@router.post("/mentor", response_model=RecommendationsResponse, summary="Personalized mentor recommendations")
async def get_mentor_recommendations(
    request: MentorRecommendationsRequest,
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[LearningRecommendationService, Depends(get_learning_recommendation_service)],
    student_uow: Annotated[SqlAlchemyStudentUnitOfWork, Depends(get_student_uow)],
) -> RecommendationsResponse:
    context.require_role(RoleName.FACULTY, RoleName.INSTITUTE_ADMIN)
    student = await student_uow.student_repo.get_by_id(context.tenant_id, UUID(request.student_id))
    if student is None:
        raise ValidationError("Student not found.", details={"student_id": request.student_id})
    return await service.get_mentor_recommendations(
        tenant_id=context.tenant_id,
        student_id=student.id,
        exam_id=request.exam_id,
        user_id=context.user_id,
        limit=request.limit,
    )


@router.get("/outcomes", response_model=RecommendationOutcomeListResponse, summary="List recommendation outcomes")
async def list_recommendation_outcomes(
    context: Annotated[TenantContext, Depends(get_current_context)],
    outcome_service: Annotated[RecommendationOutcomeService, Depends(get_recommendation_outcome_service)],
    student_uow: Annotated[SqlAlchemyStudentUnitOfWork, Depends(get_student_uow)],
    student_id: str | None = Query(default=None),
    concept_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
) -> RecommendationOutcomeListResponse:
    resolved_student_id: UUID | None = None
    if context.has_role(RoleName.STUDENT):
        resolved_student_id = await _resolve_student_id(
            context=context,
            student_uow=student_uow,
            student_id=None,
        )
    else:
        context.require_role(RoleName.FACULTY, RoleName.INSTITUTE_ADMIN)
        if student_id is not None:
            resolved_student_id = await _resolve_student_id(
                context=context,
                student_uow=student_uow,
                student_id=student_id,
            )
    return await outcome_service.list_outcomes(
        tenant_id=context.tenant_id,
        student_id=resolved_student_id,
        user_id=context.user_id if context.has_role(RoleName.STUDENT) else None,
        concept_id=concept_id,
        limit=limit,
    )


@router.get(
    "/outcomes/{concept_id}",
    response_model=RecommendationOutcomeResponse,
    summary="Get latest outcome for a concept",
)
async def get_recommendation_outcome(
    concept_id: str,
    context: Annotated[TenantContext, Depends(get_current_context)],
    outcome_service: Annotated[RecommendationOutcomeService, Depends(get_recommendation_outcome_service)],
    student_uow: Annotated[SqlAlchemyStudentUnitOfWork, Depends(get_student_uow)],
    student_id: str | None = Query(default=None),
) -> RecommendationOutcomeResponse:
    resolved_student_id = await _resolve_student_id(
        context=context,
        student_uow=student_uow,
        student_id=student_id,
    )
    outcome = await outcome_service.get_outcome_for_concept(
        tenant_id=context.tenant_id,
        student_id=resolved_student_id,
        concept_id=concept_id,
    )
    if outcome is None:
        raise ValidationError("Outcome not found.", details={"concept_id": concept_id})
    return outcome


@router.get(
    "/effectiveness",
    response_model=RecommendationEffectivenessResponse,
    summary="Recommendation effectiveness summary",
)
async def get_recommendation_effectiveness(
    context: Annotated[TenantContext, Depends(get_current_context)],
    analytics_service: Annotated[OutcomeAnalyticsService, Depends(get_outcome_analytics_service)],
    student_uow: Annotated[SqlAlchemyStudentUnitOfWork, Depends(get_student_uow)],
    student_id: str | None = Query(default=None),
    concept_id: str | None = Query(default=None),
    period_days: int = Query(default=30, ge=1, le=365),
) -> RecommendationEffectivenessResponse:
    resolved_student_id: UUID | None = None
    if context.has_role(RoleName.STUDENT):
        resolved_student_id = await _resolve_student_id(
            context=context,
            student_uow=student_uow,
            student_id=None,
        )
    elif student_id is not None:
        context.require_role(RoleName.FACULTY, RoleName.INSTITUTE_ADMIN)
        resolved_student_id = await _resolve_student_id(
            context=context,
            student_uow=student_uow,
            student_id=student_id,
        )
    else:
        context.require_role(RoleName.FACULTY, RoleName.INSTITUTE_ADMIN)
    return await analytics_service.get_effectiveness_summary(
        tenant_id=context.tenant_id,
        student_id=resolved_student_id,
        concept_id=concept_id,
        period_days=period_days,
    )


@router.get(
    "/explain/{concept_id}",
    response_model=RecommendationExplainResponse,
    summary="Explain recommendation scoring for a concept",
)
async def explain_recommendation(
    concept_id: str,
    context: Annotated[TenantContext, Depends(get_current_context)],
    service: Annotated[LearningRecommendationService, Depends(get_learning_recommendation_service)],
    analytics_service: Annotated[RecommendationAnalyticsService, Depends(get_recommendation_analytics_service)],
    outcome_service: Annotated[RecommendationOutcomeService, Depends(get_recommendation_outcome_service)],
    student_uow: Annotated[SqlAlchemyStudentUnitOfWork, Depends(get_student_uow)],
    student_id: str | None = Query(default=None),
    exam_id: str | None = Query(default=None),
) -> RecommendationExplainResponse:
    resolved_student_id = await _resolve_student_id(
        context=context,
        student_uow=student_uow,
        student_id=student_id,
    )

    explanation = await service.explain_concept(
        tenant_id=context.tenant_id,
        student_id=resolved_student_id,
        exam_id=exam_id,
        concept_id=concept_id,
    )
    historical_effectiveness, average_actual_gain = await outcome_service.get_historical_effectiveness(
        tenant_id=context.tenant_id,
        student_id=resolved_student_id,
        concept_id=concept_id,
    )
    explanation.historical_effectiveness = historical_effectiveness or None
    explanation.average_actual_gain = average_actual_gain or None

    await analytics_service.record_clicked(
        tenant_id=context.tenant_id,
        user_id=context.user_id,
        student_id=resolved_student_id,
        concept_id=concept_id,
        impact_score=explanation.impact_score,
        estimated_gain=explanation.estimated_readiness_gain,
    )
    return explanation


@router.post(
    "/{concept_id}/complete",
    response_model=CompleteRecommendationResponse,
    summary="Mark a recommendation as completed and evaluate outcome",
)
async def complete_recommendation(
    concept_id: str,
    context: Annotated[TenantContext, Depends(get_current_context)],
    analytics_service: Annotated[RecommendationAnalyticsService, Depends(get_recommendation_analytics_service)],
    outcome_service: Annotated[RecommendationOutcomeService, Depends(get_recommendation_outcome_service)],
    student_uow: Annotated[SqlAlchemyStudentUnitOfWork, Depends(get_student_uow)],
    student_id: str | None = Query(default=None),
    exam_id: str | None = Query(default=None),
    study_minutes: int = Query(default=0, ge=0, le=1440),
) -> CompleteRecommendationResponse:
    resolved_student_id = await _resolve_student_id(
        context=context,
        student_uow=student_uow,
        student_id=student_id,
    )

    await analytics_service.record_completed(
        tenant_id=context.tenant_id,
        user_id=context.user_id,
        student_id=resolved_student_id,
        concept_id=concept_id,
        readiness_gain_after=None,
    )
    outcome = await outcome_service.evaluate_on_completion(
        tenant_id=context.tenant_id,
        user_id=context.user_id,
        student_id=resolved_student_id,
        concept_id=concept_id,
        exam_id=exam_id,
        study_minutes=study_minutes,
    )
    return CompleteRecommendationResponse(status="recorded", outcome=outcome)
