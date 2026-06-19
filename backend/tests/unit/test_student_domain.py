from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest

from prepos.domain.student.entities import Student
from prepos.domain.student.exceptions import OnboardingAlreadyCompletedError, OnboardingValidationError
from prepos.domain.student.policies import OnboardingCompletionPolicy, StudentAccessPolicy
from prepos.domain.student.value_objects import ExperienceLevel


def _student(**overrides: object) -> Student:
    base = {
        "id": uuid4(),
        "tenant_id": uuid4(),
        "user_id": uuid4(),
        "target_exam_id": "upsc_cse",
        "target_year": 2026,
        "daily_study_hours": Decimal("4"),
        "experience_level": ExperienceLevel.BEGINNER,
        "onboarding_completed": False,
        "onboarding_completed_at": None,
    }
    base.update(overrides)
    return Student(**base)  # type: ignore[arg-type]


def test_onboarding_policy_requires_all_goal_fields() -> None:
    with pytest.raises(OnboardingValidationError):
        OnboardingCompletionPolicy.validate_ready_for_completion(
            _student(target_exam_id=None),
        )
    with pytest.raises(OnboardingValidationError):
        OnboardingCompletionPolicy.validate_ready_for_completion(
            _student(daily_study_hours=Decimal("20")),
        )


def test_onboarding_policy_rejects_already_completed() -> None:
    with pytest.raises(OnboardingAlreadyCompletedError):
        OnboardingCompletionPolicy.validate_ready_for_completion(
            _student(onboarding_completed=True),
        )


def test_student_access_policy_blocks_student_patch_after_onboarding() -> None:
    student = _student(onboarding_completed=True)
    actor_id = student.user_id
    assert StudentAccessPolicy.can_modify(
        actor_user_id=actor_id,
        actor_roles=frozenset({"student"}),
        student=student,
    ) is False
    assert StudentAccessPolicy.can_modify(
        actor_user_id=uuid4(),
        actor_roles=frozenset({"institute_admin"}),
        student=student,
    ) is True
