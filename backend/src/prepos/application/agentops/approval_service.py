from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from prepos.application.agentops.models import PendingActionListResponse, PendingActionRecord
from prepos.application.agentops.ports import AgentOpsRepositoryPort
from prepos.application.agents.models import AutonomousAction


class AgentApprovalService:
    def __init__(self, *, repository: AgentOpsRepositoryPort) -> None:
        self._repository = repository

    async def queue_autonomous_action(
        self,
        *,
        tenant_id: UUID,
        action: AutonomousAction,
    ) -> UUID:
        now = datetime.now(UTC)
        record = PendingActionRecord(
            action_id=uuid4(),
            action_type=action.action_type,
            proposed_by_agent=action.source_workflow,
            subject_key=action.subject_key,
            explanation=action.message,
            payload=action.payload,
            status="pending",
            created_at=now,
        )
        return await self._repository.create_pending_action(tenant_id=tenant_id, action=record, now=now)

    async def list_actions(self, *, tenant_id: UUID, status: str | None = None, limit: int = 50) -> PendingActionListResponse:
        items, total = await self._repository.list_pending_actions(
            tenant_id=tenant_id,
            status=status,
            limit=limit,
        )
        return PendingActionListResponse(items=items, total=total)

    async def approve(self, *, tenant_id: UUID, action_id: UUID, reviewer_id: UUID, review_note: str | None) -> PendingActionRecord | None:
        return await self._repository.update_pending_action_status(
            tenant_id=tenant_id,
            action_id=action_id,
            status="approved",
            reviewed_by_user_id=reviewer_id,
            review_note=review_note,
            now=datetime.now(UTC),
        )

    async def reject(self, *, tenant_id: UUID, action_id: UUID, reviewer_id: UUID, review_note: str | None) -> PendingActionRecord | None:
        return await self._repository.update_pending_action_status(
            tenant_id=tenant_id,
            action_id=action_id,
            status="rejected",
            reviewed_by_user_id=reviewer_id,
            review_note=review_note,
            now=datetime.now(UTC),
        )
