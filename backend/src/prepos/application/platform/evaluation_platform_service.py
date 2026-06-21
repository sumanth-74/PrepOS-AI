from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from pydantic import BaseModel, Field

from prepos.application.security.ports import PlatformMaturityRepositoryPort
from prepos.core.logging import get_logger

logger = get_logger(__name__)

VALID_LABELS = {"helpful", "partially_helpful", "not_helpful"}


class QuestionLabelRequest(BaseModel):
    question_id: UUID
    label: str
    notes: str | None = None


class EvaluationPlatformService:
    """Real user evaluation platform (P11.8)."""

    def __init__(self, *, repository: PlatformMaturityRepositoryPort) -> None:
        self._repository = repository

    async def capture_question(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        persona: str,
        question_text: str,
        intent: str | None,
        answer_text: str | None,
        trace_id: UUID | None = None,
    ) -> UUID:
        return await self._repository.save_real_user_question(
            tenant_id=tenant_id,
            user_id=user_id,
            persona=persona,
            question_text=question_text,
            intent=intent,
            answer_text=answer_text,
            trace_id=trace_id,
            now=datetime.now(UTC),
        )

    async def label_question(
        self,
        *,
        tenant_id: UUID,
        labeler_id: UUID,
        labeler_role: str,
        request: QuestionLabelRequest,
    ) -> UUID:
        if request.label not in VALID_LABELS:
            raise ValueError(f"Invalid label: {request.label}")
        return await self._repository.save_question_label(
            tenant_id=tenant_id,
            question_id=request.question_id,
            labeler_id=labeler_id,
            labeler_role=labeler_role,
            label=request.label,
            notes=request.notes,
            now=datetime.now(UTC),
        )

    async def list_questions(
        self,
        *,
        tenant_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        return await self._repository.list_evaluation_questions(
            tenant_id=tenant_id,
            limit=limit,
            offset=offset,
        )

    async def get_dashboard(self, *, tenant_id: UUID) -> dict:
        return await self._repository.get_evaluation_dashboard(tenant_id=tenant_id)
