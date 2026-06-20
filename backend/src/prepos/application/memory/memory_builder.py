from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from prepos.application.memory.milestone_detection import (
    detect_forecast_milestone,
    detect_goal_milestone,
    detect_readiness_milestones,
    detect_weakness_resolved_milestone,
)
from prepos.application.recommendations.recommendation_engine import format_concept_name
from prepos.infrastructure.db.models.copilot_analytics import CopilotQueryModel
from prepos.infrastructure.db.models.recommendation_analytics import RecommendationEventModel
from prepos.infrastructure.db.models.recommendation_outcomes import RecommendationOutcomeModel


class MemoryBuilder:
    def __init__(self, *, session: AsyncSession) -> None:
        self._session = session

    async def build_for_user(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        persona: str,
        student_id: UUID,
    ) -> list[dict[str, object]]:
        now = datetime.now(UTC)
        records: list[dict[str, object]] = []

        shown_stmt = select(RecommendationEventModel).where(
            RecommendationEventModel.tenant_id == tenant_id,
            RecommendationEventModel.student_id == student_id,
            RecommendationEventModel.event_type == "recommendation_shown",
        ).order_by(RecommendationEventModel.created_at.desc()).limit(50)
        shown_result = await self._session.execute(shown_stmt)
        for event in shown_result.scalars():
            if event.concept_id is None:
                continue
            records.append(
                {
                    "memory_type": "recommendation_history",
                    "memory_key": f"recommendation_history:{event.concept_id}:{event.id}",
                    "memory_value": {
                        "concept_id": event.concept_id,
                        "concept_name": format_concept_name(event.concept_id),
                        "impact_score": float(event.impact_score) if event.impact_score is not None else None,
                        "predicted_gain": float(event.estimated_gain) if event.estimated_gain is not None else None,
                        "shown_at": event.created_at.isoformat(),
                        **dict(event.metadata_json or {}),
                    },
                    "persona": persona,
                    "timestamp": event.created_at,
                }
            )

        outcome_stmt = select(RecommendationOutcomeModel).where(
            RecommendationOutcomeModel.tenant_id == tenant_id,
            RecommendationOutcomeModel.student_id == student_id,
        ).order_by(RecommendationOutcomeModel.created_at.desc()).limit(50)
        outcome_result = await self._session.execute(outcome_stmt)
        previous_readiness: float | None = None
        for outcome in outcome_result.scalars():
            concept_name = format_concept_name(outcome.concept_id)
            records.append(
                {
                    "memory_type": "recommendation_outcomes",
                    "memory_key": f"recommendation_outcomes:{outcome.concept_id}:{outcome.id}",
                    "memory_value": {
                        "concept_id": outcome.concept_id,
                        "concept_name": concept_name,
                        "effectiveness_score": float(outcome.effectiveness_score or 0),
                        "actual_gain": float(outcome.actual_gain or 0),
                        "predicted_gain": float(outcome.predicted_gain or 0),
                        "status": outcome.status,
                        "completed_at": outcome.created_at.isoformat(),
                    },
                    "persona": persona,
                    "timestamp": outcome.created_at,
                }
            )
            weakness_milestone = detect_weakness_resolved_milestone(
                concept_id=outcome.concept_id,
                weakness_before=float(outcome.weakness_before) if outcome.weakness_before is not None else None,
                weakness_after=float(outcome.weakness_after) if outcome.weakness_after is not None else None,
                occurred_at=outcome.created_at,
            )
            if weakness_milestone is not None:
                records.append(
                    {
                        "memory_type": "progress_milestones",
                        "memory_key": weakness_milestone.memory_key,
                        "memory_value": weakness_milestone.memory_value,
                        "persona": persona,
                        "timestamp": outcome.created_at,
                    }
                )
            readiness_before = float(outcome.readiness_before) if outcome.readiness_before is not None else previous_readiness
            readiness_after = float(outcome.readiness_after) if outcome.readiness_after is not None else None
            for milestone in detect_readiness_milestones(
                previous_readiness=readiness_before,
                current_readiness=readiness_after,
                occurred_at=outcome.created_at,
            ):
                records.append(
                    {
                        "memory_type": "progress_milestones",
                        "memory_key": milestone.memory_key,
                        "memory_value": milestone.memory_value,
                        "persona": persona,
                        "timestamp": outcome.created_at,
                    }
                )
            forecast_milestone = detect_forecast_milestone(
                forecast_before=float(outcome.forecast_before) if outcome.forecast_before is not None else None,
                forecast_after=float(outcome.forecast_after) if outcome.forecast_after is not None else None,
                target=float(outcome.forecast_before or 0) + float(outcome.predicted_gain or 0),
                occurred_at=outcome.created_at,
            )
            if forecast_milestone is not None:
                records.append(
                    {
                        "memory_type": "progress_milestones",
                        "memory_key": forecast_milestone.memory_key,
                        "memory_value": forecast_milestone.memory_value,
                        "persona": persona,
                        "timestamp": outcome.created_at,
                    }
                )
            previous_readiness = readiness_after

            if outcome.status == "successful" and persona == "mentor":
                records.append(
                    {
                        "memory_type": "mentor_interventions",
                        "memory_key": f"mentor_interventions:success:{outcome.concept_id}:{outcome.id}",
                        "memory_value": {
                            "concept_id": outcome.concept_id,
                            "concept_name": concept_name,
                            "effectiveness_score": float(outcome.effectiveness_score or 0),
                            "actual_gain": float(outcome.actual_gain or 0),
                            "status": outcome.status,
                        },
                        "persona": persona,
                        "timestamp": outcome.created_at,
                    }
                )
            if outcome.status == "failed" and persona == "mentor":
                records.append(
                    {
                        "memory_type": "mentor_interventions",
                        "memory_key": f"mentor_interventions:failed:{outcome.concept_id}:{outcome.id}",
                        "memory_value": {
                            "concept_id": outcome.concept_id,
                            "concept_name": concept_name,
                            "effectiveness_score": float(outcome.effectiveness_score or 0),
                            "actual_gain": float(outcome.actual_gain or 0),
                            "status": outcome.status,
                        },
                        "persona": persona,
                        "timestamp": outcome.created_at,
                    }
                )

            if outcome.weakness_before is not None and outcome.weakness_after is not None:
                trend_delta = float(outcome.weakness_before) - float(outcome.weakness_after)
                if trend_delta != 0:
                    records.append(
                        {
                            "memory_type": "weakness_trends",
                            "memory_key": f"weakness_trends:{outcome.concept_id}:{outcome.id}",
                            "memory_value": {
                                "concept_id": outcome.concept_id,
                                "concept_name": concept_name,
                                "weakness_before": float(outcome.weakness_before),
                                "weakness_after": float(outcome.weakness_after),
                                "delta": round(trend_delta, 2),
                            },
                            "persona": persona,
                            "timestamp": outcome.created_at,
                        }
                    )

        query_stmt = select(CopilotQueryModel).where(
            CopilotQueryModel.tenant_id == tenant_id,
            CopilotQueryModel.user_id == user_id,
        ).order_by(CopilotQueryModel.created_at.desc()).limit(30)
        query_result = await self._session.execute(query_stmt)
        for query in query_result.scalars():
            if query.intent in {"draft_coaching_note", "coaching_guidance"}:
                records.append(
                    {
                        "memory_type": "coaching_notes",
                        "memory_key": f"coaching_notes:{query.id}",
                        "memory_value": {
                            "intent": query.intent,
                            "question": query.query_text,
                            "created_at": query.created_at.isoformat(),
                        },
                        "persona": persona,
                        "timestamp": query.created_at,
                    }
                )

        goal_milestone = detect_goal_milestone(
            on_track=True,
            goal_probability=None,
            occurred_at=now,
        )
        if goal_milestone is not None and len(records) >= 3:
            records.append(
                {
                    "memory_type": "goal_changes",
                    "memory_key": goal_milestone.memory_key.replace("progress_milestones", "goal_changes"),
                    "memory_value": goal_milestone.memory_value,
                    "persona": persona,
                    "timestamp": now,
                }
            )

        records.sort(key=lambda item: item["timestamp"], reverse=True)  # type: ignore[index]
        return records
