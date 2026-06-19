from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from typing import cast
from uuid import UUID, uuid4

from prepos.application.exam.ports import ExamCatalogUnitOfWorkPort
from prepos.application.exam.seed_catalog import build_catalog_seed
from prepos.domain.exam.entities import (
    CatalogVersion,
    Concept,
    ConceptRelationship,
    Exam,
    ExamTrack,
    Subject,
    Topic,
)
from prepos.domain.exam.exceptions import CatalogValidationError
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


def _as_dict(value: object, *, field_name: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise CatalogValidationError(
            f"Expected object for {field_name}.",
            details={"field": field_name},
        )
    return value


def _as_list(value: object, *, field_name: str) -> list[object]:
    if not isinstance(value, list):
        raise CatalogValidationError(
            f"Expected list for {field_name}.",
            details={"field": field_name},
        )
    return value


def _as_int(value: object, *, default: int | None = None) -> int:
    if value is None and default is not None:
        return default
    return int(str(value))


class SeedValidationService:
    REQUIRED_TOP_LEVEL_KEYS = frozenset(
        {"catalog_version", "exam_id", "exam", "tracks", "subjects", "topics", "concepts", "relationships"}
    )

    @classmethod
    def validate_payload(cls, payload: dict[str, object]) -> None:
        missing = cls.REQUIRED_TOP_LEVEL_KEYS - set(payload.keys())
        if missing:
            raise CatalogValidationError(
                "Seed payload missing required keys.",
                details={"missing": sorted(missing)},
            )
        exam_obj = _as_dict(payload["exam"], field_name="exam")
        if payload.get("exam_id") != exam_obj.get("exam_id"):
            raise CatalogValidationError("exam_id mismatch between root and exam object.")

        topic_subject_map = {
            str(_as_dict(topic, field_name="topic")["topic_id"]): str(
                _as_dict(topic, field_name="topic")["subject_id"]
            )
            for topic in _as_list(payload["topics"], field_name="topics")
        }
        for raw_concept in _as_list(payload["concepts"], field_name="concepts"):
            concept = _as_dict(raw_concept, field_name="concept")
            topic_id = str(concept["topic_id"])
            if topic_id not in topic_subject_map:
                raise CatalogValidationError(
                    f"Concept references unknown topic {topic_id}.",
                    details={"concept_id": concept.get("concept_id")},
                )
            if str(concept["subject_id"]) != topic_subject_map[topic_id]:
                raise CatalogValidationError(
                    "Concept subject_id does not match topic subject_id.",
                    details={"concept_id": concept.get("concept_id"), "topic_id": topic_id},
                )


class SeedLoaderService:
    def __init__(self, uow: ExamCatalogUnitOfWorkPort) -> None:
        self._uow = uow
        self._validator = SeedValidationService()

    @staticmethod
    def load_json(path: Path) -> dict[str, object]:
        with path.open(encoding="utf-8") as handle:
            payload = json.load(handle)
        if not isinstance(payload, dict):
            raise CatalogValidationError("Seed file must contain a JSON object.")
        return payload

    @staticmethod
    def default_seed_path() -> Path:
        return Path(__file__).resolve().parents[5] / "seeds" / "upsc_cse_concepts_v1_0.json"

    async def import_seed(
        self,
        payload: dict[str, object],
        *,
        published_by: UUID | None = None,
    ) -> tuple[int, int, bool]:
        self._validator.validate_payload(payload)
        exam_id = str(payload["exam_id"])
        catalog_version = str(payload["catalog_version"])

        existing = await self._uow.catalog_version_repo.get_by_version(exam_id, catalog_version)
        idempotent = existing is not None and existing.status == CatalogVersionStatus.PUBLISHED

        exam_data = _as_dict(payload["exam"], field_name="exam")
        exam = Exam(
            exam_id=str(exam_data["exam_id"]),
            exam_code=str(exam_data["exam_code"]),
            exam_name=str(exam_data["exam_name"]),
            exam_type=ExamType(str(exam_data["exam_type"])),
            prelims_weight=Decimal(str(exam_data["prelims_weight"])),
            mains_weight=Decimal(str(exam_data["mains_weight"])),
            interview_weight=Decimal(str(exam_data["interview_weight"])),
            domain_catalog_version=catalog_version,
            status=CatalogStatus(str(exam_data.get("status", "active"))),
            essay_included=bool(exam_data.get("essay_included", True)),
        )
        await self._uow.exam_repo.save_exam(exam)

        tracks = tuple(
            self._map_tracks(
                cast(
                    list[dict[str, object]],
                    _as_list(payload["tracks"], field_name="tracks"),
                )
            )
        )
        await self._uow.exam_repo.save_tracks(tracks)

        subjects = tuple(
            self._map_subjects(
                cast(
                    list[dict[str, object]],
                    _as_list(payload["subjects"], field_name="subjects"),
                )
            )
        )
        await self._uow.subject_repo.save_subjects(subjects)

        topics = tuple(
            self._map_topics(
                cast(
                    list[dict[str, object]],
                    _as_list(payload["topics"], field_name="topics"),
                )
            )
        )
        await self._uow.topic_repo.save_topics(topics)

        concepts = tuple(
            self._map_concepts(
                cast(
                    list[dict[str, object]],
                    _as_list(payload["concepts"], field_name="concepts"),
                ),
                catalog_version,
            )
        )
        await self._uow.concept_repo.save_concepts(concepts)

        relationships = tuple(
            self._map_relationships(
                cast(
                    list[dict[str, object]],
                    _as_list(payload["relationships"], field_name="relationships"),
                )
            )
        )
        await self._uow.relationship_repo.save_relationships(relationships)

        concepts_added = len([concept for concept in concepts if concept.status == CatalogStatus.ACTIVE])
        if existing is None:
            version_row = CatalogVersion(
                id=uuid4(),
                exam_id=exam_id,
                version=catalog_version,
                status=CatalogVersionStatus.DRAFT,
                published_at=None,
                published_by=None,
                concepts_added=concepts_added,
                concepts_deprecated=0,
                change_summary="Initial UPSC CSE catalog seed import.",
            )
            await self._uow.catalog_version_repo.save(version_row)

        return len(concepts), len(relationships), idempotent

    async def import_default_seed(self, *, published_by: UUID | None = None) -> tuple[int, int, bool]:
        path = self.default_seed_path()
        payload = self.load_json(path) if path.exists() else build_catalog_seed()
        return await self.import_seed(payload, published_by=published_by)

    @staticmethod
    def _map_tracks(rows: list[dict[str, object]]) -> list[ExamTrack]:
        tracks: list[ExamTrack] = []
        for raw_row in rows:
            row = _as_dict(raw_row, field_name="track")
            subject_ids_raw = _as_list(row["subject_ids"], field_name="track.subject_ids")
            tracks.append(
                ExamTrack(
                    track_id=str(row["track_id"]),
                    exam_id=str(row["exam_id"]),
                    track_code=TrackCode(str(row["track_code"])),
                    track_name=str(row["track_name"]),
                    stage=str(row["stage"]),
                    subject_ids=tuple(str(item) for item in subject_ids_raw),
                    sort_order=_as_int(row["sort_order"]),
                    status=CatalogStatus(str(row.get("status", "active"))),
                )
            )
        return tracks

    @staticmethod
    def _map_subjects(rows: list[dict[str, object]]) -> list[Subject]:
        subjects: list[Subject] = []
        for raw_row in rows:
            row = _as_dict(raw_row, field_name="subject")
            subjects.append(
                Subject(
                    subject_id=str(row["subject_id"]),
                    exam_id=str(row["exam_id"]),
                    subject_name=str(row["subject_name"]),
                    subject_slug=str(row["subject_slug"]),
                    prelims_applicable=bool(row["prelims_applicable"]),
                    mains_applicable=bool(row["mains_applicable"]),
                    sort_order=_as_int(row["sort_order"]),
                    status=CatalogStatus(str(row.get("status", "active"))),
                )
            )
        return subjects

    @staticmethod
    def _map_topics(rows: list[dict[str, object]]) -> list[Topic]:
        topics: list[Topic] = []
        for raw_row in rows:
            row = _as_dict(raw_row, field_name="topic")
            topics.append(
                Topic(
                    topic_id=str(row["topic_id"]),
                    exam_id=str(row["exam_id"]),
                    subject_id=str(row["subject_id"]),
                    topic_name=str(row["topic_name"]),
                    topic_slug=str(row["topic_slug"]),
                    prelims_relevance=_as_int(row["prelims_relevance"]),
                    mains_relevance=_as_int(row["mains_relevance"]),
                    sort_order=_as_int(row["sort_order"]),
                    status=CatalogStatus(str(row.get("status", "active"))),
                )
            )
        return topics

    @staticmethod
    def _map_concepts(rows: list[dict[str, object]], catalog_version: str) -> list[Concept]:
        concepts: list[Concept] = []
        for raw_row in rows:
            row = _as_dict(raw_row, field_name="concept")
            parent = row.get("parent_concept_id")
            exam_stages_raw = row.get("exam_stages", [])
            tags_raw = row.get("tags", [])
            metadata_raw = row.get("metadata", {})
            exam_stages = _as_list(exam_stages_raw, field_name="concept.exam_stages") if exam_stages_raw else []
            tags = _as_list(tags_raw, field_name="concept.tags") if tags_raw else []
            metadata = _as_dict(metadata_raw, field_name="concept.metadata") if metadata_raw else {}
            concepts.append(
                Concept(
                    concept_id=str(row["concept_id"]),
                    exam_id=str(row["exam_id"]),
                    subject_id=str(row["subject_id"]),
                    topic_id=str(row["topic_id"]),
                    concept_name=str(row["concept_name"]),
                    concept_slug=str(row["concept_slug"]),
                    concept_type=ConceptType(str(row["concept_type"])),
                    prelims_relevance=_as_int(row["prelims_relevance"]),
                    mains_relevance=_as_int(row["mains_relevance"]),
                    current_affairs_linkable=bool(row.get("current_affairs_linkable", True)),
                    pyq_mappable=bool(row.get("pyq_mappable", True)),
                    status=CatalogStatus(str(row.get("status", "active"))),
                    domain_catalog_version=catalog_version,
                    parent_concept_id=str(parent) if parent else None,
                    interview_relevance=_as_int(row.get("interview_relevance"), default=0),
                    difficulty=_as_int(row.get("difficulty"), default=3),
                    importance=Decimal(str(row["importance"])) if row.get("importance") is not None else None,
                    importance_version=str(row["importance_version"]) if row.get("importance_version") else None,
                    pyq_count=_as_int(row.get("pyq_count"), default=0),
                    exam_stages=tuple(str(stage) for stage in exam_stages),
                    tags=tuple(str(tag) for tag in tags),
                    metadata=metadata,
                )
            )
        return concepts

    @staticmethod
    def _map_relationships(rows: list[dict[str, object]]) -> list[ConceptRelationship]:
        relationships: list[ConceptRelationship] = []
        for row in rows:
            rel_id = row.get("id")
            relationships.append(
                ConceptRelationship(
                    id=UUID(str(rel_id)) if rel_id else uuid4(),
                    exam_id=str(row["exam_id"]),
                    source_id=str(row["source_id"]),
                    source_type=RelationshipSourceType(str(row["source_type"])),
                    target_id=str(row["target_id"]),
                    target_type=RelationshipTargetType(str(row["target_type"])),
                    relationship_type=RelationshipType(str(row["relationship_type"])),
                    weight=Decimal(str(row.get("weight", "1.0"))),
                    status=CatalogStatus(str(row.get("status", "active"))),
                )
            )
        return relationships


class ExamCatalogService:
    def __init__(self, uow: ExamCatalogUnitOfWorkPort) -> None:
        self._uow = uow

    async def build_exam_tree(
        self,
        exam_id: str,
        *,
        include_draft: bool = False,
        catalog_version: str | None = None,
    ) -> tuple[Exam, tuple[ExamTrack, ...], tuple[Subject, ...], tuple[Topic, ...], tuple[Concept, ...]]:
        exam = await self._uow.exam_repo.get_exam(exam_id)
        if exam is None:
            from prepos.domain.exam.exceptions import ExamNotFoundError

            raise ExamNotFoundError(f"Exam {exam_id} not found.", details={"exam_id": exam_id})

        version = catalog_version or exam.domain_catalog_version
        status_filter = None if include_draft else CatalogStatus.ACTIVE.value

        tracks = await self._uow.exam_repo.list_tracks(exam_id)
        subjects = await self._uow.subject_repo.list_subjects(exam_id, status=status_filter)
        topics = await self._uow.topic_repo.list_topics(exam_id, status=status_filter)
        concepts = await self._uow.concept_repo.list_concepts_by_exam(
            exam_id,
            status=status_filter,
            catalog_version=version,
        )
        return exam, tracks, subjects, topics, concepts

    async def get_concept_ancestors(self, concept_id: str) -> tuple[Concept, list[Concept], Topic, Subject]:
        concept = await self._uow.concept_repo.get_concept(concept_id)
        if concept is None:
            from prepos.domain.exam.exceptions import ConceptNotFoundError

            raise ConceptNotFoundError(f"Concept {concept_id} not found.", details={"concept_id": concept_id})

        topic = await self._uow.topic_repo.get_topic(concept.topic_id)
        if topic is None:
            raise CatalogValidationError("Concept topic not found.", details={"topic_id": concept.topic_id})

        subjects = await self._uow.subject_repo.list_subjects(concept.exam_id)
        subject = next((item for item in subjects if item.subject_id == concept.subject_id), None)
        if subject is None:
            raise CatalogValidationError("Concept subject not found.", details={"subject_id": concept.subject_id})

        ancestors: list[Concept] = []
        current_parent = concept.parent_concept_id
        visited: set[str] = set()
        while current_parent:
            if current_parent in visited:
                break
            visited.add(current_parent)
            parent = await self._uow.concept_repo.get_concept(current_parent)
            if parent is None:
                break
            ancestors.append(parent)
            current_parent = parent.parent_concept_id

        return concept, ancestors, topic, subject

    async def get_concept_descendants(self, concept_id: str) -> tuple[Concept, list[Concept]]:
        concept = await self._uow.concept_repo.get_concept(concept_id)
        if concept is None:
            from prepos.domain.exam.exceptions import ConceptNotFoundError

            raise ConceptNotFoundError(f"Concept {concept_id} not found.", details={"concept_id": concept_id})

        direct_children = list(await self._uow.concept_repo.list_children(concept_id))
        descendants: list[Concept] = list(direct_children)
        for child in direct_children:
            grandchildren = await self._uow.concept_repo.list_children(child.concept_id)
            descendants.extend(grandchildren)
        return concept, descendants
