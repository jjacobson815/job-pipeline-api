"""
FastAPI application entry point.

Headless API — no HTML templates, no static files.  Exposes REST
endpoints for triggering pipeline stages and checking task status.
Lifespan hook validates configuration at startup.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.domains.job_ingestion.models import JobBoardSource
from app.tasks.pipeline_tasks import analyse_job, full_pipeline, ingest_jobs, sync_to_teal

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Validate configuration eagerly on startup."""
    settings = get_settings()
    logger.info(
        "Starting %s v%s [%s]",
        settings.app_name,
        settings.app_version,
        settings.environment,
    )
    yield
    logger.info("Shutting down %s", settings.app_name)


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class IngestRequest(BaseModel):
    urls: list[str] = Field(min_length=1, description="Job-board URLs to scrape")
    source: JobBoardSource = JobBoardSource.CUSTOM

class AnalyseRequest(BaseModel):
    job_description: str = Field(min_length=1)
    resume_text: str = Field(min_length=1)
    kind: str = Field(default="fit_score")
    model: str = Field(default="gpt-4o-mini")

class SyncRequest(BaseModel):
    jobs: list[dict] = Field(min_length=1)
    dry_run: bool = False

class PipelineRequest(BaseModel):
    urls: list[str] = Field(min_length=1)
    resume_text: str = Field(min_length=1)
    source: str = Field(default="custom")
    analysis_kind: str = Field(default="fit_score")
    sync_to_teal: bool = True

class TaskResponse(BaseModel):
    task_id: str
    status: str = "queued"


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        lifespan=lifespan,
    )

    # --- Health -----------------------------------------------------------

    @app.get("/health", tags=["ops"])
    async def health() -> dict[str, str]:
        return {"status": "healthy", "version": settings.app_version}


    # --- Endpoints ---------------------------------------------------------

    @app.post(
        "/api/v1/ingest",
        response_model=TaskResponse,
        status_code=status.HTTP_202_ACCEPTED,
        tags=["pipeline"],
    )
    async def trigger_ingest(body: IngestRequest) -> TaskResponse:
        """Queue a job-ingestion task."""
        task = ingest_jobs.delay(body.urls, body.source.value)
        return TaskResponse(task_id=task.id)

    @app.post(
        "/api/v1/analyse",
        response_model=TaskResponse,
        status_code=status.HTTP_202_ACCEPTED,
        tags=["pipeline"],
    )
    async def trigger_analyse(body: AnalyseRequest) -> TaskResponse:
        """Queue an LLM analysis task."""
        task = analyse_job.delay(
            body.job_description, body.resume_text, body.kind, body.model
        )
        return TaskResponse(task_id=task.id)

    @app.post(
        "/api/v1/sync",
        response_model=TaskResponse,
        status_code=status.HTTP_202_ACCEPTED,
        tags=["pipeline"],
    )
    async def trigger_sync(body: SyncRequest) -> TaskResponse:
        """Queue a Teal-sync task."""
        task = sync_to_teal.delay(body.jobs, body.dry_run)
        return TaskResponse(task_id=task.id)

    @app.post(
        "/api/v1/pipeline",
        response_model=TaskResponse,
        status_code=status.HTTP_202_ACCEPTED,
        tags=["pipeline"],
    )
    async def trigger_full_pipeline(body: PipelineRequest) -> TaskResponse:
        """Queue the full ingest → analyse → sync pipeline."""
        task = full_pipeline.delay(
            body.urls,
            body.resume_text,
            body.source,
            body.analysis_kind,
            body.sync_to_teal,
        )
        return TaskResponse(task_id=task.id)

    @app.get(
        "/api/v1/tasks/{task_id}",
        tags=["pipeline"],
    )
    async def get_task_status(task_id: str) -> dict:
        """Check the status of any queued Celery task."""
        from celery.result import AsyncResult

        from app.core.celery_app import celery_app as celery

        result = AsyncResult(task_id, app=celery)
        if result.state == "PENDING":
            return {"task_id": task_id, "status": "pending", "result": None}
        if result.state == "FAILURE":
            return {
                "task_id": task_id,
                "status": "failed",
                "error": str(result.result),
            }
        if result.state == "SUCCESS":
            return {
                "task_id": task_id,
                "status": "success",
                "result": result.result,
            }
        return {"task_id": task_id, "status": result.state.lower(), "result": None}

    return app


app = create_app()
