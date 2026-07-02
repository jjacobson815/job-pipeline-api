import pytest
from app.core.config import Settings
from app.domains.job_search.services import JobSearchService


@pytest.mark.asyncio
async def test_job_search_fallback_trigger(mock_settings: Settings):
    """Verify that JobSearchService triggers the fallback list and sets fallback flag when DDG returns 0 results."""
    # Force settings keys to be placeholders
    mock_settings.openai_api_key = "sk-your-openai-key-here"
    mock_settings.gemini_api_key = "your-gemini-api-key-here"
    
    service = JobSearchService()
    # Inject mocked settings
    service.settings = mock_settings
    
    # Run discovery on mock resume
    res = await service.discover_jobs("Senior Developer remote")
    
    assert res["status"] == "success"
    assert res["fallback"] is True
    assert len(res["urls"]) > 0
    assert res["fallback_source"] in ("Remotive API", "Pre-vetted templates")
