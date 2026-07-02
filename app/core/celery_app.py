"""
Celery application factory.

Creates a single Celery instance wired to the Redis broker defined in
Settings.  Task autodiscovery scans the ``app.tasks`` package so new
task modules are picked up automatically.
"""

from __future__ import annotations

from celery import Celery

from app.core.config import get_settings


def create_celery_app() -> Celery:
    """Build and configure the Celery application."""
    import ssl
    settings = get_settings()
    redis_url = settings.redis_url_str

    celery = Celery(
        "job_pipeline",
        broker=redis_url,
        backend=redis_url,
    )

    celery.conf.update(
        # Serialisation
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        # Timezone
        timezone="UTC",
        enable_utc=True,
        # Reliability
        task_acks_late=settings.celery_task_acks_late,
        worker_prefetch_multiplier=settings.celery_worker_prefetch_multiplier,
        task_default_queue=settings.celery_task_default_queue,
        # Result expiry — 1 hour
        result_expires=3600,
        # Autodiscover tasks inside app.tasks
        include=["app.tasks.pipeline_tasks"],
    )

    # If using secure rediss:// connection, configure broker/backend SSL requirements
    if redis_url.startswith("rediss://"):
        celery.conf.update(
            broker_use_ssl={"ssl_cert_reqs": ssl.CERT_NONE},
            redis_backend_use_ssl={"ssl_cert_reqs": ssl.CERT_NONE},
        )

    celery.autodiscover_tasks(["app.tasks"])

    return celery


celery_app = create_celery_app()
