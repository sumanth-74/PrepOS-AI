from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from prepos.application.exam.dto import (
    CatalogVersionResponse,
    ConceptAncestorsResponse,
    ConceptDescendantsResponse,
    ConceptResponse,
    ExamResponse,
    ExamTrackResponse,
    ExamTreeResponse,
    PaginatedConceptsResponse,
    SeedImportResponse,
    SubjectResponse,
    SubjectTreeResponse,
    TopicResponse,
    TopicTreeResponse,
)
from prepos.application.exam.ports import ExamCatalogUnitOfWorkPort
from prepos.application.exam.services import ExamCatalogService, SeedLoaderService
from prepos.core.tenancy import RoleName, TenantContext
from prepos.domain.exam.entities import CatalogVersion, Exam
from prepos.domain.exam.events import DomainCatalogUpdated
from prepos.domain.exam.exceptions import CatalogVersionNotFoundError, ExamNotFoundError
from prepos.domain.exam.policies import CatalogPublishPolicy
from prepos.domain.exam.value_objects import CatalogStatus, CatalogVersionStatus, ExamType
from prepos.events.outbox.publisher import OutboxPublisher


def _concept_to_dto(concept: object) -> ConceptResponse:
    from prepos.domain.exam.entities import Concept

    assert isinstance(concept, Concept)
    return ConceptResponse(
        concept_id=concept.concept_id,
        topic_id=concept.topic_id,
        subject_id=concept.subject_id,
        concept_name=concept.concept_name,
        concept_slug=concept.concept_slug,
        concept_type=concept.concept_type.value,
        prelims_relevance=concept.prelims_relevance,
        mains_relevance=concept.mains_relevance,
        parent_concept_id=concept.parent_concept_id,
        current_affairs_linkable=concept.current_affairs_linkable,
        pyq_mappable=concept.pyq_mappable,
        exam_stages=list(concept.exam_stages),
        difficulty=concept.difficulty,
        status=concept.status.value,
        domain_catalog_version=concept.domain_catalog_version,
    )


class CreateExamUseCase:
    def __init__(self, uow: ExamCatalogUnitOfWorkPort) -> None:
        self._uow = uow

    async def execute(
        self,
        *,
        context: TenantContext,
        exam_id: str,
        exam_code: str,
        exam_name: str,
        exam_type: str,
        prelims_weight: Decimal,
        mains_weight: Decimal,
        interview_weight: Decimal,
        essay_included: bool,
    ) -> ExamResponse:
        context.require_role(RoleName.SUPER_ADMIN, RoleName.INSTITUTE_ADMIN)

        existing = await self._uow.exam_repo.get_exam(exam_id)
        if existing is not None:
            from prepos.core.exceptions import ConflictError

            raise ConflictError(f"Exam {exam_id} already exists.", details={"exam_id": exam_id})

        exam = Exam(
            exam_id=exam_id,
            exam_code=exam_code,
            exam_name=exam_name,
            exam_type=ExamType(exam_type),
            prelims_weight=prelims_weight,
            mains_weight=mains_weight,
            interview_weight=interview_weight,
            domain_catalog_version="0.0.0",
            status=CatalogStatus.DRAFT,
            essay_included=essay_included,
        )
        saved = await self._uow.exam_repo.save_exam(exam)
        await self._uow.commit()
        return ExamResponse(
            exam_id=saved.exam_id,
            exam_code=saved.exam_code,
            exam_name=saved.exam_name,
            exam_type=saved.exam_type.value,
            prelims_weight=saved.prelims_weight,
            mains_weight=saved.mains_weight,
            interview_weight=saved.interview_weight,
            domain_catalog_version=saved.domain_catalog_version,
            essay_included=saved.essay_included,
            status=saved.status.value,
        )


