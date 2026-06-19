from __future__ import annotations

from decimal import Decimal

from prepos.domain.goal.milestones_v1 import MilestoneStatus
from prepos.domain.scoring.common import round_score

MILESTONE_EXPLANATIONS_V1 = "milestone_explanations_v1"


def _format_gap(value: Decimal) -> str:
    return f"{round_score(abs(value)):.2f}".rstrip("0").rstrip(".")


def explain_milestone_status_v1(
    *,
    status: MilestoneStatus,
    current_gap: Decimal,
) -> str:
    """Deterministic milestone progress copy."""
    if status == MilestoneStatus.BEHIND:
        return f"You are {_format_gap(current_gap)} readiness points behind the current milestone."
    if status == MilestoneStatus.AHEAD:
        ahead_by = round_score(abs(current_gap))
        return f"You are ahead of schedule by {_format_gap(ahead_by)} readiness points."
    return "Maintaining your current study plan keeps you on track."
