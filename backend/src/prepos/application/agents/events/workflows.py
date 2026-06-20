from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

import structlog

from prepos.application.agents.models import AgentResult, AgentSource
from prepos.application.agents.ports import AgentRepositoryPort

logger = structlog.get_logger(__name__)


@dataclass(frozen=True, slots=True)
class WorkflowNotification:
    event_type: str
    subject_key: str
    message: str
    recommended_actions: tuple[str, ...]


class ReadinessDropWorkflow:
    workflow_type = "readiness_drop"

    async def run(
        self,
        *,
        repository: AgentRepositoryPort,
        tenant_id: UUID,
        subject_key: str,
        readiness_delta: float = 0.0,
        **_: object,
    ) -> WorkflowNotification:
        now = datetime.now(UTC)
        notification = WorkflowNotification(
            event_type="readiness_drop",
            subject_key=subject_key,
            message=f"Readiness dropped by {abs(readiness_delta):.1f} points for {subject_key}.",
            recommended_actions=(
                "Review weak concepts from recommendation engine.",
                "Schedule mentor intervention review.",
                "Check adaptive plan adherence.",
            ),
        )
        workflow_id = await repository.save_workflow(
            tenant_id=tenant_id,
            workflow_type=self.workflow_type,
            trigger_event="readiness_drop",
            subject_key=subject_key,
            plan_json={"readiness_delta": readiness_delta},
            results_json=[{"notification": notification.message}],
            now=now,
        )
        await repository.record_workflow_event(
            tenant_id=tenant_id,
            workflow_id=workflow_id,
            event_type="agent_workflow_triggered",
            metadata_json={"workflow_type": self.workflow_type},
            now=now,
        )
        logger.info("agent_workflow_triggered", tenant_id=str(tenant_id), workflow_type=self.workflow_type)
        return notification


class GoalRiskWorkflow:
    workflow_type = "goal_risk"

    async def run(
        self,
        *,
        repository: AgentRepositoryPort,
        tenant_id: UUID,
        subject_key: str,
        forecast_probability: float = 0.0,
        **_: object,
    ) -> WorkflowNotification:
        now = datetime.now(UTC)
        notification = WorkflowNotification(
            event_type="goal_risk",
            subject_key=subject_key,
            message=f"Goal attainment risk flagged at {forecast_probability:.1f}% for {subject_key}.",
            recommended_actions=(
                "Run goal forecast scenario review.",
                "Prioritize high-impact recommendations.",
            ),
        )
        await repository.save_workflow(
            tenant_id=tenant_id,
            workflow_type=self.workflow_type,
            trigger_event="goal_risk",
            subject_key=subject_key,
            plan_json={"forecast_probability": forecast_probability},
            results_json=[{"notification": notification.message}],
            now=now,
        )
        return notification


class ForecastDeclineWorkflow:
    workflow_type = "forecast_decline"

    async def run(
        self,
        *,
        repository: AgentRepositoryPort,
        tenant_id: UUID,
        subject_key: str,
        forecast_delta: float = 0.0,
        **_: object,
    ) -> WorkflowNotification:
        now = datetime.now(UTC)
        notification = WorkflowNotification(
            event_type="forecast_decline",
            subject_key=subject_key,
            message=f"Forecast probability declined by {abs(forecast_delta):.1f}% for {subject_key}.",
            recommended_actions=("Launch forecast recovery initiative.", "Review planning adherence."),
        )
        await repository.save_workflow(
            tenant_id=tenant_id,
            workflow_type=self.workflow_type,
            trigger_event="forecast_decline",
            subject_key=subject_key,
            plan_json={"forecast_delta": forecast_delta},
            results_json=[{"notification": notification.message}],
            now=now,
        )
        return notification


class PlanFailureWorkflow:
    workflow_type = "plan_failure"

    async def run(
        self,
        *,
        repository: AgentRepositoryPort,
        tenant_id: UUID,
        subject_key: str,
        adherence_rate: float = 0.0,
        **_: object,
    ) -> WorkflowNotification:
        now = datetime.now(UTC)
        notification = WorkflowNotification(
            event_type="plan_failure",
            subject_key=subject_key,
            message=f"Adaptive plan adherence fell to {adherence_rate:.1f}% for {subject_key}.",
            recommended_actions=(
                "Review weekly plan workload.",
                "Trigger plan revision workflow.",
            ),
        )
        await repository.save_workflow(
            tenant_id=tenant_id,
            workflow_type=self.workflow_type,
            trigger_event="plan_failure",
            subject_key=subject_key,
            plan_json={"adherence_rate": adherence_rate},
            results_json=[{"notification": notification.message}],
            now=now,
        )
        return notification


class WeakConceptEmergenceWorkflow:
    workflow_type = "weak_concept_emergence"

    async def run(
        self,
        *,
        repository: AgentRepositoryPort,
        tenant_id: UUID,
        subject_key: str,
        concept_id: str = "unknown",
        weakness_score: float = 0.0,
        **_: object,
    ) -> WorkflowNotification:
        now = datetime.now(UTC)
        notification = WorkflowNotification(
            event_type="weak_concept_emergence",
            subject_key=subject_key,
            message=f"Weak concept {concept_id} emerged with score {weakness_score:.1f} for {subject_key}.",
            recommended_actions=(
                "Prioritize concept in recommendation engine.",
                "Add revision block to adaptive plan.",
            ),
        )
        await repository.save_workflow(
            tenant_id=tenant_id,
            workflow_type=self.workflow_type,
            trigger_event="weak_concept_emergence",
            subject_key=subject_key,
            plan_json={"concept_id": concept_id, "weakness_score": weakness_score},
            results_json=[{"notification": notification.message}],
            now=now,
        )
        return notification


class InterventionFailureWorkflow:
    workflow_type = "intervention_failure"

    async def run(
        self,
        *,
        repository: AgentRepositoryPort,
        tenant_id: UUID,
        subject_key: str,
        intervention_type: str = "unknown",
        effectiveness_score: float = 0.0,
        **_: object,
    ) -> WorkflowNotification:
        now = datetime.now(UTC)
        notification = WorkflowNotification(
            event_type="intervention_failure",
            subject_key=subject_key,
            message=(
                f"Intervention {intervention_type} underperformed "
                f"(effectiveness {effectiveness_score:.2f}) for {subject_key}."
            ),
            recommended_actions=(
                "Review intervention optimization suggestions.",
                "Escalate to mentor coaching review.",
            ),
        )
        await repository.save_workflow(
            tenant_id=tenant_id,
            workflow_type=self.workflow_type,
            trigger_event="intervention_failure",
            subject_key=subject_key,
            plan_json={
                "intervention_type": intervention_type,
                "effectiveness_score": effectiveness_score,
            },
            results_json=[{"notification": notification.message}],
            now=now,
        )
        return notification


def workflow_result_to_agent_result(notification: WorkflowNotification) -> AgentResult:
    return AgentResult(
        success=True,
        confidence="high",
        data={
            "event_type": notification.event_type,
            "subject_key": notification.subject_key,
            "recommended_actions": list(notification.recommended_actions),
        },
        reasoning=notification.message,
        sources=[AgentSource(label="Agent workflow", reference="agent_workflow")],
    )
