from __future__ import annotations


class DomainError(Exception):
    code: str = "DOMAIN_ERROR"
    message: str = "A domain error occurred."

    def __init__(self, message: str | None = None, *, details: dict[str, object] | None = None) -> None:
        self.message = message or self.message
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(DomainError):
    code = "VALIDATION_ERROR"
    message = "Validation failed."


class NotFoundError(DomainError):
    code = "NOT_FOUND"
    message = "Resource not found."


class ConflictError(DomainError):
    code = "CONFLICT"
    message = "Resource conflict."


class OptimisticLockError(DomainError):
    code = "OPTIMISTIC_LOCK"
    message = "Concurrent update conflict."


class TenantAccessDeniedError(DomainError):
    code = "TENANT_ACCESS_DENIED"
    message = "Tenant access denied."


class AuthenticationError(DomainError):
    code = "AUTHENTICATION_ERROR"
    message = "Authentication failed."


class AuthorizationError(DomainError):
    code = "AUTHORIZATION_ERROR"
    message = "Authorization failed."
