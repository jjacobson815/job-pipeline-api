"""
Tests for the teal-sync domain.

Arrange-Act-Assert pattern throughout. All Teal API calls are mocked
via ``MockTransport`` — no network access occurs.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

import httpx
import pytest

from app.domains.teal_sync.models import (
    TealApplicationStatus,
    TealJobPayload,
    TealJobResponse,
    TealSyncRequest,
    TealSyncResult,
)
from app.domains.teal_sync.services import TealAPIError, TealSyncService
from tests.conftest import SAMPLE_TEAL_API_RESPONSE, MockTransport


# ---------------------------------------------------------------------------
# Model validation tests
# ---------------------------------------------------------------------------


class TestTealModels:
    """Pydantic schema validation for Teal models."""

    def test_valid_job_payload(self) -> None:
        # Arrange & Act
        payload = TealJobPayload(
            title="ML Engineer",
            company="DeepTech",
            url="https://careers.deeptech.io/ml-eng",
        )

        # Assert
        assert payload.title == "ML Engineer"
        assert payload.status == TealApplicationStatus.BOOKMARKED
        assert payload.location == "Remote"

    def test_empty_title_rejected(self) -> None:
        # Arrange & Act & Assert
        with pytest.raises(Exception):
            TealJobPayload(
                title="",
                company="Co",
                url="https://example.com/j",
            )

    def test_sync_request_requires_at_least_one_job(self) -> None:
        # Arrange & Act & Assert
        with pytest.raises(Exception):
            TealSyncRequest(jobs=[])


# ---------------------------------------------------------------------------
# Service — successful operations
# ---------------------------------------------------------------------------


class TestTealSyncServiceSuccess:
    """Happy-path sync operations with mocked HTTP."""

    @pytest.mark.asyncio
    async def test_create_job_returns_teal_response(
        self, mock_settings, sample_teal_job_payload
    ) -> None:
        # Arrange
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                201,
                json=SAMPLE_TEAL_API_RESPONSE,
                headers={"Content-Type": "application/json"},
            )

        service = TealSyncService(settings=mock_settings)

        # Act
        transport = MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as client:
            response = await service._post_job(client, sample_teal_job_payload)

        # Assert
        assert isinstance(response, TealJobResponse)
        assert response.teal_id == "teal-job-abc123"
        assert response.title == "Senior Python Engineer"
        assert response.status == TealApplicationStatus.BOOKMARKED

    @pytest.mark.asyncio
    async def test_sync_batch_dry_run(self, mock_settings) -> None:
        # Arrange
        jobs = [
            TealJobPayload(
                title=f"Engineer {i}",
                company=f"Company {i}",
                url=f"https://example.com/j/{i}",
            )
            for i in range(3)
        ]
        request = TealSyncRequest(jobs=jobs, dry_run=True)
        service = TealSyncService(settings=mock_settings)

        # Act
        result = await service.sync_batch(request)

        # Assert
        assert isinstance(result, TealSyncResult)
        assert result.synced_count == 3
        assert result.failed_count == 0
        assert all(item.success for item in result.items)

    @pytest.mark.asyncio
    async def test_sync_batch_with_api(self, mock_settings) -> None:
        # Arrange
        call_count = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            resp_data = {
                **SAMPLE_TEAL_API_RESPONSE,
                "id": f"teal-{call_count}",
                "title": f"Job {call_count}",
            }
            return httpx.Response(
                201, json=resp_data, headers={"Content-Type": "application/json"}
            )

        jobs = [
            TealJobPayload(
                title=f"Eng {i}",
                company="Acme",
                url=f"https://example.com/{i}",
            )
            for i in range(2)
        ]
        request = TealSyncRequest(jobs=jobs, dry_run=False)
        service = TealSyncService(settings=mock_settings)

        # Override the internal method to use our transport
        original_post = service._post_job

        async def patched_post(client, job):
            transport = MockTransport(handler)
            async with httpx.AsyncClient(transport=transport) as mock_client:
                return await original_post(mock_client, job)

        service._post_job = patched_post  # type: ignore[assignment]

        # Act
        result = await service.sync_batch(request)

        # Assert
        assert result.synced_count == 2
        assert result.failed_count == 0


# ---------------------------------------------------------------------------
# Service — error handling
# ---------------------------------------------------------------------------


class TestTealSyncServiceErrors:
    """Error scenarios: 404, 429, timeouts."""

    @pytest.mark.asyncio
    async def test_404_raises_teal_api_error(self, mock_settings) -> None:
        # Arrange
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(404, text="Not Found")

        service = TealSyncService(settings=mock_settings)

        # Act & Assert
        transport = MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as client:
            with pytest.raises(TealAPIError) as exc_info:
                await service._request_with_retry(
                    client, "GET", "https://api.teal.dev/v1/jobs/nonexistent"
                )
            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_429_exhausts_retries(self, mock_settings) -> None:
        # Arrange
        call_count = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            return httpx.Response(
                429,
                text="Rate Limited",
                headers={"Retry-After": "0.01"},
            )

        service = TealSyncService(settings=mock_settings)

        # Act & Assert
        transport = MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as client:
            with pytest.raises(TealAPIError) as exc_info:
                await service._request_with_retry(
                    client, "GET", "https://api.teal.dev/v1/jobs"
                )
            assert exc_info.value.status_code == 429
            assert call_count >= 2

    @pytest.mark.asyncio
    async def test_sync_batch_isolates_per_item_errors(self, mock_settings) -> None:
        # Arrange
        call_count = 0

        service = TealSyncService(settings=mock_settings)
        original_post = service._post_job

        async def failing_post(client, job):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise TealAPIError(status_code=500, detail="Internal Server Error")

            def handler(request: httpx.Request) -> httpx.Response:
                return httpx.Response(
                    201,
                    json=SAMPLE_TEAL_API_RESPONSE,
                    headers={"Content-Type": "application/json"},
                )

            transport = MockTransport(handler)
            async with httpx.AsyncClient(transport=transport) as mock_client:
                return await original_post(mock_client, job)

        service._post_job = failing_post  # type: ignore[assignment]

        jobs = [
            TealJobPayload(
                title=f"Job {i}",
                company="Acme",
                url=f"https://example.com/{i}",
            )
            for i in range(3)
        ]
        request = TealSyncRequest(jobs=jobs, dry_run=False)

        # Act
        result = await service.sync_batch(request)

        # Assert — 1 failed, 2 succeeded, no exception propagated
        assert result.synced_count == 2
        assert result.failed_count == 1
        failed_items = [i for i in result.items if not i.success]
        assert len(failed_items) == 1
        assert "Internal Server Error" in (failed_items[0].error or "")


# ---------------------------------------------------------------------------
# Response parsing tests
# ---------------------------------------------------------------------------


class TestTealResponseParsing:
    """Verify response dict → TealJobResponse mapping."""

    def test_parse_standard_response(self) -> None:
        # Arrange
        data = {
            "id": "abc",
            "title": "SWE",
            "company": "Co",
            "status": "applied",
            "created_at": "2025-01-01T00:00:00Z",
            "updated_at": "2025-01-02T00:00:00Z",
        }

        # Act
        result = TealSyncService._parse_job_response_from_dict(data)

        # Assert
        assert result.teal_id == "abc"
        assert result.status == TealApplicationStatus.APPLIED

    def test_parse_response_with_teal_id_key(self) -> None:
        # Arrange — some API versions use "teal_id" instead of "id"
        data = {
            "teal_id": "xyz",
            "title": "PM",
            "company": "BigCo",
            "status": "interviewing",
            "created_at": "2025-06-01T00:00:00Z",
            "updated_at": "2025-06-01T00:00:00Z",
        }

        # Act
        result = TealSyncService._parse_job_response_from_dict(data)

        # Assert
        assert result.teal_id == "xyz"
        assert result.status == TealApplicationStatus.INTERVIEWING
