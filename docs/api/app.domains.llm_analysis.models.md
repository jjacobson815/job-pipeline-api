<a id="module-app.domains.llm_analysis.models"></a>

<a id="app-domains-llm-analysis-models-module"></a>

# app.domains.llm_analysis.models module

Pydantic schemas for the LLM-analysis domain.

Handles requests to OpenAI for résumé-to-JD matching, keyword extraction,
and fit scoring.

### *class* app.domains.llm_analysis.models.AnalysisError(\*, request_id: str, error_type: str, detail: str, retryable: bool = False, occurred_at: datetime = <factory>)

Bases: `BaseModel`

Structured error from a failed LLM call.

#### detail *: str*

#### error_type *: str*

#### model_config *= {'frozen': True}*

Configuration for the model, should be a dictionary conforming to [ConfigDict][pydantic.config.ConfigDict].

#### occurred_at *: datetime*

#### request_id *: str*

#### retryable *: bool*

### *class* app.domains.llm_analysis.models.AnalysisKind(\*values)

Bases: `StrEnum`

Types of LLM analysis the pipeline supports.

#### COVER_LETTER_DRAFT *= 'cover_letter_draft'*

#### FIT_SCORE *= 'fit_score'*

#### KEYWORD_EXTRACTION *= 'keyword_extraction'*

#### SUMMARY *= 'summary'*

### *class* app.domains.llm_analysis.models.AnalysisRequest(\*, id: str = <factory>, kind: ~app.domains.llm_analysis.models.AnalysisKind, job_description: ~typing.Annotated[str, ~annotated_types.MinLen(min_length=1)], resume_text: ~typing.Annotated[str, ~annotated_types.MinLen(min_length=1)], model: ~typing.Annotated[str, ~annotated_types.MaxLen(max_length=64)] = 'gpt-4o-mini', temperature: ~typing.Annotated[float, ~annotated_types.Ge(ge=0.0), ~annotated_types.Le(le=2.0)] = 0.3, max_tokens: ~typing.Annotated[int, ~annotated_types.Ge(ge=1), ~annotated_types.Le(le=16384)] = 1024)

Bases: `BaseModel`

Input payload for an LLM analysis task.

#### id *: str*

#### job_description *: str*

#### kind *: [AnalysisKind](#app.domains.llm_analysis.models.AnalysisKind)*

#### max_tokens *: int*

#### model *: str*

#### model_config *= {'frozen': True}*

Configuration for the model, should be a dictionary conforming to [ConfigDict][pydantic.config.ConfigDict].

#### resume_text *: str*

#### temperature *: float*

### *class* app.domains.llm_analysis.models.AnalysisResponse(\*, request_id: str, kind: ~app.domains.llm_analysis.models.AnalysisKind, raw_completion: ~typing.Annotated[str, ~annotated_types.MinLen(min_length=1)], fit_score: ~app.domains.llm_analysis.models.FitScoreResult | None = None, keywords: ~app.domains.llm_analysis.models.KeywordExtractionResult | None = None, cover_letter: str | None = None, summary: str | None = None, model_used: str, prompt_tokens: ~typing.Annotated[int, ~annotated_types.Ge(ge=0)], completion_tokens: ~typing.Annotated[int, ~annotated_types.Ge(ge=0)], latency_ms: ~typing.Annotated[float, ~annotated_types.Ge(ge=0)], created_at: ~datetime.datetime = <factory>)

Bases: `BaseModel`

Wrapper around any LLM analysis result.

#### completion_tokens *: int*

#### cover_letter *: str | None*

#### created_at *: datetime*

#### fit_score *: [FitScoreResult](#app.domains.llm_analysis.models.FitScoreResult) | None*

#### keywords *: [KeywordExtractionResult](#app.domains.llm_analysis.models.KeywordExtractionResult) | None*

#### kind *: [AnalysisKind](#app.domains.llm_analysis.models.AnalysisKind)*

#### latency_ms *: float*

#### model_config *= {'frozen': True}*

Configuration for the model, should be a dictionary conforming to [ConfigDict][pydantic.config.ConfigDict].

#### model_used *: str*

#### prompt_tokens *: int*

#### raw_completion *: str*

#### request_id *: str*

#### summary *: str | None*

### *class* app.domains.llm_analysis.models.FitScoreResult(\*, overall_score: ~typing.Annotated[float, ~annotated_types.Ge(ge=0.0), ~annotated_types.Le(le=100.0)], keyword_overlap: list[str] = <factory>, missing_keywords: list[str] = <factory>, strengths: list[str] = <factory>, gaps: list[str] = <factory>, recommendation: ~typing.Annotated[str, ~annotated_types.MinLen(min_length=1)])

Bases: `BaseModel`

Structured output of a fit-score analysis.

#### gaps *: list[str]*

#### keyword_overlap *: list[str]*

#### missing_keywords *: list[str]*

#### model_config *= {'frozen': True}*

Configuration for the model, should be a dictionary conforming to [ConfigDict][pydantic.config.ConfigDict].

#### overall_score *: float*

#### recommendation *: str*

#### strengths *: list[str]*

### *class* app.domains.llm_analysis.models.KeywordExtractionResult(\*, hard_skills: list[str] = <factory>, soft_skills: list[str] = <factory>, tools: list[str] = <factory>, certifications: list[str] = <factory>)

Bases: `BaseModel`

Extracted keywords grouped by category.

#### certifications *: list[str]*

#### hard_skills *: list[str]*

#### model_config *= {'frozen': True}*

Configuration for the model, should be a dictionary conforming to [ConfigDict][pydantic.config.ConfigDict].

#### soft_skills *: list[str]*

#### tools *: list[str]*
