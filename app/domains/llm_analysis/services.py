"""
LLM-analysis service.

Sends job-description + résumé pairs to OpenAI for fit scoring, keyword
extraction, cover-letter drafting, or summarisation.  All calls go through
``httpx.AsyncClient`` with structured error handling and retry logic.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time

import httpx

from app.core.config import Settings, get_settings
from app.domains.llm_analysis.models import (
    AnalysisError,
    AnalysisKind,
    AnalysisRequest,
    AnalysisResponse,
    FitScoreResult,
    KeywordExtractionResult,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# System prompts per analysis kind
# ---------------------------------------------------------------------------

_SYSTEM_PROMPTS: dict[AnalysisKind, str] = {
    AnalysisKind.FIT_SCORE: (
        "You are a career-fit analyst. Given a job description and a résumé, "
        "produce a JSON object with the following keys: overall_score (0-100), "
        "keyword_overlap (list[str]), missing_keywords (list[str]), "
        "strengths (list[str]), gaps (list[str]), recommendation (str). "
        "Respond ONLY with valid JSON."
    ),
    AnalysisKind.KEYWORD_EXTRACTION: (
        "You are a keyword extraction engine. Given a job description and a "
        "résumé, produce a JSON object with: hard_skills (list[str]), "
        "soft_skills (list[str]), tools (list[str]), certifications (list[str]). "
        "Respond ONLY with valid JSON."
    ),
    AnalysisKind.COVER_LETTER_DRAFT: (
        "You are an expert career coach. Draft a concise, compelling cover "
        "letter that connects the candidate's experience to the job requirements. "
        "Write in first person. Output the cover letter text only."
    ),
    AnalysisKind.SUMMARY: (
        "You are a career analyst. Summarise the candidate's fit for this role "
        "in 3–5 bullet points. Be specific about matching and mismatching skills."
    ),
}


class LLMAnalysisService:
    """Async OpenAI integration for job-application analysis."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._base_url = str(self._settings.openai_base_url).rstrip("/")
        self._timeout = httpx.Timeout(
            connect=10.0,
            read=self._settings.http_timeout_seconds,
            write=10.0,
            pool=5.0,
        )

    async def analyse(self, request: AnalysisRequest) -> AnalysisResponse | AnalysisError:
        """Run a single analysis request against OpenAI or Gemini."""
        # Determine if we should use Gemini
        use_gemini = self._settings.is_gemini_configured
        use_openai = self._settings.is_openai_configured

        # Check if using placeholder or missing keys to use mock fallback
        if not use_gemini and not use_openai:
            logger.info("Using mock LLM analysis (no valid OpenAI or Gemini API key provided)")
            latency_ms = 50.0
            usage = {"prompt_tokens": 120, "completion_tokens": 80}
            if request.kind == AnalysisKind.FIT_SCORE:
                raw_text = json.dumps({
                    "overall_score": 85.0,
                    "keyword_overlap": ["FastAPI", "Python", "Celery"],
                    "missing_keywords": ["Docker"],
                    "strengths": ["Strong FastAPI experience", "Background in Celery task queues"],
                    "gaps": ["Lacks production Docker experience"],
                    "recommendation": "Great fit! Recommend highlighting FastAPI and Celery work on the resume."
                })
            elif request.kind == AnalysisKind.KEYWORD_EXTRACTION:
                raw_text = json.dumps({
                    "hard_skills": ["Python", "FastAPI", "Asynchronous Programming"],
                    "soft_skills": ["Communication", "Problem Solving"],
                    "tools": ["Git", "Redis", "Celery"],
                    "certifications": []
                })
            elif request.kind == AnalysisKind.COVER_LETTER_DRAFT:
                raw_text = "Dear Hiring Manager,\n\nI am writing to express my interest in the position..."
            else:
                raw_text = "Candidate has strong alignment with python and async task queue requirements."
                
            return self._build_response(request, raw_text, usage, latency_ms)

        system_prompt = _SYSTEM_PROMPTS[request.kind]
        user_content = (
            f"### Job Description\n{request.job_description}\n\n"
            f"### Résumé\n{request.resume_text}"
        )

        # Map models and setup base url/headers for Gemini vs OpenAI
        model = request.model
        if use_gemini:
            base_url = "https://generativelanguage.googleapis.com/v1beta/openai"
            api_key = self._settings.gemini_api_key
            # Map OpenAI models to Gemini counterparts
            if model == "gpt-4o-mini":
                model = "gemini-2.5-flash"
            elif model.startswith("gpt-"):
                model = "gemini-2.5-pro"
        else:
            base_url = self._base_url
            api_key = self._settings.openai_api_key


        payload = {
            "model": model,
            "temperature": request.temperature,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
        }
        if request.kind in (AnalysisKind.FIT_SCORE, AnalysisKind.KEYWORD_EXTRACTION):
            payload["response_format"] = {"type": "json_object"}
            
        if not use_gemini:
            payload["max_tokens"] = request.max_tokens


        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        url = f"{base_url.rstrip('/')}/chat/completions"

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            result = await self._post_with_retry(
                client, url, headers, payload, request_id=request.id
            )

        if isinstance(result, AnalysisError):
            return result

        raw_text, usage, latency_ms = result
        return self._build_response(request, raw_text, usage, latency_ms)

    async def analyse_batch(
        self, requests: list[AnalysisRequest], concurrency: int = 5
    ) -> list[AnalysisResponse | AnalysisError]:
        """Run multiple analyses concurrently with bounded parallelism."""
        semaphore = asyncio.Semaphore(concurrency)

        async def _bounded(req: AnalysisRequest) -> AnalysisResponse | AnalysisError:
            async with semaphore:
                return await self.analyse(req)

        return list(await asyncio.gather(*[_bounded(r) for r in requests]))

    # -- internals ---------------------------------------------------------

    async def _post_with_retry(
        self,
        client: httpx.AsyncClient,
        url: str,
        headers: dict[str, str],
        payload: dict,
        request_id: str,
    ) -> tuple[str, dict, float] | AnalysisError:
        retries = self._settings.http_max_retries
        backoff = self._settings.http_backoff_base

        for attempt in range(1, retries + 2):
            start = time.monotonic()
            try:
                response = await client.post(url, json=payload, headers=headers)

                if response.status_code == 429:
                    retry_after = float(response.headers.get("Retry-After", backoff))
                    if attempt <= retries:
                        logger.warning(
                            "OpenAI rate-limit hit (attempt %d/%d), waiting %.1fs",
                            attempt, retries, retry_after,
                        )
                        await asyncio.sleep(retry_after)
                        backoff *= 2
                        continue
                    return AnalysisError(
                        request_id=request_id,
                        error_type="RATE_LIMITED",
                        detail=f"429 persisted after {retries} retries",
                        retryable=True,
                    )

                response.raise_for_status()
                elapsed_ms = (time.monotonic() - start) * 1000

                body = response.json()
                raw_text = body["choices"][0]["message"]["content"]
                usage = body.get("usage", {})
                return raw_text, usage, elapsed_ms

            except httpx.TimeoutException:
                if attempt <= retries:
                    logger.warning(
                        "OpenAI timeout (attempt %d/%d), retrying in %.1fs",
                        attempt, retries, backoff,
                    )
                    await asyncio.sleep(backoff)
                    backoff *= 2
                    continue
                return AnalysisError(
                    request_id=request_id,
                    error_type="TIMEOUT",
                    detail=f"OpenAI request timed out after {retries} retries",
                    retryable=True,
                )

            except httpx.HTTPStatusError as exc:
                return AnalysisError(
                    request_id=request_id,
                    error_type=f"HTTP_{exc.response.status_code}",
                    detail=str(exc),
                    retryable=exc.response.status_code >= 500,
                )

            except httpx.RequestError as exc:
                if attempt <= retries:
                    await asyncio.sleep(backoff)
                    backoff *= 2
                    continue
                return AnalysisError(
                    request_id=request_id,
                    error_type="NETWORK_ERROR",
                    detail=f"Network error after {retries} retries: {exc}",
                    retryable=True,
                )

        return AnalysisError(
            request_id=request_id,
            error_type="EXHAUSTED_RETRIES",
            detail=f"All {retries} retries exhausted",
            retryable=True,
        )

    def _build_response(
        self,
        request: AnalysisRequest,
        raw_text: str,
        usage: dict,
        latency_ms: float,
    ) -> AnalysisResponse:
        fit_score: FitScoreResult | None = None
        keywords: KeywordExtractionResult | None = None
        cover_letter: str | None = None
        summary: str | None = None

        if request.kind == AnalysisKind.FIT_SCORE:
            fit_score = self._parse_fit_score(raw_text)
        elif request.kind == AnalysisKind.KEYWORD_EXTRACTION:
            keywords = self._parse_keywords(raw_text)
        elif request.kind == AnalysisKind.COVER_LETTER_DRAFT:
            cover_letter = raw_text.strip()
        elif request.kind == AnalysisKind.SUMMARY:
            summary = raw_text.strip()

        return AnalysisResponse(
            request_id=request.id,
            kind=request.kind,
            raw_completion=raw_text,
            fit_score=fit_score,
            keywords=keywords,
            cover_letter=cover_letter,
            summary=summary,
            model_used=request.model,
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            latency_ms=latency_ms,
        )

    @staticmethod
    def _clean_json_text(text: str) -> str:
        """Strip markdown code block wrappers (e.g. ```json ... ```) from JSON string."""
        text = text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            text = "\n".join(lines).strip()
        return text

    @classmethod
    def _parse_fit_score(cls, text: str) -> FitScoreResult:
        """Parse JSON from the LLM into a FitScoreResult, with fallback."""
        cleaned = cls._clean_json_text(text)
        try:
            data = json.loads(cleaned)
            return FitScoreResult(**data)
        except (json.JSONDecodeError, TypeError, ValueError):
            logger.warning("Failed to parse fit-score JSON, using fallback")
            return FitScoreResult(
                overall_score=0.0,
                recommendation=f"Parse error — raw response: {text[:500]}",
            )

    @classmethod
    def _parse_keywords(cls, text: str) -> KeywordExtractionResult:
        """Parse JSON from the LLM into a KeywordExtractionResult."""
        cleaned = cls._clean_json_text(text)
        try:
            data = json.loads(cleaned)
            return KeywordExtractionResult(**data)
        except (json.JSONDecodeError, TypeError, ValueError):
            logger.warning("Failed to parse keyword JSON, returning empty result")
            return KeywordExtractionResult()
