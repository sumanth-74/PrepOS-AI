from __future__ import annotations

from prepos.core.exceptions import ConflictError, DomainError, NotFoundError, ValidationError


class StudentDomainError(DomainError):
    code = "STUDENT_DOMAIN_ERROR"
    message = "Student domain error."


class StudentNotFoundError(NotFoundError):
    code = "NOT_FOUND"
    message = "Student not found."


class StudentProfileExistsError(ConflictError):
    code = "CONFLICT"
    message = "Student profile already exists for this user."


class OnboardingAlreadyCompletedError(ConflictError):
    code = "CONFLICT"
    message = "Student onboarding is already completed."


class OnboardingNotCompletedError(ValidationError):
    code = "ONBOARDING_NOT_COMPLETED"
    message = "Student onboarding is not completed."


class OnboardingValidationError(ValidationError):
    code = "VALIDATION_ERROR"
    message = "Onboarding validation failed."


class StudentAccessDeniedError(NotFoundError):
    code = "NOT_FOUND"
    message = "Student access denied."
