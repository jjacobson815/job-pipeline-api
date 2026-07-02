"""
Pydantic schemas for the LLM-analysis domain.

Handles requests to OpenAI for résumé-to-JD matching, keyword extraction,
and fit scoring.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class AnalysisKind(StrEnum):
    """Types of LLM analysis the pipeline supports."""

    FIT_SCORE = "fit_score"
    KEYWORD_EXTRACTION = "keyword_extraction"
    COVER_LETTER_DRAFT = "cover_letter_draft"
    SUMMARY = "summary"


class AnalysisRequest(BaseModel):
    """Input payload for an LLM analysis task."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    kind: AnalysisKind
    job_description: str = Field(min_length=1)
    resume_text: str = Field(min_length=1)
    model: str = Field(default="gpt-4o-mini", max_length=64)
    temperature: float = Field(default=0.3, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1024, ge=1, le=16384)


class FitScoreResult(BaseModel):
    """Structured output of a fit-score analysis."""

    model_config = ConfigDict(frozen=True)

    overall_score: float = Field(ge=0.0, le=100.0)
    keyword_overlap: list[str] = Field(default_factory=list)
    missing_keywords: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    recommendation: str = Field(min_length=1)


class KeywordExtractionResult(BaseModel):
    """Extracted keywords grouped by category."""

    model_config = ConfigDict(frozen=True)

    hard_skills: list[str] = Field(default_factory=list)
    soft_skills: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)


class AnalysisResponse(BaseModel):
    """Wrapper around any LLM analysis result."""

    model_config = ConfigDict(frozen=True)

    request_id: str
    kind: AnalysisKind
    raw_completion: str = Field(min_length=1)
    fit_score: FitScoreResult | None = None
    keywords: KeywordExtractionResult | None = None
    cover_letter: str | None = None
    summary: str | None = None
    model_used: str
    prompt_tokens: int = Field(ge=0)
    completion_tokens: int = Field(ge=0)
    latency_ms: float = Field(ge=0.0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AnalysisError(BaseModel):
    """Structured error from a failed LLM call."""

    model_config = ConfigDict(frozen=True)

    request_id: str
    error_type: str
    detail: str
    retryable: bool = False
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
