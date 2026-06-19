from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from prepos.application.twin.projection_ports import TwinProjectionRepositoryPort
from prepos.application.twin.snapshot_ports import TwinSnapshotRepositoryPort
from prepos.domain.twin.profile_versions import TWIN_PROFILE_V1
from prepos.domain.twin.projection_metrics import TwinProjectionMetrics
from prepos.domain.twin.snapshot_entities import PreparationTwin
from prepos.infrastructure.db.models.student import PreparationTwinModel


def _stored_row_version(versions: dict[str, object], concept_id: str) -> int:
    raw = versions.get(concept_id, 0)
    if isinstance(raw, int):
        return raw
    if isinstance(raw, str) and raw.isdigit():
        return int(raw)
    return 0


def _max_row_version(node_versions: dict[str, object]) -> int | None:
    if not node_versions:
        return None
    return max(_stored_row_version(node_versions, concept_id) for concept_id in node_versions)


def _map_projection(row: PreparationTwinModel) -> PreparationTwin:
    return PreparationTwin(
        id=row.id,
        tenant_id=row.tenant_id,
        student_id=row.student_id,
        exam_id=row.exam_id,
        profile_version=row.profile_version or TWIN_PROFILE_V1,
        readiness_score=row.readiness_score,
        average_mastery=row.average_mastery,
        average_retention=row.average_retention,
        average_confidence=row.average_confidence,
        rated_node_count=row.rated_node_count or 0,
        due_revision_count=row.due_revision_count or 0,
        high_risk_concept_count=row.high_risk_concept_count or 0,
        largest_positive_driver=row.largest_positive_driver,
        largest_negative_driver=row.largest_negative_driver,
        recommendation_count=row.recommendation_count or 0,
        last_recommendation_at=row.last_recommendation_at,
        twin_payload=row.twin_payload or {},
        generated_at=row.generated_at or row.last_rebuilt_at,
        projection_revision=row.projection_revision or 0,
        last_learning_graph_version=row.last_learning_graph_version,
        rebuild_count=row.rebuild_count or 0,
        skipped_rebuild_count=row.skipped_rebuild_count or 0,
        incremental_update_count=row.incremental_update_count or 0,
        lock_contention_count=row.lock_contention_count or 0,
        decision_type=row.decision_type,
        decision_score=row.decision_score,
        expected_readiness_gain=row.expected_readiness_gain,
        expected_score_gain=row.expected_score_gain,
        intervention_type=row.intervention_type,
        intervention_score=row.intervention_score,
        intervention_urgency=row.intervention_urgency,
        learning_style=row.learning_style,
        risk_profile=row.risk_profile,
        consistency_score=row.consistency_score,
        discipline_score=row.discipline_score,
        engagement_score=row.engagement_score,
        best_activity_type=row.best_activity_type,
        top_multiplier=row.top_multiplier,
        historical_effectiveness=row.historical_effectiveness,
        mentor_status=row.mentor_status,
        top_mentor_message=row.top_mentor_message,
        mentor_action_type=row.mentor_action_type,
        mentor_action_priority=row.mentor_action_priority,
        escalation_level=row.escalation_level,
        active_case_status=row.active_case_status,
        active_case_priority=row.active_case_priority,
    )


def _empty_projection_shell(
    *,
    twin_id: UUID,
    tenant_id: UUID,
    student_id: UUID,
    exam_id: str,
    now: datetime,
) -> PreparationTwin:
    return PreparationTwin(
        id=twin_id,
        tenant_id=tenant_id,
        student_id=student_id,
        exam_id=exam_id,
        profile_version=TWIN_PROFILE_V1,
        readiness_score=None,
        average_mastery=None,
        average_retention=None,
        average_confidence=None,
        rated_node_count=0,
        due_revision_count=0,
        high_risk_concept_count=0,
        largest_positive_driver=None,
        largest_negative_driver=None,
        recommendation_count=0,
        last_recommendation_at=None,
        twin_payload={"profile_version": TWIN_PROFILE_V1},
        generated_at=now,
    )


