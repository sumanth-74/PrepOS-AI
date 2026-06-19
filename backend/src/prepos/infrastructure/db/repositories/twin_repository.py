from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from prepos.application.twin.ports import TwinRecommendationRepositoryPort
from prepos.application.twin.projection_ports import RecommendationSummary
from prepos.domain.twin.entities import PersistedTwinRecommendation, TwinRecommendation
from prepos.infrastructure.db.models.twin import PreparationTwinRecommendationModel


class SqlAlchemyTwinRecommendationRepository(TwinRecommendationRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def replace_recommendations(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        recommendations: tuple[TwinRecommendation, ...],
    ) -> tuple[PersistedTwinRecommendation, ...]:
        await self._session.execute(
            delete(PreparationTwinRecommendationModel).where(
                PreparationTwinRecommendationModel.tenant_id == tenant_id,
                PreparationTwinRecommendationModel.student_id == student_id,
                PreparationTwinRecommendationModel.exam_id == exam_id,
            )
        )
        now = datetime.now(UTC)
        persisted: list[PersistedTwinRecommendation] = []
        for recommendation in recommendations:
            row_id = uuid4()
            self._session.add(
                PreparationTwinRecommendationModel(
                    id=row_id,
                    tenant_id=tenant_id,
                    student_id=student_id,
                    exam_id=exam_id,
                    concept_id=recommendation.concept_id,
                    recommendation_type=recommendation.recommendation_type,
                    recommendation_score=recommendation.recommendation_score,
                    readiness_gain=recommendation.readiness_gain,
                    created_at=now,
                )
            )
            persisted.append(
                PersistedTwinRecommendation(
                    id=row_id,
                    tenant_id=tenant_id,
                    student_id=student_id,
                    exam_id=exam_id,
                    concept_id=recommendation.concept_id,
                    recommendation_type=recommendation.recommendation_type,
                    recommendation_score=recommendation.recommendation_score,
                    readiness_gain=recommendation.readiness_gain,
                    created_at=now,
                )
            )
        await self._session.flush()
        return tuple(persisted)

    async def upsert_recommendation(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        recommendation: TwinRecommendation,
    ) -> PersistedTwinRecommendation:
        now = datetime.now(UTC)
        row_id = uuid4()
        stmt = insert(PreparationTwinRecommendationModel).values(
            id=row_id,
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
            concept_id=recommendation.concept_id,
            recommendation_type=recommendation.recommendation_type,
            recommendation_score=recommendation.recommendation_score,
            readiness_gain=recommendation.readiness_gain,
            created_at=now,
        )
        upsert = stmt.on_conflict_do_update(
            index_elements=["tenant_id", "student_id", "exam_id", "concept_id"],
            set_={
                "recommendation_type": recommendation.recommendation_type,
                "recommendation_score": recommendation.recommendation_score,
                "readiness_gain": recommendation.readiness_gain,
                "created_at": now,
            },
        ).returning(PreparationTwinRecommendationModel)
        result = await self._session.execute(upsert)
        row = result.scalar_one()
        return PersistedTwinRecommendation(
            id=row.id,
            tenant_id=row.tenant_id,
            student_id=row.student_id,
            exam_id=row.exam_id,
            concept_id=row.concept_id,
            recommendation_type=row.recommendation_type,
            recommendation_score=row.recommendation_score,
            readiness_gain=row.readiness_gain,
            created_at=row.created_at,
        )

    async def delete_recommendation(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        concept_id: str,
    ) -> bool:
        result = await self._session.execute(
            delete(PreparationTwinRecommendationModel).where(
                PreparationTwinRecommendationModel.tenant_id == tenant_id,
                PreparationTwinRecommendationModel.student_id == student_id,
                PreparationTwinRecommendationModel.exam_id == exam_id,
                PreparationTwinRecommendationModel.concept_id == concept_id,
            )
        )
        deleted = int(getattr(result, "rowcount", 0) or 0)
        return deleted > 0

    async def list_recommendations(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        *,
        limit: int = 20,
    ) -> tuple[PersistedTwinRecommendation, ...]:
        stmt = (
            select(PreparationTwinRecommendationModel)
            .where(
                PreparationTwinRecommendationModel.tenant_id == tenant_id,
                PreparationTwinRecommendationModel.student_id == student_id,
                PreparationTwinRecommendationModel.exam_id == exam_id,
            )
            .order_by(
                PreparationTwinRecommendationModel.readiness_gain.desc(),
                PreparationTwinRecommendationModel.recommendation_score.desc(),
                PreparationTwinRecommendationModel.concept_id.asc(),
            )
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return tuple(
            PersistedTwinRecommendation(
                id=row.id,
                tenant_id=row.tenant_id,
                student_id=row.student_id,
                exam_id=row.exam_id,
                concept_id=row.concept_id,
                recommendation_type=row.recommendation_type,
                recommendation_score=row.recommendation_score,
                readiness_gain=row.readiness_gain,
                created_at=row.created_at,
            )
            for row in result.scalars().all()
        )

    async def get_recommendation_summary(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        *,
        top_limit: int = 10,
    ) -> RecommendationSummary:
        count_stmt = select(func.count()).select_from(PreparationTwinRecommendationModel).where(
            PreparationTwinRecommendationModel.tenant_id == tenant_id,
            PreparationTwinRecommendationModel.student_id == student_id,
            PreparationTwinRecommendationModel.exam_id == exam_id,
        )
        count_result = await self._session.execute(count_stmt)
        recommendation_count = int(count_result.scalar_one())

        last_stmt = select(func.max(PreparationTwinRecommendationModel.created_at)).where(
            PreparationTwinRecommendationModel.tenant_id == tenant_id,
            PreparationTwinRecommendationModel.student_id == student_id,
            PreparationTwinRecommendationModel.exam_id == exam_id,
        )
        last_result = await self._session.execute(last_stmt)
        last_recommendation_at = last_result.scalar_one_or_none()

        top_recommendations = await self.list_recommendations(
            tenant_id,
            student_id,
            exam_id,
            limit=top_limit,
        )
        return RecommendationSummary(
            recommendation_count=recommendation_count,
            last_recommendation_at=last_recommendation_at,
            top_recommendations=top_recommendations,
        )
