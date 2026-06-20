from __future__ import annotations

import time
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from prepos.application.copilot.analytics_service import CopilotAnalyticsService
from prepos.application.copilot.dto import CopilotQueryRequest, CopilotQueryResponse, CopilotSourceResponse
from prepos.application.copilot.handlers import admin as admin_handlers
from prepos.application.copilot.handlers import mentor as mentor_handlers
from prepos.application.copilot.handlers import student as student_handlers
from prepos.application.copilot.handlers.mentor_knowledge import (
    MENTOR_CONTENT_INTENTS,
    map_mentor_knowledge_to_copilot_response,
)
from prepos.application.copilot.handlers.student_knowledge import (
    STUDENT_CONTENT_INTENTS,
    map_knowledge_to_copilot_response,
)
from prepos.application.copilot.handlers.mentor_outcomes import (
    MENTOR_OUTCOME_INTENTS,
    build_mentor_outcome_response,
)
from prepos.application.copilot.handlers.mentor_recommendations import (
    MENTOR_RECOMMENDATION_INTENTS,
    map_mentor_recommendations_to_copilot_response,
)
from prepos.application.copilot.handlers.student_outcomes import (
    STUDENT_OUTCOME_INTENTS,
    build_student_outcome_response,
)
from prepos.application.copilot.handlers.student_recommendations import (
    STUDENT_RECOMMENDATION_INTENTS,
    map_student_recommendations_to_copilot_response,
)
from prepos.application.copilot.handlers.student_pyq import STUDENT_PYQ_INTENTS, map_pyq_to_copilot_response
from prepos.application.copilot.handlers.mentor_pyq import MENTOR_PYQ_INTENTS, map_mentor_pyq_to_copilot_response
from prepos.application.copilot.health_service import CopilotHealthService
from prepos.application.copilot.intent_router import route_intent, suggested_prompts_for_persona
from prepos.application.copilot.mentor_knowledge_context import MentorKnowledgeContextBuilder
from prepos.application.goal.service import GoalService
from prepos.application.knowledge.dto import KnowledgeAskRequest
from prepos.application.knowledge.knowledge_agent_service import KnowledgeAgentService
from prepos.application.learning_graph.read_services import LearningGraphReadService
from prepos.application.mentor.mentor_case_read_service import MentorCaseReadService
from prepos.application.pyq.pyq_service import PyqService
from prepos.application.copilot.handlers.mentor_memory import (
    MENTOR_MEMORY_INTENTS,
    build_mentor_memory_response,
)
from prepos.application.copilot.handlers.student_memory import (
    STUDENT_MEMORY_INJECTION_INTENTS,
    STUDENT_MEMORY_INTENTS,
    build_student_memory_response,
)
from prepos.application.copilot.handlers.mentor_planning import (
    MENTOR_PLANNING_INTENTS,
    build_mentor_planning_response,
)
from prepos.application.copilot.handlers.student_planning import (
    STUDENT_PLANNING_INTENTS,
    build_student_planning_response,
)
from prepos.application.memory.memory_context import append_memory_context_to_answer
from prepos.application.memory.memory_service import CoachingMemoryService
from prepos.application.copilot.handlers.mentor_forecasting import (
    MENTOR_FORECASTING_INTENTS,
    build_mentor_forecast_response,
)
from prepos.application.copilot.handlers.student_forecasting import (
    STUDENT_FORECASTING_INTENTS,
    build_student_forecast_response,
)
from prepos.application.copilot.handlers.mentor_interventions import (
    ADMIN_INTERVENTION_INTENTS,
    MENTOR_INTERVENTION_OPT_INTENTS,
    STUDENT_INTERVENTION_INTENTS,
    build_admin_intervention_response,
    build_mentor_intervention_response,
    build_student_intervention_response,
)
from prepos.application.forecasting.forecast_service import GoalForecastingService
from prepos.application.interventions.intervention_service import MentorInterventionService
from prepos.application.cohort.cohort_service import CohortIntelligenceService
from prepos.application.copilot.handlers.cohort_intelligence import (
    ADMIN_COHORT_INTENTS,
    MENTOR_COHORT_INTENTS,
    build_admin_cohort_response,
    build_mentor_cohort_response,
)
from prepos.application.institution.institution_service import InstitutionIntelligenceService
from prepos.application.copilot.handlers.institution_intelligence import (
    ADMIN_INSTITUTION_INTENTS,
    build_admin_institution_response,
)
from prepos.application.institution_outcomes.outcome_service import InstitutionOutcomeService
from prepos.application.agents.orchestrator import AgentOrchestrator
from prepos.application.copilot.handlers.institution_outcomes import (
    ADMIN_INSTITUTION_OUTCOME_INTENTS,
    build_admin_institution_outcome_response,
)
from prepos.application.recommendations.outcomes.outcome_analytics import OutcomeAnalyticsService
from prepos.application.recommendations.outcomes.outcome_service import RecommendationOutcomeService
from prepos.application.recommendations.recommendation_service import LearningRecommendationService
from prepos.application.study_plan.service import StudyPlanService
from prepos.application.twin.services import TwinRecommendationService
from prepos.application.twin.twin_read_service import TwinReadService
from prepos.core.exceptions import ValidationError
from prepos.core.tenancy import RoleName, TenantContext
from prepos.domain.learning_graph.exceptions import NodeNotFoundError
from prepos.infrastructure.db.repositories.student_repository import SqlAlchemyStudentUnitOfWork


