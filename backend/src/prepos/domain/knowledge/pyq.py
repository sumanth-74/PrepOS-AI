from __future__ import annotations

import re
from dataclasses import dataclass

PYQ_SOURCE_TYPE = "pyq"

PYQ_BOOST_KEYWORDS: tuple[str, ...] = (
    "previous year",
    "pyq",
    "asked before",
    "important questions",
    "previous years",
    "past year",
    "upsc asked",
)

PYQ_BOOST_MULTIPLIER = 1.35
DEFAULT_PYQ_MULTIPLIER = 1.0

TREND_RECENT_YEARS = 5
TREND_FLOOR = 0.5
TREND_CEIL = 2.0


def is_pyq_source_type(source_type: str | None) -> bool:
    return (source_type or "").strip().lower() == PYQ_SOURCE_TYPE


def is_pyq_boost_query(query: str) -> bool:
    normalized = re.sub(r"\s+", " ", query.strip().lower())
    return any(keyword in normalized for keyword in PYQ_BOOST_KEYWORDS)


def pyq_boost_multiplier(
    *,
    source_type: str | None,
    query: str,
    prefer_pyq: bool,
) -> float:
    if not is_pyq_source_type(source_type):
        return DEFAULT_PYQ_MULTIPLIER
    if prefer_pyq or is_pyq_boost_query(query):
        return PYQ_BOOST_MULTIPLIER
    return DEFAULT_PYQ_MULTIPLIER


def apply_pyq_ranking_boost(
    *,
    base_score: float,
    source_type: str | None,
    query: str,
    prefer_pyq: bool,
) -> float:
    return base_score * pyq_boost_multiplier(
        source_type=source_type,
        query=query,
        prefer_pyq=prefer_pyq,
    )


@dataclass(frozen=True, slots=True)
class ParsedPyqQuestion:
    year: int
    exam_stage: str
    paper: str
    question_text: str
    answer_text: str | None
    source_reference: str | None
    difficulty: int | None
    importance: str | None
    concept_ids: tuple[str, ...]
    metadata: dict[str, object]


def parse_pyq_upload(*, content: str) -> list[ParsedPyqQuestion]:
    import json

    stripped = content.strip()
    if not stripped:
        return []

    if stripped.startswith("["):
        payload = json.loads(stripped)
        if not isinstance(payload, list):
            raise ValueError("PYQ JSON upload must be an array of question objects.")
        return [_parse_json_question(item) for item in payload]

    questions: list[ParsedPyqQuestion] = []
    blocks = re.split(r"\n---+\n", stripped)
    for block in blocks:
        parsed = _parse_text_block(block.strip())
        if parsed is not None:
            questions.append(parsed)
    return questions


def _parse_json_question(item: object) -> ParsedPyqQuestion:
    if not isinstance(item, dict):
        raise ValueError("Each PYQ entry must be a JSON object.")
    question_text = str(item.get("question_text", "")).strip()
    if not question_text:
        raise ValueError("PYQ entry missing question_text.")
    year = int(item["year"])
    exam_stage = str(item.get("exam_stage", "prelims")).strip()
    paper = str(item.get("paper", "GS1")).strip()
    concept_ids_raw = item.get("concept_ids", [])
    concept_ids = tuple(str(c).strip() for c in concept_ids_raw if str(c).strip()) if isinstance(concept_ids_raw, list) else ()
    difficulty_raw = item.get("difficulty")
    difficulty = int(difficulty_raw) if difficulty_raw is not None else None
    return ParsedPyqQuestion(
        year=year,
        exam_stage=exam_stage,
        paper=paper,
        question_text=question_text,
        answer_text=str(item["answer_text"]).strip() if item.get("answer_text") else None,
        source_reference=str(item["source_reference"]).strip() if item.get("source_reference") else None,
        difficulty=difficulty,
        importance=str(item["importance"]).strip() if item.get("importance") else None,
        concept_ids=concept_ids,
        metadata={k: v for k, v in item.items() if k not in {"question_text", "answer_text", "concept_ids"}},
    )


def _parse_text_block(block: str) -> ParsedPyqQuestion | None:
    if not block:
        return None
    lines = block.splitlines()
    header = lines[0] if lines else ""
    match = re.match(
        r"^(?P<year>\d{4})\s*\|\s*(?P<stage>[^|]+)\|\s*(?P<paper>[^|]+)\|\s*(?P<rest>.+)$",
        header.strip(),
    )
    if match is None:
        return None
    question_text = match.group("rest").strip()
    body = "\n".join(lines[1:]).strip()
    answer_text = None
    if body.startswith("Answer:"):
        answer_text = body.split("Answer:", maxsplit=1)[1].strip()
    elif "Answer:" in body:
        question_part, answer_part = body.split("Answer:", maxsplit=1)
        if question_part.strip():
            question_text = question_part.strip()
        answer_text = answer_part.strip()
    elif body:
        question_text = f"{question_text}\n{body}".strip()
    concept_ids = map_concepts_from_pyq_text(body)
    return ParsedPyqQuestion(
        year=int(match.group("year")),
        exam_stage=match.group("stage").strip(),
        paper=match.group("paper").strip(),
        question_text=question_text,
        answer_text=answer_text,
        source_reference=None,
        difficulty=None,
        importance=None,
        concept_ids=concept_ids,
        metadata={},
    )


def map_concepts_from_pyq_text(text: str) -> tuple[str, ...]:
    from prepos.domain.knowledge.concept_mapping import map_concepts_from_text

    return map_concepts_from_text(title="", content_preview=text)


def format_pyq_chunk_content(question: ParsedPyqQuestion) -> str:
    lines = [
        f"Year: {question.year}",
        f"Paper: {question.paper}",
        f"Stage: {question.exam_stage}",
        f"Question: {question.question_text}",
    ]
    if question.answer_text:
        lines.append(f"Answer: {question.answer_text}")
    if question.source_reference:
        lines.append(f"Source: {question.source_reference}")
    return "\n".join(lines)
