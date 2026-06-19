from __future__ import annotations

from enum import StrEnum


class ExperienceLevel(StrEnum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    REPEATER = "repeater"


class ProvisionStatus(StrEnum):
    PENDING = "pending"
    PROVISIONED = "provisioned"
    FAILED = "failed"


class TwinStatus(StrEnum):
    PROVISIONED = "provisioned"
    ACTIVE = "active"
    ARCHIVED = "archived"