class CopilotService:
    def __init__(
        self,
        *,
        session: AsyncSession,
        student_uow: SqlAlchemyStudentUnitOfWork,
        twin_read_service: TwinReadService,
        twin_recommendation_service: TwinRecommendationService,
        learning_graph_read_service: LearningGraphReadService,
        goal_service: GoalService,
        study_plan_service: StudyPlanService,
        mentor_case_read_service: MentorCaseReadService,
        health_service: CopilotHealthService,
        analytics_service: CopilotAnalyticsService,
        knowledge_agent_service: KnowledgeAgentService,
        pyq_service: PyqService,
        recommendation_service: LearningRecommendationService,
        outcome_service: RecommendationOutcomeService,
        outcome_analytics_service: OutcomeAnalyticsService,
        memory_service: CoachingMemoryService,
        planning_service: AdaptivePlanningService,
        forecasting_service: GoalForecastingService,
        intervention_service: MentorInterventionService,
        cohort_service: CohortIntelligenceService,
        institution_service: InstitutionIntelligenceService,
        institution_outcome_service: InstitutionOutcomeService,
        agent_orchestrator: AgentOrchestrator,
    ) -> None:
        self._session = session
        self._student_uow = student_uow
        self._twin_read_service = twin_read_service
        self._twin_recommendation_service = twin_recommendation_service
        self._learning_graph_read_service = learning_graph_read_service
        self._goal_service = goal_service
        self._study_plan_service = study_plan_service
        self._mentor_case_read_service = mentor_case_read_service
        self._health_service = health_service
        self._analytics_service = analytics_service
        self._knowledge_agent_service = knowledge_agent_service
        self._pyq_service = pyq_service
        self._recommendation_service = recommendation_service
        self._outcome_service = outcome_service
        self._outcome_analytics_service = outcome_analytics_service
        self._memory_service = memory_service
        self._planning_service = planning_service
        self._forecasting_service = forecasting_service
        self._intervention_service = intervention_service
        self._cohort_service = cohort_service
        self._institution_service = institution_service
        self._institution_outcome_service = institution_outcome_service
        self._agent_orchestrator = agent_orchestrator
        self._mentor_knowledge_context_builder = MentorKnowledgeContextBuilder()

    async def query(
        self,
        *,
        context: TenantContext,
        request: CopilotQueryRequest,
    ) -> CopilotQueryResponse:
        started = time.perf_counter()
        self._validate_persona_access(context, request.persona)

        if request.agent_mode:
            student_id: UUID | None = None
            student_user_id: UUID | None = None
            if request.persona in {"student", "mentor"}:
                student_id = await self._resolve_student_id(context, request)
                student = await self._student_uow.student_repo.get_by_id(context.tenant_id, student_id)
                student_user_id = student.user_id if student is not None else context.user_id
            exam_id = request.exam_id
            if exam_id is None and student_id is not None:
                exam_id = await self._resolve_exam_id(context, student_id, request.exam_id)

            agent_response = await self._agent_orchestrator.execute(
                tenant_id=context.tenant_id,
                user_id=context.user_id,
                persona=request.persona,
                question=request.question,
                student_id=student_id,
                student_user_id=student_user_id,
                exam_id=exam_id,
            )
            response = CopilotQueryResponse(
                intent="agent_orchestration",
                answer=agent_response.answer,
                confidence=agent_response.confidence,
                sources=[
                    CopilotSourceResponse(label=source.label, reference=source.reference)
                    for source in agent_response.sources
                ],
                trace_id=agent_response.trace_id,
                execution_id=agent_response.execution_id,
            )
        else:
            routed_intent = route_intent(persona=request.persona, question=request.question)

            if routed_intent == "unknown":
                response = self._unknown_intent_response(request.persona)
            elif request.persona == "admin":
                response = await self._handle_admin_intent(routed_intent, context=context)
            elif request.persona == "mentor" and routed_intent in MENTOR_COHORT_INTENTS:
                response = await build_mentor_cohort_response(
                    intent=routed_intent,
                    cohort_service=self._cohort_service,
                    tenant_id=context.tenant_id,
                    exam_id=request.exam_id,
                )
            else:
                student_id = await self._resolve_student_id(context, request)
                exam_id = await self._resolve_exam_id(context, student_id, request.exam_id)
                if request.persona == "student":
                    response = await self._handle_student_intent(
                        intent=routed_intent,
                        question=request.question,
                        tenant_id=context.tenant_id,
                        student_id=student_id,
                        exam_id=exam_id,
                        user_id=context.user_id,
                    )
                else:
                    response = await self._handle_mentor_intent(
                        intent=routed_intent,
                        question=request.question,
                        tenant_id=context.tenant_id,
                        student_id=student_id,
                        exam_id=exam_id,
                        case_id=request.case_id,
                        user_id=context.user_id,
                    )

        elapsed_ms = max(0, int((time.perf_counter() - started) * 1000))
        recorded = await self._analytics_service.record_query(
            context=context,
            persona=request.persona,
            intent=response.intent,
            query_text=request.question,
            response_time_ms=elapsed_ms,
            session_id=request.session_id,
            citation_count=len(response.citations) if response.citations else None,
            confidence=response.confidence,
        )
        response.session_id = recorded.session_id
        return response

    def _validate_persona_access(self, context: TenantContext, persona: str) -> None:
        if persona == "student":
            context.require_role(RoleName.STUDENT)
            return
        if persona == "mentor":
            context.require_role(RoleName.FACULTY, RoleName.INSTITUTE_ADMIN)
            return
        if persona == "admin":
            context.require_role(RoleName.INSTITUTE_ADMIN)
            return
        raise ValidationError(
            "Unsupported copilot persona.",
            details={"persona": persona},
        )

    async def _resolve_student_id(
        self,
        context: TenantContext,
        request: CopilotQueryRequest,
    ) -> UUID:
        if request.persona == "student":
            student = await self._student_uow.student_repo.get_by_user_id(
                context.tenant_id,
                context.user_id,
            )
            if student is None:
                raise NodeNotFoundError(
                    "Student profile not found.",
                    details={"user_id": str(context.user_id)},
                )
            return student.id

        if request.student_id is None:
            raise ValidationError(
                "student_id is required for mentor copilot queries.",
                details={"field": "student_id"},
            )
        student = await self._student_uow.student_repo.get_by_id(context.tenant_id, request.student_id)
        if student is None:
            raise NodeNotFoundError(
                "Student not found.",
                details={"student_id": str(request.student_id)},
            )
        return student.id

    async def _resolve_exam_id(
        self,
        context: TenantContext,
        student_id: UUID,
        exam_id: str | None,
    ) -> str | None:
        if exam_id is not None:
            return exam_id
        student = await self._student_uow.student_repo.get_by_id(context.tenant_id, student_id)
        if student is None:
            return None
        return student.target_exam_id

    async def _handle_student_intent(
        self,
        *,
        intent: str,
        question: str,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str | None,
        user_id: UUID,
    ) -> CopilotQueryResponse:
        if intent in STUDENT_MEMORY_INTENTS:
            return await build_student_memory_response(
                intent=intent,
                memory_service=self._memory_service,
                tenant_id=tenant_id,
                user_id=user_id,
            )

        if intent in STUDENT_PLANNING_INTENTS:
            return await build_student_planning_response(
                intent=intent,
                planning_service=self._planning_service,
                tenant_id=tenant_id,
                user_id=user_id,
                student_id=student_id,
                exam_id=exam_id,
            )

        if intent in STUDENT_FORECASTING_INTENTS:
            return await build_student_forecast_response(
                intent=intent,
                forecast_service=self._forecasting_service,
                tenant_id=tenant_id,
                user_id=user_id,
                student_id=student_id,
                exam_id=exam_id,
            )

        if intent in STUDENT_INTERVENTION_INTENTS:
            return await build_student_intervention_response(
                intent=intent,
                intervention_service=self._intervention_service,
                tenant_id=tenant_id,
                student_user_id=user_id,
                exam_id=exam_id,
            )

        memory_lines: list[str] = []
        if intent in STUDENT_MEMORY_INJECTION_INTENTS or intent in STUDENT_OUTCOME_INTENTS:
            memory_context = await self._memory_service.load_student_context(
                tenant_id=tenant_id,
                user_id=user_id,
            )
            memory_lines = memory_context.context_lines

        if intent in STUDENT_OUTCOME_INTENTS:
            response = await build_student_outcome_response(
                intent=intent,
                outcome_service=self._outcome_service,
                tenant_id=tenant_id,
                student_id=student_id,
            )
            if memory_lines:
                response = CopilotQueryResponse(
                    intent=response.intent,
                    answer=append_memory_context_to_answer(response.answer, memory_context),
                    recommendations=response.recommendations,
                    confidence=response.confidence,
                    sources=response.sources,
                )
            return response

        if intent in STUDENT_RECOMMENDATION_INTENTS:
            recommendations = await self._recommendation_service.get_recommendations_for_intent(
                tenant_id=tenant_id,
                student_id=student_id,
                exam_id=exam_id,
                user_id=user_id,
                intent=intent,
                limit=5,
            )
            return map_student_recommendations_to_copilot_response(
                intent=intent,
                recommendations=recommendations,
                memory_lines=memory_lines,
            )

        if intent in STUDENT_CONTENT_INTENTS:
            resolved_exam_id = exam_id or "upsc_cse"
            knowledge = await self._knowledge_agent_service.ask(
                tenant_id=tenant_id,
                request=KnowledgeAskRequest(
                    query=question,
                    exam_id=resolved_exam_id,
                ),
            )
            return map_knowledge_to_copilot_response(intent=intent, knowledge=knowledge)

        if intent in STUDENT_PYQ_INTENTS:
            resolved_exam_id = exam_id or "upsc_cse"
            frequency_summary = await self._pyq_service.build_frequency_summary(
                tenant_id=tenant_id,
                exam_id=resolved_exam_id,
                concept_ids=[],
            )
            knowledge = await self._knowledge_agent_service.ask(
                tenant_id=tenant_id,
                request=KnowledgeAskRequest(
                    query=question,
                    exam_id=resolved_exam_id,
                    pyq_mode=True,
                    prefer_pyq=True,
                    frequency_summary=frequency_summary,
                ),
            )
            return map_pyq_to_copilot_response(intent=intent, knowledge=knowledge)

        dashboard = await self._twin_read_service.get_dashboard(
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
        )

        if intent == "readiness_low":
            answer, sources = await student_handlers.handle_readiness_low(dashboard=dashboard)
            return CopilotQueryResponse(intent=intent, answer=answer, sources=sources)

        if intent == "study_today":
            study_plan = await self._study_plan_service.get_study_plan(
                tenant_id=tenant_id,
                student_id=student_id,
                exam_id=exam_id,
            )
            recommendations = await self._twin_recommendation_service.list_recommendations(
                tenant_id=tenant_id,
                student_id=student_id,
                limit=5,
            )
            answer, sources = await student_handlers.handle_study_today(
                dashboard=dashboard,
                study_plan=study_plan,
                recommendations=recommendations,
            )
            return CopilotQueryResponse(intent=intent, answer=answer, sources=sources)

        if intent == "weakest_concepts":
            weaknesses = await self._learning_graph_read_service.get_weaknesses(
                tenant_id=tenant_id,
                student_id=student_id,
                limit=8,
            )
            answer, sources = await student_handlers.handle_weakest_concepts(weaknesses=weaknesses)
            return CopilotQueryResponse(intent=intent, answer=answer, sources=sources)

        if intent == "recommendation_why":
            recommendations = await self._twin_recommendation_service.list_recommendations(
                tenant_id=tenant_id,
                student_id=student_id,
                limit=5,
            )
            answer, sources = await student_handlers.handle_recommendation_why(
                recommendations=recommendations,
            )
            return CopilotQueryResponse(intent=intent, answer=answer, sources=sources)

        if intent == "goal_on_track":
            goal = None
            if exam_id is not None:
                goal = await self._goal_service.get_goal(
                    tenant_id=tenant_id,
                    student_id=student_id,
                    exam_id=exam_id,
                )
            answer, sources = await student_handlers.handle_goal_on_track(
                dashboard=dashboard,
                goal=goal,
            )
            return CopilotQueryResponse(intent=intent, answer=answer, sources=sources)

        if intent == "next_activities":
            study_plan = await self._study_plan_service.get_study_plan(
                tenant_id=tenant_id,
                student_id=student_id,
                exam_id=exam_id,
            )
            answer, sources = await student_handlers.handle_next_activities(
                study_plan=study_plan,
                due_revision_count=dashboard.due_revision_count,
            )
            return CopilotQueryResponse(intent=intent, answer=answer, sources=sources)

        return self._unknown_intent_response("student")

    async def _handle_mentor_intent(
        self,
        *,
        intent: str,
        question: str,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str | None,
        case_id: UUID | None,
        user_id: UUID,
    ) -> CopilotQueryResponse:
        student = await self._student_uow.student_repo.get_by_id(tenant_id, student_id)
        student_user_id = student.user_id if student is not None else user_id

        if intent in MENTOR_MEMORY_INTENTS:
            return await build_mentor_memory_response(
                intent=intent,
                memory_service=self._memory_service,
                tenant_id=tenant_id,
                student_user_id=student_user_id,
            )

        if intent in MENTOR_COHORT_INTENTS:
            return await build_mentor_cohort_response(
                intent=intent,
                cohort_service=self._cohort_service,
                tenant_id=tenant_id,
                exam_id=exam_id,
            )

        if intent in MENTOR_INTERVENTION_OPT_INTENTS:
            return await build_mentor_intervention_response(
                intent=intent,
                intervention_service=self._intervention_service,
                tenant_id=tenant_id,
                mentor_id=user_id,
                student_user_id=student_user_id,
                student_id=student_id,
                exam_id=exam_id,
            )

        if intent in MENTOR_PLANNING_INTENTS:
            return await build_mentor_planning_response(
                intent=intent,
                planning_service=self._planning_service,
                tenant_id=tenant_id,
                student_user_id=student_user_id,
                student_id=student_id,
                exam_id=exam_id,
            )

        if intent in MENTOR_FORECASTING_INTENTS:
            return await build_mentor_forecast_response(
                intent=intent,
                forecast_service=self._forecasting_service,
                tenant_id=tenant_id,
                student_user_id=student_user_id,
                student_id=student_id,
                exam_id=exam_id,
            )

        mentor_memory_context = await self._memory_service.load_mentor_context(
            tenant_id=tenant_id,
            user_id=user_id,
            student_user_id=student_user_id,
        )

        if intent in MENTOR_OUTCOME_INTENTS:
            response = await build_mentor_outcome_response(
                intent=intent,
                outcome_service=self._outcome_service,
                analytics_service=self._outcome_analytics_service,
                tenant_id=tenant_id,
                student_id=student_id,
            )
            if mentor_memory_context.context_lines:
                response = CopilotQueryResponse(
                    intent=response.intent,
                    answer=append_memory_context_to_answer(response.answer, mentor_memory_context),
                    recommendations=response.recommendations,
                    confidence=response.confidence,
                    sources=response.sources,
                    student_context_used=True,
                )
            return response

        if intent in MENTOR_RECOMMENDATION_INTENTS:
            recommendations = await self._recommendation_service.get_recommendations_for_intent(
                tenant_id=tenant_id,
                student_id=student_id,
                exam_id=exam_id,
                user_id=user_id,
                intent=intent,
                limit=5,
            )
            response = map_mentor_recommendations_to_copilot_response(
                intent=intent,
                recommendations=recommendations,
            )
            if mentor_memory_context.context_lines:
                response = CopilotQueryResponse(
                    intent=response.intent,
                    answer=append_memory_context_to_answer(response.answer, mentor_memory_context),
                    recommendations=response.recommendations,
                    confidence=response.confidence,
                    sources=response.sources,
                    student_context_used=True,
                )
            return response

        dashboard = await self._twin_read_service.get_dashboard(
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
        )
        mentor_case = None
        if case_id is not None:
            mentor_case = await self._mentor_case_read_service.get_case(
                tenant_id=tenant_id,
                case_id=case_id,
            )

        if intent in MENTOR_CONTENT_INTENTS:
            weaknesses = await self._learning_graph_read_service.get_weaknesses(
                tenant_id=tenant_id,
                student_id=student_id,
                limit=8,
            )
            mentor_context = self._mentor_knowledge_context_builder.build(
                student_id=student_id,
                case_id=case_id,
                dashboard=dashboard,
                weaknesses=weaknesses,
                mentor_case=mentor_case,
            )
            resolved_exam_id = exam_id or "upsc_cse"
            knowledge = await self._knowledge_agent_service.ask(
                tenant_id=tenant_id,
                request=KnowledgeAskRequest(
                    query=question,
                    exam_id=resolved_exam_id,
                    concept_ids=list(mentor_context.concept_ids),
                    retrieval_hints=list(mentor_context.retrieval_hints),
                    student_context=mentor_context.student_context_summary,
                ),
            )
            return map_mentor_knowledge_to_copilot_response(
                intent=intent,
                knowledge=knowledge,
                student_context_used=mentor_context.student_context_used,
            )

        if intent in MENTOR_PYQ_INTENTS:
            weaknesses = await self._learning_graph_read_service.get_weaknesses(
                tenant_id=tenant_id,
                student_id=student_id,
                limit=8,
            )
            mentor_context = self._mentor_knowledge_context_builder.build(
                student_id=student_id,
                case_id=case_id,
                dashboard=dashboard,
                weaknesses=weaknesses,
                mentor_case=mentor_case,
            )
            resolved_exam_id = exam_id or "upsc_cse"
            concept_ids = list(mentor_context.concept_ids)
            if intent in {"pyq_revision", "high_frequency_weak_concepts"}:
                concept_ids = [weakness.concept_id for weakness in weaknesses[:5]]
            frequency_summary = await self._pyq_service.build_frequency_summary(
                tenant_id=tenant_id,
                exam_id=resolved_exam_id,
                concept_ids=concept_ids,
            )
            knowledge = await self._knowledge_agent_service.ask(
                tenant_id=tenant_id,
                request=KnowledgeAskRequest(
                    query=question,
                    exam_id=resolved_exam_id,
                    concept_ids=concept_ids,
                    retrieval_hints=list(mentor_context.retrieval_hints),
                    student_context=mentor_context.student_context_summary,
                    pyq_mode=True,
                    prefer_pyq=True,
                    frequency_summary=frequency_summary,
                ),
            )
            if intent in {"pyq_revision", "high_frequency_weak_concepts"}:
                pass
            return map_mentor_pyq_to_copilot_response(
                intent=intent,
                knowledge=knowledge,
                student_context_used=mentor_context.student_context_used,
            )

        if intent == "summarize_student":
            answer, sources = await mentor_handlers.handle_summarize_student(
                dashboard=dashboard,
                student_id=str(student_id),
            )
            return CopilotQueryResponse(intent=intent, answer=answer, sources=sources)

        if intent == "escalation_reason":
            answer, sources = await mentor_handlers.handle_escalation_reason(
                dashboard=dashboard,
                mentor_case=mentor_case,
            )
            return CopilotQueryResponse(intent=intent, answer=answer, sources=sources)

        if intent == "top_risks":
            answer, sources = await mentor_handlers.handle_top_risks(dashboard=dashboard)
            return CopilotQueryResponse(intent=intent, answer=answer, sources=sources)

        if intent == "forecast_summary":
            answer, sources = await mentor_handlers.handle_forecast_summary(dashboard=dashboard)
            return CopilotQueryResponse(intent=intent, answer=answer, sources=sources)

        if intent == "draft_coaching_note":
            answer, sources = await mentor_handlers.handle_draft_coaching_note(
                dashboard=dashboard,
                mentor_case=mentor_case,
            )
            return CopilotQueryResponse(intent=intent, answer=answer, sources=sources)

        return self._unknown_intent_response("mentor")

    async def _handle_admin_intent(
        self,
        intent: str,
        *,
        context: TenantContext,
    ) -> CopilotQueryResponse:
        if intent in ADMIN_INSTITUTION_OUTCOME_INTENTS:
            return await build_admin_institution_outcome_response(
                intent=intent,
                outcome_service=self._institution_outcome_service,
                tenant_id=context.tenant_id,
            )

        if intent in ADMIN_INSTITUTION_INTENTS:
            return await build_admin_institution_response(
                intent=intent,
                institution_service=self._institution_service,
                tenant_id=context.tenant_id,
            )

        if intent in ADMIN_COHORT_INTENTS:
            return await build_admin_cohort_response(
                intent=intent,
                cohort_service=self._cohort_service,
                tenant_id=context.tenant_id,
            )

        if intent in ADMIN_INTERVENTION_INTENTS:
            return await build_admin_intervention_response(
                intent=intent,
                intervention_service=self._intervention_service,
                tenant_id=context.tenant_id,
            )

        if intent in {"forecast_summary", "forecast_accuracy", "cohort_projection"}:
            dashboard = await self._forecasting_service.get_admin_dashboard(tenant_id=context.tenant_id)
            if intent == "forecast_summary":
                answer = (
                    f"Total forecasts: {dashboard.total_forecasts}. "
                    f"Average probability: {dashboard.average_probability:.1f}%. "
                    f"On-track rate: {dashboard.on_track_rate * 100:.1f}%."
                )
            elif intent == "forecast_accuracy":
                answer = (
                    f"Average projected gain: +{dashboard.average_projected_gain:.1f}. "
                    f"Forecasts in last 30 days: {dashboard.forecasts_last_30_days}."
                )
            else:
                answer = (
                    f"Cohort projection: {dashboard.total_forecasts} forecasts tracked, "
                    f"average success probability {dashboard.average_probability:.1f}%."
                )
            return CopilotQueryResponse(
                intent=intent,
                answer=answer,
                confidence="high",
                sources=[CopilotSourceResponse(label="Admin forecasting", reference="GET /admin/forecasting")],
            )

        if intent == "platform_health":
            platform = await self._health_service.get_platform_health(self._session)
            answer, sources = await admin_handlers.handle_platform_health(platform)
            return CopilotQueryResponse(intent=intent, answer=answer, sources=sources)

        if intent == "worker_status":
            worker = await self._health_service.get_worker_status()
            answer, sources = await admin_handlers.handle_worker_status(worker)
            return CopilotQueryResponse(intent=intent, answer=answer, sources=sources)

        if intent == "outbox_status":
            outbox = await self._health_service.get_outbox_status(self._session)
            answer, sources = await admin_handlers.handle_outbox_status(outbox)
            return CopilotQueryResponse(intent=intent, answer=answer, sources=sources)

        if intent == "deployment_readiness":
            readiness = await self._health_service.get_deployment_readiness(self._session)
            answer, sources = await admin_handlers.handle_deployment_readiness(readiness)
            return CopilotQueryResponse(intent=intent, answer=answer, sources=sources)

        return self._unknown_intent_response("admin")

    def _unknown_intent_response(self, persona: str) -> CopilotQueryResponse:
        prompts = suggested_prompts_for_persona(persona)  # type: ignore[arg-type]
        prompt_lines = "\n".join(f"- {prompt}" for prompt in prompts[:6])
        answer = (
            "I could not match your question to a supported intent. "
            "Try one of these prompts:\n"
            f"{prompt_lines}"
        )
        return CopilotQueryResponse(
            intent="unknown",
            answer=answer,
            sources=[CopilotSourceResponse(label="Copilot intent router", reference="POST /copilot/query")],
        )
