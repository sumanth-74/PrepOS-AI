from __future__ import annotations

from prepos.core.exceptions import ConflictError, DomainError, NotFoundError, OptimisticLockError, ValidationError


class LearningGraphDomainError(DomainError):
    code = "LEARNING_GRAPH_DOMAIN_ERROR"
    message = "Learning graph domain error."


class NodeNotFoundError(NotFoundError):
    code = "NOT_FOUND"
    message = "Concept progress node not found."


class GraphProvisioningFailedError(ValidationError):
    code = "VALIDATION_ERROR"
    message = "Learning graph provisioning failed."


class OptimisticLockFailureError(OptimisticLockError):
    code = "OPTIMISTIC_LOCK"
    message = "Concurrent graph update conflict."


class DuplicateEventError(ConflictError):
    code = "CONFLICT"
    message = "Duplicate domain event already processed."
