from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from uuid import UUID

import structlog

from prepos.application.recommendations.outcomes.effectiveness_calculator import (
    calculate_actual_gain,
    calculate_effectiveness_score,
    outcome_status,
)
from prepos.application.recommendations.outcomes.outcome_models import (
    RecommendationEffectivenessAdminResponse,
    RecommendationEffectivenessItem,
    RecommendationEffectivenessResponse,
    RecommendationOutcomeListResponse,
    RecommendationOutcomeResponse,
)
from prepos.application.recommendations.outcomes.ports import RecommendationOutcomeRepositoryPort
from prepos.application.recommendations.recommendation_engine import format_concept_name

logger = structlog.get_logger(__name__)

OUTCOME_EVALUATION_DAYS = 7
SIGNIFICANT_READINESS_CHANGE = 2.0


class OutcomeAnalyticsService:
    def __init__(self, *, repository: RecommendationOutcomeRepositoryPort) -> None:
        self._repository = repository

    async def get_effectiveness_summary(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID | None = None,
        concept_id: str | None = None,
        period_days: int = 30,
    ) -> RecommendationEffectivenessResponse:
        since = datetime.now(UTC) - timedelta(days=max(1, min(period_days, 365)))
        stats = await self._repository.get_concept_effectiveness_stats(
            tenant_id=tenant_id,
            student_id=student_id,
            concept_id=concept_id,
            since=since,
        )
        items = [_map_effectiveness_item(row) for row in stats]
        if not items:
            return RecommendationEffectivenessResponse(
                average_effectiveness=0.0,
                average_actual_gain=0.0,
                completion_rate=0.0,
                success_rate=0.0,
                items=[],
            )

        avg_effectiveness = sum(item.effectiveness_score for item in items) / len(items)
        avg_actual = sum(item.actual_gain for item in items) / len(items)
        success_count = sum(1 for item in items if item.status == "successful")
        return RecommendationEffectivenessResponse(
            average_effectiveness=round(avg_effectiveness, 2),
            average_actual_gain=round(avg_actual, 2),
            completion_rate=round(len(items) / max(len(items), 1), 4),
            success_rate=round(success_count / len(items), 4),
            items=items,
        )

    async def get_admin_dashboard(
        self,
        *,
        tenant_id: UUID,
        period_days: int = 30,
    ) -> RecommendationEffectivenessAdminResponse:
        since = datetime.now(UTC) - timedelta(days=max(1, min(period_days, 365)))
        metrics = await self._repository.get_admin_effectiveness_metrics(tenant_id=tenant_id, since=since)
        rankings = [_map_effectiveness_item(row) for row in list(metrics["concept_rankings"])]
        sorted_rankings = sorted(rankings, key=lambda item: item.effectiveness_score, reverse=True)
        return RecommendationEffectivenessAdminResponse(
            average_effectiveness=float(metrics["average_effectiveness"]),
            average_actual_gain=float(metrics["average_actual_gain"]),
            completion_rate=float(metrics["completion_rate"]),
            success_rate=float(metrics["success_rate"]),
            top_performing_concepts=sorted_rankings[:5],
            lowest_performing_concepts=list(reversed(sorted_rankings[-5:])),
            readiness_uplift_trend=list(metrics["readiness_uplift_trend"]),
            forecast_uplift_trend=list(metrics["forecast_uplift_trend"]),
            concept_rankings=sorted_rankings,
        )

    async def export_csv(self, *, tenant_id: UUID, period_days: int = 30) -> str:
        dashboard = await self.get_admin_dashboard(tenant_id=tenant_id, period_days=period_days)
        lines = [
            "concept_id,predicted_gain,actual_gain,effectiveness_score,status,outcome_count",
        ]
        for item in dashboard.concept_rankings:
            lines.append(
                f"{item.concept_id},{item.predicted_gain:.2f},{item.actual_gain:.2f},"
                f"{item.effectiveness_score:.2f},{item.status},{item.outcome_count}"
            )
        return "\n".join(lines) + "\n"


def _map_effectiveness_item(row: dict[str, object]) -> RecommendationEffectivenessItem:
    return RecommendationEffectivenessItem(
        concept_id=str(row["concept_id"]),
        concept_name=format_concept_name(str(row["concept_id"])),
        predicted_gain=float(row["predicted_gain"]),
        actual_gain=float(row["actual_gain"]),
        effectiveness_score=float(row["effectiveness_score"]),
        status=str(row["status"]),  # type: ignore[arg-type]
        outcome_count=int(row.get("outcome_count", 1)),
    )


def map_outcome_row(row: dict[str, object]) -> RecommendationOutcomeResponse:
    return RecommendationOutcomeResponse(
        id=UUID(str(row["id"])),
        recommendation_event_id=UUID(str(row["recommendation_event_id"])),
        concept_id=str(row["concept_id"]),
        concept_name=format_concept_name(str(row["concept_id"])),
        predicted_gain=float(row["predicted_gain"] or 0),
        actual_gain=float(row["actual_gain"] or 0),
        effectiveness_score=float(row["effectiveness_score"] or 0),
        status=str(row["status"]),  # type: ignore[arg-type]
        readiness_before=_optional_float(row.get("readiness_before")),
        readiness_after=_optional_float(row.get("readiness_after")),
        forecast_before=_optional_float(row.get("forecast_before")),
        forecast_after=_optional_float(row.get("forecast_after")),
        weakness_before=_optional_float(row.get("weakness_before")),
        weakness_after=_optional_float(row.get("weakness_after")),
        study_minutes=int(row.get("study_minutes") or 0),
        created_at=row["created_at"],  # type: ignore[arg-type]
    )


def _optional_float(value: object | None) -> float | None:
    if value is None:
        return None
    return float(value)


def build_outcome_list(rows: list[dict[str, object]]) -> RecommendationOutcomeListResponse:
    outcomes = [map_outcome_row(row) for row in rows]
    return RecommendationOutcomeListResponse(outcomes=outcomes, total=len(outcomes))
