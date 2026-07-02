<a id="module-app.domains.teal_sync.services"></a>

<a id="app-domains-teal-sync-services-module"></a>

# app.domains.teal_sync.services module

Teal-sync service.

Full async HTTPx integration with the Teal job-tracker API. Supports
creating, updating, listing, and batch-syncing jobs. Includes robust
retry logic, rate-limit handling, and structured error reporting.

### *exception* app.domains.teal_sync.services.TealAPIError(status_code: int, detail: str)

Bases: `Exception`

Raised when a Teal API call fails after exhausting retries.

### *class* app.domains.teal_sync.services.TealSyncService(settings: [Settings](app.core.config.md#app.core.config.Settings) | None = None)

Bases: `object`

Async client for the Teal job-tracking REST API.

#### *async* create_job(job: [TealJobPayload](app.domains.teal_sync.models.md#app.domains.teal_sync.models.TealJobPayload)) → [TealJobResponse](app.domains.teal_sync.models.md#app.domains.teal_sync.models.TealJobResponse)

POST a new job to the Teal tracker.

#### *async* get_job(teal_id: str) → [TealJobResponse](app.domains.teal_sync.models.md#app.domains.teal_sync.models.TealJobResponse)

GET a single job by its Teal ID.

#### *async* list_jobs(status: [TealApplicationStatus](app.domains.teal_sync.models.md#app.domains.teal_sync.models.TealApplicationStatus) | None = None, limit: int = 100) → list[[TealJobResponse](app.domains.teal_sync.models.md#app.domains.teal_sync.models.TealJobResponse)]

GET all tracked jobs, optionally filtered by status.

#### *async* sync_batch(request: [TealSyncRequest](app.domains.teal_sync.models.md#app.domains.teal_sync.models.TealSyncRequest)) → [TealSyncResult](app.domains.teal_sync.models.md#app.domains.teal_sync.models.TealSyncResult)

Push a batch of jobs to Teal with per-item error isolation.

#### *async* update_job_status(teal_id: str, status: [TealApplicationStatus](app.domains.teal_sync.models.md#app.domains.teal_sync.models.TealApplicationStatus)) → [TealJobResponse](app.domains.teal_sync.models.md#app.domains.teal_sync.models.TealJobResponse)

PATCH the status of an existing Teal job.
