from __future__ import annotations

from contextvars import ContextVar
from datetime import UTC, datetime
from uuid import UUID

from prepos.application.twin.projection_builder import TwinProjectionBuilder
from prepos.application.twin.projection_ports import TwinProjectionRepositoryPort
from prepos.application.twin.rebuild_lock_ports import TwinRebuildLockPort
from prepos.domain.twin.projection_sections import TwinProjectionSection
from prepos.domain.twin.snapshot_entities import PreparationTwin

_session_rebuild_keys: ContextVar[set[tuple[str, str, str]] | None] = ContextVar(
    "twin_session_rebuild_keys",
    default=None,
)


def clear_twin_session_debounce() -> None:
    """Reset in-dispatch session debounce at the start of an event dispatch cycle."""
    _session_rebuild_keys.set(set())


def clear_twin_rebuild_debounce() -> None:
    """Reset all debounce state (used in tests)."""
    clear_twin_session_debounce()


def _session_keys() -> set[tuple[str, str, str]]:
    keys = _session_rebuild_keys.get()
    if keys is None:
        keys = set()
        _session_rebuild_keys.set(keys)
    return keys


class TwinRebuildService:
    """Distributed-safe incremental Twin projection orchestration."""

    def __init__(
        self,
        *,
        builder: TwinProjectionBuilder,
        lock_repo: TwinRebuildLockPort,
        projection_repo: TwinProjectionRepositoryPort,
    ) -> None:
        self._builder = builder
        self._lock_repo = lock_repo
        self._projection_repo = projection_repo

    async def request_incremental_update(
        self,
        *,
        section: TwinProjectionSection,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        correlation_id: str,
        causation_id: str | None,
        concept_id: str | None = None,
        learning_graph_row_version: int | None = None,
        current_time: datetime | None = None,
    ) -> PreparationTwin | None:
        session_key = (str(tenant_id), str(student_id), exam_id)
        if session_key in _session_keys():
            await self._projection_repo.record_projection_metric(
                tenant_id,
                student_id,
                exam_id,
                skipped_rebuild_count=1,
            )
            return None

        acquired = await self._lock_repo.try_acquire_lock(
            tenant_id,
            student_id,
            exam_id,
            correlation_id=correlation_id,
        )
        if not acquired:
            await self._projection_repo.record_projection_metric(
                tenant_id,
                student_id,
                exam_id,
                lock_contention_count=1,
            )
            return None

        _session_keys().add(session_key)
        result = await self._builder.apply_incremental_update(
            section=section,
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
            correlation_id=correlation_id,
            causation_id=causation_id,
            concept_id=concept_id,
            learning_graph_row_version=learning_graph_row_version,
            current_time=current_time or datetime.now(UTC),
        )
        if result is None:
            return None

        await self._projection_repo.record_projection_metric(
            tenant_id,
            student_id,
            exam_id,
            rebuild_count=1,
            incremental_update_count=1,
        )
        return result

    async def request_rebuild(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        correlation_id: str,
        causation_id: str | None,
        current_time: datetime | None = None,
    ) -> PreparationTwin | None:
        now = current_time or datetime.now(UTC)
        session_key = (str(tenant_id), str(student_id), exam_id)
        if session_key in _session_keys():
            await self._projection_repo.record_projection_metric(
                tenant_id,
                student_id,
                exam_id,
                skipped_rebuild_count=1,
            )
            return None

        acquired = await self._lock_repo.try_acquire_lock(
            tenant_id,
            student_id,
            exam_id,
            correlation_id=correlation_id,
        )
        if not acquired:
            await self._projection_repo.record_projection_metric(
                tenant_id,
                student_id,
                exam_id,
                lock_contention_count=1,
            )
            return None

        _session_keys().add(session_key)
        sections = (
            TwinProjectionSection.READINESS,
            TwinProjectionSection.RECOMMENDATIONS,
            TwinProjectionSection.QUEUE,
            TwinProjectionSection.STUDY_PLAN,
            TwinProjectionSection.FORECAST,
            TwinProjectionSection.PREDICTED_SCORE,
            TwinProjectionSection.MILESTONES,
            TwinProjectionSection.FORECAST_PROBABILITY,
            TwinProjectionSection.DECISION,
            TwinProjectionSection.INTERVENTION,
            TwinProjectionSection.INTERVENTION_OUTCOME,
            TwinProjectionSection.BEHAVIOR_PROFILE,
            TwinProjectionSection.PERSONALIZATION,
            TwinProjectionSection.MENTOR,
            TwinProjectionSection.MENTOR_ACTION,
            TwinProjectionSection.MENTOR_CASE,
            TwinProjectionSection.MENTOR_EFFECTIVENESS,
        )
        last: PreparationTwin | None = None
        for section in sections:
            updated = await self._builder.apply_incremental_update(
                section=section,
                tenant_id=tenant_id,
                student_id=student_id,
                exam_id=exam_id,
                correlation_id=correlation_id,
                causation_id=causation_id,
                current_time=now,
            )
            if updated is not None:
                last = updated

        if last is not None:
            await self._projection_repo.record_projection_metric(
                tenant_id,
                student_id,
                exam_id,
                rebuild_count=1,
                incremental_update_count=len(sections),
            )
        return last
