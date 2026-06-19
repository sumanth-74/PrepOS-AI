from __future__ import annotations

from enum import StrEnum


class CatalogStatus(StrEnum):
    ACTIVE = "active"
    DRAFT = "draft"
    DEPRECATED = "deprecated"


class ExamType(StrEnum):
    COMPETITIVE_CIVIL_SERVICES = "competitive_civil_services"


class ConceptType(StrEnum):
    DEFINITION = "definition"
    PROCESS = "process"
    INSTITUTION = "institution"
    EVENT = "event"
    POLICY_SCHEME = "policy_scheme"
    CASE_STUDY = "case_study"
    SKILL = "skill"
    META_CURRENT_AFFAIRS = "meta_current_affairs"


class RelationshipType(StrEnum):
    PREREQUISITE = "PREREQUISITE"
    BUILDS_ON = "BUILDS_ON"
    RELATED_TO = "RELATED_TO"
    CURRENT_AFFAIRS_OF = "CURRENT_AFFAIRS_OF"
    PYQ_OF = "PYQ_OF"


class RelationshipSourceType(StrEnum):
    CONCEPT = "concept"
    CURRENT_AFFAIR = "current_affair"
    PYQ_QUESTION = "pyq_question"


class RelationshipTargetType(StrEnum):
    CONCEPT = "concept"


class ExamStage(StrEnum):
    PRELIMS = "prelims"
    MAINS = "mains"
    ESSAY = "essay"
    INTERVIEW = "interview"


class CatalogVersionStatus(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    SUPERSEDED = "superseded"


class TrackCode(StrEnum):
    PRELIMS_GS1 = "prelims_gs1"
    PRELIMS_CSAT = "prelims_csat"
    MAINS_GS1 = "mains_gs1"
    MAINS_GS2 = "mains_gs2"
    MAINS_GS3 = "mains_gs3"
    MAINS_GS4 = "mains_gs4"
    MAINS_ESSAY = "mains_essay"


def derive_exam_stages(
    *,
    prelims_relevance: int,
    mains_relevance: int,
    subject_slug: str,
) -> tuple[str, ...]:
    stages: list[str] = []
    if prelims_relevance > 0:
        stages.append(ExamStage.PRELIMS.value)
    if mains_relevance > 0:
        stages.append(ExamStage.MAINS.value)
    if subject_slug == "essay" and mains_relevance > 0:
        stages.append(ExamStage.ESSAY.value)
    return tuple(stages)
