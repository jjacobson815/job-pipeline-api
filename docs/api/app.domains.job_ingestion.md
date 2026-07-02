<a id="app-domains-job-ingestion-package"></a>

# app.domains.job_ingestion package

<a id="submodules"></a>

## Submodules

* [app.domains.job_ingestion.models module](app.domains.job_ingestion.models.md)
  * [`IngestionError`](app.domains.job_ingestion.models.md#app.domains.job_ingestion.models.IngestionError)
    * [`IngestionError.detail`](app.domains.job_ingestion.models.md#app.domains.job_ingestion.models.IngestionError.detail)
    * [`IngestionError.error_code`](app.domains.job_ingestion.models.md#app.domains.job_ingestion.models.IngestionError.error_code)
    * [`IngestionError.model_config`](app.domains.job_ingestion.models.md#app.domains.job_ingestion.models.IngestionError.model_config)
    * [`IngestionError.occurred_at`](app.domains.job_ingestion.models.md#app.domains.job_ingestion.models.IngestionError.occurred_at)
    * [`IngestionError.source_url`](app.domains.job_ingestion.models.md#app.domains.job_ingestion.models.IngestionError.source_url)
  * [`IngestionResult`](app.domains.job_ingestion.models.md#app.domains.job_ingestion.models.IngestionResult)
    * [`IngestionResult.batch_id`](app.domains.job_ingestion.models.md#app.domains.job_ingestion.models.IngestionResult.batch_id)
    * [`IngestionResult.completed_at`](app.domains.job_ingestion.models.md#app.domains.job_ingestion.models.IngestionResult.completed_at)
    * [`IngestionResult.failed`](app.domains.job_ingestion.models.md#app.domains.job_ingestion.models.IngestionResult.failed)
    * [`IngestionResult.model_config`](app.domains.job_ingestion.models.md#app.domains.job_ingestion.models.IngestionResult.model_config)
    * [`IngestionResult.started_at`](app.domains.job_ingestion.models.md#app.domains.job_ingestion.models.IngestionResult.started_at)
    * [`IngestionResult.succeeded`](app.domains.job_ingestion.models.md#app.domains.job_ingestion.models.IngestionResult.succeeded)
    * [`IngestionResult.success_rate`](app.domains.job_ingestion.models.md#app.domains.job_ingestion.models.IngestionResult.success_rate)
    * [`IngestionResult.total`](app.domains.job_ingestion.models.md#app.domains.job_ingestion.models.IngestionResult.total)
  * [`JobBoardSource`](app.domains.job_ingestion.models.md#app.domains.job_ingestion.models.JobBoardSource)
    * [`JobBoardSource.CUSTOM`](app.domains.job_ingestion.models.md#app.domains.job_ingestion.models.JobBoardSource.CUSTOM)
    * [`JobBoardSource.GREENHOUSE`](app.domains.job_ingestion.models.md#app.domains.job_ingestion.models.JobBoardSource.GREENHOUSE)
    * [`JobBoardSource.INDEED`](app.domains.job_ingestion.models.md#app.domains.job_ingestion.models.JobBoardSource.INDEED)
    * [`JobBoardSource.LEVER`](app.domains.job_ingestion.models.md#app.domains.job_ingestion.models.JobBoardSource.LEVER)
    * [`JobBoardSource.LINKEDIN`](app.domains.job_ingestion.models.md#app.domains.job_ingestion.models.JobBoardSource.LINKEDIN)
  * [`NormalisedJobListing`](app.domains.job_ingestion.models.md#app.domains.job_ingestion.models.NormalisedJobListing)
    * [`NormalisedJobListing.company`](app.domains.job_ingestion.models.md#app.domains.job_ingestion.models.NormalisedJobListing.company)
    * [`NormalisedJobListing.currency`](app.domains.job_ingestion.models.md#app.domains.job_ingestion.models.NormalisedJobListing.currency)
    * [`NormalisedJobListing.description`](app.domains.job_ingestion.models.md#app.domains.job_ingestion.models.NormalisedJobListing.description)
    * [`NormalisedJobListing.id`](app.domains.job_ingestion.models.md#app.domains.job_ingestion.models.NormalisedJobListing.id)
    * [`NormalisedJobListing.ingested_at`](app.domains.job_ingestion.models.md#app.domains.job_ingestion.models.NormalisedJobListing.ingested_at)
    * [`NormalisedJobListing.location`](app.domains.job_ingestion.models.md#app.domains.job_ingestion.models.NormalisedJobListing.location)
    * [`NormalisedJobListing.model_config`](app.domains.job_ingestion.models.md#app.domains.job_ingestion.models.NormalisedJobListing.model_config)
    * [`NormalisedJobListing.posted_at`](app.domains.job_ingestion.models.md#app.domains.job_ingestion.models.NormalisedJobListing.posted_at)
    * [`NormalisedJobListing.salary_max`](app.domains.job_ingestion.models.md#app.domains.job_ingestion.models.NormalisedJobListing.salary_max)
    * [`NormalisedJobListing.salary_min`](app.domains.job_ingestion.models.md#app.domains.job_ingestion.models.NormalisedJobListing.salary_min)
    * [`NormalisedJobListing.salary_range_coherent()`](app.domains.job_ingestion.models.md#app.domains.job_ingestion.models.NormalisedJobListing.salary_range_coherent)
    * [`NormalisedJobListing.source`](app.domains.job_ingestion.models.md#app.domains.job_ingestion.models.NormalisedJobListing.source)
    * [`NormalisedJobListing.source_url`](app.domains.job_ingestion.models.md#app.domains.job_ingestion.models.NormalisedJobListing.source_url)
    * [`NormalisedJobListing.tags`](app.domains.job_ingestion.models.md#app.domains.job_ingestion.models.NormalisedJobListing.tags)
    * [`NormalisedJobListing.title`](app.domains.job_ingestion.models.md#app.domains.job_ingestion.models.NormalisedJobListing.title)
  * [`RawJobListing`](app.domains.job_ingestion.models.md#app.domains.job_ingestion.models.RawJobListing)
    * [`RawJobListing.fetched_at`](app.domains.job_ingestion.models.md#app.domains.job_ingestion.models.RawJobListing.fetched_at)
    * [`RawJobListing.html_content`](app.domains.job_ingestion.models.md#app.domains.job_ingestion.models.RawJobListing.html_content)
    * [`RawJobListing.model_config`](app.domains.job_ingestion.models.md#app.domains.job_ingestion.models.RawJobListing.model_config)
    * [`RawJobListing.source`](app.domains.job_ingestion.models.md#app.domains.job_ingestion.models.RawJobListing.source)
    * [`RawJobListing.source_url`](app.domains.job_ingestion.models.md#app.domains.job_ingestion.models.RawJobListing.source_url)
  * [`ScrapeTarget`](app.domains.job_ingestion.models.md#app.domains.job_ingestion.models.ScrapeTarget)
    * [`ScrapeTarget.metadata`](app.domains.job_ingestion.models.md#app.domains.job_ingestion.models.ScrapeTarget.metadata)
    * [`ScrapeTarget.model_config`](app.domains.job_ingestion.models.md#app.domains.job_ingestion.models.ScrapeTarget.model_config)
    * [`ScrapeTarget.source`](app.domains.job_ingestion.models.md#app.domains.job_ingestion.models.ScrapeTarget.source)
    * [`ScrapeTarget.url`](app.domains.job_ingestion.models.md#app.domains.job_ingestion.models.ScrapeTarget.url)
* [app.domains.job_ingestion.services module](app.domains.job_ingestion.services.md)
  * [`JobIngestionService`](app.domains.job_ingestion.services.md#app.domains.job_ingestion.services.JobIngestionService)
    * [`JobIngestionService.ingest_batch()`](app.domains.job_ingestion.services.md#app.domains.job_ingestion.services.JobIngestionService.ingest_batch)
    * [`JobIngestionService.validate_url()`](app.domains.job_ingestion.services.md#app.domains.job_ingestion.services.JobIngestionService.validate_url)

<a id="module-app.domains.job_ingestion"></a>

<a id="module-contents"></a>

## Module contents
