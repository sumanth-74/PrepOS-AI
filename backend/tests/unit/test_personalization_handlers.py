from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from prepos.domain.events.envelope import DomainEventEnvelope
from prepos.domain.twin.projection_sections import TwinProjectionSection
from prepos.events.handlers import personalization_handlers


@pytest.mark.asyncio
async def test_personalization_updated_requests_projection() -> None:
    tenant_id = uuid4()
    student_id = uuid4()
    envelope = DomainEventEnvelope(
        event_id=uuid4(),
        event_version=1,
        event_type="PersonalizationUpdated",
        occurred_at=datetime.now(UTC),
        recorded_at=datetime.now(UTC),
        tenant_id=tenant_id,
        correlation_id="corr",
        causation_id="cause",
        producer="personalization_service",
        payload={
            "student_id": str(student_id),
            "exam_id": "neet",
        },
        metadata={},
    )

    with patch(
        "prepos.events.handlers.personalization_handlers.request_twin_incremental_update",
        new=AsyncMock(),
    ) as twin_update:
        with patch(
            "prepos.events.handlers.personalization_handlers.TwinRecommendationService",
        ) as recommendation_service_cls:
            recommendation_service = AsyncMock()
            recommendation_service.recompute_and_persist = AsyncMock()
            recommendation_service_cls.return_value = recommendation_service
            with patch(
                "prepos.events.handlers.personalization_handlers.build_twin_decision_service",
                return_value=AsyncMock(publish_twin_decision_updated=AsyncMock()),
            ):
                with patch(
                    "prepos.events.handlers.personalization_handlers.build_twin_intervention_service",
                    return_value=AsyncMock(publish_twin_intervention_updated=AsyncMock()),
                ):
                    with patch(
                        "prepos.events.handlers.personalization_handlers._build_study_plan_service",
                        return_value=AsyncMock(rebuild_study_plan=AsyncMock()),
                    ):
                        with patch(
                            "prepos.events.handlers.personalization_handlers._build_read_service",
                            return_value=AsyncMock(),
                        ):
                            with patch(
                                "prepos.events.handlers.personalization_handlers.build_personalization_service",
                                return_value=AsyncMock(),
                            ):
                                with patch(
                                    "prepos.events.handlers.personalization_handlers.session_scope",
                                ) as session_scope:
                                    session_scope.return_value.__aenter__ = AsyncMock(return_value=object())
                                    session_scope.return_value.__aexit__ = AsyncMock(return_value=False)
                                    await personalization_handlers.on_personalization_updated_rebuild(envelope)

    twin_update.assert_awaited_once()
    assert twin_update.await_args.kwargs["section"] == TwinProjectionSection.PERSONALIZATION


@pytest.mark.asyncio
async def test_behavior_profile_updated_publishes_personalization() -> None:
    tenant_id = uuid4()
    student_id = uuid4()
    envelope = DomainEventEnvelope(
        event_id=uuid4(),
        event_version=1,
        event_type="BehaviorProfileUpdated",
        occurred_at=datetime.now(UTC),
        recorded_at=datetime.now(UTC),
        tenant_id=tenant_id,
        correlation_id="corr",
        causation_id="cause",
        producer="behavior_profile_service",
        payload={
            "student_id": str(student_id),
            "exam_id": "neet",
        },
        metadata={},
    )

    with patch(
        "prepos.events.handlers.personalization_handlers.build_personalization_service",
    ) as build_service:
        service = AsyncMock()
        service.publish_personalization_updated = AsyncMock(
            return_value=AsyncMock(
                summary=AsyncMock(
                    learning_style="RECOVERY_DRIVEN",
                    risk_profile="MEDIUM_RISK",
                    top_multiplier=Decimal("1.30"),
                )
            )
        )
        build_service.return_value = service
        with patch("prepos.events.handlers.personalization_handlers.session_scope") as session_scope:
            session_scope.return_value.__aenter__ = AsyncMock(return_value=object())
            session_scope.return_value.__aexit__ = AsyncMock(return_value=False)
            await personalization_handlers.on_behavior_profile_updated_personalization(envelope)

    service.publish_personalization_updated.assert_awaited_once()
