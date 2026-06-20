from __future__ import annotations

from prepos.application.institution.institution_models import (
    InstitutionDataInput,
    InstitutionInsightItem,
    InstitutionKpis,
    InstitutionRecommendationItem,
)


def explain_insight(insight: InstitutionInsightItem) -> str:
    evidence_text = "; ".join(f"{item.label}: {item.value}" for item in insight.evidence)
    return f"{insight.title}. Evidence: {evidence_text}. Calculation: {insight.calculation}."


def explain_recommendation(recommendation: InstitutionRecommendationItem) -> str:
    cohorts = ", ".join(recommendation.affected_cohorts[:3]) or "none"
    return (
        f"{recommendation.title}. Expected impact: +{recommendation.expected_impact:.1f} readiness points. "
        f"Affects {recommendation.affected_students} students across cohorts: {cohorts}. "
        f"{recommendation.explanation}"
    )


def explain_institution_summary(*, data: InstitutionDataInput, kpis: InstitutionKpis) -> list[str]:
    return [
        f"Institution health score: {kpis.institution_health_score:.1f}/100.",
        f"{kpis.total_cohorts} cohorts, {kpis.total_students} students tracked.",
        f"Average readiness {kpis.average_readiness:.1f}, forecast {kpis.average_forecast:.1f}%.",
        f"{kpis.at_risk_students} students at risk. Intervention ROI {kpis.intervention_roi:.1f}%.",
    ]
