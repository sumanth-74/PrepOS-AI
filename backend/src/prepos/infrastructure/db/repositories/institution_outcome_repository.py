from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from prepos.application.institution_outcomes.ports import InstitutionOutcomeRepositoryPort
from prepos.infrastructure.db.models.cohort_intelligence import CohortSnapshotModel
from prepos.infrastructure.db.models.institution_intelligence import InstitutionEventModel
from prepos.infrastructure.db.models.institution_outcomes import (
    InstitutionInitiativeEffectivenessModel,
    InstitutionInitiativeModel,
    InstitutionOutcomeModel,
    InstitutionRoiMetricModel,
)


class SqlAlchemyInstitutionOutcomeRepository(InstitutionOutcomeRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def load_cohort_snapshot_metrics(self, *, tenant_id: UUID) -> dict[str, object]:
        stmt = (
            select(CohortSnapshotModel)
            .where(CohortSnapshotModel.tenant_id == tenant_id)
            .order_by(CohortSnapshotModel.created_at.desc())
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        if not rows:
            return {
                "average_readiness": 0.0,
                "average_forecast": 0.0,
                "average_cohort_health": 0.0,
                "total_at_risk": 0,
            }

        latest_by_cohort: dict[str, CohortSnapshotModel] = {}
        for row in rows:
            if row.cohort_id not in latest_by_cohort:
                latest_by_cohort[row.cohort_id] = row

        cohort_rows = list(latest_by_cohort.values())
        readiness_values = [float(row.avg_readiness) for row in cohort_rows]
        forecast_values = [float(row.avg_forecast) for row in cohort_rows]
        health_values = [
            float(dict(row.metadata_json).get("cohort_health_score", 0.0)) for row in cohort_rows
        ]
        total_at_risk = sum(row.risk_count for row in cohort_rows)
        return {
            "average_readiness": round(sum(readiness_values) / len(readiness_values), 2),
            "average_forecast": round(sum(forecast_values) / len(forecast_values), 2),
            "average_cohort_health": round(sum(health_values) / len(health_values), 2),
            "total_at_risk": total_at_risk,
        }

    async def create_initiative(
        self,
        *,
        tenant_id: UUID,
        payload: dict[str, object],
        now: datetime,
    ) -> dict[str, object]:
        initiative_id = uuid4()
        model = InstitutionInitiativeModel(
            id=initiative_id,
            tenant_id=tenant_id,
            initiative_type=str(payload["initiative_type"]),
            title=str(payload["title"]),
            status=str(payload["status"]),
            start_date=payload["start_date"],  # type: ignore[arg-type]
            end_date=payload.get("end_date"),  # type: ignore[arg-type]
            affected_students=int(payload["affected_students"]),
            affected_cohorts_json=list(payload.get("affected_cohorts_json") or []),  # type: ignore[arg-type]
            expected_outcomes_json=dict(payload.get("expected_outcomes_json") or {}),
            actual_outcomes_json=dict(payload.get("actual_outcomes_json") or {}),
            before_state_json=dict(payload.get("before_state_json") or {}),
            metadata_json=dict(payload.get("metadata_json") or {}),
            created_at=now,
            updated_at=now,
        )
        self._session.add(model)
        await self._session.flush()
        return self._initiative_to_dict(model)

    async def list_initiatives(
        self,
        *,
        tenant_id: UUID,
        status: str | None,
        limit: int,
    ) -> list[dict[str, object]]:
        stmt = select(InstitutionInitiativeModel).where(InstitutionInitiativeModel.tenant_id == tenant_id)
        if status:
            stmt = stmt.where(InstitutionInitiativeModel.status == status)
        stmt = stmt.order_by(InstitutionInitiativeModel.created_at.desc()).limit(limit)
        rows = (await self._session.execute(stmt)).scalars().all()
        return [self._initiative_to_dict(row) for row in rows]

    async def get_initiative(
        self,
        *,
        tenant_id: UUID,
        initiative_id: UUID,
    ) -> dict[str, object] | None:
        stmt = select(InstitutionInitiativeModel).where(
            InstitutionInitiativeModel.tenant_id == tenant_id,
            InstitutionInitiativeModel.id == initiative_id,
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return self._initiative_to_dict(row) if row else None

    async def update_initiative_outcomes(
        self,
        *,
        tenant_id: UUID,
        initiative_id: UUID,
        actual_outcomes: dict[str, object],
        now: datetime,
    ) -> None:
        stmt = select(InstitutionInitiativeModel).where(
            InstitutionInitiativeModel.tenant_id == tenant_id,
            InstitutionInitiativeModel.id == initiative_id,
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        if row is None:
            return
        row.actual_outcomes_json = actual_outcomes
        row.updated_at = now
        await self._session.flush()

    async def save_outcomes(
        self,
        *,
        tenant_id: UUID,
        outcomes: list[dict[str, object]],
        now: datetime,
    ) -> None:
        for outcome in outcomes:
            self._session.add(
                InstitutionOutcomeModel(
                    id=uuid4(),
                    tenant_id=tenant_id,
                    initiative_id=outcome.get("initiative_id"),  # type: ignore[arg-type]
                    outcome_type=str(outcome["outcome_type"]),
                    subject_key=str(outcome["subject_key"]),
                    before_readiness=outcome["before_readiness"],  # type: ignore[arg-type]
                    after_readiness=outcome["after_readiness"],  # type: ignore[arg-type]
                    before_forecast=outcome["before_forecast"],  # type: ignore[arg-type]
                    after_forecast=outcome["after_forecast"],  # type: ignore[arg-type]
                    before_cohort_health=outcome["before_cohort_health"],  # type: ignore[arg-type]
                    after_cohort_health=outcome["after_cohort_health"],  # type: ignore[arg-type]
                    before_risk_count=int(outcome["before_risk_count"]),
                    after_risk_count=int(outcome["after_risk_count"]),
                    actual_gain=outcome["actual_gain"],  # type: ignore[arg-type]
                    expected_gain=outcome["expected_gain"],  # type: ignore[arg-type]
                    variance=outcome["variance"],  # type: ignore[arg-type]
                    metadata_json=dict(outcome.get("metadata_json") or {}),
                    created_at=now,
                )
            )
        await self._session.flush()

    async def save_roi_metrics(
        self,
        *,
        tenant_id: UUID,
        metrics: list[dict[str, object]],
        now: datetime,
    ) -> None:
        for metric in metrics:
            self._session.add(
                InstitutionRoiMetricModel(
                    id=uuid4(),
                    tenant_id=tenant_id,
                    initiative_id=metric.get("initiative_id"),  # type: ignore[arg-type]
                    subject_key=str(metric["subject_key"]),
                    roi_score=metric["roi_score"],  # type: ignore[arg-type]
                    readiness_gain=metric["readiness_gain"],  # type: ignore[arg-type]
                    forecast_gain=metric["forecast_gain"],  # type: ignore[arg-type]
                    cohort_health_gain=metric["cohort_health_gain"],  # type: ignore[arg-type]
                    risk_reduction=metric["risk_reduction"],  # type: ignore[arg-type]
                    evidence_json=list(metric.get("evidence_json") or []),  # type: ignore[arg-type]
                    calculation_json=dict(metric.get("calculation_json") or {}),
                    created_at=now,
                )
            )
        await self._session.flush()

    async def save_effectiveness(
        self,
        *,
        tenant_id: UUID,
        rows: list[dict[str, object]],
        now: datetime,
    ) -> None:
        for row in rows:
            self._session.add(
                InstitutionInitiativeEffectivenessModel(
                    id=uuid4(),
                    tenant_id=tenant_id,
                    initiative_id=row["initiative_id"],  # type: ignore[arg-type]
                    effectiveness_score=row["effectiveness_score"],  # type: ignore[arg-type]
                    readiness_delta=row["readiness_delta"],  # type: ignore[arg-type]
                    forecast_delta=row["forecast_delta"],  # type: ignore[arg-type]
                    cohort_health_delta=row["cohort_health_delta"],  # type: ignore[arg-type]
                    risk_reduction=int(row["risk_reduction"]),
                    roi_score=row["roi_score"],  # type: ignore[arg-type]
                    status=str(row["status"]),
                    evidence_json=dict(row.get("evidence_json") or {}),
                    calculation_json=dict(row.get("calculation_json") or {}),
                    measured_at=now,
                )
            )
        await self._session.flush()

    async def list_outcomes(
        self,
        *,
        tenant_id: UUID,
        limit: int,
    ) -> list[dict[str, object]]:
        stmt = (
            select(InstitutionOutcomeModel)
            .where(InstitutionOutcomeModel.tenant_id == tenant_id)
            .order_by(InstitutionOutcomeModel.created_at.desc())
            .limit(limit)
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [self._outcome_to_dict(row) for row in rows]

    async def list_roi_metrics(
        self,
        *,
        tenant_id: UUID,
        limit: int,
    ) -> list[dict[str, object]]:
        stmt = (
            select(InstitutionRoiMetricModel, InstitutionInitiativeModel)
            .outerjoin(
                InstitutionInitiativeModel,
                InstitutionInitiativeModel.id == InstitutionRoiMetricModel.initiative_id,
            )
            .where(InstitutionRoiMetricModel.tenant_id == tenant_id)
            .order_by(InstitutionRoiMetricModel.roi_score.desc())
            .limit(limit)
        )
        rows = (await self._session.execute(stmt)).all()
        result: list[dict[str, object]] = []
        for roi_row, initiative in rows:
            payload = self._roi_to_dict(roi_row)
            payload["metadata_json"] = {
                "initiative_type": initiative.initiative_type if initiative else None,
                "title": initiative.title if initiative else None,
            }
            result.append(payload)
        return result

    async def list_effectiveness(
        self,
        *,
        tenant_id: UUID,
        limit: int,
    ) -> list[dict[str, object]]:
        stmt = (
            select(InstitutionInitiativeEffectivenessModel, InstitutionInitiativeModel)
            .join(
                InstitutionInitiativeModel,
                InstitutionInitiativeModel.id == InstitutionInitiativeEffectivenessModel.initiative_id,
            )
            .where(InstitutionInitiativeEffectivenessModel.tenant_id == tenant_id)
            .order_by(InstitutionInitiativeEffectivenessModel.effectiveness_score.desc())
            .limit(limit)
        )
        rows = (await self._session.execute(stmt)).all()
        result: list[dict[str, object]] = []
        for effectiveness, initiative in rows:
            payload = self._effectiveness_to_dict(effectiveness)
            payload["metadata_json"] = {
                "initiative_type": initiative.initiative_type,
                "title": initiative.title,
            }
            result.append(payload)
        return result

    async def record_event(
        self,
        *,
        tenant_id: UUID,
        event_type: str,
        metadata_json: dict[str, object],
        now: datetime,
    ) -> UUID:
        event_id = uuid4()
        self._session.add(
            InstitutionEventModel(
                id=event_id,
                tenant_id=tenant_id,
                event_type=event_type,
                metadata_json=metadata_json,
                created_at=now,
            )
        )
        await self._session.flush()
        return event_id

    async def export_roi_rows(self, *, tenant_id: UUID, limit: int) -> list[dict[str, object]]:
        stmt = (
            select(InstitutionRoiMetricModel, InstitutionInitiativeModel)
            .outerjoin(
                InstitutionInitiativeModel,
                InstitutionInitiativeModel.id == InstitutionRoiMetricModel.initiative_id,
            )
            .where(InstitutionRoiMetricModel.tenant_id == tenant_id)
            .order_by(InstitutionRoiMetricModel.roi_score.desc())
            .limit(limit)
        )
        rows = (await self._session.execute(stmt)).all()
        result: list[dict[str, object]] = []
        for roi_row, initiative in rows:
            result.append(
                {
                    "subject_key": roi_row.subject_key,
                    "initiative_type": initiative.initiative_type if initiative else "",
                    "title": initiative.title if initiative else "",
                    "roi_score": float(roi_row.roi_score),
                    "readiness_gain": float(roi_row.readiness_gain),
                    "forecast_gain": float(roi_row.forecast_gain),
                    "cohort_health_gain": float(roi_row.cohort_health_gain),
                    "risk_reduction": float(roi_row.risk_reduction),
                    "created_at": roi_row.created_at.isoformat(),
                }
            )
        return result

    @staticmethod
    def _initiative_to_dict(row: InstitutionInitiativeModel) -> dict[str, object]:
        return {
            "id": row.id,
            "initiative_type": row.initiative_type,
            "title": row.title,
            "status": row.status,
            "start_date": row.start_date,
            "end_date": row.end_date,
            "affected_students": row.affected_students,
            "affected_cohorts_json": list(row.affected_cohorts_json),
            "expected_outcomes_json": dict(row.expected_outcomes_json),
            "actual_outcomes_json": dict(row.actual_outcomes_json),
            "before_state_json": dict(row.before_state_json),
            "metadata_json": dict(row.metadata_json),
            "created_at": row.created_at,
            "updated_at": row.updated_at,
        }

    @staticmethod
    def _outcome_to_dict(row: InstitutionOutcomeModel) -> dict[str, object]:
        return {
            "initiative_id": row.initiative_id,
            "outcome_type": row.outcome_type,
            "subject_key": row.subject_key,
            "before_readiness": float(row.before_readiness),
            "after_readiness": float(row.after_readiness),
            "before_forecast": float(row.before_forecast),
            "after_forecast": float(row.after_forecast),
            "before_cohort_health": float(row.before_cohort_health),
            "after_cohort_health": float(row.after_cohort_health),
            "before_risk_count": row.before_risk_count,
            "after_risk_count": row.after_risk_count,
            "actual_gain": float(row.actual_gain),
            "expected_gain": float(row.expected_gain),
            "variance": float(row.variance),
            "metadata_json": dict(row.metadata_json),
            "created_at": row.created_at,
        }

    @staticmethod
    def _roi_to_dict(row: InstitutionRoiMetricModel) -> dict[str, object]:
        return {
            "initiative_id": row.initiative_id,
            "subject_key": row.subject_key,
            "roi_score": float(row.roi_score),
            "readiness_gain": float(row.readiness_gain),
            "forecast_gain": float(row.forecast_gain),
            "cohort_health_gain": float(row.cohort_health_gain),
            "risk_reduction": float(row.risk_reduction),
            "evidence_json": list(row.evidence_json) if isinstance(row.evidence_json, list) else row.evidence_json,
            "calculation_json": dict(row.calculation_json),
            "metadata_json": {},
            "created_at": row.created_at,
        }

    @staticmethod
    def _effectiveness_to_dict(row: InstitutionInitiativeEffectivenessModel) -> dict[str, object]:
        return {
            "initiative_id": row.initiative_id,
            "effectiveness_score": float(row.effectiveness_score),
            "readiness_delta": float(row.readiness_delta),
            "forecast_delta": float(row.forecast_delta),
            "cohort_health_delta": float(row.cohort_health_delta),
            "risk_reduction": row.risk_reduction,
            "roi_score": float(row.roi_score),
            "status": row.status,
            "evidence_json": dict(row.evidence_json),
            "calculation_json": dict(row.calculation_json),
            "metadata_json": {},
            "measured_at": row.measured_at,
        }
