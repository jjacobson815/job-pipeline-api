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
) -> dict:
    """Run LLM analysis on a job description / résumé pair.

    Parameters
    ----------
    job_description:
        The full job description text.
    resume_text:
        The candidate's résumé text.
    kind:
        Analysis type (``fit_score``, ``keyword_extraction``,
        ``cover_letter_draft``, ``summary``).
    model:
        OpenAI model to use.

    Returns
    -------
    dict
        Serialised ``AnalysisResponse`` or ``AnalysisError``.
    """
    request = AnalysisRequest(
        kind=AnalysisKind(kind),
        job_description=job_description,
        resume_text=resume_text,
        model=model,
    )
    service = LLMAnalysisService()

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
def sync_to_teal(self: Any, jobs_data: list[dict], dry_run: bool = False) -> dict:
    """Push a batch of jobs to the Teal tracker.

    Parameters
    ----------
    jobs_data:
        List of dicts matching ``TealJobPayload`` schema.
    dry_run:
        If ``True``, validate without actually creating in Teal.

    Returns
    -------
    dict
        Serialised ``TealSyncResult``.
    """
    payloads = [TealJobPayload(**jd) for jd in jobs_data]
    request = TealSyncRequest(jobs=payloads, dry_run=dry_run)
    service = TealSyncService()

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
) -> dict:
    """End-to-end pipeline: ingest → analyse → sync.

    Orchestrates the three domain services sequentially for a batch of URLs.

    Returns
    -------
    dict
        Combined results from all three stages.
    """
    # Stage 1: Ingest
    ingestion_result = ingest_jobs.apply(args=[urls, source]).get()

    # Stage 2: Analyse each successfully ingested job
    analysis_results: list[dict] = []
    for job in ingestion_result.get("succeeded", []):
        analysis = analyse_job.apply(
            args=[job["description"], resume_text, analysis_kind]
        ).get()
        analysis_results.append(analysis)

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
        teal_result = sync_to_teal.apply(args=[teal_payloads]).get()

    return {
        "ingestion": ingestion_result,
        "analyses": analysis_results,
        "teal_sync": teal_result,
    }