class PublishCatalogVersionUseCase:
    def __init__(self, uow: ExamCatalogUnitOfWorkPort, outbox: OutboxPublisher) -> None:
        self._uow = uow
        self._outbox = outbox
        self._catalog_service = ExamCatalogService(uow)

    async def execute(
        self,
        *,
        context: TenantContext,
        exam_id: str,
        version: str,
        change_summary: str | None = None,
    ) -> CatalogVersionResponse:
        context.require_role(RoleName.SUPER_ADMIN)

        catalog_version = await self._uow.catalog_version_repo.get_by_version(exam_id, version)
        if catalog_version is None:
            raise CatalogVersionNotFoundError(
                f"Catalog version {version} not found for exam {exam_id}.",
                details={"exam_id": exam_id, "version": version},
            )
        CatalogPublishPolicy.can_publish(catalog_version)

        exam, _, subjects, topics, concepts = await self._catalog_service.build_exam_tree(
            exam_id,
            include_draft=True,
            catalog_version=version,
        )
        if exam is None:
            raise ExamNotFoundError(f"Exam {exam_id} not found.", details={"exam_id": exam_id})

        relationships = await self._uow.relationship_repo.list_by_exam(exam_id, status=CatalogStatus.ACTIVE.value)
        CatalogPublishPolicy.validate_publish(
            concepts=concepts,
            topics=topics,
            subjects=subjects,
            relationships=relationships,
        )

        previous = await self._uow.catalog_version_repo.get_latest_published(exam_id)
        deprecated: list[str] = []
        if previous is not None:
            previous_concepts = await self._uow.concept_repo.list_concepts_by_exam(
                exam_id,
                status=CatalogStatus.ACTIVE.value,
                catalog_version=previous.version,
            )
            current_ids = {concept.concept_id for concept in concepts if concept.status == CatalogStatus.ACTIVE}
            deprecated = [
                concept.concept_id
                for concept in previous_concepts
                if concept.concept_id not in current_ids
            ]

        added = [
            concept.concept_id
            for concept in concepts
            if concept.status == CatalogStatus.ACTIVE and concept.domain_catalog_version == version
        ]

        now = datetime.now(UTC)
        published = CatalogVersion(
            id=catalog_version.id,
            exam_id=exam_id,
            version=version,
            status=CatalogVersionStatus.PUBLISHED,
            published_at=now,
            published_by=context.user_id,
            concepts_added=len(added),
            concepts_deprecated=len(deprecated),
            change_summary=change_summary or catalog_version.change_summary,
        )
        await self._uow.catalog_version_repo.save(published)
        await self._uow.catalog_version_repo.supersede_published(exam_id, except_version=version)

        updated_exam = Exam(
            exam_id=exam.exam_id,
            exam_code=exam.exam_code,
            exam_name=exam.exam_name,
            exam_type=exam.exam_type,
            prelims_weight=exam.prelims_weight,
            mains_weight=exam.mains_weight,
            interview_weight=exam.interview_weight,
            domain_catalog_version=version,
            status=CatalogStatus.ACTIVE,
            essay_included=exam.essay_included,
            created_at=exam.created_at,
            updated_at=exam.updated_at,
        )
        await self._uow.exam_repo.save_exam(updated_exam)

        event = DomainCatalogUpdated(
            exam_id=exam_id,
            catalog_version=version,
            concepts_added=tuple(added),
            concepts_deprecated=tuple(deprecated),
            occurred_at=now,
            correlation_id=context.correlation_id or context.request_id or str(uuid4()),
            actor_user_id=context.user_id,
        )
        await self._outbox.enqueue_domain_catalog_updated(event)
        await self._uow.commit()

        return CatalogVersionResponse(
            id=published.id,
            exam_id=published.exam_id,
            version=published.version,
            status=published.status.value,
            published_at=published.published_at,
            concepts_added=published.concepts_added,
            concepts_deprecated=published.concepts_deprecated,
            change_summary=published.change_summary,
        )


class GetExamTreeUseCase:
    def __init__(self, uow: ExamCatalogUnitOfWorkPort) -> None:
        self._catalog_service = ExamCatalogService(uow)

    async def execute(
        self,
        exam_id: str,
        *,
        include_draft: bool = False,
        catalog_version: str | None = None,
    ) -> ExamTreeResponse:
        exam, tracks, subjects, topics, concepts = await self._catalog_service.build_exam_tree(
            exam_id,
            include_draft=include_draft,
            catalog_version=catalog_version,
        )
        concepts_by_topic: dict[str, list[ConceptResponse]] = {}
        for concept in concepts:
            concepts_by_topic.setdefault(concept.topic_id, []).append(_concept_to_dto(concept))

        topics_by_subject: dict[str, list[TopicTreeResponse]] = {}
        for topic in topics:
            topics_by_subject.setdefault(topic.subject_id, []).append(
                TopicTreeResponse(
                    topic=TopicResponse(
                        topic_id=topic.topic_id,
                        subject_id=topic.subject_id,
                        topic_name=topic.topic_name,
                        topic_slug=topic.topic_slug,
                        prelims_relevance=topic.prelims_relevance,
                        mains_relevance=topic.mains_relevance,
                        sort_order=topic.sort_order,
                        status=topic.status.value,
                    ),
                    concepts=concepts_by_topic.get(topic.topic_id, []),
                )
            )

        subject_trees = [
            SubjectTreeResponse(
                subject=SubjectResponse(
                    subject_id=subject.subject_id,
                    subject_name=subject.subject_name,
                    subject_slug=subject.subject_slug,
                    prelims_applicable=subject.prelims_applicable,
                    mains_applicable=subject.mains_applicable,
                    sort_order=subject.sort_order,
                    status=subject.status.value,
                ),
                topics=topics_by_subject.get(subject.subject_id, []),
            )
            for subject in subjects
        ]

        return ExamTreeResponse(
            exam=ExamResponse(
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
            ),
            tracks=[
                ExamTrackResponse(
                    track_id=track.track_id,
                    track_code=track.track_code.value,
                    track_name=track.track_name,
                    stage=track.stage,
                    subject_ids=list(track.subject_ids),
                    sort_order=track.sort_order,
                    status=track.status.value,
                )
                for track in tracks
            ],
            subjects=subject_trees,
            catalog_version=catalog_version or exam.domain_catalog_version,
        )


