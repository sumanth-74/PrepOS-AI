from __future__ import annotations

from prepos.application.institution.institution_models import (
    CohortSnapshotInput,
    InstitutionDataInput,
    InstitutionEvidence,
    InstitutionInsightItem,
    MentorEffectivenessInput,
)
from prepos.application.recommendations.recommendation_engine import format_concept_name

INSTITUTION_INSIGHT_ENGINE_V1 = "institution_insight_engine_v1"

CONCEPT_WEAKNESS_COHORT_THRESHOLD = 2
READINESS_DROP_THRESHOLD = 5.0
FORECAST_DECLINE_THRESHOLD = 3.0
CURRENT_AFFAIRS_DROP_THRESHOLD = 5.0
MENTOR_OUTPERFORMANCE_THRESHOLD = 15.0
PYQ_GAIN_SIGNAL_THRESHOLD = 60.0
INTERVENTION_ROI_LOW_THRESHOLD = 45.0
AT_RISK_SPIKE_THRESHOLD = 20


def generate_institution_insights(data: InstitutionDataInput) -> list[InstitutionInsightItem]:
    insights: list[InstitutionInsightItem] = []
    insights.extend(_concept_weakness_insights(data))
    insights.extend(_mentor_outperformance_insights(data))
    insights.extend(_readiness_drop_insight(data))
    insights.extend(_forecast_decline_insights(data))
    insights.extend(_current_affairs_drop_insight(data))
    insights.extend(_pyq_gain_insight(data))
    insights.extend(_intervention_underperformance_insight(data))
    insights.extend(_cohort_risk_spike_insights(data))
    severity_rank = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    return sorted(insights, key=lambda item: severity_rank.get(item.severity, 4))


def _concept_weakness_insights(data: InstitutionDataInput) -> list[InstitutionInsightItem]:
    items: list[InstitutionInsightItem] = []
    for concept, cohort_count in sorted(
        data.concept_cohort_counts.items(),
        key=lambda pair: pair[1],
        reverse=True,
    ):
        if cohort_count < CONCEPT_WEAKNESS_COHORT_THRESHOLD:
            continue
        concept_name = format_concept_name(concept)
        items.append(
            InstitutionInsightItem(
                insight_type="concept_weakness",
                insight_key=concept,
                title=f"{concept_name} is weak across {cohort_count} cohorts",
                severity="high" if cohort_count >= 4 else "medium",
                evidence=[
                    InstitutionEvidence(label="Affected cohorts", value=str(cohort_count)),
                    InstitutionEvidence(label="Concept", value=concept_name),
                ],
                calculation=(
                    f"count(cohorts where '{concept}' in top_risks) >= "
                    f"{CONCEPT_WEAKNESS_COHORT_THRESHOLD}"
                ),
                source_metrics={
                    "cohort_count": cohort_count,
                    "threshold": CONCEPT_WEAKNESS_COHORT_THRESHOLD,
                },
            )
        )
    return items[:5]


def _mentor_outperformance_insights(data: InstitutionDataInput) -> list[InstitutionInsightItem]:
    if not data.mentors:
        return []
    cohort_avg = sum(item.intervention_success_rate for item in data.mentors) / len(data.mentors)
    items: list[InstitutionInsightItem] = []
    for mentor in data.mentors:
        delta_pct = (mentor.intervention_success_rate - cohort_avg) * 100.0
        if delta_pct < MENTOR_OUTPERFORMANCE_THRESHOLD:
            continue
        items.append(
            InstitutionInsightItem(
                insight_type="mentor_outperformance",
                insight_key=mentor.mentor_id,
                title=(
                    f"Mentor {mentor.mentor_id[:8]} interventions outperform cohort average "
                    f"by {delta_pct:.0f}%"
                ),
                severity="medium",
                evidence=[
                    InstitutionEvidence(
                        label="Mentor success rate",
                        value=f"{mentor.intervention_success_rate * 100:.1f}%",
                    ),
                    InstitutionEvidence(label="Cohort average", value=f"{cohort_avg * 100:.1f}%"),
                    InstitutionEvidence(label="Students served", value=str(mentor.student_count)),
                ],
                calculation=(
                    f"(mentor_success_rate - cohort_avg) * 100 >= {MENTOR_OUTPERFORMANCE_THRESHOLD}"
                ),
                source_metrics={
                    "mentor_success_rate": round(mentor.intervention_success_rate, 4),
                    "cohort_average": round(cohort_avg, 4),
                    "delta_pct": round(delta_pct, 2),
                },
            )
        )
    return items[:3]


def _readiness_drop_insight(data: InstitutionDataInput) -> list[InstitutionInsightItem]:
    if data.previous_readiness_avg is None:
        return []
    delta = data.current_readiness_avg - data.previous_readiness_avg
    if delta > -READINESS_DROP_THRESHOLD:
        return []
    return [
        InstitutionInsightItem(
            insight_type="readiness_drop",
            insight_key="institution_readiness",
            title=f"Institution readiness dropped {abs(delta):.1f} points this month",
            severity="high" if abs(delta) >= 10 else "medium",
            evidence=[
                InstitutionEvidence(label="Previous average", value=f"{data.previous_readiness_avg:.1f}"),
                InstitutionEvidence(label="Current average", value=f"{data.current_readiness_avg:.1f}"),
            ],
            calculation=f"current_readiness - previous_readiness <= -{READINESS_DROP_THRESHOLD}",
            source_metrics={
                "previous_readiness": round(data.previous_readiness_avg, 2),
                "current_readiness": round(data.current_readiness_avg, 2),
                "delta": round(delta, 2),
            },
        )
    ]


