from __future__ import annotations

from prepos.application.exam.seed_catalog import (
    CATALOG_VERSION,
    EXAM_ID,
    SubjectTargetCounts,
    build_catalog_seed,
    count_active_concepts_by_subject,
)
from prepos.application.exam.services import SeedValidationService


def test_build_catalog_seed_meets_minimum_concept_targets() -> None:
    build_catalog_seed()
    counts = count_active_concepts_by_subject()
    for subject_slug, target in SubjectTargetCounts.items():
        assert counts.get(subject_slug, 0) >= target, subject_slug
    assert sum(counts.values()) >= 497


def test_seed_payload_structure() -> None:
    payload = build_catalog_seed()
    SeedValidationService.validate_payload(payload)
    assert payload["exam_id"] == EXAM_ID
    assert payload["catalog_version"] == CATALOG_VERSION
    assert len(payload["tracks"]) == 7
    assert len(payload["subjects"]) >= 17


def test_every_active_topic_has_minimum_concepts() -> None:
    payload = build_catalog_seed()
    concepts_by_topic: dict[str, int] = {}
    for concept in payload["concepts"]:
        if concept["status"] != "active":
            continue
        topic_id = str(concept["topic_id"])
        concepts_by_topic[topic_id] = concepts_by_topic.get(topic_id, 0) + 1
    for topic in payload["topics"]:
        if topic["status"] != "active":
            continue
        assert concepts_by_topic.get(str(topic["topic_id"]), 0) >= 3
