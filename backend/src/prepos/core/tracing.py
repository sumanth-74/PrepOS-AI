from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator
from uuid import UUID, uuid4

from opentelemetry import trace
from opentelemetry.trace import SpanKind, Status, StatusCode

TRACER = trace.get_tracer("prepos.pipeline")


def new_trace_id() -> UUID:
    span_context = trace.get_current_span().get_span_context()
    if span_context.trace_id:
        return UUID(int=span_context.trace_id)
    return uuid4()


def new_execution_id() -> UUID:
    return uuid4()


@contextmanager
def trace_pipeline_stage(
    name: str,
    *,
    attributes: dict[str, str | int | float | bool] | None = None,
) -> Iterator[None]:
    with TRACER.start_as_current_span(name, kind=SpanKind.INTERNAL) as span:
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, value)
        try:
            yield
        except Exception as exc:
            span.set_status(Status(StatusCode.ERROR, str(exc)))
            span.record_exception(exc)
            raise


def inject_trace_headers(headers: dict[str, str]) -> dict[str, str]:
    span = trace.get_current_span()
    ctx = span.get_span_context()
    if ctx.trace_id:
        headers["x-trace-id"] = format(ctx.trace_id, "032x")
    return headers
