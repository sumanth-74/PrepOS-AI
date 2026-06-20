from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

import structlog

from prepos.application.institution_outcomes.initiative_effectiveness import evaluate_all_initiatives
from prepos.application.institution_outcomes.outcome_analytics import InstitutionOutcomeAnalyticsService
from prepos.application.institution_outcomes.outcome_engine import (
    aggregate_outcome_metrics,
    default_expected_gains,
    measure_outcomes,
)
from prepos.application.institution_outcomes.outcome_models import (
    CreateInitiativeRequest,
    InitiativeEffectivenessItem,
    InitiativeEffectivenessResponse,
    InitiativeInput,
    InitiativeItem,
    InitiativesResponse,
    MetricSnapshot,
    OutcomeItem,
    OutcomesResponse,
    OutcomeState,
    RoiItem,
    RoiResponse,
)
from prepos.application.institution_outcomes.ports import InstitutionOutcomeRepositoryPort
from prepos.application.institution_outcomes.roi_engine import calculate_roi_for_initiatives, split_best_and_failed
from prepos.core.exceptions import ValidationError

logger = structlog.get_logger(__name__)


class InstitutionOutcomeService:
    def __init__(
        self,
        *,
        repository: InstitutionOutcomeRepositoryPort,
        analytics_service: InstitutionOutcomeAnalyticsService | None = None,
    ) -> None:
        self._repository = repository
        self._analytics = analytics_service or InstitutionOutcomeAnalyticsService(repository=repository)

    async def create_initiative(
        self,
        *,
        tenant_id: UUID,
        request: CreateInitiativeRequest,
    ) -> InitiativeItem:
        if request.initiative_type not in {
            "revision_campaign",
            "mentor_training",
            "current_affairs_boost",
            "forecast_recovery",
            "weak_concept_program",
            "pyq_focus_program",
        }:
            raise ValidationError(
                "Unsupported initiative type.",
                details={"initiative_type": request.initiative_type},
            )

        now = datetime.now(UTC)
        metrics = await self._repository.load_cohort_snapshot_metrics(tenant_id=tenant_id)
        before_state = {
            "readiness": metrics.get("average_readiness", 0.0),
            "forecast": metrics.get("average_forecast", 0.0),
            "cohort_health": metrics.get("average_cohort_health", 0.0),
            "risk_count": metrics.get("total_at_risk", 0),
        }
        expected = default_expected_gains(request.initiative_type)
        expected.update(
            {
                "readiness_gain": request.expected_readiness_gain,
                "forecast_gain": request.expected_forecast_gain,
                "cohort_health_gain": request.expected_cohort_health_gain,
                "risk_reduction": request.expected_risk_reduction,
            }
        )
        row = await self._repository.create_initiative(
            tenant_id=tenant_id,
            payload={
                "initiative_type": request.initiative_type,
                "title": request.title,
                "status": "active",
                "start_date": request.start_date,
                "end_date": request.end_date,
                "affected_students": request.affected_students,
                "affected_cohorts_json": request.affected_cohorts,
                "expected_outcomes_json": expected,
                "actual_outcomes_json": {},
                "before_state_json": before_state,
                "metadata_json": {},
            },
            now=now,
        )
        await self._repository.record_event(
            tenant_id=tenant_id,
            event_type="institution_initiative_created",
            metadata_json={"initiative_id": str(row["id"]), "initiative_type": request.initiative_type},
            now=now,
        )
        logger.info(
            "institution_initiative_created",
            tenant_id=str(tenant_id),
            initiative_id=str(row["id"]),
            initiative_type=request.initiative_type,
        )
        return self._row_to_initiative(row)

    async def list_initiatives(
        self,
        *,
        tenant_id: UUID,
        status: str | None = None,
        limit: int = 50,
    ) -> InitiativesResponse:
        rows = await self._repository.list_initiatives(tenant_id=tenant_id, status=status, limit=limit)
        initiatives = [self._row_to_initiative(row) for row in rows]
        return InitiativesResponse(initiatives=initiatives, total=len(initiatives))

    async def get_outcomes(
        self,
        *,
        tenant_id: UUID,
        refresh: bool = False,
    ) -> OutcomesResponse:
        if refresh:
            await self.refresh_outcomes(tenant_id=tenant_id)
        rows = await self._repository.list_outcomes(tenant_id=tenant_id, limit=100)
        if rows:
            outcomes = [self._row_to_outcome(row) for row in rows]
        else:
            initiatives = await self._build_initiative_inputs(tenant_id=tenant_id)
            outcomes = measure_outcomes(initiatives)
        metrics = aggregate_outcome_metrics(outcomes)
        return OutcomesResponse(
            outcomes=outcomes,
            total=len(outcomes),
            average_readiness_uplift=metrics["average_readiness_uplift"],
            average_forecast_uplift=metrics["average_forecast_uplift"],
            average_risk_reduction=metrics["average_risk_reduction"],
            generated_at=datetime.now(UTC),
        )

    async def get_roi(
        self,
        *,
        tenant_id: UUID,
        refresh: bool = False,
    ) -> RoiResponse:
        if refresh:
            await self.refresh_outcomes(tenant_id=tenant_id)
        rows = await self._repository.list_roi_metrics(tenant_id=tenant_id, limit=100)
        if rows:
            items = [self._row_to_roi(row) for row in rows]
        else:
            initiatives = await self._build_initiative_inputs(tenant_id=tenant_id)
            outcomes = measure_outcomes(initiatives)
            items = calculate_roi_for_initiatives(initiatives=initiatives, outcomes=outcomes)
        best, failed = split_best_and_failed(items)
        average = round(sum(item.roi_score for item in items) / len(items), 2) if items else 0.0
        return RoiResponse(
            items=items,
            total=len(items),
            average_roi_score=average,
            best_initiatives=best[:5],
            failed_initiatives=failed[:5],
            generated_at=datetime.now(UTC),
        )

    async def get_effectiveness(
        self,
        *,
        tenant_id: UUID,
        refresh: bool = False,
    ) -> InitiativeEffectivenessResponse:
        if refresh:
            await self.refresh_outcomes(tenant_id=tenant_id)
        rows = await self._repository.list_effectiveness(tenant_id=tenant_id, limit=100)
        if rows:
            items = [self._row_to_effectiveness(row) for row in rows]
        else:
            initiatives = await self._build_initiative_inputs(tenant_id=tenant_id)
            outcomes = measure_outcomes(initiatives)
            items = evaluate_all_initiatives(initiatives=initiatives, outcomes=outcomes)
        return InitiativeEffectivenessResponse(
            items=items,
            total=len(items),
            generated_at=datetime.now(UTC),
        )

    async def refresh_outcomes(self, *, tenant_id: UUID) -> None:
        now = datetime.now(UTC)
        initiatives = await self._build_initiative_inputs(tenant_id=tenant_id)
        outcomes = measure_outcomes(initiatives)
        roi_items = calculate_roi_for_initiatives(initiatives=initiatives, outcomes=outcomes)
        effectiveness = evaluate_all_initiatives(initiatives=initiatives, outcomes=outcomes)

        await self._repository.save_outcomes(
            tenant_id=tenant_id,
            outcomes=[self._outcome_to_row(outcome) for outcome in outcomes],
            now=now,
        )
        await self._repository.save_roi_metrics(
            tenant_id=tenant_id,
            metrics=[self._roi_to_row(item) for item in roi_items],
            now=now,
        )
        await self._repository.save_effectiveness(
            tenant_id=tenant_id,
            rows=[self._effectiveness_to_row(item) for item in effectiveness],
            now=now,
        )

        for initiative, outcome in zip(initiatives, outcomes, strict=False):
            await self._repository.update_initiative_outcomes(
                tenant_id=tenant_id,
                initiative_id=initiative.initiative_id,
                actual_outcomes={
                    "readiness_gain": outcome.readiness_gain,
                    "forecast_gain": outcome.forecast_gain,
                    "cohort_health_gain": outcome.cohort_health_gain,
                    "risk_reduction": outcome.risk_reduction,
                    "actual_gain": outcome.actual_gain,
                    "variance": outcome.variance,
                },
                now=now,
            )

        await self._repository.record_event(
            tenant_id=tenant_id,
            event_type="institution_outcome_generated",
            metadata_json={"outcome_count": len(outcomes)},
            now=now,
        )
        await self._repository.record_event(
            tenant_id=tenant_id,
            event_type="institution_roi_calculated",
            metadata_json={"roi_count": len(roi_items), "average_roi": round(
                sum(item.roi_score for item in roi_items) / len(roi_items), 2
            ) if roi_items else 0.0},
            now=now,
        )
        logger.info(
            "institution_outcome_generated",
            tenant_id=str(tenant_id),
            outcome_count=len(outcomes),
            roi_count=len(roi_items),
        )

    async def export_roi_csv(self, *, tenant_id: UUID) -> str:
        now = datetime.now(UTC)
        await self._repository.record_event(
            tenant_id=tenant_id,
            event_type="institution_roi_exported",
            metadata_json={},
            now=now,
        )
        logger.info("institution_roi_exported", tenant_id=str(tenant_id))
        return await self._analytics.export_roi_csv(tenant_id=tenant_id)

    async def _build_initiative_inputs(self, *, tenant_id: UUID) -> list[InitiativeInput]:
        rows = await self._repository.list_initiatives(tenant_id=tenant_id, status=None, limit=100)
        current_metrics = await self._repository.load_cohort_snapshot_metrics(tenant_id=tenant_id)
        after = MetricSnapshot(
            readiness=float(current_metrics.get("average_readiness", 0.0)),
            forecast=float(current_metrics.get("average_forecast", 0.0)),
            cohort_health=float(current_metrics.get("average_cohort_health", 0.0)),
            risk_count=int(current_metrics.get("total_at_risk", 0)),
        )
        inputs: list[InitiativeInput] = []
        for row in rows:
            before_json = dict(row.get("before_state_json") or {})
            expected = dict(row.get("expected_outcomes_json") or {})
            inputs.append(
                InitiativeInput(
                    initiative_id=row["id"],  # type: ignore[arg-type]
                    initiative_type=str(row["initiative_type"]),
                    title=str(row["title"]),
                    status=str(row["status"]),
                    affected_students=int(row["affected_students"]),
                    affected_cohorts=tuple(str(item) for item in row.get("affected_cohorts_json") or []),
                    before=MetricSnapshot(
                        readiness=float(before_json.get("readiness", after.readiness)),
                        forecast=float(before_json.get("forecast", after.forecast)),
                        cohort_health=float(before_json.get("cohort_health", after.cohort_health)),
                        risk_count=int(before_json.get("risk_count", after.risk_count)),
                    ),
                    after=after,
                    expected_readiness_gain=float(expected.get("readiness_gain", 5.0)),
                    expected_forecast_gain=float(expected.get("forecast_gain", 3.0)),
                    expected_cohort_health_gain=float(expected.get("cohort_health_gain", 4.0)),
                    expected_risk_reduction=int(expected.get("risk_reduction", 5)),
                )
            )
        return inputs

    @staticmethod
    def _row_to_initiative(row: dict[str, object]) -> InitiativeItem:
        return InitiativeItem(
            id=row["id"],  # type: ignore[arg-type]
            initiative_type=str(row["initiative_type"]),
            title=str(row["title"]),
            status=str(row["status"]),
            start_date=row["start_date"],  # type: ignore[arg-type]
            end_date=row.get("end_date"),  # type: ignore[arg-type]
            affected_students=int(row["affected_students"]),
            affected_cohorts=list(row.get("affected_cohorts_json") or []),  # type: ignore[arg-type]
            expected_outcomes=dict(row.get("expected_outcomes_json") or {}),  # type: ignore[arg-type]
            actual_outcomes=dict(row.get("actual_outcomes_json") or {}),  # type: ignore[arg-type]
            created_at=row["created_at"],  # type: ignore[arg-type]
        )

    @staticmethod
    def _row_to_outcome(row: dict[str, object]) -> OutcomeItem:
        return OutcomeItem(
            initiative_id=row.get("initiative_id"),  # type: ignore[arg-type]
            outcome_type=str(row["outcome_type"]),
            subject_key=str(row["subject_key"]),
            before=OutcomeState(
                readiness=float(row["before_readiness"]),
                forecast=float(row["before_forecast"]),
                cohort_health=float(row["before_cohort_health"]),
                risk_count=int(row["before_risk_count"]),
            ),
            after=OutcomeState(
                readiness=float(row["after_readiness"]),
                forecast=float(row["after_forecast"]),
                cohort_health=float(row["after_cohort_health"]),
                risk_count=int(row["after_risk_count"]),
            ),
            actual_gain=float(row["actual_gain"]),
            expected_gain=float(row["expected_gain"]),
            variance=float(row["variance"]),
            readiness_gain=float(row["after_readiness"]) - float(row["before_readiness"]),
            forecast_gain=float(row["after_forecast"]) - float(row["before_forecast"]),
            cohort_health_gain=float(row["after_cohort_health"]) - float(row["before_cohort_health"]),
            risk_reduction=float(int(row["before_risk_count"]) - int(row["after_risk_count"])),
        )

    @staticmethod
    def _row_to_roi(row: dict[str, object]) -> RoiItem:
        from prepos.application.institution_outcomes.outcome_models import RoiEvidence

        evidence_rows = row.get("evidence_json") or []
        evidence = [
            RoiEvidence(label=str(item["label"]), value=str(item["value"]))  # type: ignore[index]
            for item in evidence_rows  # type: ignore[union-attr]
        ] if isinstance(evidence_rows, list) else []
        calculation = row.get("calculation_json") or {}
        metadata = dict(row.get("metadata_json") or {})
        return RoiItem(
            initiative_id=row.get("initiative_id"),  # type: ignore[arg-type]
            subject_key=str(row["subject_key"]),
            initiative_type=metadata.get("initiative_type"),  # type: ignore[arg-type]
            title=metadata.get("title"),  # type: ignore[arg-type]
            roi_score=float(row["roi_score"]),
            readiness_gain=float(row["readiness_gain"]),
            forecast_gain=float(row["forecast_gain"]),
            cohort_health_gain=float(row["cohort_health_gain"]),
            risk_reduction=float(row["risk_reduction"]),
            evidence=evidence,
            calculation=str(calculation.get("formula", "") if isinstance(calculation, dict) else ""),
        )

    @staticmethod
    def _row_to_effectiveness(row: dict[str, object]) -> InitiativeEffectivenessItem:
        metadata = dict(row.get("metadata_json") or {})
        return InitiativeEffectivenessItem(
            initiative_id=row["initiative_id"],  # type: ignore[arg-type]
            initiative_type=str(metadata.get("initiative_type", "")),
            title=str(metadata.get("title", "")),
            effectiveness_score=float(row["effectiveness_score"]),
            readiness_delta=float(row["readiness_delta"]),
            forecast_delta=float(row["forecast_delta"]),
            cohort_health_delta=float(row["cohort_health_delta"]),
            risk_reduction=int(row["risk_reduction"]),
            roi_score=float(row["roi_score"]),
            status=str(row["status"]),
        )

    @staticmethod
    def _outcome_to_row(outcome: OutcomeItem) -> dict[str, object]:
        return {
            "initiative_id": outcome.initiative_id,
            "outcome_type": outcome.outcome_type,
            "subject_key": outcome.subject_key,
            "before_readiness": outcome.before.readiness,
            "after_readiness": outcome.after.readiness,
            "before_forecast": outcome.before.forecast,
            "after_forecast": outcome.after.forecast,
            "before_cohort_health": outcome.before.cohort_health,
            "after_cohort_health": outcome.after.cohort_health,
            "before_risk_count": outcome.before.risk_count,
            "after_risk_count": outcome.after.risk_count,
            "actual_gain": outcome.actual_gain,
            "expected_gain": outcome.expected_gain,
            "variance": outcome.variance,
            "metadata_json": {},
        }

    @staticmethod
    def _roi_to_row(item: RoiItem) -> dict[str, object]:
        return {
            "initiative_id": item.initiative_id,
            "subject_key": item.subject_key,
            "roi_score": item.roi_score,
            "readiness_gain": item.readiness_gain,
            "forecast_gain": item.forecast_gain,
            "cohort_health_gain": item.cohort_health_gain,
            "risk_reduction": item.risk_reduction,
            "evidence_json": [entry.model_dump() for entry in item.evidence],
            "calculation_json": {"formula": item.calculation},
            "metadata_json": {"initiative_type": item.initiative_type, "title": item.title},
        }

    @staticmethod
    def _effectiveness_to_row(item: InitiativeEffectivenessItem) -> dict[str, object]:
        return {
            "initiative_id": item.initiative_id,
            "effectiveness_score": item.effectiveness_score,
            "readiness_delta": item.readiness_delta,
            "forecast_delta": item.forecast_delta,
            "cohort_health_delta": item.cohort_health_delta,
            "risk_reduction": item.risk_reduction,
            "roi_score": item.roi_score,
            "status": item.status,
            "evidence_json": {"initiative_type": item.initiative_type, "title": item.title},
            "calculation_json": {},
            "metadata_json": {"initiative_type": item.initiative_type, "title": item.title},
        }