class SqlAlchemyTwinProjectionRepository(TwinProjectionRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def resolve_twin_id(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
    ) -> UUID | None:
        result = await self._session.execute(
            select(PreparationTwinModel.id).where(
                PreparationTwinModel.tenant_id == tenant_id,
                PreparationTwinModel.student_id == student_id,
                PreparationTwinModel.exam_id == exam_id,
            )
        )
        return result.scalar_one_or_none()

    async def _get_model(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
    ) -> PreparationTwinModel | None:
        result = await self._session.execute(
            select(PreparationTwinModel).where(
                PreparationTwinModel.tenant_id == tenant_id,
                PreparationTwinModel.student_id == student_id,
                PreparationTwinModel.exam_id == exam_id,
            )
        )
        return result.scalar_one_or_none()

    async def upsert_projection(self, twin: PreparationTwin) -> PreparationTwin:
        return await self.persist_partial_projection(
            twin,
            increment_revision=True,
        )

    async def is_stale_learning_graph_event(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        concept_id: str,
        row_version: int,
    ) -> bool:
        row = await self._get_model(tenant_id, student_id, exam_id)
        if row is None:
            return False
        versions = dict(row.learning_graph_node_versions or {})
        stored_version = _stored_row_version(versions, concept_id)
        return row_version <= stored_version

    async def persist_partial_projection(
        self,
        twin: PreparationTwin,
        *,
        learning_graph_node_version: tuple[str, int] | None = None,
        increment_revision: bool = True,
    ) -> PreparationTwin:
        now = datetime.now(UTC)
        existing = await self._get_model(twin.tenant_id, twin.student_id, twin.exam_id)
        node_versions = dict(existing.learning_graph_node_versions or {}) if existing else {}
        projection_revision = existing.projection_revision if existing else 0
        if increment_revision:
            projection_revision += 1

        if learning_graph_node_version is not None:
            concept_id, row_version = learning_graph_node_version
            node_versions[concept_id] = row_version

        last_learning_graph_version = _max_row_version(node_versions)

        metrics = {
            "rebuild_count": twin.rebuild_count,
            "skipped_rebuild_count": twin.skipped_rebuild_count,
            "incremental_update_count": twin.incremental_update_count,
            "lock_contention_count": twin.lock_contention_count,
        }
        if existing is not None:
            metrics = {
                "rebuild_count": max(existing.rebuild_count, twin.rebuild_count),
                "skipped_rebuild_count": max(existing.skipped_rebuild_count, twin.skipped_rebuild_count),
                "incremental_update_count": max(existing.incremental_update_count, twin.incremental_update_count),
                "lock_contention_count": max(existing.lock_contention_count, twin.lock_contention_count),
            }

        stmt = insert(PreparationTwinModel).values(
            id=twin.id,
            tenant_id=twin.tenant_id,
            student_id=twin.student_id,
            exam_id=twin.exam_id,
            status="active",
            academic_profile={},
            behavioral_profile={},
            prediction_profile={},
            metadata_json={},
            projection_version="twin_projection_v1",
            row_version=1,
            last_rebuilt_at=now,
            profile_version=twin.profile_version,
            readiness_score=twin.readiness_score,
            average_mastery=twin.average_mastery,
            average_retention=twin.average_retention,
            average_confidence=twin.average_confidence,
            rated_node_count=twin.rated_node_count,
            due_revision_count=twin.due_revision_count,
            high_risk_concept_count=twin.high_risk_concept_count,
            largest_positive_driver=twin.largest_positive_driver,
            largest_negative_driver=twin.largest_negative_driver,
            recommendation_count=twin.recommendation_count,
            last_recommendation_at=twin.last_recommendation_at,
            twin_payload=twin.twin_payload,
            generated_at=twin.generated_at,
            last_learning_graph_version=last_learning_graph_version,
            learning_graph_node_versions=node_versions,
            projection_revision=projection_revision,
            rebuild_count=metrics["rebuild_count"],
            skipped_rebuild_count=metrics["skipped_rebuild_count"],
            incremental_update_count=metrics["incremental_update_count"],
            lock_contention_count=metrics["lock_contention_count"],
            decision_type=twin.decision_type,
            decision_score=twin.decision_score,
            expected_readiness_gain=twin.expected_readiness_gain,
            expected_score_gain=twin.expected_score_gain,
            intervention_type=twin.intervention_type,
            intervention_score=twin.intervention_score,
            intervention_urgency=twin.intervention_urgency,
            learning_style=twin.learning_style,
            risk_profile=twin.risk_profile,
            consistency_score=twin.consistency_score,
            discipline_score=twin.discipline_score,
            engagement_score=twin.engagement_score,
            best_activity_type=twin.best_activity_type,
            top_multiplier=twin.top_multiplier,
            historical_effectiveness=twin.historical_effectiveness,
            mentor_status=twin.mentor_status,
            top_mentor_message=twin.top_mentor_message,
            mentor_action_type=twin.mentor_action_type,
            mentor_action_priority=twin.mentor_action_priority,
            escalation_level=twin.escalation_level,
            active_case_status=twin.active_case_status,
            active_case_priority=twin.active_case_priority,
            created_at=now,
            updated_at=now,
        )
        upsert_stmt = stmt.on_conflict_do_update(
            index_elements=["tenant_id", "student_id", "exam_id"],
            set_={
                "profile_version": twin.profile_version,
                "readiness_score": twin.readiness_score,
                "average_mastery": twin.average_mastery,
                "average_retention": twin.average_retention,
                "average_confidence": twin.average_confidence,
                "rated_node_count": twin.rated_node_count,
                "due_revision_count": twin.due_revision_count,
                "high_risk_concept_count": twin.high_risk_concept_count,
                "largest_positive_driver": twin.largest_positive_driver,
                "largest_negative_driver": twin.largest_negative_driver,
                "recommendation_count": twin.recommendation_count,
                "last_recommendation_at": twin.last_recommendation_at,
                "twin_payload": twin.twin_payload,
                "generated_at": twin.generated_at,
                "last_rebuilt_at": twin.generated_at,
                "last_learning_graph_version": last_learning_graph_version,
                "learning_graph_node_versions": node_versions,
                "projection_revision": projection_revision,
                "rebuild_count": metrics["rebuild_count"],
                "skipped_rebuild_count": metrics["skipped_rebuild_count"],
                "incremental_update_count": metrics["incremental_update_count"],
                "lock_contention_count": metrics["lock_contention_count"],
                "decision_type": twin.decision_type,
                "decision_score": twin.decision_score,
                "expected_readiness_gain": twin.expected_readiness_gain,
                "expected_score_gain": twin.expected_score_gain,
                "intervention_type": twin.intervention_type,
                "intervention_score": twin.intervention_score,
                "intervention_urgency": twin.intervention_urgency,
                "learning_style": twin.learning_style,
                "risk_profile": twin.risk_profile,
                "consistency_score": twin.consistency_score,
                "discipline_score": twin.discipline_score,
                "engagement_score": twin.engagement_score,
                "best_activity_type": twin.best_activity_type,
                "top_multiplier": twin.top_multiplier,
                "historical_effectiveness": twin.historical_effectiveness,
                "mentor_status": twin.mentor_status,
                "top_mentor_message": twin.top_mentor_message,
                "mentor_action_type": twin.mentor_action_type,
                "mentor_action_priority": twin.mentor_action_priority,
                "escalation_level": twin.escalation_level,
                "active_case_status": twin.active_case_status,
                "active_case_priority": twin.active_case_priority,
                "updated_at": now,
            },
        ).returning(PreparationTwinModel)
        result = await self._session.execute(upsert_stmt)
        return _map_projection(result.scalar_one())

    async def record_projection_metric(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        *,
        rebuild_count: int = 0,
        skipped_rebuild_count: int = 0,
        incremental_update_count: int = 0,
        lock_contention_count: int = 0,
    ) -> None:
        row = await self._get_model(tenant_id, student_id, exam_id)
        if row is None:
            shell = _empty_projection_shell(
                twin_id=uuid4(),
                tenant_id=tenant_id,
                student_id=student_id,
                exam_id=exam_id,
                now=datetime.now(UTC),
            )
            shell = replace(
                shell,
                rebuild_count=rebuild_count,
                skipped_rebuild_count=skipped_rebuild_count,
                incremental_update_count=incremental_update_count,
                lock_contention_count=lock_contention_count,
            )
            await self.persist_partial_projection(shell, increment_revision=False)
            return

        row.rebuild_count += rebuild_count
        row.skipped_rebuild_count += skipped_rebuild_count
        row.incremental_update_count += incremental_update_count
        row.lock_contention_count += lock_contention_count
        await self._session.flush()

    async def get_projection_metrics(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
    ) -> TwinProjectionMetrics | None:
        row = await self._get_model(tenant_id, student_id, exam_id)
        if row is None:
            return None
        return TwinProjectionMetrics(
            rebuild_count=row.rebuild_count,
            skipped_rebuild_count=row.skipped_rebuild_count,
            incremental_update_count=row.incremental_update_count,
            lock_contention_count=row.lock_contention_count,
        )

    async def get_projection(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
    ) -> PreparationTwin | None:
        row = await self._get_model(tenant_id, student_id, exam_id)
        if row is None or row.generated_at is None:
            return None
        return _map_projection(row)

    async def get_projection_for_student(
        self,
        tenant_id: UUID,
        student_id: UUID,
    ) -> PreparationTwin | None:
        result = await self._session.execute(
            select(PreparationTwinModel)
            .where(
                PreparationTwinModel.tenant_id == tenant_id,
                PreparationTwinModel.student_id == student_id,
            )
            .order_by(PreparationTwinModel.generated_at.desc().nullslast())
            .limit(1)
        )
        row = result.scalar_one_or_none()
        if row is None or row.generated_at is None:
            return None
        return _map_projection(row)


class SqlAlchemyTwinSnapshotRepository(TwinSnapshotRepositoryPort):
    """Backward-compatible read adapter delegating to the canonical projection repository."""

    def __init__(self, session: AsyncSession) -> None:
        self._projection_repo = SqlAlchemyTwinProjectionRepository(session)

    async def upsert_snapshot(self, snapshot: PreparationTwin) -> PreparationTwin:
        return await self._projection_repo.upsert_projection(snapshot)

    async def get_snapshot(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
    ) -> PreparationTwin | None:
        return await self._projection_repo.get_projection(tenant_id, student_id, exam_id)

    async def get_snapshot_for_student(
        self,
        tenant_id: UUID,
        student_id: UUID,
    ) -> PreparationTwin | None:
        return await self._projection_repo.get_projection_for_student(tenant_id, student_id)

    async def resolve_twin_id(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
    ) -> UUID | None:
        return await self._projection_repo.resolve_twin_id(tenant_id, student_id, exam_id)
