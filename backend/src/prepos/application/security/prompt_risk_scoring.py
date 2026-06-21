from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from prepos.application.security.prompt_injection_detector import DetectionResult

CATEGORY_WEIGHTS: dict[str, float] = {
    "ignore_instructions": 25.0,
    "reveal_system_prompt": 30.0,
    "bypass_restrictions": 35.0,
    "cross_tenant_data": 40.0,
    "jailbreak": 30.0,
}

BLOCK_THRESHOLD = 70.0
HIGH_THRESHOLD = 50.0
MEDIUM_THRESHOLD = 25.0


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class RiskAssessment:
    risk_score: float
    risk_level: RiskLevel
    blocked: bool
    blocked_reason: str | None


def score_prompt_risk(detection: DetectionResult) -> RiskAssessment:
    if not detection.categories:
        return RiskAssessment(
            risk_score=0.0,
            risk_level=RiskLevel.LOW,
            blocked=False,
            blocked_reason=None,
        )

    score = min(
        100.0,
        sum(CATEGORY_WEIGHTS.get(category, 15.0) for category in detection.categories),
    )
    if score >= BLOCK_THRESHOLD or "cross_tenant_data" in detection.categories:
        level = RiskLevel.CRITICAL
        blocked = True
        reason = f"Blocked: detected {', '.join(detection.categories)}"
    elif score >= HIGH_THRESHOLD:
        level = RiskLevel.HIGH
        blocked = True
        reason = f"Blocked: high-risk prompt ({', '.join(detection.categories)})"
    elif score >= MEDIUM_THRESHOLD:
        level = RiskLevel.MEDIUM
        blocked = False
        reason = None
    else:
        level = RiskLevel.LOW
        blocked = False
        reason = None

    return RiskAssessment(
        risk_score=score,
        risk_level=level,
        blocked=blocked,
        blocked_reason=reason,
    )
