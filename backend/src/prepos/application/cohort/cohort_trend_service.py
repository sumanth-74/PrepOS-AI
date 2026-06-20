from __future__ import annotations

from prepos.application.cohort.cohort_models import StudentCohortInput
from prepos.application.recommendations.recommendation_engine import format_concept_name


def compute_concept_trends(
    *,
    students: list[StudentCohortInput],
    previous_avg_readiness: float | None,
    current_avg_readiness: float,
    period: str = "weekly",
) -> list[dict[str, object]]:
    concept_deltas: dict[str, list[float]] = {}
    for student in students:
        weight = max(0.5, (100.0 - student.readiness) / 100.0)
        for concept in student.negative_drivers:
            concept_deltas.setdefault(concept, []).append(weight * max(0.0, -student.readiness_delta + 1.0))

    trends: list[dict[str, object]] = []
    for concept, weights in concept_deltas.items():
        avg_weight = sum(weights) / len(weights)
        delta = round(avg_weight * 2.5, 2)
        direction = "down" if delta >= 1.5 else "flat" if delta >= 0.5 else "up"
        trends.append(
            {
                "concept_id": concept,
                "concept_name": format_concept_name(concept),
                "trend_direction": direction,
                "readiness_delta": delta if direction == "down" else round(-delta, 2),
                "period": period,
            }
        )
    trends.sort(key=lambda item: abs(float(item["readiness_delta"])), reverse=True)
    return trends[:10]


def compute_macro_trends(
    *,
    current_avg_readiness: float,
    current_avg_forecast: float,
    previous_avg_readiness: float | None,
    previous_avg_forecast: float | None,
    current_count: int,
    previous_count: int | None,
) -> tuple[str, str, float]:
    readiness_trend = "stable"
    if previous_avg_readiness is not None:
        delta = current_avg_readiness - previous_avg_readiness
        if delta >= 1.0:
            readiness_trend = "improving"
        elif delta <= -1.0:
            readiness_trend = "declining"

    forecast_trend = "stable"
    if previous_avg_forecast is not None:
        delta = current_avg_forecast - previous_avg_forecast
        if delta >= 1.0:
            forecast_trend = "improving"
        elif delta <= -1.0:
            forecast_trend = "declining"

    growth = 0.0
    if previous_count and previous_count > 0:
        growth = round((current_count - previous_count) / previous_count, 4)
    return readiness_trend, forecast_trend, growth
