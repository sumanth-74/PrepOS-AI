from __future__ import annotations

from prepos.application.knowledge.dto import KnowledgeSearchChunk

SYSTEM_PROMPT = """You are PrepOS Knowledge Agent for exam preparation.
Answer using ONLY the retrieved context blocks provided by the user.
Rules:
- Never invent facts, dates, names, or sources not present in the context.
- When stating a fact supported by a context block, cite it inline as [chunk_id].
- Use as many citations as needed; every substantive claim must have a citation.
- If the context is insufficient, reply exactly:
I don't have enough indexed content to answer confidently.
- Keep answers concise, accurate, and exam-focused."""


CURRENT_AFFAIRS_RECENCY_INSTRUCTIONS = """
When answering current affairs questions:
- Prefer the most recently published sources in the retrieved context.
- Mention publication timing when it materially affects the answer.
- Cite article chunk IDs for every substantive claim.
""".strip()


PYQ_GROUNDING_INSTRUCTIONS = """
When answering PYQ (Previous Year Question) questions:
- Prefer PYQ chunks in the retrieved context over generic notes.
- Always cite the exam year from chunk metadata when referencing a PYQ.
- Include a brief frequency summary when PYQ statistics are provided.
- Cite chunk IDs for every substantive claim.
""".strip()


def build_grounded_prompt(
    *,
    query: str,
    chunks: list[KnowledgeSearchChunk],
    student_context: str | None = None,
    current_affairs_mode: bool = False,
    pyq_mode: bool = False,
    frequency_summary: str | None = None,
) -> tuple[str, str]:
    system_prompt = SYSTEM_PROMPT
    if current_affairs_mode:
        system_prompt = f"{SYSTEM_PROMPT}\n\n{CURRENT_AFFAIRS_RECENCY_INSTRUCTIONS}"
    if pyq_mode:
        system_prompt = f"{system_prompt}\n\n{PYQ_GROUNDING_INSTRUCTIONS}"
    if not chunks:
        user_prompt = query.strip()
        if student_context:
            user_prompt = f"{student_context.strip()}\n\nQuestion: {user_prompt}"
        return SYSTEM_PROMPT, user_prompt

    context_lines: list[str] = [f"Question: {query.strip()}"]
    if student_context:
        context_lines.extend(["", "Student coaching context:", student_context.strip()])
    if frequency_summary:
        context_lines.extend(["", frequency_summary.strip()])
    context_lines.extend(
        [
            "",
            "Retrieved context:",
        ]
    )
    for index, chunk in enumerate(chunks, start=1):
        published = chunk.source.published_at.isoformat() if chunk.source.published_at else "unknown"
        pyq_year = chunk.metadata.get("year", "unknown")
        pyq_paper = chunk.metadata.get("paper", "unknown")
        context_lines.extend(
            [
                f"[{index}] chunk_id={chunk.chunk_id}",
                f"source_title={chunk.source.title}",
                f"source_type={chunk.source.source_type}",
                f"published_at={published}",
                f"pyq_year={pyq_year}",
                f"pyq_paper={pyq_paper}",
                f"source_authority={chunk.source.source_authority or 'unknown'}",
                chunk.content.strip(),
                "",
            ]
        )
    context_lines.append(
        "Write a grounded answer. Cite supporting chunk IDs inline using [chunk_id] format."
    )
    return SYSTEM_PROMPT, "\n".join(context_lines)
