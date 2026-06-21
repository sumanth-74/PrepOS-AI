from __future__ import annotations

from fastapi import APIRouter

from prepos.api.v1.admin.copilot.router import router as admin_copilot_router
from prepos.api.v1.admin.knowledge.router import router as admin_knowledge_router
from prepos.api.v1.admin.rag_quality.router import router as admin_rag_quality_router
from prepos.api.v1.admin.forecasting.router import router as admin_forecasting_router
from prepos.api.v1.admin.interventions.router import router as admin_interventions_router
from prepos.api.v1.admin.cohort.router import router as admin_cohort_router
from prepos.api.v1.admin.institution.router import router as admin_institution_router
from prepos.api.v1.admin.agents.router import router as admin_agents_router
from prepos.api.v1.admin.agentops.router import (
    approvals_router as admin_approvals_router,
    costs_router as admin_agent_costs_router,
    evaluation_router as admin_agent_evaluation_router,
    traces_router as admin_agent_traces_router,
)
from prepos.api.v1.admin.agentops.health_router import benchmark_router as admin_agent_benchmarks_router
from prepos.api.v1.admin.agentops.health_router import router as admin_agent_health_router
from prepos.api.v1.admin.platform.router import (
    adoption_router as admin_adoption_router,
    disaster_recovery_router as admin_disaster_recovery_router,
    evaluations_router as admin_evaluations_router,
    forecast_accuracy_router as admin_forecast_accuracy_router,
    jobs_router as admin_jobs_router,
    monitoring_router as admin_monitoring_router,
    outcomes_router as admin_outcomes_router,
    platform_readiness_router as admin_platform_readiness_router,
    recommendation_validation_router as admin_recommendation_validation_router,
    security_router as admin_security_router,
)
from prepos.api.v1.admin.planning.router import router as admin_planning_router
from prepos.api.v1.admin.memory.router import router as admin_memory_router
from prepos.api.v1.admin.recommendation_effectiveness.router import (
    router as admin_recommendation_effectiveness_router,
)
from prepos.api.v1.admin.recommendations.router import router as admin_recommendations_router
from prepos.api.v1.auth.router import router as auth_router
from prepos.api.v1.copilot.router import router as copilot_router
from prepos.api.v1.concepts.router import router as concepts_router
from prepos.api.v1.current_affairs.router import router as current_affairs_router
from prepos.api.v1.forecasting.router import router as forecasting_router
from prepos.api.v1.cohort.router import router as cohort_router
from prepos.api.v1.interventions.router import router as interventions_router
from prepos.api.v1.planning.router import router as planning_router
from prepos.api.v1.memory.router import router as memory_router
from prepos.api.v1.pyq.router import router as pyq_router
from prepos.api.v1.recommendations.router import router as recommendations_router
from prepos.api.v1.exams.router import router as exams_router
from prepos.api.v1.faculty.router import router as faculty_router
from prepos.api.v1.goals.router import router as goals_router
from prepos.api.v1.knowledge.router import router as knowledge_router
from prepos.api.v1.learning_graph.router import router as learning_graph_router
from prepos.api.v1.mentor.router import router as mentor_router
from prepos.api.v1.students.router import router as students_router
from prepos.api.v1.study_plan.router import router as study_plan_router
from prepos.api.v1.syllabus.router import router as syllabus_router
from prepos.api.v1.twin.router import router as twin_router

router = APIRouter()
router.include_router(auth_router)
router.include_router(exams_router)
router.include_router(syllabus_router)
router.include_router(concepts_router)
router.include_router(students_router)
router.include_router(learning_graph_router)
router.include_router(study_plan_router)
router.include_router(goals_router)
router.include_router(mentor_router)
router.include_router(twin_router)
router.include_router(copilot_router)
router.include_router(faculty_router)
router.include_router(recommendations_router)
router.include_router(memory_router)
router.include_router(planning_router)
router.include_router(forecasting_router)
router.include_router(interventions_router)
router.include_router(cohort_router)
router.include_router(admin_copilot_router)
router.include_router(knowledge_router)
router.include_router(current_affairs_router)
router.include_router(pyq_router)
router.include_router(admin_knowledge_router)
router.include_router(admin_rag_quality_router)
router.include_router(admin_recommendations_router)
router.include_router(admin_recommendation_effectiveness_router)
router.include_router(admin_memory_router)
router.include_router(admin_planning_router)
router.include_router(admin_forecasting_router)
router.include_router(admin_interventions_router)
router.include_router(admin_cohort_router)
router.include_router(admin_institution_router)
router.include_router(admin_agents_router)
router.include_router(admin_agent_traces_router)
router.include_router(admin_agent_evaluation_router)
router.include_router(admin_agent_costs_router)
router.include_router(admin_approvals_router)
router.include_router(admin_agent_health_router)
router.include_router(admin_agent_benchmarks_router)
router.include_router(admin_security_router)
router.include_router(admin_jobs_router)
router.include_router(admin_evaluations_router)
router.include_router(admin_forecast_accuracy_router)
router.include_router(admin_recommendation_validation_router)
router.include_router(admin_monitoring_router)
router.include_router(admin_disaster_recovery_router)
router.include_router(admin_adoption_router)
router.include_router(admin_outcomes_router)
router.include_router(admin_platform_readiness_router)
