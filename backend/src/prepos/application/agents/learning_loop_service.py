from __future__ import annotations

from uuid import UUID

import structlog

from prepos.application.agents.models import AgentLearningSignal
from prepos.application.agents.ports import AgentRepositoryPort
from prepos.application.recommendations.outcomes.outcome_service import RecommendationOutcomeService

logger = structlog.get_logger(__name__)

EFFECTIVE_THRESHOLD = 1.0
WEAK_THRESHOLD = 0.5


class AgentLearningLoopService:
    """Tracks recommendation outcomes and intervention effectiveness for planner signals."""

    def __init__(
        self,
        *,
        repository: AgentRepositoryPort,
        outcome_service: RecommendationOutcomeService | None = None,
    ) -> None:
        self._repository = repository
        self._outcome_service = outcome_service

    async def build_signals(
        self,
        *,
        tenant_id: UUID,
        subject_key: str,
        student_id: UUID | None = None,
        exam_id: str | None = None,
    ) -> list[AgentLearningSignal]:
        cached = await self._repository.list_learning_signals(
            tenant_id=tenant_id,
            signal_type="recommendation_effectiveness",
            limit=20,
        )
        if cached:
            return cached

        signals: list[AgentLearningSignal] = []
        if self._outcome_service is not None and student_id is not None:
            outcomes = await self._outcome_service.list_outcomes(
                tenant_id=tenant_id,
                student_id=student_id,
                exam_id=exam_id,
            )
            for outcome in outcomes.outcomes[:10]:
                effectiveness = float(outcome.effectiveness_score)
                signal_type = (
                    "high_effectiveness_concept"
                    if effectiveness >= EFFECTIVE_THRESHOLD
                    else "weak_effectiveness_concept"
                    if effectiveness < WEAK_THRESHOLD
                    else "recommendation_effectiveness"
                )
                signals.append(
                    AgentLearningSignal(
                        signal_type=signal_type,
                        subject_key=subject_key,
                        concept_id=outcome.concept_id,
                        effectiveness_score=effectiveness,
                        explanation=(
                            f"Concept {outcome.concept_id} effectiveness {effectiveness:.2f} "
                            f"with status {outcome.status}."
                        ),
                        metadata={
                            "actual_gain": outcome.actual_gain,
                            "predicted_gain": outcome.predicted_gain,
                            "status": outcome.status,
                        },
                    )
                )

        if signals:
            from datetime import UTC, datetime

            await self._repository.save_learning_signals(
                tenant_id=tenant_id,
                signals=signals,
                now=datetime.now(UTC),
            )
        logger.info(
            "agent_learning_signals_built",
            tenant_id=str(tenant_id),
            signal_count=len(signals),
        )
        return signals
