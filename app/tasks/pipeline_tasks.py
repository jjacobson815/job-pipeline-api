"""
Celery tasks that orchestrate the end-to-end job-application pipeline.

Each task is a thin shim that instantiates the relevant domain service,
runs the async logic via ``asyncio.run``, and returns serialisable results.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from app.core.celery_app import celery_app
from app.domains.job_ingestion.models import JobBoardSource, ScrapeTarget
from app.domains.job_ingestion.services import JobIngestionService
from app.domains.llm_analysis.models import AnalysisKind, AnalysisRequest
from app.domains.llm_analysis.services import LLMAnalysisService
from app.domains.teal_sync.models import TealJobPayload, TealSyncRequest
from app.domains.teal_sync.services import TealSyncService

logger = logging.getLogger(__name__)


def _run_async(coro: Any) -> Any:
    """Bridge sync Celery workers to async domain services."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop is not None and loop.is_running():
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(asyncio.run, coro).result()
    return asyncio.run(coro)


@celery_app.task(
    name="pipeline.ingest_jobs",
    bind=True,
    max_retries=2,
    default_retry_delay=30,
    acks_late=True,
)
def ingest_jobs(self: Any, urls: list[str], source: str = "custom") -> dict:
    """Scrape a list of job-board URLs and return normalised listings.

    Parameters
    ----------
    urls:
        Raw URL strings to scrape.
    source:
        One of the ``JobBoardSource`` values.

    Returns
    -------
    dict
        Serialised ``IngestionResult``.
    """
    board = JobBoardSource(source)
    targets = [ScrapeTarget(url=u, source=board) for u in urls]
    service = JobIngestionService()

    try:
        result = _run_async(service.ingest_batch(targets))
        logger.info(
            "Ingestion batch %s: %d succeeded, %d failed (%.0f%% success)",
            result.batch_id,
            len(result.succeeded),
            len(result.failed),
            result.success_rate * 100,
        )
        return result.model_dump(mode="json")
    except Exception as exc:
        logger.exception("Ingestion task failed: %s", exc)
        raise self.retry(exc=exc)


@celery_app.task(
    name="pipeline.analyse_job",
    bind=True,
    max_retries=2,
    default_retry_delay=15,
    acks_late=True,
)
def analyse_job(
    self: Any,
    job_description: str,
    resume_text: str,
    kind: str = "fit_score",
    model: str = "gpt-4o-mini",
    gemini_api_key: str | None = None,
) -> dict:
    """Run LLM analysis on a job description / résumé pair."""
    request = AnalysisRequest(
        kind=AnalysisKind(kind),
        job_description=job_description,
        resume_text=resume_text,
        model=model,
    )
    service = LLMAnalysisService(gemini_api_key=gemini_api_key)

    try:
        result = _run_async(service.analyse(request))
        logger.info("Analysis %s (%s) completed", request.id, kind)
        return result.model_dump(mode="json")
    except Exception as exc:
        logger.exception("Analysis task failed: %s", exc)
        raise self.retry(exc=exc)


@celery_app.task(
    name="pipeline.sync_to_teal",
    bind=True,
    max_retries=2,
    default_retry_delay=20,
    acks_late=True,
)
def sync_to_teal(
    self: Any,
    jobs_data: list[dict],
    dry_run: bool = False,
    teal_api_key: str | None = None,
) -> dict:
    """Push a batch of jobs to the Teal tracker."""
    payloads = [TealJobPayload(**jd) for jd in jobs_data]
    request = TealSyncRequest(jobs=payloads, dry_run=dry_run)
    service = TealSyncService(api_key=teal_api_key)

    try:
        result = _run_async(service.sync_batch(request))
        logger.info(
            "Teal sync %s: %d synced, %d failed",
            result.sync_id, result.synced_count, result.failed_count,
        )
        return result.model_dump(mode="json")
    except Exception as exc:
        logger.exception("Teal sync task failed: %s", exc)
        raise self.retry(exc=exc)


