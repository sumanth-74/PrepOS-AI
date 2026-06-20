from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

import structlog

from prepos.application.agents.autonomous_agent_service import AutonomousAgentService
from prepos.application.agents.events.workflows import (
    ForecastDeclineWorkflow,
    GoalRiskWorkflow,
    InterventionFailureWorkflow,
    PlanFailureWorkflow,
    ReadinessDropWorkflow,
    WeakConceptEmergenceWorkflow,
)
from prepos.application.agents.models import AutonomousAction
from prepos.application.agents.ports import AgentRepositoryPort

logger = structlog.get_logger(__name__)


@dataclass(frozen=True, slots=True)
class AgentEventPayload:
    event_type: str
    subject_key: str
    metadata: dict[str, object]


class AgentEventDispatcher:
    """Routes domain events to autonomous agent workflows."""

    def __init__(
        self,
        *,
        repository: AgentRepositoryPort,
        autonomous_service: AutonomousAgentService,
    ) -> None:
        self._repository = repository
        self._autonomous = autonomous_service
        self._workflows = {
            "readiness_drop": ReadinessDropWorkflow(),
            "forecast_decline": ForecastDeclineWorkflow(),
            "goal_risk": GoalRiskWorkflow(),
            "plan_failure": PlanFailureWorkflow(),
            "weak_concept_emergence": WeakConceptEmergenceWorkflow(),
            "intervention_failure": InterventionFailureWorkflow(),
        }

    async def dispatch(self, *, tenant_id: UUID, event: AgentEventPayload) -> list[AutonomousAction]:
        workflow = self._workflows.get(event.event_type)
        if workflow is None:
            logger.warning("agent_event_unhandled", event_type=event.event_type)
            return []

        logger.info(
            "agent_workflow_triggered",
            tenant_id=str(tenant_id),
            event_type=event.event_type,
            subject_key=event.subject_key,
        )
        notification = await workflow.run(
            repository=self._repository,
            tenant_id=tenant_id,
            subject_key=event.subject_key,
            **event.metadata,
        )
        actions = [
            AutonomousAction(
                action_type="notification",
                subject_key=event.subject_key,
                message=notification.message,
                payload={"recommended_actions": list(notification.recommended_actions)},
                source_workflow=notification.event_type,
            )
        ]
        if event.event_type in {"readiness_drop", "goal_risk", "weak_concept_emergence"}:
            actions.append(
                AutonomousAction(
                    action_type="recommendation",
                    subject_key=event.subject_key,
                    message="Review ranked recommendations for recovery.",
                    payload={"trigger": event.event_type},
                    source_workflow=notification.event_type,
                )
            )
        if event.event_type in {"plan_failure", "forecast_decline"}:
            actions.append(
                AutonomousAction(
                    action_type="plan_revision",
                    subject_key=event.subject_key,
                    message="Review adaptive plan adherence and propose revision.",
                    payload={"trigger": event.event_type},
                    source_workflow=notification.event_type,
                )
            )
        if event.event_type in {"intervention_failure", "goal_risk"}:
            actions.append(
                AutonomousAction(
                    action_type="mentor_alert",
                    subject_key=event.subject_key,
                    message="Mentor review required for at-risk student.",
                    payload={"trigger": event.event_type},
                    source_workflow=notification.event_type,
                )
            )
        return await self._autonomous.execute_actions(tenant_id=tenant_id, actions=actions)
