from __future__ import annotations

from uuid import UUID

from prepos.application.twin.snapshot_dto import TwinSnapshotResponse
from prepos.application.twin.snapshot_ports import TwinSnapshotRepositoryPort


class TwinSnapshotReadService:
    def __init__(self, *, snapshot_repo: TwinSnapshotRepositoryPort) -> None:
        self._snapshot_repo = snapshot_repo

    async def get_snapshot(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str | None = None,
    ) -> TwinSnapshotResponse:
        if exam_id is not None:
            snapshot = await self._snapshot_repo.get_snapshot(tenant_id, student_id, exam_id)
        else:
            snapshot = await self._snapshot_repo.get_snapshot_for_student(tenant_id, student_id)

        if snapshot is None:
            return TwinSnapshotResponse(
                readiness_score=None,
                average_mastery=None,
                average_retention=None,
                average_confidence=None,
                due_revision_count=0,
                high_risk_concept_count=0,
                largest_positive_driver=None,
                largest_negative_driver=None,
                generated_at=None,
            )

        return TwinSnapshotResponse(
            readiness_score=snapshot.readiness_score,
            average_mastery=snapshot.average_mastery,
            average_retention=snapshot.average_retention,
            average_confidence=snapshot.average_confidence,
            due_revision_count=snapshot.due_revision_count,
            high_risk_concept_count=snapshot.high_risk_concept_count,
            largest_positive_driver=snapshot.largest_positive_driver,
            largest_negative_driver=snapshot.largest_negative_driver,
            generated_at=snapshot.generated_at,
        )