class GetConceptUseCase:
    def __init__(self, uow: ExamCatalogUnitOfWorkPort) -> None:
        self._uow = uow

    async def execute(self, concept_id: str) -> ConceptResponse:
        concept = await self._uow.concept_repo.get_concept(concept_id)
        if concept is None:
            from prepos.domain.exam.exceptions import ConceptNotFoundError

            raise ConceptNotFoundError(f"Concept {concept_id} not found.", details={"concept_id": concept_id})
        return _concept_to_dto(concept)


class GetConceptAncestorsUseCase:
    def __init__(self, uow: ExamCatalogUnitOfWorkPort) -> None:
        self._catalog_service = ExamCatalogService(uow)

    async def execute(self, concept_id: str) -> ConceptAncestorsResponse:
        concept, ancestors, topic, subject = await self._catalog_service.get_concept_ancestors(concept_id)
        return ConceptAncestorsResponse(
            concept=_concept_to_dto(concept),
            ancestors=[_concept_to_dto(item) for item in ancestors],
            topic=TopicResponse(
                topic_id=topic.topic_id,
                subject_id=topic.subject_id,
                topic_name=topic.topic_name,
                topic_slug=topic.topic_slug,
                prelims_relevance=topic.prelims_relevance,
                mains_relevance=topic.mains_relevance,
                sort_order=topic.sort_order,
                status=topic.status.value,
            ),
            subject=SubjectResponse(
                subject_id=subject.subject_id,
                subject_name=subject.subject_name,
                subject_slug=subject.subject_slug,
                prelims_applicable=subject.prelims_applicable,
                mains_applicable=subject.mains_applicable,
                sort_order=subject.sort_order,
                status=subject.status.value,
            ),
        )


class GetConceptDescendantsUseCase:
    def __init__(self, uow: ExamCatalogUnitOfWorkPort) -> None:
        self._catalog_service = ExamCatalogService(uow)

    async def execute(self, concept_id: str) -> ConceptDescendantsResponse:
        concept, descendants = await self._catalog_service.get_concept_descendants(concept_id)
        return ConceptDescendantsResponse(
            concept=_concept_to_dto(concept),
            descendants=[_concept_to_dto(item) for item in descendants],
        )


class SearchConceptsUseCase:
    def __init__(self, uow: ExamCatalogUnitOfWorkPort) -> None:
        self._uow = uow

    async def execute(
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
    ) -> PaginatedConceptsResponse:
        concepts, total = await self._uow.concept_repo.search_concepts(
            exam_id=exam_id,
            query=query,
            subject_id=subject_id,
            topic_id=topic_id,
            status=status,
            catalog_version=catalog_version,
            offset=offset,
            limit=limit,
        )
        return PaginatedConceptsResponse(
            items=[_concept_to_dto(concept) for concept in concepts],
            total=total,
            offset=offset,
            limit=limit,
        )


class ImportSeedUseCase:
    def __init__(self, uow: ExamCatalogUnitOfWorkPort) -> None:
        self._uow = uow
        self._loader = SeedLoaderService(uow)

    async def execute(self, *, context: TenantContext) -> SeedImportResponse:
        context.require_role(RoleName.SUPER_ADMIN)
        concepts_count, relationships_count, idempotent = await self._loader.import_default_seed(
            published_by=context.user_id,
        )
        await self._uow.commit()
        from prepos.application.exam.seed_catalog import CATALOG_VERSION, EXAM_ID

        return SeedImportResponse(
            exam_id=EXAM_ID,
            catalog_version=CATALOG_VERSION,
            concepts_imported=concepts_count,
            relationships_imported=relationships_count,
            idempotent=idempotent,
        )
