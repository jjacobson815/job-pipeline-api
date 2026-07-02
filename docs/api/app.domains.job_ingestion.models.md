<a id="module-app.domains.job_ingestion.models"></a>

<a id="app-domains-job-ingestion-models-module"></a>

# app.domains.job_ingestion.models module

Pydantic schemas for the job-ingestion domain.

Covers the full lifecycle: raw scrape input → validated listing →
ingestion result with error context.

### *class* app.domains.job_ingestion.models.IngestionError(\*, source_url: HttpUrl, error_code: str, detail: str, occurred_at: datetime = <factory>)

Bases: `BaseModel`

Structured error record for a failed ingestion attempt.

#### detail *: str*

#### error_code *: str*

#### model_config *= {'frozen': True}*

Configuration for the model, should be a dictionary conforming to [ConfigDict][pydantic.config.ConfigDict].

#### occurred_at *: datetime*

#### source_url *: HttpUrl*

### *class* app.domains.job_ingestion.models.IngestionResult(\*, batch_id: str = <factory>, succeeded: list[[NormalisedJobListing](#app.domains.job_ingestion.models.NormalisedJobListing)] = <factory>, failed: list[[IngestionError](#app.domains.job_ingestion.models.IngestionError)] = <factory>, started_at: datetime = <factory>, completed_at: datetime | None = None)

Bases: `BaseModel`

Aggregate result of an ingestion batch.

#### batch_id *: str*

#### completed_at *: datetime | None*

#### failed *: list[[IngestionError](#app.domains.job_ingestion.models.IngestionError)]*

#### model_config *= {'frozen': True}*

Configuration for the model, should be a dictionary conforming to [ConfigDict][pydantic.config.ConfigDict].

#### started_at *: datetime*

#### succeeded *: list[[NormalisedJobListing](#app.domains.job_ingestion.models.NormalisedJobListing)]*

#### *property* success_rate *: float*

#### *property* total *: int*

### *class* app.domains.job_ingestion.models.JobBoardSource(\*values)

Bases: `StrEnum`

Known upstream job-board providers.

#### CUSTOM *= 'custom'*

#### GREENHOUSE *= 'greenhouse'*

#### INDEED *= 'indeed'*

#### LEVER *= 'lever'*

#### LINKEDIN *= 'linkedin'*

### *class* app.domains.job_ingestion.models.NormalisedJobListing(\*, id: str = <factory>, title: ~typing.Annotated[str, ~annotated_types.MinLen(min_length=1), ~annotated_types.MaxLen(max_length=512)], company: ~typing.Annotated[str, ~annotated_types.MinLen(min_length=1), ~annotated_types.MaxLen(max_length=256)], location: ~typing.Annotated[str, ~annotated_types.MaxLen(max_length=256)] = 'Remote', description: ~typing.Annotated[str, ~annotated_types.MinLen(min_length=1)], source_url: ~pydantic.networks.HttpUrl, source: ~app.domains.job_ingestion.models.JobBoardSource, salary_min: ~typing.Annotated[float | None, ~annotated_types.Ge(ge=0)] = None, salary_max: ~typing.Annotated[float | None, ~annotated_types.Ge(ge=0)] = None, currency: ~typing.Annotated[str, ~annotated_types.MaxLen(max_length=3)] = 'USD', posted_at: ~datetime.datetime | None = None, ingested_at: ~datetime.datetime = <factory>, tags: list[str] = <factory>)

Bases: `BaseModel`

Clean, structured representation of a scraped job posting.

#### company *: str*

#### currency *: str*

#### description *: str*

#### id *: str*

#### ingested_at *: datetime*

#### location *: str*

#### model_config *= {'frozen': True}*

Configuration for the model, should be a dictionary conforming to [ConfigDict][pydantic.config.ConfigDict].

#### posted_at *: datetime | None*

#### salary_max *: float | None*

#### salary_min *: float | None*

#### salary_range_coherent() → Self

Ensure salary_min ≤ salary_max when both are present.

#### source *: [JobBoardSource](#app.domains.job_ingestion.models.JobBoardSource)*

#### source_url *: HttpUrl*

#### tags *: list[str]*

#### title *: str*

### *class* app.domains.job_ingestion.models.RawJobListing(\*, source_url: ~pydantic.networks.HttpUrl, source: ~app.domains.job_ingestion.models.JobBoardSource, html_content: ~typing.Annotated[str, ~annotated_types.MinLen(min_length=1)], fetched_at: ~datetime.datetime = <factory>)

Bases: `BaseModel`

Unvalidated blob produced by the scraper before normalisation.

#### fetched_at *: datetime*

#### html_content *: str*

#### model_config *= {'frozen': True}*

Configuration for the model, should be a dictionary conforming to [ConfigDict][pydantic.config.ConfigDict].

#### source *: [JobBoardSource](#app.domains.job_ingestion.models.JobBoardSource)*

#### source_url *: HttpUrl*

### *class* app.domains.job_ingestion.models.ScrapeTarget(\*, url: HttpUrl, source: [JobBoardSource](#app.domains.job_ingestion.models.JobBoardSource) = JobBoardSource.CUSTOM, metadata: dict[str, str]=<factory>)

Bases: `BaseModel`

A single URL to scrape, optionally pinned to a source.

#### metadata *: dict[str, str]*

#### model_config *= {'frozen': True}*

Configuration for the model, should be a dictionary conforming to [ConfigDict][pydantic.config.ConfigDict].

#### source *: [JobBoardSource](#app.domains.job_ingestion.models.JobBoardSource)*

#### url *: HttpUrl*
