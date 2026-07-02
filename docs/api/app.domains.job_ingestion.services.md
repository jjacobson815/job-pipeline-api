<a id="module-app.domains.job_ingestion.services"></a>

<a id="app-domains-job-ingestion-services-module"></a>

# app.domains.job_ingestion.services module

Job-ingestion service.

Async scraping of job-board URLs with robust error handling for timeouts,
rate-limiting (429), dead links (404), and generic network failures.
Produces normalised job listings from raw HTML.

### *class* app.domains.job_ingestion.services.JobIngestionService(settings: [Settings](app.core.config.md#app.core.config.Settings) | None = None)

Bases: `object`

Scrapes job-board URLs and normalises the results.

#### *async* ingest_batch(targets: list[[ScrapeTarget](app.domains.job_ingestion.models.md#app.domains.job_ingestion.models.ScrapeTarget)], concurrency: int = 10) → [IngestionResult](app.domains.job_ingestion.models.md#app.domains.job_ingestion.models.IngestionResult)

Scrape a batch of URLs concurrently, return aggregated results.

#### *async* validate_url(url: str) → tuple[bool, str]

HEAD-check a URL. Returns (is_alive, detail).
