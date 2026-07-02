"""
Teal-sync service.

Full async HTTPx integration with the Teal job-tracker API. Supports
creating, updating, listing, and batch-syncing jobs. Includes robust
retry logic, rate-limit handling, and structured error reporting.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

import httpx

from app.core.config import Settings, get_settings
from app.domains.teal_sync.models import (
    TealApplicationStatus,
    TealJobPayload,
    TealJobResponse,
    TealSyncItemResult,
    TealSyncRequest,
    TealSyncResult,
)

logger = logging.getLogger(__name__)


class TealSyncService:
    """Async client for the Teal job-tracking REST API."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._base_url = str(self._settings.teal_base_url).rstrip("/")
        self._timeout = httpx.Timeout(
            connect=10.0,
            read=self._settings.http_timeout_seconds,
            write=10.0,
            pool=5.0,
        )

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._settings.teal_api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    # -- public API --------------------------------------------------------

    async def create_job(self, job: TealJobPayload) -> TealJobResponse:
        """POST a new job to the Teal tracker."""
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            return await self._post_job(client, job)

    async def update_job_status(
        self, teal_id: str, status: TealApplicationStatus
    ) -> TealJobResponse:
        """PATCH the status of an existing Teal job."""
        url = f"{self._base_url}/jobs/{teal_id}"
        payload = {"status": status.value}

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await self._request_with_retry(
                client, "PATCH", url, json_payload=payload
            )
        return self._parse_job_response(response)

    async def get_job(self, teal_id: str) -> TealJobResponse:
        """GET a single job by its Teal ID."""
        url = f"{self._base_url}/jobs/{teal_id}"
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await self._request_with_retry(client, "GET", url)
        return self._parse_job_response(response)

    async def list_jobs(
        self, status: TealApplicationStatus | None = None, limit: int = 100
    ) -> list[TealJobResponse]:
        """GET all tracked jobs, optionally filtered by status."""
        url = f"{self._base_url}/jobs"
        params: dict[str, str | int] = {"limit": limit}
        if status is not None:
            params["status"] = status.value

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await self._request_with_retry(
                client, "GET", url, params=params
            )
        body = response.json()
        items = body if isinstance(body, list) else body.get("items", body.get("data", []))
        return [self._parse_job_response_from_dict(item) for item in items]

    async def sync_batch(self, request: TealSyncRequest) -> TealSyncResult:
        """Push a batch of jobs to Teal with per-item error isolation."""
        started = datetime.now(timezone.utc)
        items: list[TealSyncItemResult] = []
        synced = 0
        failed = 0

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            for job in request.jobs:
                if (
                    request.dry_run
                    or not self._settings.is_teal_configured
                ):
                    items.append(
                        TealSyncItemResult(
                            title=job.title,
                            company=job.company,
                            teal_id=None,
                            success=True,
                            error=None,
                        )
                    )
                    synced += 1
                    continue

                try:
                    teal_resp = await self._post_job(client, job)
                    items.append(
                        TealSyncItemResult(
                            title=job.title,
                            company=job.company,
                            teal_id=teal_resp.teal_id,
                            success=True,
                            error=None,
                        )
                    )
                    synced += 1
                except TealAPIError as exc:
                    logger.error(
                        "Failed to sync job '%s' at '%s': %s",
                        job.title, job.company, exc.detail,
                    )
                    items.append(
                        TealSyncItemResult(
                            title=job.title,
                            company=job.company,
                            teal_id=None,
                            success=False,
                            error=exc.detail,
                        )
                    )
                    failed += 1

        return TealSyncResult(
            sync_id=request.sync_id,
            items=items,
            synced_count=synced,
            failed_count=failed,
            started_at=started,
            completed_at=datetime.now(timezone.utc),
        )

    # -- internals ---------------------------------------------------------

    async def _post_job(
        self, client: httpx.AsyncClient, job: TealJobPayload
    ) -> TealJobResponse:
        url = f"{self._base_url}/jobs"
        payload = {
            "title": job.title,
            "company": job.company,
            "url": str(job.url),
            "location": job.location,
            "description": job.description,
            "salary": job.salary,
            "status": job.status.value,
            "notes": job.notes,
            "tags": job.tags,
        }
        response = await self._request_with_retry(
            client, "POST", url, json_payload=payload
        )
        return self._parse_job_response(response)

    async def _request_with_retry(
        self,
        client: httpx.AsyncClient,
        method: str,
        url: str,
        json_payload: dict | None = None,
        params: dict | None = None,
    ) -> httpx.Response:
        """Execute an HTTP request with exponential backoff retry."""
        retries = self._settings.http_max_retries
        backoff = self._settings.http_backoff_base

        for attempt in range(1, retries + 2):
            try:
                response = await client.request(
                    method,
                    url,
                    json=json_payload,
                    params=params,
                    headers=self._headers(),
                )

                if response.status_code == 404:
                    raise TealAPIError(
                        status_code=404,
                        detail=f"Resource not found: {url}",
                    )

                if response.status_code == 429:
                    retry_after = float(response.headers.get("Retry-After", backoff))
                    if attempt <= retries:
                        logger.warning(
                            "Teal rate-limit (attempt %d/%d), waiting %.1fs",
                            attempt, retries, retry_after,
                        )
                        await asyncio.sleep(retry_after)
                        backoff *= 2
                        continue
                    raise TealAPIError(
                        status_code=429,
                        detail=f"Rate-limited after {retries} retries on {url}",
                    )

                response.raise_for_status()
                return response

            except httpx.TimeoutException:
                if attempt <= retries:
                    logger.warning(
                        "Teal timeout (attempt %d/%d), retrying in %.1fs",
                        attempt, retries, backoff,
                    )
                    await asyncio.sleep(backoff)
                    backoff *= 2
                    continue
                raise TealAPIError(
                    status_code=0,
                    detail=f"Timeout after {retries} retries on {url}",
                )

            except httpx.HTTPStatusError as exc:
                raise TealAPIError(
                    status_code=exc.response.status_code,
                    detail=f"HTTP {exc.response.status_code}: {exc.response.text[:500]}",
                )

            except httpx.RequestError as exc:
                if attempt <= retries:
                    logger.warning(
                        "Teal network error (attempt %d/%d): %s",
                        attempt, retries, exc,
                    )
                    await asyncio.sleep(backoff)
                    backoff *= 2
                    continue
                raise TealAPIError(
                    status_code=0,
                    detail=f"Network error after {retries} retries: {exc}",
                )

        raise TealAPIError(
            status_code=0,
            detail=f"All {retries} retries exhausted for {method} {url}",
        )

    @staticmethod
    def _parse_job_response(response: httpx.Response) -> TealJobResponse:
        """Parse httpx.Response into a TealJobResponse."""
        data = response.json()
        return TealSyncService._parse_job_response_from_dict(data)

    @staticmethod
    def _parse_job_response_from_dict(data: dict) -> TealJobResponse:
        """Parse a raw dict into a TealJobResponse."""
        return TealJobResponse(
            teal_id=data.get("id", data.get("teal_id", "")),
            title=data.get("title", ""),
            company=data.get("company", ""),
            status=TealApplicationStatus(
                data.get("status", TealApplicationStatus.BOOKMARKED.value)
            ),
            created_at=data.get("created_at", datetime.now(timezone.utc)),
            updated_at=data.get("updated_at", datetime.now(timezone.utc)),
        )


class TealAPIError(Exception):
    """Raised when a Teal API call fails after exhausting retries."""

    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)
