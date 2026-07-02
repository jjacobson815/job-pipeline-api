<a id="app-domains-llm-analysis-package"></a>

# app.domains.llm_analysis package

<a id="submodules"></a>

## Submodules

* [app.domains.llm_analysis.models module](app.domains.llm_analysis.models.md)
  * [`AnalysisError`](app.domains.llm_analysis.models.md#app.domains.llm_analysis.models.AnalysisError)
    * [`AnalysisError.detail`](app.domains.llm_analysis.models.md#app.domains.llm_analysis.models.AnalysisError.detail)
    * [`AnalysisError.error_type`](app.domains.llm_analysis.models.md#app.domains.llm_analysis.models.AnalysisError.error_type)
    * [`AnalysisError.model_config`](app.domains.llm_analysis.models.md#app.domains.llm_analysis.models.AnalysisError.model_config)
    * [`AnalysisError.occurred_at`](app.domains.llm_analysis.models.md#app.domains.llm_analysis.models.AnalysisError.occurred_at)
    * [`AnalysisError.request_id`](app.domains.llm_analysis.models.md#app.domains.llm_analysis.models.AnalysisError.request_id)
    * [`AnalysisError.retryable`](app.domains.llm_analysis.models.md#app.domains.llm_analysis.models.AnalysisError.retryable)
  * [`AnalysisKind`](app.domains.llm_analysis.models.md#app.domains.llm_analysis.models.AnalysisKind)
    * [`AnalysisKind.COVER_LETTER_DRAFT`](app.domains.llm_analysis.models.md#app.domains.llm_analysis.models.AnalysisKind.COVER_LETTER_DRAFT)
    * [`AnalysisKind.FIT_SCORE`](app.domains.llm_analysis.models.md#app.domains.llm_analysis.models.AnalysisKind.FIT_SCORE)
    * [`AnalysisKind.KEYWORD_EXTRACTION`](app.domains.llm_analysis.models.md#app.domains.llm_analysis.models.AnalysisKind.KEYWORD_EXTRACTION)
    * [`AnalysisKind.SUMMARY`](app.domains.llm_analysis.models.md#app.domains.llm_analysis.models.AnalysisKind.SUMMARY)
  * [`AnalysisRequest`](app.domains.llm_analysis.models.md#app.domains.llm_analysis.models.AnalysisRequest)
    * [`AnalysisRequest.id`](app.domains.llm_analysis.models.md#app.domains.llm_analysis.models.AnalysisRequest.id)
    * [`AnalysisRequest.job_description`](app.domains.llm_analysis.models.md#app.domains.llm_analysis.models.AnalysisRequest.job_description)
    * [`AnalysisRequest.kind`](app.domains.llm_analysis.models.md#app.domains.llm_analysis.models.AnalysisRequest.kind)
    * [`AnalysisRequest.max_tokens`](app.domains.llm_analysis.models.md#app.domains.llm_analysis.models.AnalysisRequest.max_tokens)
    * [`AnalysisRequest.model`](app.domains.llm_analysis.models.md#app.domains.llm_analysis.models.AnalysisRequest.model)
    * [`AnalysisRequest.model_config`](app.domains.llm_analysis.models.md#app.domains.llm_analysis.models.AnalysisRequest.model_config)
    * [`AnalysisRequest.resume_text`](app.domains.llm_analysis.models.md#app.domains.llm_analysis.models.AnalysisRequest.resume_text)
    * [`AnalysisRequest.temperature`](app.domains.llm_analysis.models.md#app.domains.llm_analysis.models.AnalysisRequest.temperature)
  * [`AnalysisResponse`](app.domains.llm_analysis.models.md#app.domains.llm_analysis.models.AnalysisResponse)
    * [`AnalysisResponse.completion_tokens`](app.domains.llm_analysis.models.md#app.domains.llm_analysis.models.AnalysisResponse.completion_tokens)
    * [`AnalysisResponse.cover_letter`](app.domains.llm_analysis.models.md#app.domains.llm_analysis.models.AnalysisResponse.cover_letter)
    * [`AnalysisResponse.created_at`](app.domains.llm_analysis.models.md#app.domains.llm_analysis.models.AnalysisResponse.created_at)
    * [`AnalysisResponse.fit_score`](app.domains.llm_analysis.models.md#app.domains.llm_analysis.models.AnalysisResponse.fit_score)
    * [`AnalysisResponse.keywords`](app.domains.llm_analysis.models.md#app.domains.llm_analysis.models.AnalysisResponse.keywords)
    * [`AnalysisResponse.kind`](app.domains.llm_analysis.models.md#app.domains.llm_analysis.models.AnalysisResponse.kind)
    * [`AnalysisResponse.latency_ms`](app.domains.llm_analysis.models.md#app.domains.llm_analysis.models.AnalysisResponse.latency_ms)
    * [`AnalysisResponse.model_config`](app.domains.llm_analysis.models.md#app.domains.llm_analysis.models.AnalysisResponse.model_config)
    * [`AnalysisResponse.model_used`](app.domains.llm_analysis.models.md#app.domains.llm_analysis.models.AnalysisResponse.model_used)
    * [`AnalysisResponse.prompt_tokens`](app.domains.llm_analysis.models.md#app.domains.llm_analysis.models.AnalysisResponse.prompt_tokens)
    * [`AnalysisResponse.raw_completion`](app.domains.llm_analysis.models.md#app.domains.llm_analysis.models.AnalysisResponse.raw_completion)
    * [`AnalysisResponse.request_id`](app.domains.llm_analysis.models.md#app.domains.llm_analysis.models.AnalysisResponse.request_id)
    * [`AnalysisResponse.summary`](app.domains.llm_analysis.models.md#app.domains.llm_analysis.models.AnalysisResponse.summary)
  * [`FitScoreResult`](app.domains.llm_analysis.models.md#app.domains.llm_analysis.models.FitScoreResult)
    * [`FitScoreResult.gaps`](app.domains.llm_analysis.models.md#app.domains.llm_analysis.models.FitScoreResult.gaps)
    * [`FitScoreResult.keyword_overlap`](app.domains.llm_analysis.models.md#app.domains.llm_analysis.models.FitScoreResult.keyword_overlap)
    * [`FitScoreResult.missing_keywords`](app.domains.llm_analysis.models.md#app.domains.llm_analysis.models.FitScoreResult.missing_keywords)
    * [`FitScoreResult.model_config`](app.domains.llm_analysis.models.md#app.domains.llm_analysis.models.FitScoreResult.model_config)
    * [`FitScoreResult.overall_score`](app.domains.llm_analysis.models.md#app.domains.llm_analysis.models.FitScoreResult.overall_score)
    * [`FitScoreResult.recommendation`](app.domains.llm_analysis.models.md#app.domains.llm_analysis.models.FitScoreResult.recommendation)
    * [`FitScoreResult.strengths`](app.domains.llm_analysis.models.md#app.domains.llm_analysis.models.FitScoreResult.strengths)
  * [`KeywordExtractionResult`](app.domains.llm_analysis.models.md#app.domains.llm_analysis.models.KeywordExtractionResult)
    * [`KeywordExtractionResult.certifications`](app.domains.llm_analysis.models.md#app.domains.llm_analysis.models.KeywordExtractionResult.certifications)
    * [`KeywordExtractionResult.hard_skills`](app.domains.llm_analysis.models.md#app.domains.llm_analysis.models.KeywordExtractionResult.hard_skills)
    * [`KeywordExtractionResult.model_config`](app.domains.llm_analysis.models.md#app.domains.llm_analysis.models.KeywordExtractionResult.model_config)
    * [`KeywordExtractionResult.soft_skills`](app.domains.llm_analysis.models.md#app.domains.llm_analysis.models.KeywordExtractionResult.soft_skills)
    * [`KeywordExtractionResult.tools`](app.domains.llm_analysis.models.md#app.domains.llm_analysis.models.KeywordExtractionResult.tools)
* [app.domains.llm_analysis.services module](app.domains.llm_analysis.services.md)
  * [`LLMAnalysisService`](app.domains.llm_analysis.services.md#app.domains.llm_analysis.services.LLMAnalysisService)
    * [`LLMAnalysisService.analyse()`](app.domains.llm_analysis.services.md#app.domains.llm_analysis.services.LLMAnalysisService.analyse)
    * [`LLMAnalysisService.analyse_batch()`](app.domains.llm_analysis.services.md#app.domains.llm_analysis.services.LLMAnalysisService.analyse_batch)

<a id="module-app.domains.llm_analysis"></a>

<a id="module-contents"></a>

## Module contents
