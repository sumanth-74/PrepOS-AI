from __future__ import annotations

from prepos.application.institution.institution_models import InstitutionDataInput, InstitutionTrendItem

INSTITUTION_TREND_ANALYZER_V1 = "institution_trend_analyzer_v1"

TREND_THRESHOLD = 2.0


def analyze_institution_trends(
    *,
    data: InstitutionDataInput,
    period: str = "monthly",
) -> tuple[list[InstitutionTrendItem], str, str]:
    trends: list[InstitutionTrendItem] = []

    readiness_delta = 0.0
    if data.previous_readiness_avg is not None:
        readiness_delta = data.current_readiness_avg - data.previous_readiness_avg
        trends.append(
            InstitutionTrendItem(
                trend_type="readiness",
                trend_key="institution",
                trend_direction=_direction(readiness_delta),
                delta_value=round(readiness_delta, 2),
                period=period,
                label="Institution readiness",
            )
        )

    forecast_delta = 0.0
    if data.previous_forecast_avg is not None:
        forecast_delta = data.current_forecast_avg - data.previous_forecast_avg
        trends.append(
            InstitutionTrendItem(
                trend_type="forecast",
                trend_key="institution",
                trend_direction=_direction(forecast_delta),
                delta_value=round(forecast_delta, 2),
                period=period,
                label="Institution forecast probability",
            )
        )

    for cohort in data.cohorts:
        trends.append(
            InstitutionTrendItem(
                trend_type="cohort_readiness",
                trend_key=cohort.cohort_id,
                trend_direction=_direction(cohort.avg_readiness - 60.0),
                delta_value=round(cohort.avg_readiness - 60.0, 2),
                period=period,
                label=f"Cohort {cohort.cohort_id} readiness vs target",
            )
        )

    for mentor in data.mentors[:5]:
        trends.append(
            InstitutionTrendItem(
                trend_type="mentor_effectiveness",
                trend_key=mentor.mentor_id,
                trend_direction=_direction(mentor.average_gain),
                delta_value=round(mentor.average_gain, 2),
                period=period,
                label=f"Mentor {mentor.mentor_id[:8]} average gain",
            )
        )

    trends.append(
        InstitutionTrendItem(
            trend_type="intervention_roi",
            trend_key="institution",
            trend_direction=_direction(data.intervention_roi - 50.0),
            delta_value=round(data.intervention_roi - 50.0, 2),
            period=period,
            label="Intervention ROI vs baseline",
        )
    )

    return trends, _direction(readiness_delta), _direction(forecast_delta)


def _direction(delta: float) -> str:
    if delta >= TREND_THRESHOLD:
        return "up"
    if delta <= -TREND_THRESHOLD:
        return "down"
    return "stable"
