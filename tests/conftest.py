"""
Shared pytest fixtures.

Provides mock HTTP transports, pre-built domain objects, and patched
settings for deterministic, network-free testing.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock

import httpx
import pytest
import pytest_asyncio

from app.core.config import Settings
from app.domains.job_ingestion.models import JobBoardSource, ScrapeTarget
from app.domains.llm_analysis.models import AnalysisKind, AnalysisRequest
from app.domains.teal_sync.models import TealApplicationStatus, TealJobPayload


# ---------------------------------------------------------------------------
# Settings fixture — no real env vars needed
# ---------------------------------------------------------------------------

@pytest.fixture()
def mock_settings() -> Settings:
    """Return a Settings instance with safe test defaults."""
    return Settings(
        teal_api_key="test-teal-key-0123456789",
        openai_api_key="test-openai-key-0123456789",
        redis_url="redis://localhost:6379/15",
        environment="development",
        http_timeout_seconds=5.0,
        http_max_retries=1,
        http_backoff_base=0.01,
    )


# ---------------------------------------------------------------------------
# httpx mock transport
# ---------------------------------------------------------------------------

class MockTransport(httpx.AsyncBaseTransport):
    """Programmable async transport for httpx — returns canned responses."""

    def __init__(self, handler: Any) -> None:
        self._handler = handler

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        return self._handler(request)


@pytest.fixture()
def mock_transport_factory():
    """Factory that builds a MockTransport from a handler callable."""

    def _factory(handler: Any) -> MockTransport:
        return MockTransport(handler)

    return _factory


# ---------------------------------------------------------------------------
# Job-ingestion fixtures
# ---------------------------------------------------------------------------

SAMPLE_JOB_HTML = """
<html>
<head><title>Senior Python Engineer at Acme Corp</title></head>
<body>
<h1>Senior Python Engineer</h1>
<p>Company: Acme Corp</p>
<p>Location: Remote</p>
<div class="description">
  We are looking for a Senior Python Engineer with 5+ years of experience
  in building scalable backend services using FastAPI, SQLAlchemy, and
  PostgreSQL. Experience with async Python is a must.
</div>
</body>
</html>
"""


@pytest.fixture()
def sample_scrape_target() -> ScrapeTarget:
    return ScrapeTarget(
        url="https://boards.example.com/jobs/123",
        source=JobBoardSource.GREENHOUSE,
    )


@pytest.fixture()
def sample_scrape_targets() -> list[ScrapeTarget]:
    return [
        ScrapeTarget(url="https://boards.example.com/jobs/1", source=JobBoardSource.GREENHOUSE),
        ScrapeTarget(url="https://boards.example.com/jobs/2", source=JobBoardSource.LEVER),
        ScrapeTarget(url="https://boards.example.com/jobs/3", source=JobBoardSource.LINKEDIN),
    ]


# ---------------------------------------------------------------------------
# LLM-analysis fixtures
# ---------------------------------------------------------------------------

SAMPLE_FIT_SCORE_JSON = json.dumps(
    {
        "overall_score": 82.5,
        "keyword_overlap": ["Python", "FastAPI", "PostgreSQL"],
        "missing_keywords": ["Kubernetes", "Terraform"],
        "strengths": ["Strong backend experience", "Async Python expertise"],
        "gaps": ["No infrastructure-as-code experience listed"],
        "recommendation": "Strong candidate — consider for phone screen.",
    }
)

SAMPLE_KEYWORD_JSON = json.dumps(
    {
        "hard_skills": ["Python", "FastAPI", "SQLAlchemy"],
        "soft_skills": ["Communication", "Leadership"],
        "tools": ["Docker", "PostgreSQL"],
        "certifications": ["AWS Solutions Architect"],
    }
)


@pytest.fixture()
def sample_analysis_request() -> AnalysisRequest:
    return AnalysisRequest(
        kind=AnalysisKind.FIT_SCORE,
        job_description="We need a Python engineer with FastAPI experience.",
        resume_text="5 years of Python, FastAPI, PostgreSQL, async programming.",
        model="gpt-4o-mini",
        temperature=0.2,
    )


# ---------------------------------------------------------------------------
# Teal-sync fixtures
# ---------------------------------------------------------------------------

SAMPLE_TEAL_API_RESPONSE = {
    "id": "teal-job-abc123",
    "title": "Senior Python Engineer",
    "company": "Acme Corp",
    "status": TealApplicationStatus.BOOKMARKED.value,
    "created_at": datetime.now(timezone.utc).isoformat(),
    "updated_at": datetime.now(timezone.utc).isoformat(),
}


@pytest.fixture()
def sample_teal_job_payload() -> TealJobPayload:
    return TealJobPayload(
        title="Senior Python Engineer",
        company="Acme Corp",
        url="https://boards.example.com/jobs/123",
        location="Remote",
        description="Build scalable Python backends.",
        status=TealApplicationStatus.BOOKMARKED,
    )
