from __future__ import annotations

from prepos.domain.exam.entities import (
    CatalogVersion,
    Concept,
    ConceptRelationship,
    Subject,
    Topic,
    compute_concept_depth,
    validate_prerequisite_dag,
)
from prepos.domain.exam.exceptions import CatalogValidationError
from prepos.domain.exam.value_objects import CatalogStatus, CatalogVersionStatus, RelationshipType


class ConceptHierarchyPolicy:
    MAX_DEPTH = 2

    @classmethod
    def validate(cls, concepts: tuple[Concept, ...]) -> None:
        parent_map = {concept.concept_id: concept.parent_concept_id for concept in concepts}
        concept_ids = frozenset(parent_map)
        for concept in concepts:
            if concept.parent_concept_id and concept.parent_concept_id not in concept_ids:
                raise CatalogValidationError(
                    f"Concept {concept.concept_id} references unknown parent.",
                    details={"concept_id": concept.concept_id, "parent_concept_id": concept.parent_concept_id},
                )
            compute_concept_depth(concept.concept_id, parent_map)


class PrerequisiteDagPolicy:
    @classmethod
    def validate(cls, relationships: tuple[ConceptRelationship, ...], concepts: tuple[Concept, ...]) -> None:
        active_concepts = frozenset(
            concept.concept_id for concept in concepts if concept.status == CatalogStatus.ACTIVE
        )
        validate_prerequisite_dag(relationships, active_concepts)


class CatalogPublishPolicy:
    @classmethod
    def validate_publish(
        cls,
        *,
        concepts: tuple[Concept, ...],
        topics: tuple[Topic, ...],
        subjects: tuple[Subject, ...],
        relationships: tuple[ConceptRelationship, ...],
    ) -> None:
        topic_map = {topic.topic_id: topic for topic in topics}
        subject_map = {subject.subject_id: subject for subject in subjects}
        active_topics = {topic.topic_id for topic in topics if topic.status == CatalogStatus.ACTIVE}
        active_subjects = {subject.subject_id for subject in subjects if subject.status == CatalogStatus.ACTIVE}

        for concept in concepts:
            if concept.status != CatalogStatus.ACTIVE:
                continue
            topic = topic_map.get(concept.topic_id)
            if topic is None:
                raise CatalogValidationError(
                    f"Active concept {concept.concept_id} references missing topic.",
                    details={"concept_id": concept.concept_id},
                )
            concept.validate_against_topic(topic)
            if topic.status != CatalogStatus.ACTIVE or topic.topic_id not in active_topics:
                raise CatalogValidationError(
                    f"Active concept {concept.concept_id} belongs to inactive topic.",
                    details={"concept_id": concept.concept_id, "topic_id": concept.topic_id},
                )
            if concept.subject_id not in active_subjects:
                raise CatalogValidationError(
                    f"Active concept {concept.concept_id} belongs to inactive subject.",
                    details={"concept_id": concept.concept_id, "subject_id": concept.subject_id},
                )
            subject = subject_map.get(concept.subject_id)
            if subject is None:
                raise CatalogValidationError(
                    f"Active concept {concept.concept_id} references missing subject.",
                    details={"concept_id": concept.concept_id},
                )

        ConceptHierarchyPolicy.validate(concepts)
        PrerequisiteDagPolicy.validate(relationships, concepts)

        concepts_by_topic: dict[str, list[Concept]] = {}
        for concept in concepts:
            if concept.status != CatalogStatus.ACTIVE:
                continue
            concepts_by_topic.setdefault(concept.topic_id, []).append(concept)
        for topic in topics:
            if topic.status != CatalogStatus.ACTIVE:
                continue
            active_count = len(concepts_by_topic.get(topic.topic_id, []))
            if active_count < 3:
                raise CatalogValidationError(
                    f"Topic {topic.topic_id} requires at least 3 active concepts before publish.",
                    details={"topic_id": topic.topic_id, "active_concepts": active_count},
                )

    @classmethod
    def can_publish(cls, catalog_version: CatalogVersion) -> None:
        if catalog_version.status == CatalogVersionStatus.PUBLISHED:
            from prepos.domain.exam.exceptions import CatalogAlreadyPublishedError

            raise CatalogAlreadyPublishedError(
                f"Catalog version {catalog_version.version} is already published.",
                details={"version": catalog_version.version},
            )


class ConceptRelationshipPolicy:
    @classmethod
    def validate(cls, relationship: ConceptRelationship, concepts: dict[str, Concept]) -> None:
        if relationship.relationship_type == RelationshipType.PREREQUISITE:
            source = concepts.get(relationship.source_id)
            target = concepts.get(relationship.target_id)
            if source is None or target is None:
                raise CatalogValidationError(
                    "PREREQUISITE relationship references unknown concept.",
                    details={"source_id": relationship.source_id, "target_id": relationship.target_id},
                )
            if source.status != CatalogStatus.ACTIVE or target.status != CatalogStatus.ACTIVE:
                raise CatalogValidationError(
                    "PREREQUISITE relationship requires active concepts.",
                    details={"source_id": relationship.source_id, "target_id": relationship.target_id},
                )
