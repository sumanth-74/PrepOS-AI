from __future__ import annotations

from enum import StrEnum


class KnowledgeSourceStatus(StrEnum):
    DRAFT = "draft"
    PROCESSING = "processing"
    ACTIVE = "active"
    FAILED = "failed"
    QUARANTINED = "quarantined"
    ARCHIVED = "archived"


class KnowledgeSourceType(StrEnum):
    NCERT = "ncert"
    PYQ = "pyq"
    CURRENT_AFFAIRS = "current_affairs"
    PIB = "pib"
    PRS = "prs"
    GOVERNMENT_SCHEME = "government_scheme"
    BUDGET = "budget"
    ECONOMIC_SURVEY = "economic_survey"
    BOOK = "book"
    SYLLABUS = "syllabus"
    MENTOR_NOTE = "mentor_note"
    UPLOAD = "upload"
