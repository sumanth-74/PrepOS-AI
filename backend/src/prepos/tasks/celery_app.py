from __future__ import annotations

from celery import Celery

from prepos.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "prepos",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_always_eager=settings.celery_task_always_eager,
    task_routes={
        "prepos.tasks.event_tasks.*": {"queue": "events"},
        "prepos.tasks.outbox_tasks.*": {"queue": "default"},
    },
    beat_schedule={
        "publish-outbox-events": {
            "task": "prepos.tasks.outbox_tasks.publish_outbox_batch",
            "schedule": 30.0,
        },
    },
    timezone="UTC",
)

celery_app.autodiscover_tasks(["prepos.tasks"])
