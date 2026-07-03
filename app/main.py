"""
FastAPI application entry point.

Serves the Web GUI dashboard and exposes REST endpoints for triggering
pipeline stages and checking task status, all protected by API Key authentication.
Lifespan hook validates configuration at startup.
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException, status, APIRouter, Depends, Header
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, HttpUrl
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.domains.auth.models import User
from app.domains.auth.routes import router as auth_router, get_current_user
from app.domains.job_ingestion.models import JobBoardSource
from app.tasks.pipeline_tasks import analyse_job, full_pipeline, ingest_jobs, sync_to_teal
from app.core.celery_app import celery_app


logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Validate configuration and initialize database tables on startup."""
    settings = get_settings()
    logger.info(
        "Starting %s v%s [%s]",
        settings.app_name,
        settings.app_version,
        settings.environment,
    )
    
    # Eagerly initialize SQLite/PostgreSQL database tables
    try:
        from app.core.database import Base, engine
        from app.domains.auth.models import User, PipelineRun
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized successfully.")
    except Exception as db_exc:
        logger.error("Failed to initialize database tables: %s", db_exc)

    yield
    logger.info("Shutting down %s", settings.app_name)


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class IngestRequest(BaseModel):
    urls: list[HttpUrl] = Field(
        min_length=1, 
        max_length=10, 
        description="Job-board URLs to scrape (max 10)."
    )
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
    urls: list[HttpUrl] = Field(
        min_length=1, 
        max_length=10, 
        description="Job URLs to process (max 10)."
    )
    resume_text: str | None = Field(default=None)
    source: str = Field(default="custom")
    analysis_kind: str = Field(default="fit_score")
    sync_to_teal: bool = True

class TaskResponse(BaseModel):
    task_id: str
    status: str = "queued"

class DiscoverRequest(BaseModel):
    resume_text: str | None = Field(default=None)


# ---------------------------------------------------------------------------
# API Key Verification Dependency
# ---------------------------------------------------------------------------

