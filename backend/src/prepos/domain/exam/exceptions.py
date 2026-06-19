from __future__ import annotations

from prepos.core.exceptions import ConflictError, DomainError, NotFoundError, ValidationError


class ExamDomainError(DomainError):
    code = "EXAM_DOMAIN_ERROR"
    message = "Exam domain error."


class ExamNotFoundError(NotFoundError):
    code = "EXAM_NOT_FOUND"
    message = "Exam not found."


class ConceptNotFoundError(NotFoundError):
    code = "CONCEPT_NOT_FOUND"
    message = "Concept not found."


class CatalogVersionNotFoundError(NotFoundError):
    code = "CATALOG_VERSION_NOT_FOUND"
    message = "Catalog version not found."


class CatalogValidationError(ValidationError):
    code = "CATALOG_VALIDATION_ERROR"
    message = "Catalog validation failed."


class PrerequisiteCycleError(CatalogValidationError):
    code = "PREREQUISITE_CYCLE"
    message = "PREREQUISITE relationships must form a DAG."


class ConceptHierarchyDepthError(CatalogValidationError):
    code = "CONCEPT_HIERARCHY_DEPTH"
    message = "Concept hierarchy exceeds maximum depth of 2."


class SubjectTopicMismatchError(CatalogValidationError):
    code = "SUBJECT_TOPIC_MISMATCH"
    message = "Concept subject_id must match topic subject_id."


class CatalogAlreadyPublishedError(ConflictError):
    code = "CATALOG_ALREADY_PUBLISHED"
    message = "Catalog version is already published."
