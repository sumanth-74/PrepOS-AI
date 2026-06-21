from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from prepos.api.v1.health import router as health_router
from prepos.api.v1.router import router as v1_router
from prepos.core.config import get_settings
from prepos.core.database import create_engine, dispose_engine
from prepos.core.exceptions import DomainError
from prepos.core.logging import configure_logging, get_logger
from prepos.core.observability import instrument_fastapi_app, setup_opentelemetry, setup_sentry
from prepos.events.handlers import (  # noqa: F401
    behavior_profile_handlers,
    decision_handlers,
    exam_handlers,
    forecast_probability_handlers,
    foundation_handlers,
    goal_handlers,
    intervention_handlers,
    intervention_outcome_handlers,
    learning_graph_handlers,
    mentor_action_handlers,
    mentor_case_handlers,
    mentor_effectiveness_handlers,
    mentor_handlers,
    milestone_handlers,
    personalization_handlers,
    predicted_score_handlers,
    student_handlers,
    study_plan_handlers,
    twin_handlers,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings.log_level)
    create_engine(settings)
    setup_sentry(settings)
    setup_opentelemetry(settings)
    yield
    await dispose_engine()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from prepos.api.middleware.rate_limit_middleware import RateLimitMiddleware

    app.add_middleware(RateLimitMiddleware)

    @app.exception_handler(DomainError)
    async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
        status_code = 400
        if exc.code == "NOT_FOUND":
            status_code = 404
        elif exc.code in {"TENANT_ACCESS_DENIED", "AUTHORIZATION_ERROR"}:
            status_code = 403
        elif exc.code in {"AUTHENTICATION_ERROR"}:
            status_code = 401
        elif exc.code == "PROMPT_INJECTION_BLOCKED":
            status_code = 403
        elif exc.code in {"CONFLICT", "OPTIMISTIC_LOCK"}:
            status_code = 409
        elif exc.code == "VALIDATION_ERROR":
            status_code = 422
        logger = get_logger(__name__)
        logger.warning(
            "domain_error",
            code=exc.code,
            message=exc.message,
            path=str(request.url.path),
        )
        return JSONResponse(
            status_code=status_code,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details,
                    "correlation_id": request.headers.get("x-request-id"),
                }
            },
        )

    app.include_router(health_router)
    app.include_router(v1_router, prefix=settings.api_v1_prefix)
    instrument_fastapi_app(app, settings)
    return app


app = create_app()


def run() -> None:
    import uvicorn

    uvicorn.run("prepos.api.main:app", host="0.0.0.0", port=8000, reload=True)
