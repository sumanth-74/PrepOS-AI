from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, cast
from uuid import UUID

from sqlalchemy import and_, func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from prepos.application.learning_graph.ports import LearningGraphReadRepositoryPort, LearningGraphRepositoryPort
from prepos.domain.learning_graph.entities import (
    ConceptProgressNode,
    LearningGraphEvent,
    ScoreAuditLog,
    StudentGraphSummary,
)
from prepos.domain.learning_graph.exceptions import OptimisticLockFailureError
from prepos.domain.learning_graph.policies import NodeStatus
from prepos.infrastructure.db.models.learning_graph import (
    LearningGraphEventModel,
    ScoreAuditLogModel,
    StudentConceptProgressModel,
)
from prepos.infrastructure.db.models.student import LearningGraphProvisionModel, StudentModel


def _weighted_average(numerator: object, denominator: object) -> Decimal | None:
    if numerator is None or denominator is None:
        return None
    den = Decimal(str(denominator))
    if den == 0:
        return None
    return (Decimal(str(numerator)) / den).quantize(Decimal("0.01"))


def _map_node(row: StudentConceptProgressModel) -> ConceptProgressNode:
    return ConceptProgressNode(
        id=row.id,
        tenant_id=row.tenant_id,
        student_id=row.student_id,
        exam_id=row.exam_id,
        catalog_version=row.catalog_version,
        concept_id=row.concept_id,
        subject_id=row.subject_id,
        topic_id=row.topic_id,
        mastery_score=row.mastery_score,
        mastery_nonmcq_score=row.mastery_nonmcq_score,
        retention_score=row.retention_score,
        retention_stability_s=row.retention_stability_s,
        retention_last_event_at=row.retention_last_event_at,
        retention_last_review_at=row.retention_last_review_at,
        retention_last_grade=row.retention_last_grade,
        confidence_score=row.confidence_score,
        importance_score=row.importance_score,
        overconfidence_flag=row.overconfidence_flag,
        mcq_attempt_count=row.mcq_attempt_count,
        mcq_correct_count=row.mcq_correct_count,
        nonmcq_attempt_count=row.nonmcq_attempt_count,
        revision_count=row.revision_count,
        study_minutes=row.study_minutes,
        node_state=row.node_state,
        mastery_version=row.mastery_version,
        mastery_nonmcq_version=row.mastery_nonmcq_version,
        retention_version=row.retention_version,
        confidence_version=row.confidence_version,
        importance_version=row.importance_version,
        first_seen_at=row.first_seen_at,
        last_activity_at=row.last_activity_at,
        row_version=row.row_version,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class SqlAlchemyLearningGraphRepository(LearningGraphRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_node(
        self,
        tenant_id: UUID,
        student_id: UUID,
        concept_id: str,
    ) -> ConceptProgressNode | None:
        result = await self._session.execute(
            select(StudentConceptProgressModel).where(
                StudentConceptProgressModel.tenant_id == tenant_id,
                StudentConceptProgressModel.student_id == student_id,
                StudentConceptProgressModel.concept_id == concept_id,
            )
        )
        row = result.scalar_one_or_none()
        return _map_node(row) if row else None

    async def save_node(self, node: ConceptProgressNode, *, expected_row_version: int) -> ConceptProgressNode:
        stmt = (
            update(StudentConceptProgressModel)
            .where(
                StudentConceptProgressModel.id == node.id,
                StudentConceptProgressModel.tenant_id == node.tenant_id,
                StudentConceptProgressModel.row_version == expected_row_version,
            )
            .values(
                mastery_score=node.mastery_score,
                mastery_nonmcq_score=node.mastery_nonmcq_score,
                retention_score=node.retention_score,
                retention_stability_s=node.retention_stability_s,
                retention_last_event_at=node.retention_last_event_at,
                retention_last_review_at=node.retention_last_review_at,
                retention_last_grade=node.retention_last_grade,
                confidence_score=node.confidence_score,
                importance_score=node.importance_score,
                overconfidence_flag=node.overconfidence_flag,
                mcq_attempt_count=node.mcq_attempt_count,
                mcq_correct_count=node.mcq_correct_count,
                nonmcq_attempt_count=node.nonmcq_attempt_count,
                revision_count=node.revision_count,
                study_minutes=node.study_minutes,
                node_state=node.node_state,
                mastery_version=node.mastery_version,
                mastery_nonmcq_version=node.mastery_nonmcq_version,
                retention_version=node.retention_version,
                confidence_version=node.confidence_version,
                importance_version=node.importance_version,
                last_activity_at=node.last_activity_at,
                row_version=expected_row_version + 1,
                updated_at=datetime.now(UTC),
            )
            .returning(StudentConceptProgressModel)
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            raise OptimisticLockFailureError(
                "Concurrent graph update conflict.",
                details={
                    "node_id": str(node.id),
                    "expected_row_version": expected_row_version,
                },
            )
        return _map_node(row)

    async def bulk_insert_nodes(self, nodes: tuple[ConceptProgressNode, ...]) -> int:
        if not nodes:
            return 0
        rows = [
            {
                "id": node.id,
                "tenant_id": node.tenant_id,
                "student_id": node.student_id,
                "exam_id": node.exam_id,
                "catalog_version": node.catalog_version,
                "concept_id": node.concept_id,
                "subject_id": node.subject_id,
                "topic_id": node.topic_id,
                "mastery_score": node.mastery_score,
                "mastery_nonmcq_score": node.mastery_nonmcq_score,
                "retention_score": node.retention_score,
                "retention_stability_s": node.retention_stability_s,
                "retention_last_event_at": node.retention_last_event_at,
                "retention_last_review_at": node.retention_last_review_at,
                "retention_last_grade": node.retention_last_grade,
                "confidence_score": node.confidence_score,
                "importance_score": node.importance_score,
                "overconfidence_flag": node.overconfidence_flag,
                "mcq_attempt_count": node.mcq_attempt_count,
                "mcq_correct_count": node.mcq_correct_count,
                "nonmcq_attempt_count": node.nonmcq_attempt_count,
                "revision_count": node.revision_count,
                "study_minutes": node.study_minutes,
                "node_state": node.node_state,
                "mastery_version": node.mastery_version,
                "mastery_nonmcq_version": node.mastery_nonmcq_version,
                "retention_version": node.retention_version,
                "confidence_version": node.confidence_version,
                "importance_version": node.importance_version,
                "first_seen_at": node.first_seen_at,
                "last_activity_at": node.last_activity_at,
                "row_version": node.row_version,
            }
            for node in nodes
        ]
        stmt = insert(StudentConceptProgressModel).values(rows)
        stmt = stmt.on_conflict_do_nothing(
            index_elements=["tenant_id", "student_id", "concept_id"],
        )
        result = cast(CursorResult[Any], await self._session.execute(stmt))
        return int(result.rowcount or 0)

    async def count_nodes(self, tenant_id: UUID, student_id: UUID) -> int:
        stmt = (
            select(func.count())
            .select_from(StudentConceptProgressModel)
            .where(
                StudentConceptProgressModel.tenant_id == tenant_id,
                StudentConceptProgressModel.student_id == student_id,
            )
        )
        return int((await self._session.execute(stmt)).scalar_one())

    async def append_graph_event(self, event: LearningGraphEvent) -> None:
        self._session.add(
            LearningGraphEventModel(
                id=event.id,
                tenant_id=event.tenant_id,
                student_id=event.student_id,
                concept_id=event.concept_id,
                event_type=event.event_type,
                event_payload=event.event_payload,
                causation_id=event.causation_id,
                correlation_id=event.correlation_id,
                event_version=event.event_version,
                occurred_at=event.occurred_at,
                recorded_at=event.recorded_at,
                scoring_versions=event.scoring_versions,
                created_at=event.created_at,
            )
        )
        await self._session.flush()

    async def append_score_audit(self, entry: ScoreAuditLog) -> None:
        self._session.add(
            ScoreAuditLogModel(
                id=entry.id,
                tenant_id=entry.tenant_id,
                student_id=entry.student_id,
                concept_id=entry.concept_id,
                score_type=entry.score_type,
                previous_value=entry.previous_value,
                new_value=entry.new_value,
                reason=entry.reason,
                causation_id=entry.causation_id,
                created_at=entry.created_at,
            )
        )
        await self._session.flush()

    async def update_provision_count(
        self,
        tenant_id: UUID,
        student_id: UUID,
        *,
        provisioned_node_count: int,
        status: str,
    ) -> None:
        await self._session.execute(
            update(LearningGraphProvisionModel)
            .where(
                LearningGraphProvisionModel.tenant_id == tenant_id,
                LearningGraphProvisionModel.student_id == student_id,
            )
            .values(
                provisioned_node_count=provisioned_node_count,
                status=status,
                updated_at=datetime.now(UTC),
            )
        )


class SqlAlchemyLearningGraphReadRepository(LearningGraphReadRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_nodes(
        self,
        tenant_id: UUID,
        student_id: UUID,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[ConceptProgressNode, ...]:
        result = await self._session.execute(
            select(StudentConceptProgressModel)
            .where(
                StudentConceptProgressModel.tenant_id == tenant_id,
                StudentConceptProgressModel.student_id == student_id,
            )
            .order_by(StudentConceptProgressModel.concept_id.asc())
            .offset(offset)
            .limit(limit)
        )
        return tuple(_map_node(row) for row in result.scalars().all())

    async def get_summary(self, tenant_id: UUID, student_id: UUID) -> StudentGraphSummary | None:
        rated = StudentConceptProgressModel.node_state == NodeStatus.RATED
        has_confidence = and_(rated, StudentConceptProgressModel.confidence_score.is_not(None))

        mastery_numerator = func.sum(
            StudentConceptProgressModel.mastery_score * StudentConceptProgressModel.importance_score
        ).filter(rated)
        mastery_denominator = func.sum(StudentConceptProgressModel.importance_score).filter(rated)
        confidence_numerator = func.sum(
            StudentConceptProgressModel.confidence_score * StudentConceptProgressModel.importance_score
        ).filter(has_confidence)
        confidence_denominator = func.sum(StudentConceptProgressModel.importance_score).filter(has_confidence)

        agg = await self._session.execute(
            select(
                func.count(StudentConceptProgressModel.id),
                func.count().filter(rated),
                mastery_numerator,
                mastery_denominator,
                confidence_numerator,
                confidence_denominator,
                func.max(StudentConceptProgressModel.exam_id),
            ).where(
                StudentConceptProgressModel.tenant_id == tenant_id,
                StudentConceptProgressModel.student_id == student_id,
            )
        )
        row = agg.one()
        total = int(row[0])
        if total == 0:
            return None
        weakest_result = await self._session.execute(
            select(StudentConceptProgressModel.concept_id)
            .where(
                StudentConceptProgressModel.tenant_id == tenant_id,
                StudentConceptProgressModel.student_id == student_id,
            )
            .order_by(StudentConceptProgressModel.mastery_score.asc())
            .limit(5)
        )
        exam_id = str(row[6])
        return StudentGraphSummary(
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
            total_nodes=total,
            active_nodes=int(row[1]),
            average_mastery=_weighted_average(row[2], row[3]),
            average_retention=None,
            average_confidence=_weighted_average(row[4], row[5]),
            weakest_concept_ids=tuple(weakest_result.scalars().all()),
        )

    async def list_rated_nodes(
        self,
        tenant_id: UUID,
        student_id: UUID,
    ) -> tuple[ConceptProgressNode, ...]:
        result = await self._session.execute(
            select(StudentConceptProgressModel)
            .where(
                StudentConceptProgressModel.tenant_id == tenant_id,
                StudentConceptProgressModel.student_id == student_id,
                StudentConceptProgressModel.node_state == NodeStatus.RATED,
            )
            .order_by(StudentConceptProgressModel.concept_id.asc())
        )
        return tuple(_map_node(row) for row in result.scalars().all())

    async def list_weakest_nodes(
        self,
        tenant_id: UUID,
        student_id: UUID,
        *,
        limit: int = 10,
    ) -> tuple[ConceptProgressNode, ...]:
        result = await self._session.execute(
            select(StudentConceptProgressModel)
            .where(
                StudentConceptProgressModel.tenant_id == tenant_id,
                StudentConceptProgressModel.student_id == student_id,
                StudentConceptProgressModel.node_state == NodeStatus.RATED,
            )
            .order_by(StudentConceptProgressModel.mastery_score.asc())
            .limit(limit)
        )
        return tuple(_map_node(row) for row in result.scalars().all())

    async def get_student_exam(self, tenant_id: UUID, student_id: UUID) -> tuple[str, str] | None:
        result = await self._session.execute(
            select(StudentModel.target_exam_id, LearningGraphProvisionModel.catalog_version)
            .join(
                LearningGraphProvisionModel,
                (LearningGraphProvisionModel.student_id == StudentModel.id)
                & (LearningGraphProvisionModel.tenant_id == StudentModel.tenant_id),
            )
            .where(StudentModel.tenant_id == tenant_id, StudentModel.id == student_id)
        )
        row = result.one_or_none()
        if row is None or row[0] is None:
            return None
        return str(row[0]), str(row[1])

    async def get_provision(
        self,
        tenant_id: UUID,
        student_id: UUID,
    ) -> tuple[int, int, str] | None:
        result = await self._session.execute(
            select(
                LearningGraphProvisionModel.expected_node_count,
                LearningGraphProvisionModel.provisioned_node_count,
                LearningGraphProvisionModel.status,
            ).where(
                LearningGraphProvisionModel.tenant_id == tenant_id,
                LearningGraphProvisionModel.student_id == student_id,
            )
        )
        row = result.one_or_none()
        if row is None:
            return None
        return int(row[0]), int(row[1]), str(row[2])
