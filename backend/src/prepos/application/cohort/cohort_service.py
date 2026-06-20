from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import UUID

import structlog

from prepos.application.cohort.cohort_analytics import CohortAnalyticsService
from prepos.application.cohort.cohort_explainer import explain_cohort_summary
from prepos.application.cohort.cohort_intelligence_engine import (
    aggregate_cohort_metrics,
    build_segment_distribution,
    top_cohort_risk_concepts,
)
from prepos.application.cohort.cohort_models import (
    CohortAdminResponse,
    CohortMetrics,
    CohortRisksResponse,
    CohortRiskItem,
    CohortSegmentsResponse,
    CohortStudentsResponse,
    CohortSummaryResponse,
    CohortTrendItem,
    CohortTrendsResponse,
    StudentCohortInput,
    StudentSegmentItem,
)
from prepos.application.cohort.cohort_risk_engine import build_risk_items, count_at_risk
from prepos.application.cohort.cohort_segmentation_engine import segment_student
from prepos.application.cohort.cohort_trend_service import compute_concept_trends, compute_macro_trends
from prepos.application.cohort.ports import CohortRepositoryPort
from prepos.application.recommendations.recommendation_engine import format_concept_name

logger = structlog.get_logger(__name__)


def build_cohort_id(*, exam_id: str, target_year: int | None = None) -> str:
    if target_year:
        return f"{exam_id}_{target_year}"
    return f"{exam_id}_cohort"


