"""
Pydantic schemas for the Teal-sync domain.

Models the Teal job-tracker entities: jobs, applications, and the sync
lifecycle.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class TealApplicationStatus(StrEnum):
    """Application statuses recognised by Teal."""

    BOOKMARKED = "bookmarked"
    APPLYING = "applying"
    APPLIED = "applied"
    INTERVIEWING = "interviewing"
    NEGOTIATING = "negotiating"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class TealJobPayload(BaseModel):
    """Payload sent to Teal to create or update a tracked job."""

    model_config = ConfigDict(frozen=True)

    title: str = Field(min_length=1, max_length=512)
    company: str = Field(min_length=1, max_length=256)
    url: HttpUrl
    location: str = Field(default="Remote", max_length=256)
    description: str = Field(default="", max_length=10000)
    salary: str = Field(default="", max_length=128)
    status: TealApplicationStatus = TealApplicationStatus.BOOKMARKED
    notes: str = Field(default="", max_length=5000)
    tags: list[str] = Field(default_factory=list)


class TealJobResponse(BaseModel):
    """Response from the Teal API after creating/updating a job."""

    model_config = ConfigDict(frozen=True)

    teal_id: str = Field(min_length=1)
    title: str
    company: str
    status: TealApplicationStatus
    created_at: datetime
    updated_at: datetime


class TealSyncRequest(BaseModel):
    """A batch of jobs to push to Teal."""

    model_config = ConfigDict(frozen=True)

    sync_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    jobs: list[TealJobPayload] = Field(min_length=1)
    dry_run: bool = False


class TealSyncItemResult(BaseModel):
    """Outcome of syncing a single job to Teal."""

    model_config = ConfigDict(frozen=True)

    title: str
    company: str
    teal_id: str | None = None
    success: bool
    error: str | None = None


class TealSyncResult(BaseModel):
    """Aggregate outcome of a sync batch."""

    model_config = ConfigDict(frozen=True)

    sync_id: str
    items: list[TealSyncItemResult] = Field(default_factory=list)
    synced_count: int = 0
    failed_count: int = 0
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None
