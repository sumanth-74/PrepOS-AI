from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from prepos.domain.student.entities import Student
from prepos.domain.student.exceptions import OnboardingAlreadyCompletedError, OnboardingValidationError


class OnboardingCompletionPolicy:
    MIN_DAILY_HOURS = Decimal("0.5")
    MAX_DAILY_HOURS = Decimal("16")
    MIN_TARGET_YEAR = 2024
    MAX_TARGET_YEAR = 2040

    @classmethod
    def validate_ready_for_completion(cls, student: Student) -> None:
        if student.onboarding_completed:
            raise OnboardingAlreadyCompletedError(
                "Student onboarding is already completed.",
                details={"student_id": str(student.id)},
            )
        if not student.target_exam_id:
            raise OnboardingValidationError(
                "target_exam_id is required before completing onboarding.",
                details={"field": "target_exam_id"},
            )
        if student.target_year is None:
            raise OnboardingValidationError(
                "target_year is required before completing onboarding.",
                details={"field": "target_year"},
            )
        if student.target_year < cls.MIN_TARGET_YEAR or student.target_year > cls.MAX_TARGET_YEAR:
            raise OnboardingValidationError(
                "target_year is out of allowed range.",
                details={"field": "target_year", "value": student.target_year},
            )
        if student.daily_study_hours is None:
            raise OnboardingValidationError(
                "daily_study_hours is required before completing onboarding.",
                details={"field": "daily_study_hours"},
            )
        if (
            student.daily_study_hours < cls.MIN_DAILY_HOURS
            or student.daily_study_hours > cls.MAX_DAILY_HOURS
        ):
            raise OnboardingValidationError(
                "daily_study_hours must be between 0.5 and 16.",
                details={"field": "daily_study_hours", "value": str(student.daily_study_hours)},
            )
        if student.experience_level is None:
            raise OnboardingValidationError(
                "experience_level is required before completing onboarding.",
                details={"field": "experience_level"},
            )


class StudentAccessPolicy:
    @classmethod
    def can_view(
        cls,
        *,
        actor_user_id: UUID,
        actor_roles: frozenset[str],
        student: Student,
    ) -> bool:
        if "super_admin" in actor_roles or "institute_admin" in actor_roles:
            return True
        return student.user_id == actor_user_id

    @classmethod
    def can_modify(
        cls,
        *,
        actor_user_id: UUID,
        actor_roles: frozenset[str],
        student: Student,
    ) -> bool:
        if student.onboarding_completed and "institute_admin" not in actor_roles and "super_admin" not in actor_roles:
            return False
        return cls.can_view(actor_user_id=actor_user_id, actor_roles=actor_roles, student=student)
