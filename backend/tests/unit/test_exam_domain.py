from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest

from prepos.domain.exam.entities import Concept, ConceptRelationship, Subject, Topic, compute_concept_depth
from prepos.domain.exam.exceptions import ConceptHierarchyDepthError, PrerequisiteCycleError
from prepos.domain.exam.policies import CatalogPublishPolicy, ConceptHierarchyPolicy, PrerequisiteDagPolicy
from prepos.domain.exam.value_objects import (
    CatalogStatus,
    ConceptType,
    RelationshipSourceType,
    RelationshipTargetType,
    RelationshipType,
)


def _concept(
    concept_id: str,
    *,
    topic_id: str = "upsc.cse.polity.fundamental_rights",
    subject_id: str = "upsc.cse.polity",
    parent: str | None = None,
) -> Concept:
    return Concept(
        concept_id=concept_id,
        exam_id="upsc_cse",
        subject_id=subject_id,
        topic_id=topic_id,
        concept_name=concept_id,
        concept_slug=concept_id.split(".")[-1],
        concept_type=ConceptType.DEFINITION,
        prelims_relevance=90,
        mains_relevance=90,
        current_affairs_linkable=True,
        pyq_mappable=True,
        status=CatalogStatus.ACTIVE,
        domain_catalog_version="1.0.0",
        parent_concept_id=parent,
    )


def test_compute_concept_depth_allows_two_levels() -> None:
    parent_map = {
        "a": None,
        "b": "a",
        "c": "b",
    }
    assert compute_concept_depth("c", parent_map) == 2


def test_compute_concept_depth_rejects_depth_three() -> None:
    parent_map = {"a": None, "b": "a", "c": "b", "d": "c"}
    with pytest.raises(ConceptHierarchyDepthError):
        compute_concept_depth("d", parent_map)


def test_prerequisite_dag_detects_cycle() -> None:
    concepts = (_concept("a"), _concept("b"))
    relationships = (
        ConceptRelationship(
            id=uuid4(),
            exam_id="upsc_cse",
            source_id="a",
            source_type=RelationshipSourceType.CONCEPT,
            target_id="b",
            target_type=RelationshipTargetType.CONCEPT,
            relationship_type=RelationshipType.PREREQUISITE,
            weight=Decimal("1.0"),
            status=CatalogStatus.ACTIVE,
        ),
        ConceptRelationship(
            id=uuid4(),
            exam_id="upsc_cse",
            source_id="b",
            source_type=RelationshipSourceType.CONCEPT,
            target_id="a",
            target_type=RelationshipTargetType.CONCEPT,
            relationship_type=RelationshipType.PREREQUISITE,
            weight=Decimal("1.0"),
            status=CatalogStatus.ACTIVE,
        ),
    )
    with pytest.raises(PrerequisiteCycleError):
        PrerequisiteDagPolicy.validate(relationships, concepts)


def test_concept_hierarchy_policy_validates_parent_exists() -> None:
    concepts = (_concept("child", parent="missing"),)
    with pytest.raises(Exception):
        ConceptHierarchyPolicy.validate(concepts)


def test_catalog_publish_requires_three_concepts_per_topic() -> None:
    topic = Topic(
        topic_id="upsc.cse.polity.fundamental_rights",
        exam_id="upsc_cse",
        subject_id="upsc.cse.polity",
        topic_name="Fundamental Rights",
        topic_slug="fundamental_rights",
        prelims_relevance=95,
        mains_relevance=95,
        sort_order=1,
        status=CatalogStatus.ACTIVE,
    )
    subject = Subject(
        subject_id="upsc.cse.polity",
        exam_id="upsc_cse",
        subject_name="Polity",
        subject_slug="polity",
        prelims_applicable=True,
        mains_applicable=True,
        sort_order=1,
        status=CatalogStatus.ACTIVE,
    )
    concepts = (_concept("only_one"),)
    with pytest.raises(Exception):
        CatalogPublishPolicy.validate_publish(
            concepts=concepts,
            topics=(topic,),
            subjects=(subject,),
            relationships=(),
        )
