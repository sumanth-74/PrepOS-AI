from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

import structlog

from prepos.application.institution.institution_analytics import InstitutionAnalyticsService
from prepos.application.institution.institution_explainer import explain_institution_summary
from prepos.application.institution.institution_insight_engine import generate_institution_insights
from prepos.application.institution.institution_models import (
    CohortComparisonItem,
    CohortSnapshotInput,
    InstitutionDashboardResponse,
    InstitutionDataInput,
    InstitutionEvidence,
    InstitutionInsightItem,
    InstitutionInsightsResponse,
    InstitutionKpis,
    InstitutionMentorEffectivenessResponse,
    InstitutionRecommendationItem,
    InstitutionRecommendationsResponse,
    InstitutionTrendItem,
    InstitutionTrendsResponse,
    MentorEffectivenessInput,
    MentorEffectivenessItem,
)
from prepos.application.institution.institution_recommendation_engine import (
    generate_institution_recommendations,
)
from prepos.application.institution.institution_trend_analyzer import analyze_institution_trends
from prepos.application.institution.ports import InstitutionRepositoryPort

logger = structlog.get_logger(__name__)


class InstitutionIntelligenceService:
    def __init__(
        self,
        *,
        repository: InstitutionRepositoryPort,
        analytics_service: InstitutionAnalyticsService | None = None,
    ) -> None:
        self._repository = repository
        self._analytics = analytics_service or InstitutionAnalyticsService(repository=repository)

    async def refresh_institution_intelligence(self, *, tenant_id: UUID) -> InstitutionDashboardResponse:
        now = datetime.now(UTC)
        data = self._parse_institution_data(await self._repository.load_institution_data(tenant_id=tenant_id))
        insights = generate_institution_insights(data)
        recommendations = generate_institution_recommendations(data=data, insights=insights)
        trends, readiness_trend, forecast_trend = analyze_institution_trends(data=data)

        await self._repository.save_insights(
            tenant_id=tenant_id,
            insights=[self._insight_to_row(item) for item in insights],
            now=now,
        )
        await self._repository.save_recommendations(
            tenant_id=tenant_id,
            recommendations=[self._recommendation_to_row(item) for item in recommendations],
            now=now,
        )
        await self._repository.save_trends(
            tenant_id=tenant_id,
            trends=[self._trend_to_row(item) for item in trends],
            now=now,
        )
        await self._repository.record_event(
            tenant_id=tenant_id,
            event_type="institution_insight_generated",
            metadata_json={"insight_count": len(insights)},
            now=now,
        )
        await self._repository.record_event(
            tenant_id=tenant_id,
            event_type="institution_recommendation_generated",
            metadata_json={"recommendation_count": len(recommendations)},
            now=now,
        )
        logger.info(
            "institution_insight_generated",
            tenant_id=str(tenant_id),
            insight_count=len(insights),
            recommendation_count=len(recommendations),
            trend_count=len(trends),
        )
        dashboard = self._build_dashboard(data=data, insights=insights, recommendations=recommendations, now=now)
        _ = readiness_trend, forecast_trend
        return dashboard

    async def get_dashboard(
        self,
        *,
        tenant_id: UUID,
        refresh: bool = False,
    ) -> InstitutionDashboardResponse:
        if refresh:
            return await self.refresh_institution_intelligence(tenant_id=tenant_id)
        data = self._parse_institution_data(await self._repository.load_institution_data(tenant_id=tenant_id))
        insights = await self._load_insights(tenant_id=tenant_id, data=data)
        recommendations = await self._load_recommendations(tenant_id=tenant_id, data=data, insights=insights)
        return self._build_dashboard(
            data=data,
            insights=insights,
            recommendations=recommendations,
            now=datetime.now(UTC),
        )

    async def get_insights(self, *, tenant_id: UUID, refresh: bool = False) -> InstitutionInsightsResponse:
        if refresh:
            await self.refresh_institution_intelligence(tenant_id=tenant_id)
        rows = await self._repository.list_insights(tenant_id=tenant_id, limit=50)
        if rows:
            insights = [self._row_to_insight(row) for row in rows]
        else:
            data = self._parse_institution_data(await self._repository.load_institution_data(tenant_id=tenant_id))
            insights = generate_institution_insights(data)
        return InstitutionInsightsResponse(
            insights=insights,
            total=len(insights),
            generated_at=datetime.now(UTC),
        )

    async def get_recommendations(
        self,
        *,
        tenant_id: UUID,
        refresh: bool = False,
    ) -> InstitutionRecommendationsResponse:
        if refresh:
            await self.refresh_institution_intelligence(tenant_id=tenant_id)
        rows = await self._repository.list_recommendations(tenant_id=tenant_id, limit=20)
        if rows:
            recommendations = [self._row_to_recommendation(row) for row in rows]
        else:
            data = self._parse_institution_data(await self._repository.load_institution_data(tenant_id=tenant_id))
            insights = generate_institution_insights(data)
            recommendations = generate_institution_recommendations(data=data, insights=insights)
        return InstitutionRecommendationsResponse(
            recommendations=recommendations,
            total=len(recommendations),
            generated_at=datetime.now(UTC),
        )

    async def get_trends(
        self,
        *,
        tenant_id: UUID,
        period: str = "monthly",
        refresh: bool = False,
    ) -> InstitutionTrendsResponse:
        if refresh:
            await self.refresh_institution_intelligence(tenant_id=tenant_id)
        rows = await self._repository.list_trends(tenant_id=tenant_id, period=period, limit=50)
        data = self._parse_institution_data(await self._repository.load_institution_data(tenant_id=tenant_id))
        if rows:
            trends = [self._row_to_trend(row) for row in rows]
            readiness_trend = next(
                (item.trend_direction for item in trends if item.trend_type == "readiness"),
                "stable",
            )
            forecast_trend = next(
                (item.trend_direction for item in trends if item.trend_type == "forecast"),
                "stable",
            )
        else:
            trends, readiness_trend, forecast_trend = analyze_institution_trends(data=data, period=period)
        return InstitutionTrendsResponse(
            trends=trends,
            readiness_trend=readiness_trend,
            forecast_trend=forecast_trend,
            intervention_roi=data.intervention_roi,
            generated_at=datetime.now(UTC),
        )

    async def get_mentor_effectiveness(
        self,
        *,
        tenant_id: UUID,
    ) -> InstitutionMentorEffectivenessResponse:
        data = self._parse_institution_data(await self._repository.load_institution_data(tenant_id=tenant_id))
        cohort_avg = (
            sum(item.intervention_success_rate for item in data.mentors) / len(data.mentors)
            if data.mentors
            else 0.0
        )
        mentors = [
            MentorEffectivenessItem(
                mentor_id=mentor.mentor_id,
                intervention_success_rate=round(mentor.intervention_success_rate, 4),
                student_count=mentor.student_count,
                average_gain=round(mentor.average_gain, 2),
                cohort_average_success_rate=round(cohort_avg, 4),
                outperformance_pct=round((mentor.intervention_success_rate - cohort_avg) * 100.0, 2),
            )
            for mentor in sorted(data.mentors, key=lambda item: item.intervention_success_rate, reverse=True)
        ]
        return InstitutionMentorEffectivenessResponse(
            mentors=mentors,
            cohort_average_success_rate=round(cohort_avg, 4),
            total=len(mentors),
            generated_at=datetime.now(UTC),
        )

    async def export_csv(self, *, tenant_id: UUID) -> str:
        await self._repository.record_event(
            tenant_id=tenant_id,
            event_type="institution_exported",
            metadata_json={},
            now=datetime.now(UTC),
        )
        logger.info("institution_exported", tenant_id=str(tenant_id))
        return await self._analytics.export_csv(tenant_id=tenant_id)

    async def _load_insights(
        self,
        *,
        tenant_id: UUID,
        data: InstitutionDataInput,
    ) -> list[InstitutionInsightItem]:
        rows = await self._repository.list_insights(tenant_id=tenant_id, limit=50)
        if rows:
            return [self._row_to_insight(row) for row in rows]
        return generate_institution_insights(data)

    async def _load_recommendations(
        self,
        *,
        tenant_id: UUID,
        data: InstitutionDataInput,
        insights: list[InstitutionInsightItem],
    ) -> list[InstitutionRecommendationItem]:
        rows = await self._repository.list_recommendations(tenant_id=tenant_id, limit=20)
        if rows:
            return [self._row_to_recommendation(row) for row in rows]
        return generate_institution_recommendations(data=data, insights=insights)

    def _build_dashboard(
        self,
        *,
        data: InstitutionDataInput,
        insights: list[InstitutionInsightItem],
        recommendations: list[InstitutionRecommendationItem],
        now: datetime,
    ) -> InstitutionDashboardResponse:
        kpis = self._compute_kpis(data)
        cohort_comparisons = [
            CohortComparisonItem(
                cohort_id=cohort.cohort_id,
                exam_id=cohort.exam_id,
                student_count=cohort.student_count,
                average_readiness=round(cohort.avg_readiness, 2),
                average_forecast=round(cohort.avg_forecast, 2),
                cohort_health_score=round(cohort.cohort_health_score, 2),
                at_risk_count=cohort.segment_counts.get("at_risk", 0)
                + cohort.segment_counts.get("critical_risk", 0),
            )
            for cohort in sorted(data.cohorts, key=lambda item: item.cohort_health_score)
        ]
        weak_concepts = [
            concept
            for concept, _ in sorted(
                data.concept_cohort_counts.items(),
                key=lambda pair: pair[1],
                reverse=True,
            )[:8]
        ]
        _ = explain_institution_summary(data=data, kpis=kpis)
        return InstitutionDashboardResponse(
            kpis=kpis,
            cohort_comparisons=cohort_comparisons,
            weak_concepts=weak_concepts,
            top_insights=insights[:5],
            top_recommendations=recommendations[:5],
            generated_at=now,
        )

    @staticmethod
    def _compute_kpis(data: InstitutionDataInput) -> InstitutionKpis:
        total_students = sum(cohort.student_count for cohort in data.cohorts)
        avg_readiness = data.current_readiness_avg
        avg_forecast = data.current_forecast_avg
        avg_health = (
            sum(cohort.cohort_health_score for cohort in data.cohorts) / len(data.cohorts)
            if data.cohorts
            else 0.0
        )
        institution_health = (
            avg_readiness * 0.30
            + avg_forecast * 0.25
            + avg_health * 0.25
            + data.intervention_roi * 0.20
        )
        return InstitutionKpis(
            total_students=total_students,
            total_cohorts=len(data.cohorts),
            average_readiness=round(avg_readiness, 2),
            average_forecast=round(avg_forecast, 2),
            average_cohort_health=round(avg_health, 2),
            at_risk_students=data.total_at_risk,
            intervention_roi=round(data.intervention_roi, 2),
            institution_health_score=round(min(100.0, institution_health), 2),
        )

    @staticmethod
    def _parse_institution_data(payload: dict[str, object]) -> InstitutionDataInput:
        cohorts = tuple(
            CohortSnapshotInput(
                cohort_id=str(item["cohort_id"]),
                exam_id=str(item["exam_id"]),
                student_count=int(item["student_count"]),
                avg_readiness=float(item["avg_readiness"]),
                avg_forecast=float(item["avg_forecast"]),
                avg_effectiveness=float(item["avg_effectiveness"]),
                risk_count=int(item["risk_count"]),
                segment_counts=dict(item.get("segment_counts") or {}),  # type: ignore[arg-type]
                top_risks=tuple(str(risk) for risk in item.get("top_risks", [])),  # type: ignore[arg-type]
                cohort_health_score=float(item.get("cohort_health_score", 0.0)),
                current_affairs_preparedness=float(item.get("current_affairs_preparedness", 0.0)),
                pyq_preparedness=float(item.get("pyq_preparedness", 0.0)),
                snapshot_date=item["snapshot_date"],  # type: ignore[arg-type]
            )
            for item in payload.get("cohorts", [])  # type: ignore[union-attr]
        )
        mentors = tuple(
            MentorEffectivenessInput(
                mentor_id=str(item["mentor_id"]),
                intervention_success_rate=float(item["intervention_success_rate"]),
                student_count=int(item["student_count"]),
                average_gain=float(item["average_gain"]),
            )
            for item in payload.get("mentors", [])  # type: ignore[union-attr]
        )
        return InstitutionDataInput(
            cohorts=cohorts,
            mentors=mentors,
            concept_cohort_counts=dict(payload.get("concept_cohort_counts") or {}),  # type: ignore[arg-type]
            previous_readiness_avg=payload.get("previous_readiness_avg"),  # type: ignore[arg-type]
            current_readiness_avg=float(payload.get("current_readiness_avg", 0.0)),  # type: ignore[arg-type]
            previous_forecast_avg=payload.get("previous_forecast_avg"),  # type: ignore[arg-type]
            current_forecast_avg=float(payload.get("current_forecast_avg", 0.0)),  # type: ignore[arg-type]
            previous_ca_avg=payload.get("previous_ca_avg"),  # type: ignore[arg-type]
            current_ca_avg=float(payload.get("current_ca_avg", 0.0)),  # type: ignore[arg-type]
            intervention_roi=float(payload.get("intervention_roi", 0.0)),  # type: ignore[arg-type]
            pyq_gain_signal=float(payload.get("pyq_gain_signal", 0.0)),  # type: ignore[arg-type]
            total_at_risk=int(payload.get("total_at_risk", 0)),  # type: ignore[arg-type]
        )

    @staticmethod
    def _insight_to_row(item: InstitutionInsightItem) -> dict[str, object]:
        return {
            "insight_type": item.insight_type,
            "insight_key": item.insight_key,
            "title": item.title,
            "severity": item.severity,
            "evidence_json": [entry.model_dump() for entry in item.evidence],
            "calculation_json": {"formula": item.calculation},
            "source_metrics_json": item.source_metrics,
        }

    @staticmethod
    def _recommendation_to_row(item: InstitutionRecommendationItem) -> dict[str, object]:
        return {
            "recommendation_type": item.recommendation_type,
            "title": item.title,
            "expected_impact": item.expected_impact,
            "affected_students": item.affected_students,
            "affected_cohorts_json": item.affected_cohorts,
            "explanation": item.explanation,
            "priority_score": item.priority_score,
            "metadata_json": {},
        }

    @staticmethod
    def _trend_to_row(item: InstitutionTrendItem) -> dict[str, object]:
        return {
            "trend_type": item.trend_type,
            "trend_key": item.trend_key,
            "trend_direction": item.trend_direction,
            "delta_value": item.delta_value,
            "period": item.period,
            "metadata_json": {"label": item.label},
        }

    @staticmethod
    def _row_to_insight(row: dict[str, object]) -> InstitutionInsightItem:
        evidence_rows = row.get("evidence_json") or []
        evidence = [
            InstitutionEvidence(label=str(item["label"]), value=str(item["value"]))  # type: ignore[index]
            for item in evidence_rows  # type: ignore[union-attr]
        ]
        calculation = row.get("calculation_json") or {}
        return InstitutionInsightItem(
            insight_type=str(row["insight_type"]),
            insight_key=str(row["insight_key"]),
            title=str(row["title"]),
            severity=str(row["severity"]),
            evidence=evidence,
            calculation=str(calculation.get("formula", "") if isinstance(calculation, dict) else ""),
            source_metrics=dict(row.get("source_metrics_json") or {}),  # type: ignore[arg-type]
        )

    @staticmethod
    def _row_to_recommendation(row: dict[str, object]) -> InstitutionRecommendationItem:
        return InstitutionRecommendationItem(
            recommendation_type=str(row["recommendation_type"]),
            title=str(row["title"]),
            expected_impact=float(row["expected_impact"]),
            affected_students=int(row["affected_students"]),
            affected_cohorts=list(row.get("affected_cohorts_json") or []),  # type: ignore[arg-type]
            explanation=str(row["explanation"]),
            priority_score=float(row["priority_score"]),
        )

    @staticmethod
    def _row_to_trend(row: dict[str, object]) -> InstitutionTrendItem:
        metadata = dict(row.get("metadata_json") or {})
        return InstitutionTrendItem(
            trend_type=str(row["trend_type"]),
            trend_key=str(row["trend_key"]),
            trend_direction=str(row["trend_direction"]),
            delta_value=float(row["delta_value"]),
            period=str(row["period"]),
            label=str(metadata.get("label", row["trend_key"])),
        )