def _forecast_decline_insights(data: InstitutionDataInput) -> list[InstitutionInsightItem]:
    declining = [
        cohort
        for cohort in data.cohorts
        if cohort.avg_forecast < 55.0 and cohort.risk_count >= 5
    ]
    if not declining:
        return []
    exam_groups: dict[str, list[CohortSnapshotInput]] = {}
    for cohort in declining:
        exam_groups.setdefault(cohort.exam_id, []).append(cohort)
    items: list[InstitutionInsightItem] = []
    for exam_id, cohorts in exam_groups.items():
        if len(cohorts) < 1:
            continue
        items.append(
            InstitutionInsightItem(
                insight_type="forecast_decline",
                insight_key=exam_id,
                title=(
                    f"{exam_id.upper()} forecast probability decreased in "
                    f"{len(cohorts)} cohort{'s' if len(cohorts) != 1 else ''}"
                ),
                severity="high" if len(cohorts) >= 3 else "medium",
                evidence=[
                    InstitutionEvidence(label="Exam", value=exam_id),
                    InstitutionEvidence(label="Affected cohorts", value=str(len(cohorts))),
                ],
                calculation="avg_forecast < 55 AND risk_count >= 5 per cohort",
                source_metrics={
                    "affected_cohorts": len(cohorts),
                    "avg_forecast": round(
                        sum(item.avg_forecast for item in cohorts) / len(cohorts),
                        2,
                    ),
                },
            )
        )
    return items


def _current_affairs_drop_insight(data: InstitutionDataInput) -> list[InstitutionInsightItem]:
    if data.previous_ca_avg is None:
        return []
    delta = data.current_ca_avg - data.previous_ca_avg
    if delta > -CURRENT_AFFAIRS_DROP_THRESHOLD:
        return []
    return [
        InstitutionInsightItem(
            insight_type="current_affairs_drop",
            insight_key="current_affairs",
            title=f"Current Affairs readiness dropped {abs(delta):.1f}% this month",
            severity="high" if abs(delta) >= 8 else "medium",
            evidence=[
                InstitutionEvidence(label="Previous average", value=f"{data.previous_ca_avg:.1f}%"),
                InstitutionEvidence(label="Current average", value=f"{data.current_ca_avg:.1f}%"),
            ],
            calculation=f"current_ca - previous_ca <= -{CURRENT_AFFAIRS_DROP_THRESHOLD}",
            source_metrics={
                "previous_ca": round(data.previous_ca_avg, 2),
                "current_ca": round(data.current_ca_avg, 2),
                "delta": round(delta, 2),
            },
        )
    ]


def _pyq_gain_insight(data: InstitutionDataInput) -> list[InstitutionInsightItem]:
    if data.pyq_gain_signal < PYQ_GAIN_SIGNAL_THRESHOLD:
        return []
    return [
        InstitutionInsightItem(
            insight_type="pyq_gain_signal",
            insight_key="pyq_preparedness",
            title="PYQ-heavy concepts show highest readiness gains",
            severity="low",
            evidence=[
                InstitutionEvidence(
                    label="PYQ preparedness signal",
                    value=f"{data.pyq_gain_signal:.1f}",
                ),
            ],
            calculation=f"avg_pyq_preparedness >= {PYQ_GAIN_SIGNAL_THRESHOLD}",
            source_metrics={"pyq_gain_signal": round(data.pyq_gain_signal, 2)},
        )
    ]


def _intervention_underperformance_insight(data: InstitutionDataInput) -> list[InstitutionInsightItem]:
    if data.intervention_roi >= INTERVENTION_ROI_LOW_THRESHOLD:
        return []
    return [
        InstitutionInsightItem(
            insight_type="intervention_underperformance",
            insight_key="intervention_roi",
            title=f"Intervention ROI is below target at {data.intervention_roi:.1f}%",
            severity="high",
            evidence=[
                InstitutionEvidence(label="Intervention ROI", value=f"{data.intervention_roi:.1f}%"),
                InstitutionEvidence(label="Target", value=f"{INTERVENTION_ROI_LOW_THRESHOLD:.1f}%"),
            ],
            calculation=f"intervention_roi < {INTERVENTION_ROI_LOW_THRESHOLD}",
            source_metrics={"intervention_roi": round(data.intervention_roi, 2)},
        )
    ]


def _cohort_risk_spike_insights(data: InstitutionDataInput) -> list[InstitutionInsightItem]:
    items: list[InstitutionInsightItem] = []
    for cohort in data.cohorts:
        at_risk = cohort.segment_counts.get("at_risk", 0) + cohort.segment_counts.get("critical_risk", 0)
        if cohort.student_count == 0:
            continue
        at_risk_pct = (at_risk / cohort.student_count) * 100.0
        if at_risk_pct < AT_RISK_SPIKE_THRESHOLD:
            continue
        items.append(
            InstitutionInsightItem(
                insight_type="cohort_risk_spike",
                insight_key=cohort.cohort_id,
                title=(
                    f"Cohort {cohort.cohort_id} has {at_risk_pct:.0f}% students at risk "
                    f"({at_risk}/{cohort.student_count})"
                ),
                severity="critical" if at_risk_pct >= 35 else "high",
                evidence=[
                    InstitutionEvidence(label="At-risk students", value=str(at_risk)),
                    InstitutionEvidence(label="Total students", value=str(cohort.student_count)),
                ],
                calculation=f"(at_risk / student_count) * 100 >= {AT_RISK_SPIKE_THRESHOLD}",
                source_metrics={
                    "at_risk_count": at_risk,
                    "student_count": cohort.student_count,
                    "at_risk_pct": round(at_risk_pct, 2),
                },
            )
        )
    return items[:3]