@celery_app.task(
    name="pipeline.full_pipeline",
    bind=True,
    max_retries=1,
    default_retry_delay=60,
    acks_late=True,
)
def full_pipeline(
    self: Any,
    urls: list[str],
    resume_text: str,
    source: str = "custom",
    analysis_kind: str = "fit_score",
    sync_to_teal_flag: bool = True,
    user_id: int | None = None,
    gemini_api_key: str | None = None,
    teal_api_key: str | None = None,
) -> dict:
    """End-to-end pipeline: ingest → analyse → sync."""
    # Stage 1: Ingest
    board = JobBoardSource(source)
    targets = [ScrapeTarget(url=u, source=board) for u in urls]
    ingestion_service = JobIngestionService()
    
    try:
        ingestion_result_obj = _run_async(ingestion_service.ingest_batch(targets))
        ingestion_result = ingestion_result_obj.model_dump(mode="json")
    except Exception as exc:
        logger.exception("Ingestion step failed inside full_pipeline: %s", exc)
        raise self.retry(exc=exc)

    # Stage 2: Analyse each successfully ingested job concurrently
    analysis_results: list[dict] = []
    analysis_service = LLMAnalysisService(gemini_api_key=gemini_api_key)
    succeeded_jobs = ingestion_result.get("succeeded", [])
    if succeeded_jobs:
        requests = [
            AnalysisRequest(
                kind=AnalysisKind(analysis_kind),
                job_description=job["description"],
                resume_text=resume_text,
            )
            for job in succeeded_jobs
        ]
        try:
            batch_results = _run_async(analysis_service.analyse_batch(requests))
            for res in batch_results:
                analysis_results.append(res.model_dump(mode="json"))
        except Exception as exc:
            logger.exception("Analysis step failed inside full_pipeline: %s", exc)
            raise self.retry(exc=exc)

    # Stage 3: Sync to Teal
    teal_result: dict | None = None
    if sync_to_teal_flag and ingestion_result.get("succeeded"):
        teal_payloads = [
            {
                "title": job["title"],
                "company": job["company"],
                "url": job["source_url"],
                "location": job.get("location", "Remote"),
                "description": job.get("description", "")[:10000],
                "status": "bookmarked",
            }
            for job in ingestion_result["succeeded"]
        ]
        payloads = [TealJobPayload(**jd) for jd in teal_payloads]
        sync_request = TealSyncRequest(jobs=payloads, dry_run=False)
        sync_service = TealSyncService(api_key=teal_api_key)
        try:
            sync_result_obj = _run_async(sync_service.sync_batch(sync_request))
            teal_result = sync_result_obj.model_dump(mode="json")
        except Exception as exc:
            logger.exception("Sync step failed inside full_pipeline: %s", exc)
            raise self.retry(exc=exc)

    result = {
        "ingestion": ingestion_result,
        "analyses": analysis_results,
        "teal_sync": teal_result,
    }

    # Persist the run metadata and result to Database (user-specific) or Redis (global fallback)
    try:
        import json
        import time

        run_id = self.request.id or f"run_{int(time.time())}"
        succeeded_count = len(ingestion_result.get("succeeded", []))
        total_count = len(urls)
        
        valid_scores = [
            a["fit_score"]["overall_score"]
            for a in analysis_results
            if a.get("fit_score") and a["fit_score"].get("overall_score") is not None
        ]
        avg_score = sum(valid_scores) / len(valid_scores) if valid_scores else 0.0

        if user_id is not None:
            # Persistent Relational DB flow
            from app.core.database import SessionLocal
            from app.domains.auth.models import PipelineRun

            db = SessionLocal()
            try:
                run = PipelineRun(
                    user_id=user_id,
                    run_id=run_id,
                    timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    total_jobs=total_count,
                    succeeded_jobs=succeeded_count,
                    avg_score=round(avg_score, 1),
                    result_json=json.dumps(result),
                )
                db.add(run)
                db.commit()
                logger.info("Successfully persisted user %d pipeline run %s to Database", user_id, run_id)
            finally:
                db.close()
        else:
            # Fallback to general Redis log for local CLI / mock tests
            import redis
            from app.core.config import get_settings

            settings = get_settings()
            r = redis.Redis.from_url(settings.redis_url_str)
            run_summary = {
                "run_id": run_id,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "total_jobs": total_count,
                "succeeded_jobs": succeeded_count,
                "avg_score": round(avg_score, 1),
                "result": result
            }
            r.lpush("pipeline:runs", json.dumps(run_summary))
            r.ltrim("pipeline:runs", 0, 19)
            logger.info("Successfully persisted pipeline run %s to Redis fallback history", run_id)

    except Exception as persist_exc:
        logger.warning("Failed to persist pipeline run: %s", persist_exc)

    return result
