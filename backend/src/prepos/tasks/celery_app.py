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
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_default_retry_delay=60,
    task_max_retries=3,
    broker_transport_options={"visibility_timeout": 3600},
    task_routes={
        "prepos.tasks.event_tasks.*": {"queue": "events"},
        "prepos.tasks.outbox_tasks.*": {"queue": "default"},
        "prepos.tasks.knowledge_tasks.*": {"queue": "knowledge"},
    },
    beat_schedule={
        "publish-outbox-events": {
            "task": "prepos.tasks.outbox_tasks.publish_outbox_batch",
            "schedule": 30.0,
        },
    },
    timezone="UTC",
)

# Dead letter / poison queue routing for failed tasks after max retries
celery_app.conf.task_routes.update(
    {"prepos.tasks.*.dead_letter_*": {"queue": "dead_letter"}},
)

celery_app.autodiscover_tasks(["prepos.tasks"])