async def verify_api_key(x_api_key: str | None = Header(None, alias="X-API-Key")) -> None:
    """Verifies that the X-API-Key header matches the configured settings API Key."""
    settings = get_settings()
    if x_api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API Key"
        )


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

    # --- Public Authentication Router --------------------------------------
    app.include_router(auth_router, prefix="/api/v1")

    # --- APIRouter (Authenticated) ----------------------------------------
    api_router = APIRouter(prefix="/api/v1", dependencies=[Depends(get_current_user)])

    @api_router.post(
        "/ingest",
        response_model=TaskResponse,
        status_code=status.HTTP_202_ACCEPTED,
        tags=["pipeline"],
    )
    async def trigger_ingest(body: IngestRequest) -> TaskResponse:
        """Queue a job-ingestion task."""
        task = ingest_jobs.delay([str(u) for u in body.urls], body.source.value)
        return TaskResponse(task_id=task.id)

    @api_router.post(
        "/analyse",
        response_model=TaskResponse,
        status_code=status.HTTP_202_ACCEPTED,
        tags=["pipeline"],
    )
    async def trigger_analyse(
        body: AnalyseRequest,
        current_user: User = Depends(get_current_user)
    ) -> TaskResponse:
        """Queue an LLM analysis task."""
        gemini_key = current_user.gemini_api_key or settings.gemini_api_key
        task = analyse_job.delay(
            body.job_description,
            body.resume_text or current_user.resume_text,
            body.kind,
            body.model,
            gemini_api_key=gemini_key,
        )
        return TaskResponse(task_id=task.id)

    @api_router.post(
        "/sync",
        response_model=TaskResponse,
        status_code=status.HTTP_202_ACCEPTED,
        tags=["pipeline"],
    )
    async def trigger_sync(
        body: SyncRequest,
        current_user: User = Depends(get_current_user)
    ) -> TaskResponse:
        """Queue a Teal-sync task."""
        teal_key = current_user.teal_api_key or settings.teal_api_key
        task = sync_to_teal.delay(body.jobs, body.dry_run, teal_api_key=teal_key)
        return TaskResponse(task_id=task.id)

    @api_router.post(
        "/pipeline",
        response_model=TaskResponse,
        status_code=status.HTTP_202_ACCEPTED,
        tags=["pipeline"],
    )
    async def trigger_full_pipeline(
        body: PipelineRequest,
        current_user: User = Depends(get_current_user)
    ) -> TaskResponse:
        """Queue the full ingest → analyse → sync pipeline."""
        gemini_key = current_user.gemini_api_key or settings.gemini_api_key
        teal_key = current_user.teal_api_key or settings.teal_api_key

        task = full_pipeline.delay(
            [str(u) for u in body.urls],
            body.resume_text or current_user.resume_text,
            body.source,
            body.analysis_kind,
            body.sync_to_teal,
            user_id=current_user.id,
            gemini_api_key=gemini_key,
            teal_api_key=teal_key,
        )
        return TaskResponse(task_id=task.id)

    @api_router.post(
        "/jobs/discover",
        tags=["pipeline"]
    )
    async def discover_jobs(
        body: DiscoverRequest,
        current_user: User = Depends(get_current_user)
    ) -> dict:
        """Discover relevant job URLs based on resume details."""
        from app.domains.job_search.services import JobSearchService
        service = JobSearchService()
        resume_text = body.resume_text or current_user.resume_text
        if not resume_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No resume text provided or saved in profile."
            )
        return await service.discover_jobs(resume_text)

    @api_router.get(
        "/pipeline/history",
        tags=["pipeline"],
    )
    async def get_pipeline_history(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> list[dict]:
        """Fetch the history of previous pipeline runs from Database."""
        from app.domains.auth.models import PipelineRun
        import json

        runs = (
            db.query(PipelineRun)
            .filter(PipelineRun.user_id == current_user.id)
            .order_by(PipelineRun.id.desc())
            .all()
        )
        results = []
        for run in runs:
            try:
                res_data = json.loads(run.result_json)
            except Exception:
                res_data = {}
            results.append({
                "run_id": run.run_id,
                "timestamp": run.timestamp,
                "total_jobs": run.total_jobs,
                "succeeded_jobs": run.succeeded_jobs,
                "avg_score": run.avg_score,
                "result": res_data
            })
        return results

    @api_router.get(
        "/tasks/{task_id}",
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

    @api_router.get("/workers/status", tags=["ops"])
    async def get_workers_status() -> dict:
        """Query Celery active workers and status."""
        try:
            inspect = celery_app.control.inspect()
            inspect.timeout = 2.0
            
            ping = inspect.ping() or {}
            active = inspect.active() or {}
            reserved = inspect.reserved() or {}
            
            workers = []
            for name in ping.keys():
                workers.append({
                    "name": name,
                    "status": "online",
                    "active_tasks_count": len(active.get(name, [])),
                    "reserved_tasks_count": len(reserved.get(name, []))
                })
            
            return {
                "status": "ok",
                "workers": workers,
                "total_workers_count": len(workers),
                "active_tasks_total": sum(len(tasks) for tasks in active.values())
            }
        except Exception as e:
            logger.exception("Failed to query Celery workers status: %s", e)
            return {
                "status": "error",
                "detail": str(e),
                "workers": [],
                "total_workers_count": 0,
                "active_tasks_total": 0
            }

    @api_router.get("/profile/resume", tags=["profile"])
    async def get_resume(current_user: User = Depends(get_current_user)) -> dict[str, str]:
        """Read and return user resume contents or fallback to default template."""
        if current_user.resume_text:
            return {"resume_text": current_user.resume_text}

        path = os.path.join(os.path.dirname(__file__), "data", "resume.txt")
        if not os.path.exists(path):
            return {"resume_text": ""}
        with open(path, "r", encoding="utf-8") as f:
            return {"resume_text": f.read()}

    @api_router.get("/profile/jobs", tags=["profile"])
    async def get_jobs() -> dict[str, str]:
        """Read and return default jobs contents securely."""
        path = os.path.join(os.path.dirname(__file__), "data", "jobs.txt")
        if not os.path.exists(path):
            raise HTTPException(status_code=404, detail="Jobs template not found")
        with open(path, "r", encoding="utf-8") as f:
            return {"jobs_text": f.read()}

    # Include protected router
    app.include_router(api_router)

    # --- Static Dashboard Mount --------------------------------------------

    static_dir = os.path.join(os.path.dirname(__file__), "static")
    os.makedirs(static_dir, exist_ok=True)
    app.mount("/dashboard", StaticFiles(directory=static_dir, html=True), name="static")

    @app.get("/")
    async def redirect_to_dashboard():
        return RedirectResponse(url="/dashboard/")

    return app


app = create_app()
