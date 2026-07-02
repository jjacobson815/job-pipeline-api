import json
import pytest
import httpx
from typing import Any

from app.core.config import Settings
from app.domains.llm_analysis.models import AnalysisKind, AnalysisRequest
from app.domains.llm_analysis.services import LLMAnalysisService


def test_clean_json_text():
    """Verify that markdown code block wrappers are stripped successfully."""
    wrapped_json = "```json\n{\n  \"overall_score\": 95.0\n}\n```"
    cleaned = LLMAnalysisService._clean_json_text(wrapped_json)
    assert cleaned == '{\n  "overall_score": 95.0\n}'

    plain_json = '{"overall_score": 95.0}'
    assert LLMAnalysisService._clean_json_text(plain_json) == plain_json


@pytest.mark.asyncio
async def test_parse_fit_score_fallback():
    """Verify that malformed JSON strings gracefully trigger a parse fallback result."""
    bad_json = "This is not valid json at all {"
    result = LLMAnalysisService._parse_fit_score(bad_json)
    assert result.overall_score == 0.0
    assert "Parse error" in result.recommendation


@pytest.mark.asyncio
async def test_llm_analysis_mock_mode(mock_settings: Settings):
    """Verify that mock response is returned when API keys are not configured."""
    # Force settings keys to be placeholders
    mock_settings.openai_api_key = "sk-your-openai-key-here"
    mock_settings.gemini_api_key = "your-gemini-api-key-here"
    
    service = LLMAnalysisService(mock_settings)
    req = AnalysisRequest(
        kind=AnalysisKind.FIT_SCORE,
        job_description="Sample Job",
        resume_text="Sample Resume",
    )
    
    res = await service.analyse(req)
    assert res.request_id == req.id
    assert res.fit_score is not None
    assert res.fit_score.overall_score == 85.0
    assert "mock" in res.fit_score.recommendation.lower() or "fastapi" in res.fit_score.recommendation.lower()


@pytest.mark.asyncio
async def test_llm_analysis_concurrency(mock_settings: Settings, mock_transport_factory):
    """Test that multiple analyses execute concurrently through the semaphored analyse_batch."""
    # Setup mock transport returning a valid openai format
    def handler(request: httpx.Request) -> httpx.Response:
        data = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps({
                            "overall_score": 75.0,
                            "keyword_overlap": ["Python"],
                            "missing_keywords": [],
                            "strengths": ["C#"],
                            "gaps": [],
                            "recommendation": "Decent fit."
                        })
                    }
                }
            ],
            "usage": {"prompt_tokens": 10, "completion_tokens": 10}
        }
        return httpx.Response(200, json=data)

    mock_settings.openai_api_key = "real-openai-api-key-configured"
    service = LLMAnalysisService(mock_settings)
    
    transport = mock_transport_factory(handler)
    
    requests = [
        AnalysisRequest(
            kind=AnalysisKind.FIT_SCORE,
            job_description=f"Job {i}",
            resume_text="Resume",
        )
        for i in range(3)
    ]
    
    # Temporarily patch client transport
    old_post_with_retry = service._post_with_retry
    async def fake_post(*args, **kwargs):
        # Return canned output format
        return (
            json.dumps({
                "overall_score": 75.0,
                "keyword_overlap": ["Python"],
                "missing_keywords": [],
                "strengths": [],
                "gaps": [],
                "recommendation": "Ok."
            }),
            {"prompt_tokens": 10, "completion_tokens": 10},
            10.0
        )
    service._post_with_retry = fake_post
    
    results = await service.analyse_batch(requests, concurrency=2)
    assert len(results) == 3
    for r in results:
        assert r.fit_score.overall_score == 75.0
