from __future__ import annotations

from prepos.application.cohort.cohort_models import StudentCohortInput
from prepos.application.cohort.cohort_segmentation_engine import segment_student
from prepos.application.recommendations.recommendation_engine import format_concept_name


def build_risk_items(
    students: list[StudentCohortInput],
    *,
    limit: int = 20,
) -> list[dict[str, object]]:
    items: list[dict[str, object]] = []
    for student in students:
        result = segment_student(student)
        if result.risk_score < 40 and result.segment_type not in {"at_risk", "critical_risk"}:
            continue
        items.append(
            {
                "student_id": student.student_id,
                "risk_score": result.risk_score,
                "segment_type": result.segment_type,
                "readiness": student.readiness,
                "forecast_probability": student.forecast_probability,
                "top_risk_factors": list(result.risk_factors),
            }
        )
    items.sort(key=lambda row: float(row["risk_score"]), reverse=True)
    return items[:limit]


def count_at_risk(students: list[StudentCohortInput]) -> int:
    return sum(
        1
        for student in students
        if segment_student(student).segment_type in {"at_risk", "critical_risk"}
    )


def top_improvers(students: list[StudentCohortInput], limit: int = 10) -> list[StudentCohortInput]:
    return sorted(students, key=lambda item: item.readiness_delta, reverse=True)[:limit]


def stagnant_students(students: list[StudentCohortInput], limit: int = 10) -> list[StudentCohortInput]:
    stagnant = [
        student
        for student in students
        if segment_student(student).segment_type == "stagnant"
    ]
    return stagnant[:limit]
