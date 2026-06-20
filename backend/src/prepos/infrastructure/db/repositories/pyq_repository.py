from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from prepos.application.pyq.ports import (
    CreatePyqQuestionInput,
    PyqMappingRecord,
    PyqQuestionRecord,
    PyqRepositoryPort,
    PyqStatisticRecord,
)
from prepos.infrastructure.db.models.pyq import PyqMappingModel, PyqQuestionModel, PyqStatisticModel


class SqlAlchemyPyqRepository(PyqRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_questions_batch(
        self,
        *,
        tenant_id: UUID | None,
        exam_id: str,
        questions: list[CreatePyqQuestionInput],
    ) -> list[PyqQuestionRecord]:
        now = datetime.now(UTC)
        created: list[PyqQuestionRecord] = []
        for question in questions:
            question_id = uuid4()
            model = PyqQuestionModel(
                id=question_id,
                tenant_id=tenant_id,
                exam_id=exam_id,
                year=question.year,
                exam_stage=question.exam_stage,
                paper=question.paper,
                question_text=question.question_text,
                answer_text=question.answer_text,
                source_reference=question.source_reference,
                difficulty=question.difficulty,
                importance=question.importance,
                knowledge_source_id=question.knowledge_source_id,
                knowledge_chunk_id=question.knowledge_chunk_id,
                metadata_json=question.metadata_json,
                created_at=now,
                updated_at=now,
            )
            self._session.add(model)
            mapping_models: list[PyqMappingModel] = []
            for concept_id in question.concept_ids:
                mapping_models.append(
                    PyqMappingModel(
                        id=uuid4(),
                        pyq_id=question_id,
                        concept_id=concept_id,
                        confidence_score=question.confidence_score,
                        created_at=now,
                    )
                )
            self._session.add_all(mapping_models)
            await self._session.flush()
            created.append(_to_question_record(model, concept_ids=question.concept_ids))
        return created

    async def get_question_by_id(
        self,
        question_id: UUID,
        *,
        tenant_id: UUID | None,
    ) -> PyqQuestionRecord | None:
        stmt = select(PyqQuestionModel).where(PyqQuestionModel.id == question_id)
        if tenant_id is not None:
            stmt = stmt.where(
                or_(PyqQuestionModel.tenant_id.is_(None), PyqQuestionModel.tenant_id == tenant_id)
            )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        concept_ids = await self._list_concept_ids(model.id)
        return _to_question_record(model, concept_ids=concept_ids)

    async def list_questions(
        self,
        *,
        tenant_id: UUID | None,
        exam_id: str | None = None,
        year_from: int | None = None,
        year_to: int | None = None,
        paper: str | None = None,
        exam_stage: str | None = None,
        concept_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[PyqQuestionRecord]:
        stmt = select(PyqQuestionModel)
        if tenant_id is not None:
            stmt = stmt.where(
                or_(PyqQuestionModel.tenant_id.is_(None), PyqQuestionModel.tenant_id == tenant_id)
            )
        if exam_id is not None:
            stmt = stmt.where(PyqQuestionModel.exam_id == exam_id)
        if year_from is not None:
            stmt = stmt.where(PyqQuestionModel.year >= year_from)
        if year_to is not None:
            stmt = stmt.where(PyqQuestionModel.year <= year_to)
        if paper is not None:
            stmt = stmt.where(func.lower(PyqQuestionModel.paper) == paper.lower())
        if exam_stage is not None:
            stmt = stmt.where(func.lower(PyqQuestionModel.exam_stage) == exam_stage.lower())
        if concept_id is not None:
            stmt = stmt.join(PyqMappingModel, PyqMappingModel.pyq_id == PyqQuestionModel.id).where(
                PyqMappingModel.concept_id == concept_id
            )
        stmt = stmt.order_by(PyqQuestionModel.year.desc(), PyqQuestionModel.created_at.desc())
        stmt = stmt.offset(offset).limit(limit)
        result = await self._session.execute(stmt)
        records: list[PyqQuestionRecord] = []
        for model in result.scalars().unique().all():
            concept_ids = await self._list_concept_ids(model.id)
            records.append(_to_question_record(model, concept_ids=concept_ids))
        return records

    async def list_mapping_hits(
        self,
        *,
        tenant_id: UUID | None,
        exam_id: str,
    ) -> list[tuple[str, int, float]]:
        stmt = (
            select(
                PyqMappingModel.concept_id,
                PyqQuestionModel.year,
                PyqMappingModel.confidence_score,
            )
            .join(PyqQuestionModel, PyqQuestionModel.id == PyqMappingModel.pyq_id)
            .where(PyqQuestionModel.exam_id == exam_id)
        )
        if tenant_id is not None:
            stmt = stmt.where(
                or_(PyqQuestionModel.tenant_id.is_(None), PyqQuestionModel.tenant_id == tenant_id)
            )
        result = await self._session.execute(stmt)
        return [
            (str(row.concept_id), int(row.year), float(row.confidence_score)) for row in result.all()
        ]

    async def replace_statistics(
        self,
        *,
        exam_id: str,
        statistics: list[PyqStatisticRecord],
    ) -> None:
        await self._session.execute(delete(PyqStatisticModel).where(PyqStatisticModel.exam_id == exam_id))
        for stat in statistics:
            self._session.add(
                PyqStatisticModel(
                    exam_id=stat.exam_id,
                    concept_id=stat.concept_id,
                    pyq_count=stat.pyq_count,
                    first_appearance_year=stat.first_appearance_year,
                    last_appearance_year=stat.last_appearance_year,
                    frequency_score=stat.frequency_score,
                    trend_score=stat.trend_score,
                    updated_at=stat.updated_at,
                )
            )
        await self._session.flush()

    async def list_statistics(
        self,
        *,
        exam_id: str,
        limit: int = 50,
    ) -> list[PyqStatisticRecord]:
        stmt = (
            select(PyqStatisticModel)
            .where(PyqStatisticModel.exam_id == exam_id)
            .order_by(PyqStatisticModel.frequency_score.desc(), PyqStatisticModel.pyq_count.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return [_to_statistic_record(row) for row in result.scalars()]

    async def list_mappings_for_review(
        self,
        *,
        tenant_id: UUID | None,
        exam_id: str | None = None,
        limit: int = 50,
    ) -> list[tuple[PyqQuestionRecord, list[PyqMappingRecord]]]:
        questions = await self.list_questions(
            tenant_id=tenant_id,
            exam_id=exam_id,
            limit=limit,
        )
        review: list[tuple[PyqQuestionRecord, list[PyqMappingRecord]]] = []
        for question in questions:
            stmt = select(PyqMappingModel).where(PyqMappingModel.pyq_id == question.id)
            result = await self._session.execute(stmt)
            mappings = [_to_mapping_record(row) for row in result.scalars()]
            review.append((question, mappings))
        return review

    async def count_questions(
        self,
        *,
        tenant_id: UUID | None,
        exam_id: str | None = None,
    ) -> int:
        stmt = select(func.count(PyqQuestionModel.id))
        if tenant_id is not None:
            stmt = stmt.where(
                or_(PyqQuestionModel.tenant_id.is_(None), PyqQuestionModel.tenant_id == tenant_id)
            )
        if exam_id is not None:
            stmt = stmt.where(PyqQuestionModel.exam_id == exam_id)
        result = await self._session.execute(stmt)
        return int(result.scalar_one())

    async def _list_concept_ids(self, pyq_id: UUID) -> tuple[str, ...]:
        stmt = select(PyqMappingModel.concept_id).where(PyqMappingModel.pyq_id == pyq_id)
        result = await self._session.execute(stmt)
        return tuple(str(row) for row in result.scalars())


def _to_question_record(model: PyqQuestionModel, *, concept_ids: tuple[str, ...]) -> PyqQuestionRecord:
    return PyqQuestionRecord(
        id=model.id,
        tenant_id=model.tenant_id,
        exam_id=model.exam_id,
        year=model.year,
        exam_stage=model.exam_stage,
        paper=model.paper,
        question_text=model.question_text,
        answer_text=model.answer_text,
        source_reference=model.source_reference,
        difficulty=model.difficulty,
        importance=model.importance,
        knowledge_source_id=model.knowledge_source_id,
        knowledge_chunk_id=model.knowledge_chunk_id,
        concept_ids=concept_ids,
        metadata_json=dict(model.metadata_json or {}),
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _to_mapping_record(model: PyqMappingModel) -> PyqMappingRecord:
    return PyqMappingRecord(
        id=model.id,
        pyq_id=model.pyq_id,
        concept_id=model.concept_id,
        confidence_score=float(model.confidence_score),
        created_at=model.created_at,
    )


def _to_statistic_record(model: PyqStatisticModel) -> PyqStatisticRecord:
    return PyqStatisticRecord(
        exam_id=model.exam_id,
        concept_id=model.concept_id,
        pyq_count=model.pyq_count,
        first_appearance_year=model.first_appearance_year,
        last_appearance_year=model.last_appearance_year,
        frequency_score=float(model.frequency_score),
        trend_score=float(model.trend_score),
        updated_at=model.updated_at,
    )
