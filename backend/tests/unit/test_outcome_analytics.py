from __future__ import annotations

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from prepos.application.recommendations.outcomes.outcome_analytics import OutcomeAnalyticsService


@pytest.mark.asyncio
async def test_get_effectiveness_summary_aggregates_rows() -> None:
    repo = AsyncMock()
    repo.get_concept_effectiveness_stats.return_value = [
        {
            "concept_id": "upsc.polity_federalism",
            "predicted_gain": 3.0,
            "actual_gain": 4.1,
            "effectiveness_score": 1.37,
            "status": "successful",
            "outcome_count": 2,
        },
        {
            "concept_id": "upsc.history_ancient",
            "predicted_gain": 2.0,
            "actual_gain": 1.0,
            "effectiveness_score": 0.5,
            "status": "partial",
            "outcome_count": 1,
        },
    ]
    service = OutcomeAnalyticsService(repository=repo)

    summary = await service.get_effectiveness_summary(
        tenant_id=uuid4(),
        student_id=uuid4(),
        period_days=30,
    )

    assert summary.average_effectiveness == pytest.approx(0.94, abs=0.01)
    assert summary.average_actual_gain == pytest.approx(2.55, abs=0.01)
    assert len(summary.items) == 2


@pytest.mark.asyncio
async def test_export_csv_contains_header() -> None:
    repo = AsyncMock()
    repo.get_admin_effectiveness_metrics.return_value = {
        "average_effectiveness": 1.0,
        "average_actual_gain": 2.0,
        "completion_rate": 0.5,
        "success_rate": 0.5,
        "concept_rankings": [
            {
                "concept_id": "upsc.polity_federalism",
                "predicted_gain": 3.0,
                "actual_gain": 4.0,
                "effectiveness_score": 1.33,
                "status": "successful",
                "outcome_count": 1,
            }
        ],
        "readiness_uplift_trend": [],
        "forecast_uplift_trend": [],
    }
    service = OutcomeAnalyticsService(repository=repo)
    csv_content = await service.export_csv(tenant_id=uuid4(), period_days=30)
    assert csv_content.startswith("concept_id,predicted_gain,actual_gain,effectiveness_score,status,outcome_count")
