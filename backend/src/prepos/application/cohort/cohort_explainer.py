from __future__ import annotations

from prepos.application.cohort.cohort_models import CohortMetrics, SegmentationResult, StudentCohortInput


def explain_segment(
    *,
    inputs: StudentCohortInput,
    result: SegmentationResult,
) -> list[str]:
    lines = [
        f"Segment: {result.segment_type.replace('_', ' ')} (score {result.segment_score:.1f}).",
        f"Risk score {result.risk_score:.1f}/100.",
        f"Readiness {inputs.readiness:.1f}, forecast success {inputs.forecast_probability:.1f}%.",
    ]
    if result.risk_factors:
        lines.append("Risk factors: " + ", ".join(result.risk_factors) + ".")
    lines.append(
        f"Planning adherence {inputs.planning_adherence:.1f}%, "
        f"recommendation effectiveness {inputs.recommendation_effectiveness:.1f}%, "
        f"intervention effectiveness {inputs.intervention_effectiveness:.1f}%."
    )
    return lines


def explain_cohort_summary(
    *,
    cohort_id: str,
    student_count: int,
    segments: dict[str, int],
    metrics: CohortMetrics,
    top_risks: list[str],
) -> list[str]:
    lines = [
        f"Cohort {cohort_id} has {student_count} students.",
        f"Cohort health score: {metrics.cohort_health_score:.1f}/100.",
        f"Average readiness {metrics.average_readiness:.1f}, forecast {metrics.average_forecast:.1f}%.",
    ]
    if segments:
        top_segment = max(segments.items(), key=lambda pair: pair[1])
        lines.append(f"Largest segment: {top_segment[0].replace('_', ' ')} ({top_segment[1]} students).")
    if top_risks:
        lines.append("Top concept risks: " + ", ".join(top_risks) + ".")
    return lines
