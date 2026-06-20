from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

import structlog

from prepos.application.agentops.approval_service import AgentApprovalService
from prepos.application.agents.models import AutonomousAction
from prepos.application.agents.ports import AgentRepositoryPort

logger = structlog.get_logger(__name__)

NOTIFICATION_ONLY_ACTIONS = frozenset({"notification"})


class AutonomousAgentService:
    """Queues autonomous actions for approval; notifications are logged only."""

    def __init__(
        self,
        *,
        repository: AgentRepositoryPort,
        approval_service: AgentApprovalService | None = None,
        notification_sink: list[AutonomousAction] | None = None,
    ) -> None:
        self._repository = repository
        self._approval_service = approval_service
        self._notification_sink = notification_sink if notification_sink is not None else []

    async def execute_actions(
        self,
        *,
        tenant_id: UUID,
        actions: list[AutonomousAction],
    ) -> list[AutonomousAction]:
        now = datetime.now(UTC)
        queued: list[AutonomousAction] = []
        for action in actions:
            self._notification_sink.append(action)
            await self._repository.record_workflow_event(
                tenant_id=tenant_id,
                workflow_id=None,
                event_type="autonomous_action_generated",
                metadata_json={
                    "action_type": action.action_type,
                    "subject_key": action.subject_key,
                    "source_workflow": action.source_workflow,
                    "message": action.message,
                    "payload": action.payload,
                },
                now=now,
            )
            if action.action_type in NOTIFICATION_ONLY_ACTIONS:
                logger.info(
                    "agent_autonomous_notification_logged",
                    tenant_id=str(tenant_id),
                    action_type=action.action_type,
                )
            elif self._approval_service is not None:
                await self._approval_service.queue_autonomous_action(tenant_id=tenant_id, action=action)
                logger.info(
                    "agent_autonomous_action_queued_for_approval",
                    tenant_id=str(tenant_id),
                    action_type=action.action_type,
                )
            queued.append(action)
        return queued
