from __future__ import annotations

import asyncio
from collections.abc import Callable, Coroutine
from datetime import UTC, datetime
from decimal import Decimal
from typing import TypeVar
from uuid import UUID, uuid4

from prepos.application.exam.ports import ExamCatalogUnitOfWorkPort
from prepos.application.learning_graph.ports import LearningGraphRepositoryPort
from prepos.domain.exam.value_objects import CatalogStatus
from prepos.domain.learning_graph.entities import ConceptProgressNode, LearningGraphEvent, ScoreAuditLog
from prepos.domain.learning_graph.events import LearningGraphUpdated
from prepos.domain.learning_graph.exceptions import GraphProvisioningFailedError, NodeNotFoundError
from prepos.domain.learning_graph.policies import LearningGraphPolicy, NodeStatus
from prepos.domain.scoring.confidence_v1 import CONFIDENCE_V1, ConfidenceInputs, compute_confidence_v1
from prepos.domain.scoring.importance_copy_v1 import (
    IMPORTANCE_COPY_V1,
    ImportanceCopyInputs,
    compute_importance_copy_v1,
)
from prepos.domain.scoring.mastery_nonmcq_v1 import MASTERY_NONMCQ_V1, compute_mastery_nonmcq_v1
from prepos.domain.scoring.mastery_v1 import (
    MASTERY_V1,
    McqAttemptEvidence,
    McqDifficulty,
    RecencyWeightedEvidence,
    build_mastery_evidence,
    compute_mastery_v1,
)
from prepos.domain.scoring.retention_v1 import (
    RETENTION_V1,
    apply_revision_retention_update,
)
from prepos.events.outbox.publisher import OutboxPublisher
from prepos.infrastructure.cache.learning_graph_cache import LearningGraphCachePort

T = TypeVar("T")


