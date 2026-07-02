"""
Pydantic schemas for the job-ingestion domain.

Covers the full lifecycle: raw scrape input → validated listing →
ingestion result with error context.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import StrEnum
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator


class JobBoardSource(StrEnum):
    """Known upstream job-board providers."""

    LINKEDIN = "linkedin"
    INDEED = "indeed"
    GREENHOUSE = "greenhouse"
    LEVER = "lever"
    CUSTOM = "custom"


class ScrapeTarget(BaseModel):
    """A single URL to scrape, optionally pinned to a source."""

    model_config = ConfigDict(frozen=True)

    url: HttpUrl
    source: JobBoardSource = JobBoardSource.CUSTOM
    metadata: dict[str, str] = Field(default_factory=dict)


class RawJobListing(BaseModel):
    """Unvalidated blob produced by the scraper before normalisation."""

    model_config = ConfigDict(frozen=True)

    source_url: HttpUrl
    source: JobBoardSource
    html_content: str = Field(min_length=1)
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class NormalisedJobListing(BaseModel):
    """Clean, structured representation of a scraped job posting."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    title: str = Field(min_length=1, max_length=512)
    company: str = Field(min_length=1, max_length=256)
    location: str = Field(max_length=256, default="Remote")
    description: str = Field(min_length=1)
    source_url: HttpUrl
    source: JobBoardSource
    salary_min: float | None = Field(default=None, ge=0)
    salary_max: float | None = Field(default=None, ge=0)
    currency: str = Field(default="USD", max_length=3)
    posted_at: datetime | None = None
    ingested_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    tags: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def salary_range_coherent(self) -> Self:
        """Ensure salary_min ≤ salary_max when both are present."""
        if (
            self.salary_min is not None
            and self.salary_max is not None
            and self.salary_min > self.salary_max
        ):
            raise ValueError(
                f"salary_min ({self.salary_min}) exceeds salary_max ({self.salary_max})"
            )
        return self


class IngestionError(BaseModel):
    """Structured error record for a failed ingestion attempt."""

    model_config = ConfigDict(frozen=True)

    source_url: HttpUrl
    error_code: str
    detail: str
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class IngestionResult(BaseModel):
    """Aggregate result of an ingestion batch."""

    model_config = ConfigDict(frozen=True)

    batch_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    succeeded: list[NormalisedJobListing] = Field(default_factory=list)
    failed: list[IngestionError] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None

    @property
    def total(self) -> int:
        return len(self.succeeded) + len(self.failed)

    @property
    def success_rate(self) -> float:
        return len(self.succeeded) / self.total if self.total else 0.0
