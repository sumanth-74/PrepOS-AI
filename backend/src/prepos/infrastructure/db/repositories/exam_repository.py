from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from prepos.application.exam.ports import (
    CatalogVersionRepositoryPort,
    ConceptRelationshipRepositoryPort,
    ConceptRepositoryPort,
    ExamCatalogUnitOfWorkPort,
    ExamRepositoryPort,
    SubjectRepositoryPort,
    TopicRepositoryPort,
)
from prepos.domain.exam.entities import (
    CatalogVersion,
    Concept,
    ConceptRelationship,
    Exam,
    ExamTrack,
    Subject,
    Topic,
)
from prepos.domain.exam.value_objects import (
    CatalogStatus,
    CatalogVersionStatus,
    ConceptType,
    ExamType,
    RelationshipSourceType,
    RelationshipTargetType,
    RelationshipType,
    TrackCode,
)
from prepos.infrastructure.db.models.exam import (
    CatalogVersionModel,
    ConceptModel,
    ConceptRelationshipModel,
    ExamModel,
    ExamTrackModel,
    SubjectModel,
    TopicModel,
)


def _map_exam(row: ExamModel) -> Exam:
    return Exam(
        exam_id=row.exam_id,
        exam_code=row.exam_code,
        exam_name=row.exam_name,
        exam_type=ExamType(row.exam_type),
        prelims_weight=row.prelims_weight,
        mains_weight=row.mains_weight,
        interview_weight=row.interview_weight,
        domain_catalog_version=row.domain_catalog_version,
        status=CatalogStatus(row.status),
        essay_included=row.essay_included,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _map_track(row: ExamTrackModel) -> ExamTrack:
    return ExamTrack(
        track_id=row.track_id,
        exam_id=row.exam_id,
        track_code=TrackCode(row.track_code),
        track_name=row.track_name,
        stage=row.stage,
        subject_ids=tuple(row.subject_ids),
        sort_order=row.sort_order,
        status=CatalogStatus(row.status),
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _map_subject(row: SubjectModel) -> Subject:
    return Subject(
        subject_id=row.subject_id,
        exam_id=row.exam_id,
        subject_name=row.subject_name,
        subject_slug=row.subject_slug,
        prelims_applicable=row.prelims_applicable,
        mains_applicable=row.mains_applicable,
        sort_order=row.sort_order,
        status=CatalogStatus(row.status),
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _map_topic(row: TopicModel) -> Topic:
    return Topic(
        topic_id=row.topic_id,
        exam_id=row.exam_id,
        subject_id=row.subject_id,
        topic_name=row.topic_name,
        topic_slug=row.topic_slug,
        prelims_relevance=row.prelims_relevance,
        mains_relevance=row.mains_relevance,
        sort_order=row.sort_order,
        status=CatalogStatus(row.status),
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _map_concept(row: ConceptModel) -> Concept:
    return Concept(
        concept_id=row.concept_id,
        exam_id=row.exam_id,
        subject_id=row.subject_id,
        topic_id=row.topic_id,
        concept_name=row.concept_name,
        concept_slug=row.concept_slug,
        concept_type=ConceptType(row.concept_type),
        prelims_relevance=row.prelims_relevance,
        mains_relevance=row.mains_relevance,
        current_affairs_linkable=row.current_affairs_linkable,
        pyq_mappable=row.pyq_mappable,
        status=CatalogStatus(row.status),
        domain_catalog_version=row.domain_catalog_version,
        parent_concept_id=row.parent_concept_id,
        interview_relevance=row.interview_relevance,
        difficulty=row.difficulty,
        importance=row.importance,
        importance_version=row.importance_version,
        pyq_count=row.pyq_count,
        exam_stages=tuple(row.exam_stages),
        tags=tuple(row.tags),
        metadata=dict(row.metadata_json),
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _map_relationship(row: ConceptRelationshipModel) -> ConceptRelationship:
    return ConceptRelationship(
        id=row.id,
        exam_id=row.exam_id,
        source_id=row.source_id,
        source_type=RelationshipSourceType(row.source_type),
        target_id=row.target_id,
        target_type=RelationshipTargetType(row.target_type),
        relationship_type=RelationshipType(row.relationship_type),
        weight=row.weight,
        status=CatalogStatus(row.status),
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _map_catalog_version(row: CatalogVersionModel) -> CatalogVersion:
    return CatalogVersion(
        id=row.id,
        exam_id=row.exam_id,
        version=row.version,
        status=CatalogVersionStatus(row.status),
        published_at=row.published_at,
        published_by=row.published_by,
        concepts_added=row.concepts_added,
        concepts_deprecated=row.concepts_deprecated,
        change_summary=row.change_summary,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class SqlAlchemyExamRepository(ExamRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_exam(self, exam_id: str) -> Exam | None:
        row = await self._session.get(ExamModel, exam_id)
        return _map_exam(row) if row else None

    async def get_exam_by_code(self, exam_code: str) -> Exam | None:
        result = await self._session.execute(select(ExamModel).where(ExamModel.exam_code == exam_code))
        row = result.scalar_one_or_none()
        return _map_exam(row) if row else None

    async def list_exams(self, *, status: str | None = None) -> tuple[Exam, ...]:
        stmt = select(ExamModel).order_by(ExamModel.exam_name)
        if status:
            stmt = stmt.where(ExamModel.status == status)
        result = await self._session.execute(stmt)
        return tuple(_map_exam(row) for row in result.scalars().all())

    async def save_exam(self, exam: Exam) -> Exam:
        row = await self._session.get(ExamModel, exam.exam_id)
        if row is None:
            row = ExamModel(
                exam_id=exam.exam_id,
                exam_code=exam.exam_code,
                exam_name=exam.exam_name,
                exam_type=exam.exam_type.value,
                prelims_weight=exam.prelims_weight,
                mains_weight=exam.mains_weight,
                interview_weight=exam.interview_weight,
                domain_catalog_version=exam.domain_catalog_version,
                essay_included=exam.essay_included,
                status=exam.status.value,
            )
            self._session.add(row)
        else:
            row.exam_name = exam.exam_name
            row.domain_catalog_version = exam.domain_catalog_version
            row.status = exam.status.value
        await self._session.flush()
        return _map_exam(row)

    async def save_tracks(self, tracks: tuple[ExamTrack, ...]) -> None:
        for track in tracks:
            stmt = insert(ExamTrackModel).values(
                track_id=track.track_id,
                exam_id=track.exam_id,
                track_code=track.track_code.value,
                track_name=track.track_name,
                stage=track.stage,
                subject_ids=list(track.subject_ids),
                sort_order=track.sort_order,
                status=track.status.value,
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=[ExamTrackModel.track_id],
                set_={
                    "track_name": track.track_name,
                    "stage": track.stage,
                    "subject_ids": list(track.subject_ids),
                    "sort_order": track.sort_order,
                    "status": track.status.value,
                },
            )
            await self._session.execute(stmt)
        await self._session.flush()

    async def list_tracks(self, exam_id: str) -> tuple[ExamTrack, ...]:
        result = await self._session.execute(
            select(ExamTrackModel)
            .where(ExamTrackModel.exam_id == exam_id)
            .order_by(ExamTrackModel.sort_order)
        )
        return tuple(_map_track(row) for row in result.scalars().all())


class SqlAlchemySubjectRepository(SubjectRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_subjects(self, exam_id: str, *, status: str | None = None) -> tuple[Subject, ...]:
        stmt = select(SubjectModel).where(SubjectModel.exam_id == exam_id).order_by(SubjectModel.sort_order)
        if status:
            stmt = stmt.where(SubjectModel.status == status)
        result = await self._session.execute(stmt)
        return tuple(_map_subject(row) for row in result.scalars().all())

    async def save_subjects(self, subjects: tuple[Subject, ...]) -> None:
        for subject in subjects:
            stmt = insert(SubjectModel).values(
                subject_id=subject.subject_id,
                exam_id=subject.exam_id,
                subject_name=subject.subject_name,
                subject_slug=subject.subject_slug,
                prelims_applicable=subject.prelims_applicable,
                mains_applicable=subject.mains_applicable,
                sort_order=subject.sort_order,
                status=subject.status.value,
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=[SubjectModel.subject_id],
                set_={
                    "subject_name": subject.subject_name,
                    "prelims_applicable": subject.prelims_applicable,
                    "mains_applicable": subject.mains_applicable,
                    "sort_order": subject.sort_order,
                    "status": subject.status.value,
                },
            )
            await self._session.execute(stmt)
        await self._session.flush()


class SqlAlchemyTopicRepository(TopicRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_topics(
        self,
        exam_id: str,
        *,
        subject_id: str | None = None,
        status: str | None = None,
    ) -> tuple[Topic, ...]:
        stmt = select(TopicModel).where(TopicModel.exam_id == exam_id).order_by(TopicModel.sort_order)
        if subject_id:
            stmt = stmt.where(TopicModel.subject_id == subject_id)
        if status:
            stmt = stmt.where(TopicModel.status == status)
        result = await self._session.execute(stmt)
        return tuple(_map_topic(row) for row in result.scalars().all())

    async def get_topic(self, topic_id: str) -> Topic | None:
        row = await self._session.get(TopicModel, topic_id)
        return _map_topic(row) if row else None

    async def save_topics(self, topics: tuple[Topic, ...]) -> None:
        for topic in topics:
            stmt = insert(TopicModel).values(
                topic_id=topic.topic_id,
                exam_id=topic.exam_id,
                subject_id=topic.subject_id,
                topic_name=topic.topic_name,
                topic_slug=topic.topic_slug,
                prelims_relevance=topic.prelims_relevance,
                mains_relevance=topic.mains_relevance,
                sort_order=topic.sort_order,
                status=topic.status.value,
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=[TopicModel.topic_id],
                set_={
                    "topic_name": topic.topic_name,
                    "prelims_relevance": topic.prelims_relevance,
                    "mains_relevance": topic.mains_relevance,
                    "sort_order": topic.sort_order,
                    "status": topic.status.value,
                },
            )
            await self._session.execute(stmt)
        await self._session.flush()


class SqlAlchemyConceptRepository(ConceptRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_concept(self, concept_id: str) -> Concept | None:
        row = await self._session.get(ConceptModel, concept_id)
        return _map_concept(row) if row else None

    async def list_concepts_by_topic(self, topic_id: str, *, status: str | None = None) -> tuple[Concept, ...]:
        stmt = select(ConceptModel).where(ConceptModel.topic_id == topic_id).order_by(ConceptModel.concept_name)
        if status:
            stmt = stmt.where(ConceptModel.status == status)
        result = await self._session.execute(stmt)
        return tuple(_map_concept(row) for row in result.scalars().all())

    async def list_concepts_by_exam(
        self,
        exam_id: str,
        *,
        status: str | None = None,
        catalog_version: str | None = None,
    ) -> tuple[Concept, ...]:
        stmt = select(ConceptModel).where(ConceptModel.exam_id == exam_id)
        if status:
            stmt = stmt.where(ConceptModel.status == status)
        if catalog_version:
            stmt = stmt.where(ConceptModel.domain_catalog_version == catalog_version)
        result = await self._session.execute(stmt)
        return tuple(_map_concept(row) for row in result.scalars().all())

    async def list_children(self, parent_concept_id: str) -> tuple[Concept, ...]:
        result = await self._session.execute(
            select(ConceptModel)
            .where(ConceptModel.parent_concept_id == parent_concept_id)
            .order_by(ConceptModel.concept_name)
        )
        return tuple(_map_concept(row) for row in result.scalars().all())

    async def search_concepts(
        self,
        *,
        exam_id: str,
        query: str | None = None,
        subject_id: str | None = None,
        topic_id: str | None = None,
        status: str | None = "active",
        catalog_version: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[tuple[Concept, ...], int]:
        filters = [ConceptModel.exam_id == exam_id]
        if status:
            filters.append(ConceptModel.status == status)
        if subject_id:
            filters.append(ConceptModel.subject_id == subject_id)
        if topic_id:
            filters.append(ConceptModel.topic_id == topic_id)
        if catalog_version:
            filters.append(ConceptModel.domain_catalog_version == catalog_version)
        if query:
            pattern = f"%{query.strip()}%"
            filters.append(
                or_(
                    ConceptModel.concept_name.ilike(pattern),
                    ConceptModel.concept_id.ilike(pattern),
                    ConceptModel.concept_slug.ilike(pattern),
                )
            )

        count_stmt = select(func.count()).select_from(ConceptModel).where(*filters)
        total = int((await self._session.execute(count_stmt)).scalar_one())

        stmt = (
            select(ConceptModel)
            .where(*filters)
            .order_by(ConceptModel.concept_name)
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return tuple(_map_concept(row) for row in result.scalars().all()), total

    async def save_concepts(self, concepts: tuple[Concept, ...]) -> None:
        for concept in concepts:
            stmt = insert(ConceptModel).values(
                concept_id=concept.concept_id,
                exam_id=concept.exam_id,
                subject_id=concept.subject_id,
                topic_id=concept.topic_id,
                parent_concept_id=concept.parent_concept_id,
                concept_name=concept.concept_name,
                concept_slug=concept.concept_slug,
                concept_type=concept.concept_type.value,
                prelims_relevance=concept.prelims_relevance,
                mains_relevance=concept.mains_relevance,
                interview_relevance=concept.interview_relevance,
                difficulty=concept.difficulty,
                importance=concept.importance,
                importance_version=concept.importance_version,
                current_affairs_linkable=concept.current_affairs_linkable,
                pyq_mappable=concept.pyq_mappable,
                pyq_count=concept.pyq_count,
                exam_stages=list(concept.exam_stages),
                tags=list(concept.tags),
                metadata_json=concept.metadata,
                status=concept.status.value,
                domain_catalog_version=concept.domain_catalog_version,
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=[ConceptModel.concept_id],
                set_={
                    "concept_name": concept.concept_name,
                    "concept_type": concept.concept_type.value,
                    "prelims_relevance": concept.prelims_relevance,
                    "mains_relevance": concept.mains_relevance,
                    "parent_concept_id": concept.parent_concept_id,
                    "current_affairs_linkable": concept.current_affairs_linkable,
                    "pyq_mappable": concept.pyq_mappable,
                    "exam_stages": list(concept.exam_stages),
                    "tags": list(concept.tags),
                    "metadata_json": concept.metadata,
                    "status": concept.status.value,
                    "domain_catalog_version": concept.domain_catalog_version,
                },
            )
            await self._session.execute(stmt)
        await self._session.flush()

    async def count_active_by_exam(self, exam_id: str) -> int:
        stmt = (
            select(func.count())
            .select_from(ConceptModel)
            .where(ConceptModel.exam_id == exam_id, ConceptModel.status == CatalogStatus.ACTIVE.value)
        )
        return int((await self._session.execute(stmt)).scalar_one())


class SqlAlchemyConceptRelationshipRepository(ConceptRelationshipRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_exam(self, exam_id: str, *, status: str | None = None) -> tuple[ConceptRelationship, ...]:
        stmt = select(ConceptRelationshipModel).where(ConceptRelationshipModel.exam_id == exam_id)
        if status:
            stmt = stmt.where(ConceptRelationshipModel.status == status)
        result = await self._session.execute(stmt)
        return tuple(_map_relationship(row) for row in result.scalars().all())

    async def list_prerequisites_for_concept(self, concept_id: str) -> tuple[ConceptRelationship, ...]:
        result = await self._session.execute(
            select(ConceptRelationshipModel).where(
                ConceptRelationshipModel.source_id == concept_id,
                ConceptRelationshipModel.relationship_type == RelationshipType.PREREQUISITE.value,
                ConceptRelationshipModel.status == CatalogStatus.ACTIVE.value,
            )
        )
        return tuple(_map_relationship(row) for row in result.scalars().all())

    async def save_relationships(self, relationships: tuple[ConceptRelationship, ...]) -> None:
        for rel in relationships:
            stmt = insert(ConceptRelationshipModel).values(
                id=rel.id,
                exam_id=rel.exam_id,
                source_id=rel.source_id,
                source_type=rel.source_type.value,
                target_id=rel.target_id,
                target_type=rel.target_type.value,
                relationship_type=rel.relationship_type.value,
                weight=rel.weight,
                status=rel.status.value,
            )
            stmt = stmt.on_conflict_do_update(
                constraint="uq_concept_relationships_edge",
                set_={"weight": rel.weight, "status": rel.status.value},
            )
            await self._session.execute(stmt)
        await self._session.flush()


class SqlAlchemyCatalogVersionRepository(CatalogVersionRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_version(self, exam_id: str, version: str) -> CatalogVersion | None:
        result = await self._session.execute(
            select(CatalogVersionModel).where(
                CatalogVersionModel.exam_id == exam_id,
                CatalogVersionModel.version == version,
            )
        )
        row = result.scalar_one_or_none()
        return _map_catalog_version(row) if row else None

    async def get_latest_published(self, exam_id: str) -> CatalogVersion | None:
        result = await self._session.execute(
            select(CatalogVersionModel)
            .where(
                CatalogVersionModel.exam_id == exam_id,
                CatalogVersionModel.status == CatalogVersionStatus.PUBLISHED.value,
            )
            .order_by(CatalogVersionModel.published_at.desc())
            .limit(1)
        )
        row = result.scalar_one_or_none()
        return _map_catalog_version(row) if row else None

    async def save(self, catalog_version: CatalogVersion) -> CatalogVersion:
        row = await self._session.get(CatalogVersionModel, catalog_version.id)
        if row is None:
            row = CatalogVersionModel(
                id=catalog_version.id,
                exam_id=catalog_version.exam_id,
                version=catalog_version.version,
                status=catalog_version.status.value,
                published_at=catalog_version.published_at,
                published_by=catalog_version.published_by,
                concepts_added=catalog_version.concepts_added,
                concepts_deprecated=catalog_version.concepts_deprecated,
                change_summary=catalog_version.change_summary,
            )
            self._session.add(row)
        else:
            row.status = catalog_version.status.value
            row.published_at = catalog_version.published_at
            row.published_by = catalog_version.published_by
            row.concepts_added = catalog_version.concepts_added
            row.concepts_deprecated = catalog_version.concepts_deprecated
            row.change_summary = catalog_version.change_summary
        await self._session.flush()
        return _map_catalog_version(row)

    async def supersede_published(self, exam_id: str, except_version: str) -> None:
        result = await self._session.execute(
            select(CatalogVersionModel).where(
                CatalogVersionModel.exam_id == exam_id,
                CatalogVersionModel.status == CatalogVersionStatus.PUBLISHED.value,
                CatalogVersionModel.version != except_version,
            )
        )
        for row in result.scalars().all():
            row.status = CatalogVersionStatus.SUPERSEDED.value
        await self._session.flush()

    async def list_versions(self, exam_id: str) -> tuple[CatalogVersion, ...]:
        result = await self._session.execute(
            select(CatalogVersionModel)
            .where(CatalogVersionModel.exam_id == exam_id)
            .order_by(CatalogVersionModel.created_at.desc())
        )
        return tuple(_map_catalog_version(row) for row in result.scalars().all())


class SqlAlchemyExamCatalogUnitOfWork(ExamCatalogUnitOfWorkPort):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self.exam_repo = SqlAlchemyExamRepository(session)
        self.subject_repo = SqlAlchemySubjectRepository(session)
        self.topic_repo = SqlAlchemyTopicRepository(session)
        self.concept_repo = SqlAlchemyConceptRepository(session)
        self.relationship_repo = SqlAlchemyConceptRelationshipRepository(session)
        self.catalog_version_repo = SqlAlchemyCatalogVersionRepository(session)

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()
