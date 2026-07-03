"""
Celery application factory.

Creates a single Celery instance wired to the Redis broker defined in
Settings.  Task autodiscovery scans the ``app.tasks`` package so new
task modules are picked up automatically.
"""

from __future__ import annotations

import time
import redis
from celery import Celery
from celery.signals import task_prerun, task_postrun

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
        # Reliability (optimized tuning parameters)
        task_acks_late=True,
        worker_prefetch_multiplier=1,
        task_default_queue=settings.celery_task_default_queue,
        # Strict dual-lane task routing mapping
        task_routes={
            # Routing by module paths (as requested)
            "app.tasks.pipeline_tasks.full_pipeline": {"queue": "io_bound"},
            "app.tasks.pipeline_tasks.ingest_jobs": {"queue": "io_bound"},
            "app.tasks.pipeline_tasks.analyse_job": {"queue": "cpu_bound"},
            "app.tasks.pipeline_tasks.sync_to_teal": {"queue": "io_bound"},
            # Routing by registered Celery task names (existing codebase definitions)
            "pipeline.full_pipeline": {"queue": "io_bound"},
            "pipeline.ingest_jobs": {"queue": "io_bound"},
            "pipeline.analyse_job": {"queue": "cpu_bound"},
            "pipeline.sync_to_teal": {"queue": "io_bound"},
        },
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


# --- Real-Time Ingestion Telemetry Signals ---
# Zero-discard execution policy dictates we never fail a task due to telemetry bugs.
# Using in-memory dict to track starts.
_task_starts = {}

@task_prerun.connect
def on_task_prerun(task_id, task, *args, **kwargs):
    """Record the execution start time of the task."""
    try:
        _task_starts[task_id] = time.time()
    except Exception:
        pass


@task_postrun.connect
def on_task_postrun(task_id, task, *args, **kwargs):
    """Calculate latency and store metrics in Redis sorted sets by queue name."""
    try:
        start_time = _task_starts.pop(task_id, None)
        if start_time is None:
            return

        latency_ms = (time.time() - start_time) * 1000.0

        # Resolve the queue name for this task to organize metrics
        routes = celery_app.conf.task_routes or {}
        task_route = routes.get(task.name, {})
        queue_name = task_route.get("queue", celery_app.conf.task_default_queue)

        # Connect to Redis
        settings = get_settings()
        r = redis.Redis.from_url(settings.redis_url_str)
        
        current_time = time.time()
        member_data = f"{task_id}:{task.name}:{latency_ms:.2f}"
        
        zset_key = f"telemetry:{queue_name}"
        r.zadd(zset_key, {member_data: current_time})
        r.zremrangebyrank(zset_key, 0, -1001)  # Keep only the last 1000 metrics per lane
    except Exception:
        pass
