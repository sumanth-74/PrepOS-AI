from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from prepos.domain.exam.exceptions import (
    CatalogValidationError,
    ConceptHierarchyDepthError,
    PrerequisiteCycleError,
    SubjectTopicMismatchError,
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
    derive_exam_stages,
)


@dataclass(frozen=True, slots=True)
class Exam:
    exam_id: str
    exam_code: str
    exam_name: str
    exam_type: ExamType
    prelims_weight: Decimal
    mains_weight: Decimal
    interview_weight: Decimal
    domain_catalog_version: str
    status: CatalogStatus
    essay_included: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class ExamTrack:
    track_id: str
    exam_id: str
    track_code: TrackCode
    track_name: str
    stage: str
    subject_ids: tuple[str, ...]
    sort_order: int
    status: CatalogStatus
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class Subject:
    subject_id: str
    exam_id: str
    subject_name: str
    subject_slug: str
    prelims_applicable: bool
    mains_applicable: bool
    sort_order: int
    status: CatalogStatus
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class Topic:
    topic_id: str
    exam_id: str
    subject_id: str
    topic_name: str
    topic_slug: str
    prelims_relevance: int
    mains_relevance: int
    sort_order: int
    status: CatalogStatus
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class Concept:
    concept_id: str
    exam_id: str
    subject_id: str
    topic_id: str
    concept_name: str
    concept_slug: str
    concept_type: ConceptType
    prelims_relevance: int
    mains_relevance: int
    current_affairs_linkable: bool
    pyq_mappable: bool
    status: CatalogStatus
    domain_catalog_version: str
    parent_concept_id: str | None = None
    interview_relevance: int = 0
    difficulty: int = 3
    importance: Decimal | None = None
    importance_version: str | None = None
    pyq_count: int = 0
    exam_stages: tuple[str, ...] = field(default_factory=tuple)
    tags: tuple[str, ...] = field(default_factory=tuple)
    metadata: dict[str, object] = field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def validate_against_topic(self, topic: Topic) -> None:
        if self.subject_id != topic.subject_id:
            raise SubjectTopicMismatchError(
                f"Concept {self.concept_id} subject_id does not match topic {topic.topic_id}.",
                details={"concept_id": self.concept_id, "topic_id": topic.topic_id},
            )
        if self.topic_id != topic.topic_id:
            raise CatalogValidationError(
                f"Concept {self.concept_id} topic_id mismatch.",
                details={"concept_id": self.concept_id, "expected_topic_id": topic.topic_id},
            )

    def with_derived_stages(self, subject_slug: str) -> Concept:
        stages = derive_exam_stages(
            prelims_relevance=self.prelims_relevance,
            mains_relevance=self.mains_relevance,
            subject_slug=subject_slug,
        )
        if stages == self.exam_stages:
            return self
        return Concept(
            concept_id=self.concept_id,
            exam_id=self.exam_id,
            subject_id=self.subject_id,
            topic_id=self.topic_id,
            concept_name=self.concept_name,
            concept_slug=self.concept_slug,
            concept_type=self.concept_type,
            prelims_relevance=self.prelims_relevance,
            mains_relevance=self.mains_relevance,
            current_affairs_linkable=self.current_affairs_linkable,
            pyq_mappable=self.pyq_mappable,
            status=self.status,
            domain_catalog_version=self.domain_catalog_version,
            parent_concept_id=self.parent_concept_id,
            interview_relevance=self.interview_relevance,
            difficulty=self.difficulty,
            importance=self.importance,
            importance_version=self.importance_version,
            pyq_count=self.pyq_count,
            exam_stages=stages,
            tags=self.tags,
            metadata=self.metadata,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )


@dataclass(frozen=True, slots=True)
class ConceptRelationship:
    id: UUID
    exam_id: str
    source_id: str
    source_type: RelationshipSourceType
    target_id: str
    target_type: RelationshipTargetType
    relationship_type: RelationshipType
    weight: Decimal
    status: CatalogStatus
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class CatalogVersion:
    id: UUID
    exam_id: str
    version: str
    status: CatalogVersionStatus
    published_at: datetime | None
    published_by: UUID | None
    concepts_added: int
    concepts_deprecated: int
    change_summary: str | None
    created_at: datetime | None = None
    updated_at: datetime | None = None


def compute_concept_depth(
    concept_id: str,
    parent_map: dict[str, str | None],
) -> int:
    depth = 0
    current: str | None = concept_id
    visited: set[str] = set()
    while current is not None:
        if current in visited:
            raise ConceptHierarchyDepthError(
                "Concept parent chain contains a cycle.",
                details={"concept_id": concept_id},
            )
        visited.add(current)
        parent = parent_map.get(current)
        if parent is None:
            break
        depth += 1
        if depth > 2:
            raise ConceptHierarchyDepthError(
                f"Concept {concept_id} exceeds maximum hierarchy depth of 2.",
                details={"concept_id": concept_id, "depth": depth},
            )
        current = parent
    return depth


def validate_prerequisite_dag(
    relationships: tuple[ConceptRelationship, ...],
    concept_ids: frozenset[str],
) -> None:
    adjacency: dict[str, list[str]] = {concept_id: [] for concept_id in concept_ids}
    for rel in relationships:
        if rel.relationship_type != RelationshipType.PREREQUISITE:
            continue
        if rel.source_type != RelationshipSourceType.CONCEPT:
            continue
        if rel.target_type != RelationshipTargetType.CONCEPT:
            continue
        if rel.status != CatalogStatus.ACTIVE:
            continue
        if rel.source_id not in concept_ids or rel.target_id not in concept_ids:
            continue
        adjacency.setdefault(rel.source_id, []).append(rel.target_id)

    visiting: set[str] = set()
    visited: set[str] = set()

    def dfs(node: str) -> None:
        if node in visiting:
            raise PrerequisiteCycleError(
                "PREREQUISITE graph contains a cycle.",
                details={"concept_id": node},
            )
        if node in visited:
            return
        visiting.add(node)
        for neighbor in adjacency.get(node, []):
            dfs(neighbor)
        visiting.remove(node)
        visited.add(node)

    for concept_id in concept_ids:
        dfs(concept_id)