class CohortIntelligenceService:
    def __init__(
        self,
        *,
        repository: CohortRepositoryPort,
        analytics_service: CohortAnalyticsService | None = None,
    ) -> None:
        self._repository = repository
        self._analytics = analytics_service or CohortAnalyticsService(repository=repository)

    async def refresh_cohort(
        self,
        *,
        tenant_id: UUID,
        exam_id: str = "upsc_cse",
        cohort_id: str | None = None,
    ) -> CohortSummaryResponse:
        resolved_exam = exam_id or "upsc_cse"
        resolved_cohort = cohort_id or build_cohort_id(exam_id=resolved_exam)
        now = datetime.now(UTC)
        students = await self._load_student_inputs(tenant_id=tenant_id, exam_id=resolved_exam)
        return await self._persist_and_summarize(
            tenant_id=tenant_id,
            cohort_id=resolved_cohort,
            exam_id=resolved_exam,
            students=students,
            now=now,
        )

    async def get_cohort_summary(
        self,
        *,
        tenant_id: UUID,
        exam_id: str = "upsc_cse",
        cohort_id: str | None = None,
        refresh: bool = False,
    ) -> CohortSummaryResponse:
        resolved_exam = exam_id or "upsc_cse"
        resolved_cohort = cohort_id or build_cohort_id(exam_id=resolved_exam)
        if refresh or not await self._repository.get_latest_snapshot(
            tenant_id=tenant_id,
            cohort_id=resolved_cohort,
        ):
            return await self.refresh_cohort(
                tenant_id=tenant_id,
                exam_id=resolved_exam,
                cohort_id=resolved_cohort,
            )
        students = await self._load_student_inputs(tenant_id=tenant_id, exam_id=resolved_exam)
        return self._build_summary(
            cohort_id=resolved_cohort,
            exam_id=resolved_exam,
            students=students,
            generated_at=datetime.now(UTC),
        )

    async def get_cohort_students(
        self,
        *,
        tenant_id: UUID,
        exam_id: str = "upsc_cse",
        cohort_id: str | None = None,
        limit: int = 100,
    ) -> CohortStudentsResponse:
        summary = await self.get_cohort_summary(
            tenant_id=tenant_id,
            exam_id=exam_id,
            cohort_id=cohort_id,
        )
        students = await self._load_student_inputs(tenant_id=tenant_id, exam_id=exam_id)
        items = [self._map_student_item(student) for student in students[:limit]]
        return CohortStudentsResponse(
            cohort_id=summary.cohort_id,
            students=items,
            total=len(items),
        )

    async def get_cohort_segments(
        self,
        *,
        tenant_id: UUID,
        exam_id: str = "upsc_cse",
        cohort_id: str | None = None,
        segment_type: str | None = None,
        limit: int = 100,
    ) -> CohortSegmentsResponse:
        summary = await self.get_cohort_summary(
            tenant_id=tenant_id,
            exam_id=exam_id,
            cohort_id=cohort_id,
        )
        students = await self._load_student_inputs(tenant_id=tenant_id, exam_id=exam_id)
        items = [self._map_student_item(student) for student in students]
        if segment_type:
            items = [item for item in items if item.segment_type == segment_type]
        return CohortSegmentsResponse(
            cohort_id=summary.cohort_id,
            distribution=summary.segments,
            students=items[:limit],
            total=len(items[:limit]),
        )

    async def get_cohort_risks(
        self,
        *,
        tenant_id: UUID,
        exam_id: str = "upsc_cse",
        cohort_id: str | None = None,
        limit: int = 20,
    ) -> CohortRisksResponse:
        summary = await self.get_cohort_summary(
            tenant_id=tenant_id,
            exam_id=exam_id,
            cohort_id=cohort_id,
        )
        students = await self._load_student_inputs(tenant_id=tenant_id, exam_id=exam_id)
        risk_rows = build_risk_items(students, limit=limit)
        risks = [
            CohortRiskItem(
                student_id=row["student_id"],  # type: ignore[arg-type]
                risk_score=float(row["risk_score"]),
                segment_type=str(row["segment_type"]),
                readiness=float(row["readiness"]),
                forecast_probability=float(row["forecast_probability"]),
                top_risk_factors=list(row["top_risk_factors"]),  # type: ignore[arg-type]
            )
            for row in risk_rows
        ]
        return CohortRisksResponse(
            cohort_id=summary.cohort_id,
            risks=risks,
            top_concept_risks=summary.top_risks,
            total=len(risks),
        )

    async def get_cohort_trends(
        self,
        *,
        tenant_id: UUID,
        exam_id: str = "upsc_cse",
        cohort_id: str | None = None,
        period: str = "weekly",
    ) -> CohortTrendsResponse:
        resolved_cohort = cohort_id or build_cohort_id(exam_id=exam_id)
        students = await self._load_student_inputs(tenant_id=tenant_id, exam_id=exam_id)
        metrics = aggregate_cohort_metrics(students)
        previous = await self._repository.get_previous_snapshot(
            tenant_id=tenant_id,
            cohort_id=resolved_cohort,
            before_date=date.today(),
        )
        previous_readiness = float(previous["avg_readiness"]) if previous else None
        previous_forecast = float(previous["avg_forecast"]) if previous else None
        previous_count = int(previous["student_count"]) if previous else None
        readiness_trend, forecast_trend, growth = compute_macro_trends(
            current_avg_readiness=metrics.average_readiness,
            current_avg_forecast=metrics.average_forecast,
            previous_avg_readiness=previous_readiness,
            previous_avg_forecast=previous_forecast,
            current_count=len(students),
            previous_count=previous_count,
        )
        concept_trends = compute_concept_trends(
            students=students,
            previous_avg_readiness=previous_readiness,
            current_avg_readiness=metrics.average_readiness,
            period=period,
        )
        return CohortTrendsResponse(
            cohort_id=resolved_cohort,
            trends=[
                CohortTrendItem(
                    concept_id=str(item["concept_id"]),
                    concept_name=str(item.get("concept_name", format_concept_name(str(item["concept_id"])))),
                    trend_direction=str(item["trend_direction"]),
                    readiness_delta=float(item["readiness_delta"]),
                    period=str(item["period"]),
                )
                for item in concept_trends
            ],
            readiness_trend=readiness_trend,
            forecast_trend=forecast_trend,
            cohort_growth=growth,
        )

    async def get_admin_dashboard(self, *, tenant_id: UUID) -> CohortAdminResponse:
        metrics = await self._analytics.get_admin_dashboard(tenant_id=tenant_id)
        return CohortAdminResponse(**metrics)

    async def export_csv(self, *, tenant_id: UUID) -> str:
        return await self._analytics.export_csv(tenant_id=tenant_id)

    async def load_student_inputs_for_exam(
        self,
        *,
        tenant_id: UUID,
        exam_id: str,
    ) -> list[StudentCohortInput]:
        return await self._load_student_inputs(tenant_id=tenant_id, exam_id=exam_id)

    async def _load_student_inputs(
        self,
        *,
        tenant_id: UUID,
        exam_id: str,
    ) -> list[StudentCohortInput]:
        rows = await self._repository.list_cohort_student_rows(
            tenant_id=tenant_id,
            exam_id=exam_id,
        )
        return [
            StudentCohortInput(
                student_id=row["student_id"],  # type: ignore[arg-type]
                exam_id=str(row["exam_id"]),
                readiness=float(row["readiness"]),
                forecast_probability=float(row["forecast_probability"]),
                projected_readiness=float(row["projected_readiness"]),
                on_track=bool(row["on_track"]),
                goal_attainment=float(row["goal_attainment"]),
                planning_adherence=float(row["planning_adherence"]),
                recommendation_effectiveness=float(row["recommendation_effectiveness"]),
                intervention_effectiveness=float(row["intervention_effectiveness"]),
                intervention_count=int(row["intervention_count"]),
                readiness_delta=float(row["readiness_delta"]),
                weekly_progress=float(row["weekly_progress"]),
                consistency_score=float(row["consistency_score"]),
                pyq_preparedness=float(row["pyq_preparedness"]),
                current_affairs_preparedness=float(row["current_affairs_preparedness"]),
                negative_drivers=tuple(str(item) for item in row.get("negative_drivers", [])),  # type: ignore[arg-type]
                failed_intervention_count=int(row["failed_intervention_count"]),
            )
            for row in rows
        ]

    async def _persist_and_summarize(
        self,
        *,
        tenant_id: UUID,
        cohort_id: str,
        exam_id: str,
        students: list[StudentCohortInput],
        now: datetime,
    ) -> CohortSummaryResponse:
        metrics = aggregate_cohort_metrics(students)
        segments = build_segment_distribution(students)
        top_risks = top_cohort_risk_concepts(students)
        risk_count = count_at_risk(students)
        previous = await self._repository.get_previous_snapshot(
            tenant_id=tenant_id,
            cohort_id=cohort_id,
            before_date=now.date(),
        )
        concept_trends = compute_concept_trends(
            students=students,
            previous_avg_readiness=float(previous["avg_readiness"]) if previous else None,
            current_avg_readiness=metrics.average_readiness,
        )
        segment_rows = []
        for student in students:
            result = segment_student(student)
            segment_rows.append(
                {
                    "student_id": student.student_id,
                    "segment_type": result.segment_type,
                    "segment_score": result.segment_score,
                    "risk_score": result.risk_score,
                    "metadata_json": {"risk_factors": list(result.risk_factors)},
                }
            )
            logger.info(
                "student_segment_calculated",
                tenant_id=str(tenant_id),
                cohort_id=cohort_id,
                student_id=str(student.student_id),
                segment_type=result.segment_type,
                risk_score=result.risk_score,
            )

        await self._repository.save_segments(
            tenant_id=tenant_id,
            cohort_id=cohort_id,
            segments=segment_rows,
            now=now,
        )
        await self._repository.save_trends(
            tenant_id=tenant_id,
            cohort_id=cohort_id,
            trends=concept_trends,
            now=now,
        )
        snapshot_id = await self._repository.save_snapshot(
            tenant_id=tenant_id,
            cohort_id=cohort_id,
            exam_id=exam_id,
            snapshot_date=now.date(),
            student_count=len(students),
            avg_readiness=metrics.average_readiness,
            avg_forecast=metrics.average_forecast,
            avg_effectiveness=metrics.recommendation_effectiveness,
            risk_count=risk_count,
            segment_counts=segments,
            metadata_json={
                "cohort_health_score": metrics.cohort_health_score,
                "top_risks": top_risks,
                "explanations": explain_cohort_summary(
                    cohort_id=cohort_id,
                    student_count=len(students),
                    segments=segments,
                    metrics=metrics,
                    top_risks=top_risks,
                ),
            },
            now=now,
        )
        await self._repository.record_event(
            tenant_id=tenant_id,
            cohort_id=cohort_id,
            event_type="cohort_snapshot_generated",
            metadata_json={"snapshot_id": str(snapshot_id), "segment_counts": segments, "risk_count": risk_count},
            now=now,
        )
        if risk_count > 0:
            await self._repository.record_event(
                tenant_id=tenant_id,
                cohort_id=cohort_id,
                event_type="risk_detected",
                metadata_json={"risk_count": risk_count},
                now=now,
            )
        await self._repository.record_event(
            tenant_id=tenant_id,
            cohort_id=cohort_id,
            event_type="trend_generated",
            metadata_json={"trend_count": len(concept_trends)},
            now=now,
        )
        logger.info(
            "cohort_snapshot_generated",
            tenant_id=str(tenant_id),
            cohort_id=cohort_id,
            student_count=len(students),
            risk_count=risk_count,
            segment_counts=segments,
        )
        return self._build_summary(
            cohort_id=cohort_id,
            exam_id=exam_id,
            students=students,
            generated_at=now,
        )

    def _build_summary(
        self,
        *,
        cohort_id: str,
        exam_id: str,
        students: list[StudentCohortInput],
        generated_at: datetime,
    ) -> CohortSummaryResponse:
        metrics = aggregate_cohort_metrics(students)
        segments = build_segment_distribution(students)
        top_risks = top_cohort_risk_concepts(students)
        return CohortSummaryResponse(
            cohort_id=cohort_id,
            exam_id=exam_id,
            student_count=len(students),
            segments=segments,
            metrics=metrics,
            top_risks=top_risks,
            generated_at=generated_at,
        )

    @staticmethod
    def _map_student_item(student: StudentCohortInput) -> StudentSegmentItem:
        result = segment_student(student)
        return StudentSegmentItem(
            student_id=student.student_id,
            segment_type=result.segment_type,
            segment_score=result.segment_score,
            risk_score=result.risk_score,
            readiness=student.readiness,
            forecast_probability=student.forecast_probability,
            exam_id=student.exam_id,
        )