class LearningGraphService:
    """Sole writer of student_concept_progress score and evidence columns."""

    BATCH_SIZE = 500

    def __init__(
        self,
        *,
        repo: LearningGraphRepositoryPort,
        exam_uow: ExamCatalogUnitOfWorkPort,
        outbox: OutboxPublisher,
        cache: LearningGraphCachePort,
        max_retries: int = 3,
    ) -> None:
        self._repo = repo
        self._exam_uow = exam_uow
        self._outbox = outbox
        self._cache = cache
        self._max_retries = max_retries

    async def provision_from_onboarding(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        catalog_version: str,
        correlation_id: str,
        causation_id: str | None,
    ) -> int:
        provision = await self._repo.count_nodes(tenant_id, student_id)
        concepts = await self._exam_uow.concept_repo.list_concepts_by_exam(
            exam_id,
            status=CatalogStatus.ACTIVE.value,
            catalog_version=catalog_version,
        )
        if not concepts:
            raise GraphProvisioningFailedError(
                "No active concepts found for provisioning.",
                details={"exam_id": exam_id, "catalog_version": catalog_version},
            )

        expected = len(concepts)
        if provision >= expected:
            await self._repo.update_provision_count(
                tenant_id,
                student_id,
                provisioned_node_count=provision,
                status="complete",
            )
            return provision

        now = datetime.now(UTC)
        inserted_total = 0
        batch: list[ConceptProgressNode] = []
        for concept in concepts:
            importance = (
                concept.importance
                if concept.importance is not None
                else LearningGraphPolicy.DEFAULT_IMPORTANCE
            )
            if importance is None:
                importance = LearningGraphPolicy.DEFAULT_IMPORTANCE
            batch.append(
                ConceptProgressNode(
                    id=uuid4(),
                    tenant_id=tenant_id,
                    student_id=student_id,
                    exam_id=exam_id,
                    catalog_version=catalog_version,
                    concept_id=concept.concept_id,
                    subject_id=concept.subject_id,
                    topic_id=concept.topic_id,
                    mastery_score=Decimal("0"),
                    mastery_nonmcq_score=Decimal("0"),
                    retention_score=None,
                    confidence_score=None,
                    importance_score=Decimal(str(importance)),
                    overconfidence_flag=False,
                    mcq_attempt_count=0,
                    mcq_correct_count=0,
                    nonmcq_attempt_count=0,
                    revision_count=0,
                    study_minutes=0,
                    node_state=NodeStatus.UNRATED,
                    mastery_version=MASTERY_V1,
                    mastery_nonmcq_version=MASTERY_NONMCQ_V1,
                    retention_version=RETENTION_V1,
                    confidence_version=CONFIDENCE_V1,
                    importance_version=IMPORTANCE_COPY_V1,
                    first_seen_at=now,
                    last_activity_at=None,
                    row_version=1,
                    created_at=now,
                    updated_at=now,
                )
            )
            if len(batch) >= self.BATCH_SIZE:
                inserted_total += await self._repo.bulk_insert_nodes(tuple(batch))
                batch.clear()

        if batch:
            inserted_total += await self._repo.bulk_insert_nodes(tuple(batch))

        final_count = await self._repo.count_nodes(tenant_id, student_id)
        await self._repo.update_provision_count(
            tenant_id,
            student_id,
            provisioned_node_count=final_count,
            status="complete" if final_count >= expected else "provisioned",
        )
        await self._cache.invalidate_student(tenant_id, student_id)
        return final_count

    async def handle_assessment_completed(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        concept_id: str,
        mcq_correct: bool,
        self_confidence: Decimal | None,
        correlation_id: str,
        causation_id: str | None,
    ) -> ConceptProgressNode:
        async def mutate() -> ConceptProgressNode:
            node = await self._repo.get_node(tenant_id, student_id, concept_id)
            if node is None:
                raise NodeNotFoundError(
                    "Concept progress node not found.",
                    details={"concept_id": concept_id, "student_id": str(student_id)},
                )
            return await self._apply_assessment_evidence_update(
                node=node,
                reason="AssessmentCompleted",
                correlation_id=correlation_id,
                causation_id=causation_id,
                mcq_delta=(1, 1 if mcq_correct else 0),
                self_confidence=self_confidence,
            )

        return await self._with_retry(mutate)

    async def handle_revision_completed(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        concept_id: str,
        recall_grade: str,
        correlation_id: str,
        causation_id: str | None,
    ) -> ConceptProgressNode:
        async def mutate() -> ConceptProgressNode:
            node = await self._repo.get_node(tenant_id, student_id, concept_id)
            if node is None:
                raise NodeNotFoundError(
                    "Concept progress node not found.",
                    details={"concept_id": concept_id},
                )
            revision_component = Decimal("1") if recall_grade in {"good", "easy"} else Decimal("0.5")
            return await self._apply_revision_evidence_update(
                node=node,
                reason="RevisionCompleted",
                correlation_id=correlation_id,
                causation_id=causation_id,
                revision_delta=1,
                revision_component_override=revision_component,
                recall_grade=recall_grade,
            )

        return await self._with_retry(mutate)

    async def handle_study_session_logged(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        concept_id: str,
        engaged_minutes: int,
        correlation_id: str,
        causation_id: str | None,
    ) -> ConceptProgressNode:
        async def mutate() -> ConceptProgressNode:
            node = await self._repo.get_node(tenant_id, student_id, concept_id)
            if node is None:
                raise NodeNotFoundError(
                    "Concept progress node not found.",
                    details={"concept_id": concept_id},
                )
            return await self._apply_study_evidence_update(
                node=node,
                reason="StudySessionLogged",
                correlation_id=correlation_id,
                causation_id=causation_id,
                study_minutes_delta=engaged_minutes,
            )

        return await self._with_retry(mutate)

    async def handle_pyq_data_changed(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        concept_id: str,
        global_importance: Decimal,
        correlation_id: str,
        causation_id: str | None,
    ) -> ConceptProgressNode:
        async def mutate() -> ConceptProgressNode:
            node = await self._repo.get_node(tenant_id, student_id, concept_id)
            if node is None:
                raise NodeNotFoundError(
                    "Concept progress node not found.",
                    details={"concept_id": concept_id},
                )
            importance_result = compute_importance_copy_v1(
                ImportanceCopyInputs(global_importance=global_importance)
            )
            updated = self._replace_scores(
                node,
                importance_score=importance_result.value,
                changed_scores=("importance",),
                now=datetime.now(UTC),
            )
            return await self._persist_mutation(
                previous=node,
                updated=updated,
                reason="PYQDataChanged",
                correlation_id=correlation_id,
                causation_id=causation_id,
            )

        return await self._with_retry(mutate)

    async def _apply_assessment_evidence_update(
        self,
        *,
        node: ConceptProgressNode,
        reason: str,
        correlation_id: str,
        causation_id: str | None,
        mcq_delta: tuple[int, int],
        self_confidence: Decimal | None = None,
    ) -> ConceptProgressNode:
        """Assessment path: mastery, mastery_nonmcq, and confidence only."""
        return await self._apply_evidence_update(
            node=node,
            reason=reason,
            correlation_id=correlation_id,
            causation_id=causation_id,
            mcq_delta=mcq_delta,
            self_confidence=self_confidence,
            recompute_confidence=True,
            update_retention=False,
        )

    async def _apply_revision_evidence_update(
        self,
        *,
        node: ConceptProgressNode,
        reason: str,
        correlation_id: str,
        causation_id: str | None,
        revision_delta: int,
        revision_component_override: Decimal | None = None,
        recall_grade: str,
    ) -> ConceptProgressNode:
        """Revision path: owns retention state; preserves confidence."""
        return await self._apply_evidence_update(
            node=node,
            reason=reason,
            correlation_id=correlation_id,
            causation_id=causation_id,
            revision_delta=revision_delta,
            revision_component_override=revision_component_override,
            recompute_confidence=False,
            update_retention="revision",
            recall_grade=recall_grade,
        )

    async def _apply_study_evidence_update(
        self,
        *,
        node: ConceptProgressNode,
        reason: str,
        correlation_id: str,
        causation_id: str | None,
        study_minutes_delta: int,
    ) -> ConceptProgressNode:
        """Study path: reinforcement evidence only; updates retention_last_event_at."""
        return await self._apply_evidence_update(
            node=node,
            reason=reason,
            correlation_id=correlation_id,
            causation_id=causation_id,
            study_minutes_delta=study_minutes_delta,
            recompute_confidence=False,
            update_retention="study_event",
        )

    async def _apply_evidence_update(
        self,
        *,
        node: ConceptProgressNode,
        reason: str,
        correlation_id: str,
        causation_id: str | None,
        mcq_delta: tuple[int, int] | None = None,
        revision_delta: int = 0,
        revision_component_override: Decimal | None = None,
        study_minutes_delta: int = 0,
        self_confidence: Decimal | None = None,
        recompute_confidence: bool = False,
        update_retention: bool | str = False,
        recall_grade: str | None = None,
    ) -> ConceptProgressNode:
        if not LearningGraphPolicy.can_mutate(node):
            return node

        now = datetime.now(UTC)
        mcq_attempt_count = node.mcq_attempt_count + (mcq_delta[0] if mcq_delta else 0)
        mcq_correct_count = node.mcq_correct_count + (mcq_delta[1] if mcq_delta else 0)
        revision_count = node.revision_count + revision_delta
        study_minutes = node.study_minutes + study_minutes_delta

        mcq_attempts: tuple[McqAttemptEvidence, ...] = ()
        if mcq_attempt_count > 0:
            accuracy = mcq_correct_count / mcq_attempt_count
            mcq_attempts = (
                McqAttemptEvidence(
                    correct=accuracy >= Decimal("0.5"),
                    difficulty=McqDifficulty.MEDIUM,
                    age_days=Decimal("0"),
                ),
            ) * mcq_attempt_count

        revision_evidences: tuple[RecencyWeightedEvidence, ...] = ()
        if revision_count > 0:
            revision_evidences = (
                RecencyWeightedEvidence(
                    value_unit=revision_component_override or Decimal("0.7"),
                    age_days=Decimal("0"),
                ),
            )

        evidence = build_mastery_evidence(
            mcq_attempts=mcq_attempts,
            revision_evidences=revision_evidences,
            study_minutes=Decimal(study_minutes),
            n_study_sessions=1 if study_minutes > 0 else 0,
        )

        mastery_result = compute_mastery_v1(evidence)
        nonmcq_result = compute_mastery_nonmcq_v1(evidence)
        nonmcq_value = (
            nonmcq_result.value
            if nonmcq_result is not None and nonmcq_result.value is not None
            else Decimal("0")
        )
        if recompute_confidence:
            confidence_result = compute_confidence_v1(
                ConfidenceInputs(
                    n_mcq=mcq_attempt_count,
                    mcq_accuracy_unit=(
                        Decimal(mcq_correct_count) / Decimal(mcq_attempt_count)
                        if mcq_attempt_count > 0
                        else Decimal("0")
                    ),
                    self_confidence=self_confidence,
                )
            )
            confidence_score: Decimal | None = confidence_result.value
            confidence_version = CONFIDENCE_V1
        else:
            confidence_score = node.confidence_score
            confidence_version = node.confidence_version

        retention_score = node.retention_score
        retention_stability_s = node.retention_stability_s
        retention_last_event_at = node.retention_last_event_at
        retention_last_review_at = node.retention_last_review_at
        retention_last_grade = node.retention_last_grade

        if update_retention == "revision" and recall_grade is not None:
            (
                retention_stability_s,
                retention_score,
                retention_last_review_at,
                retention_last_event_at,
                retention_last_grade,
            ) = apply_revision_retention_update(
                mastery_score=mastery_result.value,
                prior_stability_s=node.retention_stability_s,
                recall_grade=recall_grade,
                current_time=now,
            )
        elif update_retention == "study_event":
            retention_last_event_at = now

        overconfidence = (
            LearningGraphPolicy.compute_overconfidence_flag(
                mastery=mastery_result.value,
                confidence=confidence_score,
            )
            if confidence_score is not None
            else False
        )
        node_state = LearningGraphPolicy.transition_on_evidence(node)

        updated = ConceptProgressNode(
            id=node.id,
            tenant_id=node.tenant_id,
            student_id=node.student_id,
            exam_id=node.exam_id,
            catalog_version=node.catalog_version,
            concept_id=node.concept_id,
            subject_id=node.subject_id,
            topic_id=node.topic_id,
            mastery_score=mastery_result.value,
            mastery_nonmcq_score=nonmcq_value,
            retention_score=retention_score,
            retention_stability_s=retention_stability_s,
            retention_last_event_at=retention_last_event_at,
            retention_last_review_at=retention_last_review_at,
            retention_last_grade=retention_last_grade,
            confidence_score=confidence_score,
            importance_score=node.importance_score,
            overconfidence_flag=overconfidence,
            mcq_attempt_count=mcq_attempt_count,
            mcq_correct_count=mcq_correct_count,
            nonmcq_attempt_count=node.nonmcq_attempt_count,
            revision_count=revision_count,
            study_minutes=study_minutes,
            node_state=node_state,
            mastery_version=MASTERY_V1,
            mastery_nonmcq_version=MASTERY_NONMCQ_V1,
            retention_version=RETENTION_V1,
            confidence_version=confidence_version,
            importance_version=node.importance_version,
            first_seen_at=node.first_seen_at,
            last_activity_at=now,
            row_version=node.row_version,
            created_at=node.created_at,
            updated_at=now,
        )
        return await self._persist_mutation(
            previous=node,
            updated=updated,
            reason=reason,
            correlation_id=correlation_id,
            causation_id=causation_id,
        )

    def _replace_scores(
        self,
        node: ConceptProgressNode,
        *,
        mastery_score: Decimal | None = None,
        mastery_nonmcq_score: Decimal | None = None,
        retention_score: Decimal | None = None,
        confidence_score: Decimal | None = None,
        importance_score: Decimal | None = None,
        overconfidence_flag: bool | None = None,
        changed_scores: tuple[str, ...] = (),
        now: datetime,
    ) -> ConceptProgressNode:
        return ConceptProgressNode(
            id=node.id,
            tenant_id=node.tenant_id,
            student_id=node.student_id,
            exam_id=node.exam_id,
            catalog_version=node.catalog_version,
            concept_id=node.concept_id,
            subject_id=node.subject_id,
            topic_id=node.topic_id,
            mastery_score=mastery_score if mastery_score is not None else node.mastery_score,
            mastery_nonmcq_score=(
                mastery_nonmcq_score if mastery_nonmcq_score is not None else node.mastery_nonmcq_score
            ),
            retention_score=retention_score if retention_score is not None else node.retention_score,
            retention_stability_s=node.retention_stability_s,
            retention_last_event_at=node.retention_last_event_at,
            retention_last_review_at=node.retention_last_review_at,
            retention_last_grade=node.retention_last_grade,
            confidence_score=confidence_score if confidence_score is not None else node.confidence_score,
            importance_score=importance_score if importance_score is not None else node.importance_score,
            overconfidence_flag=overconfidence_flag if overconfidence_flag is not None else node.overconfidence_flag,
            mcq_attempt_count=node.mcq_attempt_count,
            mcq_correct_count=node.mcq_correct_count,
            nonmcq_attempt_count=node.nonmcq_attempt_count,
            revision_count=node.revision_count,
            study_minutes=node.study_minutes,
            node_state=node.node_state,
            mastery_version=node.mastery_version,
            mastery_nonmcq_version=node.mastery_nonmcq_version,
            retention_version=node.retention_version,
            confidence_version=node.confidence_version,
            importance_version=(
                IMPORTANCE_COPY_V1 if importance_score is not None else node.importance_version
            ),
            first_seen_at=node.first_seen_at,
            last_activity_at=node.last_activity_at,
            row_version=node.row_version,
            created_at=node.created_at,
            updated_at=now,
        )

    async def _persist_mutation(
        self,
        *,
        previous: ConceptProgressNode,
        updated: ConceptProgressNode,
        reason: str,
        correlation_id: str,
        causation_id: str | None,
    ) -> ConceptProgressNode:
        now = datetime.now(UTC)
        saved = await self._repo.save_node(updated, expected_row_version=previous.row_version)

        scoring_versions = self._node_scoring_versions(saved)
        changed_scores = [
            name
            for name, old_val, new_val in (
                ("mastery", previous.mastery_score, saved.mastery_score),
                ("mastery_nonmcq", previous.mastery_nonmcq_score, saved.mastery_nonmcq_score),
                ("retention", previous.retention_score, saved.retention_score),
                ("confidence", previous.confidence_score, saved.confidence_score),
                ("importance", previous.importance_score, saved.importance_score),
            )
            if old_val != new_val
        ]

        for score_type, old_val, new_val in (
            ("mastery", previous.mastery_score, saved.mastery_score),
            ("mastery_nonmcq", previous.mastery_nonmcq_score, saved.mastery_nonmcq_score),
            ("retention", previous.retention_score, saved.retention_score),
            ("confidence", previous.confidence_score, saved.confidence_score),
            ("importance", previous.importance_score, saved.importance_score),
        ):
            if old_val != new_val:
                await self._repo.append_score_audit(
                    ScoreAuditLog(
                        id=uuid4(),
                        tenant_id=saved.tenant_id,
                        student_id=saved.student_id,
                        concept_id=saved.concept_id,
                        score_type=score_type,
                        previous_value=old_val,
                        new_value=new_val,
                        reason=reason,
                        causation_id=causation_id,
                        created_at=now,
                    )
                )

        await self._repo.append_graph_event(
            LearningGraphEvent(
                id=uuid4(),
                tenant_id=saved.tenant_id,
                student_id=saved.student_id,
                concept_id=saved.concept_id,
                event_type=reason,
                event_payload={"reason": reason, "changed_scores": changed_scores},
                causation_id=causation_id,
                correlation_id=correlation_id,
                event_version=1,
                occurred_at=now,
                recorded_at=now,
                scoring_versions=scoring_versions,
                created_at=now,
            )
        )

        lg_event = LearningGraphUpdated(
            tenant_id=saved.tenant_id,
            student_id=saved.student_id,
            concept_id=saved.concept_id,
            exam_id=saved.exam_id,
            mastery_score=saved.mastery_score,
            mastery_nonmcq_score=saved.mastery_nonmcq_score,
            retention_score=saved.retention_score,
            confidence_score=saved.confidence_score,
            importance_score=saved.importance_score,
            overconfidence_flag=saved.overconfidence_flag,
            node_state=saved.node_state,
            row_version=saved.row_version,
            changed_scores=tuple(changed_scores),
            scoring_versions=scoring_versions,
            causation_id=causation_id,
            correlation_id=correlation_id,
            occurred_at=now,
        )
        await self._outbox.enqueue_learning_graph_updated(lg_event)

        await self._cache.set_node(saved)
        await self._cache.invalidate_summary(saved.tenant_id, saved.student_id)
        return saved

    @staticmethod
    def _node_scoring_versions(node: ConceptProgressNode) -> dict[str, str]:
        return {
            "mastery": node.mastery_version,
            "mastery_nonmcq": node.mastery_nonmcq_version,
            "retention": node.retention_version,
            "confidence": node.confidence_version,
            "importance": node.importance_version,
        }

    async def _with_retry(self, operation: Callable[[], Coroutine[None, None, T]]) -> T:
        last_error: Exception | None = None
        for attempt in range(self._max_retries):
            try:
                return await operation()
            except Exception as exc:
                from prepos.domain.learning_graph.exceptions import OptimisticLockFailureError

                if not isinstance(exc, OptimisticLockFailureError):
                    raise
                last_error = exc
                if attempt < self._max_retries - 1:
                    await asyncio.sleep(0.01 * (attempt + 1))
        assert last_error is not None
        raise last_error
