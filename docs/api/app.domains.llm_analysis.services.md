<a id="module-app.domains.llm_analysis.services"></a>

<a id="app-domains-llm-analysis-services-module"></a>

# app.domains.llm_analysis.services module

LLM-analysis service.

Sends job-description + résumé pairs to OpenAI for fit scoring, keyword
extraction, cover-letter drafting, or summarisation.  All calls go through
`httpx.AsyncClient` with structured error handling and retry logic.

### *class* app.domains.llm_analysis.services.LLMAnalysisService(settings: [Settings](app.core.config.md#app.core.config.Settings) | None = None)

Bases: `object`

Async OpenAI integration for job-application analysis.

#### *async* analyse(request: [AnalysisRequest](app.domains.llm_analysis.models.md#app.domains.llm_analysis.models.AnalysisRequest)) → [AnalysisResponse](app.domains.llm_analysis.models.md#app.domains.llm_analysis.models.AnalysisResponse) | [AnalysisError](app.domains.llm_analysis.models.md#app.domains.llm_analysis.models.AnalysisError)

Run a single analysis request against OpenAI.

#### *async* analyse_batch(requests: list[[AnalysisRequest](app.domains.llm_analysis.models.md#app.domains.llm_analysis.models.AnalysisRequest)], concurrency: int = 5) → list[[AnalysisResponse](app.domains.llm_analysis.models.md#app.domains.llm_analysis.models.AnalysisResponse) | [AnalysisError](app.domains.llm_analysis.models.md#app.domains.llm_analysis.models.AnalysisError)]

Run multiple analyses concurrently with bounded parallelism.
