from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from uuid import UUID, uuid4

import structlog

from prepos.application.knowledge.dto import CreateKnowledgeSourceRequest
from prepos.application.knowledge.ports import KnowledgeRepositoryPort, KnowledgeStoragePort
from prepos.application.pyq.dto import CreatePyqUploadRequest, PyqQuestionResponse, PyqUploadResponse
from prepos.application.pyq.ports import CreatePyqQuestionInput, PyqQuestionRecord, PyqRepositoryPort, PyqStatisticRecord
from prepos.core.config import Settings
from prepos.core.exceptions import NotFoundError, ValidationError
from prepos.domain.knowledge.chunking import estimate_token_count
from prepos.domain.knowledge.entities import KnowledgeSourceStatus, KnowledgeSourceType
from prepos.domain.knowledge.pyq import (
    PYQ_SOURCE_TYPE,
    ParsedPyqQuestion,
    format_pyq_chunk_content,
    map_concepts_from_pyq_text,
    parse_pyq_upload,
)
from prepos.domain.pyq.trends import PyqQuestionYearHit, compute_concept_statistics

logger = structlog.get_logger(__name__)


class PYQIngestionService:
    def __init__(
        self,
        *,
        settings: Settings,
        repository: PyqRepositoryPort,
        knowledge_repository: KnowledgeRepositoryPort,
        storage: KnowledgeStoragePort,
        embed_task: object | None = None,
    ) -> None:
        self._settings = settings
        self._repository = repository
        self._knowledge_repository = knowledge_repository
        self._storage = storage
        self._embed_task = embed_task

    async def ingest_upload(
        self,
        *,
        tenant_id: UUID | None,
        request: CreatePyqUploadRequest,
        file_name: str,
        mime_type: str | None,
        file_bytes: bytes,
    ) -> PyqUploadResponse:
        if not file_bytes:
            raise ValidationError("Uploaded file is empty.")

        try:
            text = file_bytes.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValidationError("Uploaded file must be UTF-8 encoded text.") from exc

        try:
            parsed_questions = parse_pyq_upload(content=text)
        except (ValueError, KeyError) as exc:
            raise ValidationError(f"Invalid PYQ upload format: {exc}") from exc

        if not parsed_questions:
            raise ValidationError("No PYQ questions found in upload.")

        enriched = [_ensure_concepts(question) for question in parsed_questions]
        combined_text = "\n\n---PYQ---\n\n".join(format_pyq_chunk_content(q) for q in enriched)
        content_hash = hashlib.sha256(combined_text.encode("utf-8")).hexdigest()
        source_id = uuid4()
        started_at = datetime.now(UTC)

        external_uri = await self._storage.save_upload(
            tenant_id=tenant_id,
            source_id=source_id,
            file_name=file_name,
            content=combined_text.encode("utf-8"),
        )
        source = await self._knowledge_repository.create_source(
            tenant_id=tenant_id,
            exam_id=request.exam_id,
            source_type=KnowledgeSourceType.PYQ.value,
            title=request.title,
            external_uri=external_uri,
            content_hash=content_hash,
            catalog_version=request.catalog_version,
            status=KnowledgeSourceStatus.PROCESSING.value,
            file_name=file_name,
            mime_type=mime_type,
            metadata_json={"source_type": PYQ_SOURCE_TYPE},
            source_id=source_id,
            exam_stage=enriched[0].exam_stage if enriched else None,
        )
        source_id = source.id

        chunk_rows: list[tuple[int, str, int, dict[str, object]]] = []
        for index, question in enumerate(enriched):
            content = format_pyq_chunk_content(question)
            chunk_rows.append(
                (
                    index,
                    content,
                    estimate_token_count(content),
                    {
                        "source_type": PYQ_SOURCE_TYPE,
                        "year": question.year,
                        "paper": question.paper,
                        "exam_stage": question.exam_stage,
                        "concept_ids": list(question.concept_ids),
                    },
                )
            )

        chunk_records = await self._knowledge_repository.replace_chunks(source_id, chunk_rows)
        await self._knowledge_repository.update_source_status(
            source_id,
            status=KnowledgeSourceStatus.PROCESSING.value,
            chunk_count=len(chunk_records),
            ingestion_started_at=started_at,
        )

        create_inputs: list[CreatePyqQuestionInput] = []
        for question, chunk in zip(enriched, chunk_records, strict=True):
            create_inputs.append(
                CreatePyqQuestionInput(
                    year=question.year,
                    exam_stage=question.exam_stage,
                    paper=question.paper,
                    question_text=question.question_text,
                    answer_text=question.answer_text,
                    source_reference=question.source_reference,
                    difficulty=question.difficulty,
                    importance=question.importance,
                    concept_ids=question.concept_ids,
                    confidence_score=1.0,
                    metadata_json=dict(question.metadata),
                    knowledge_source_id=source_id,
                    knowledge_chunk_id=chunk.id,
                )
            )

        created = await self._repository.create_questions_batch(
            tenant_id=tenant_id,
            exam_id=request.exam_id,
            questions=create_inputs,
        )

        for record in created:
            if record.knowledge_chunk_id is not None:
                await self._knowledge_repository.update_chunk_metadata(
                    record.knowledge_chunk_id,
                    {
                        "source_type": PYQ_SOURCE_TYPE,
                        "year": record.year,
                        "paper": record.paper,
                        "exam_stage": record.exam_stage,
                        "concept_ids": list(record.concept_ids),
                        "pyq_id": str(record.id),
                    },
                )

        if self._embed_task is not None:
            self._embed_task.delay(str(source_id))

        await self._refresh_statistics(tenant_id=tenant_id, exam_id=request.exam_id)

        logger.info(
            "pyq_ingestion_started",
            source_id=str(source_id),
            question_count=len(created),
            tenant_id=str(tenant_id) if tenant_id else None,
        )

        refreshed = await self._knowledge_repository.get_source_by_id(source_id, tenant_id=tenant_id)
        if refreshed is None:
            raise NotFoundError("PYQ knowledge source not found after ingestion.")

        return PyqUploadResponse(
            knowledge_source_id=source_id,
            questions_ingested=len(created),
            questions=[_to_response(record) for record in created],
        )

    async def _refresh_statistics(self, *, tenant_id: UUID | None, exam_id: str) -> None:
        hits_raw = await self._repository.list_mapping_hits(tenant_id=tenant_id, exam_id=exam_id)
        hits = [
            PyqQuestionYearHit(concept_id=concept_id, year=year, confidence_score=score)
            for concept_id, year, score in hits_raw
        ]
        reference_year = datetime.now(UTC).year
        aggregates = compute_concept_statistics(hits=hits, reference_year=reference_year)
        now = datetime.now(UTC)
        stat_rows = [
            PyqStatisticRecord(
                exam_id=exam_id,
                concept_id=item.concept_id,
                pyq_count=item.pyq_count,
                first_appearance_year=item.first_appearance_year,
                last_appearance_year=item.last_appearance_year,
                frequency_score=item.frequency_score,
                trend_score=item.trend_score,
                updated_at=now,
            )
            for item in aggregates
        ]
        await self._repository.replace_statistics(exam_id=exam_id, statistics=stat_rows)


def _ensure_concepts(question: ParsedPyqQuestion) -> ParsedPyqQuestion:
    if question.concept_ids:
        return question
    mapped = map_concepts_from_pyq_text(question.question_text)
    return ParsedPyqQuestion(
        year=question.year,
        exam_stage=question.exam_stage,
        paper=question.paper,
        question_text=question.question_text,
        answer_text=question.answer_text,
        source_reference=question.source_reference,
        difficulty=question.difficulty,
        importance=question.importance,
        concept_ids=mapped,
        metadata=question.metadata,
    )


def _to_response(record: PyqQuestionRecord) -> PyqQuestionResponse:
    return PyqQuestionResponse(
        id=record.id,
        tenant_id=record.tenant_id,
        exam_id=record.exam_id,
        year=record.year,
        exam_stage=record.exam_stage,
        paper=record.paper,
        question_text=record.question_text,
        answer_text=record.answer_text,
        source_reference=record.source_reference,
        difficulty=record.difficulty,
        importance=record.importance,
        concept_ids=list(record.concept_ids),
        knowledge_source_id=record.knowledge_source_id,
        knowledge_chunk_id=record.knowledge_chunk_id,
        metadata=record.metadata_json,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )
