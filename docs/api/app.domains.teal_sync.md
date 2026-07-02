<a id="app-domains-teal-sync-package"></a>

# app.domains.teal_sync package

<a id="submodules"></a>

## Submodules

* [app.domains.teal_sync.models module](app.domains.teal_sync.models.md)
  * [`TealApplicationStatus`](app.domains.teal_sync.models.md#app.domains.teal_sync.models.TealApplicationStatus)
    * [`TealApplicationStatus.ACCEPTED`](app.domains.teal_sync.models.md#app.domains.teal_sync.models.TealApplicationStatus.ACCEPTED)
    * [`TealApplicationStatus.APPLIED`](app.domains.teal_sync.models.md#app.domains.teal_sync.models.TealApplicationStatus.APPLIED)
    * [`TealApplicationStatus.APPLYING`](app.domains.teal_sync.models.md#app.domains.teal_sync.models.TealApplicationStatus.APPLYING)
    * [`TealApplicationStatus.BOOKMARKED`](app.domains.teal_sync.models.md#app.domains.teal_sync.models.TealApplicationStatus.BOOKMARKED)
    * [`TealApplicationStatus.INTERVIEWING`](app.domains.teal_sync.models.md#app.domains.teal_sync.models.TealApplicationStatus.INTERVIEWING)
    * [`TealApplicationStatus.NEGOTIATING`](app.domains.teal_sync.models.md#app.domains.teal_sync.models.TealApplicationStatus.NEGOTIATING)
    * [`TealApplicationStatus.REJECTED`](app.domains.teal_sync.models.md#app.domains.teal_sync.models.TealApplicationStatus.REJECTED)
    * [`TealApplicationStatus.WITHDRAWN`](app.domains.teal_sync.models.md#app.domains.teal_sync.models.TealApplicationStatus.WITHDRAWN)
  * [`TealJobPayload`](app.domains.teal_sync.models.md#app.domains.teal_sync.models.TealJobPayload)
    * [`TealJobPayload.company`](app.domains.teal_sync.models.md#app.domains.teal_sync.models.TealJobPayload.company)
    * [`TealJobPayload.description`](app.domains.teal_sync.models.md#app.domains.teal_sync.models.TealJobPayload.description)
    * [`TealJobPayload.location`](app.domains.teal_sync.models.md#app.domains.teal_sync.models.TealJobPayload.location)
    * [`TealJobPayload.model_config`](app.domains.teal_sync.models.md#app.domains.teal_sync.models.TealJobPayload.model_config)
    * [`TealJobPayload.notes`](app.domains.teal_sync.models.md#app.domains.teal_sync.models.TealJobPayload.notes)
    * [`TealJobPayload.salary`](app.domains.teal_sync.models.md#app.domains.teal_sync.models.TealJobPayload.salary)
    * [`TealJobPayload.status`](app.domains.teal_sync.models.md#app.domains.teal_sync.models.TealJobPayload.status)
    * [`TealJobPayload.tags`](app.domains.teal_sync.models.md#app.domains.teal_sync.models.TealJobPayload.tags)
    * [`TealJobPayload.title`](app.domains.teal_sync.models.md#app.domains.teal_sync.models.TealJobPayload.title)
    * [`TealJobPayload.url`](app.domains.teal_sync.models.md#app.domains.teal_sync.models.TealJobPayload.url)
  * [`TealJobResponse`](app.domains.teal_sync.models.md#app.domains.teal_sync.models.TealJobResponse)
    * [`TealJobResponse.company`](app.domains.teal_sync.models.md#app.domains.teal_sync.models.TealJobResponse.company)
    * [`TealJobResponse.created_at`](app.domains.teal_sync.models.md#app.domains.teal_sync.models.TealJobResponse.created_at)
    * [`TealJobResponse.model_config`](app.domains.teal_sync.models.md#app.domains.teal_sync.models.TealJobResponse.model_config)
    * [`TealJobResponse.status`](app.domains.teal_sync.models.md#app.domains.teal_sync.models.TealJobResponse.status)
    * [`TealJobResponse.teal_id`](app.domains.teal_sync.models.md#app.domains.teal_sync.models.TealJobResponse.teal_id)
    * [`TealJobResponse.title`](app.domains.teal_sync.models.md#app.domains.teal_sync.models.TealJobResponse.title)
    * [`TealJobResponse.updated_at`](app.domains.teal_sync.models.md#app.domains.teal_sync.models.TealJobResponse.updated_at)
  * [`TealSyncItemResult`](app.domains.teal_sync.models.md#app.domains.teal_sync.models.TealSyncItemResult)
    * [`TealSyncItemResult.company`](app.domains.teal_sync.models.md#app.domains.teal_sync.models.TealSyncItemResult.company)
    * [`TealSyncItemResult.error`](app.domains.teal_sync.models.md#app.domains.teal_sync.models.TealSyncItemResult.error)
    * [`TealSyncItemResult.model_config`](app.domains.teal_sync.models.md#app.domains.teal_sync.models.TealSyncItemResult.model_config)
    * [`TealSyncItemResult.success`](app.domains.teal_sync.models.md#app.domains.teal_sync.models.TealSyncItemResult.success)
    * [`TealSyncItemResult.teal_id`](app.domains.teal_sync.models.md#app.domains.teal_sync.models.TealSyncItemResult.teal_id)
    * [`TealSyncItemResult.title`](app.domains.teal_sync.models.md#app.domains.teal_sync.models.TealSyncItemResult.title)
  * [`TealSyncRequest`](app.domains.teal_sync.models.md#app.domains.teal_sync.models.TealSyncRequest)
    * [`TealSyncRequest.dry_run`](app.domains.teal_sync.models.md#app.domains.teal_sync.models.TealSyncRequest.dry_run)
    * [`TealSyncRequest.jobs`](app.domains.teal_sync.models.md#app.domains.teal_sync.models.TealSyncRequest.jobs)
    * [`TealSyncRequest.model_config`](app.domains.teal_sync.models.md#app.domains.teal_sync.models.TealSyncRequest.model_config)
    * [`TealSyncRequest.sync_id`](app.domains.teal_sync.models.md#app.domains.teal_sync.models.TealSyncRequest.sync_id)
  * [`TealSyncResult`](app.domains.teal_sync.models.md#app.domains.teal_sync.models.TealSyncResult)
    * [`TealSyncResult.completed_at`](app.domains.teal_sync.models.md#app.domains.teal_sync.models.TealSyncResult.completed_at)
    * [`TealSyncResult.failed_count`](app.domains.teal_sync.models.md#app.domains.teal_sync.models.TealSyncResult.failed_count)
    * [`TealSyncResult.items`](app.domains.teal_sync.models.md#app.domains.teal_sync.models.TealSyncResult.items)
    * [`TealSyncResult.model_config`](app.domains.teal_sync.models.md#app.domains.teal_sync.models.TealSyncResult.model_config)
    * [`TealSyncResult.started_at`](app.domains.teal_sync.models.md#app.domains.teal_sync.models.TealSyncResult.started_at)
    * [`TealSyncResult.sync_id`](app.domains.teal_sync.models.md#app.domains.teal_sync.models.TealSyncResult.sync_id)
    * [`TealSyncResult.synced_count`](app.domains.teal_sync.models.md#app.domains.teal_sync.models.TealSyncResult.synced_count)
* [app.domains.teal_sync.services module](app.domains.teal_sync.services.md)
  * [`TealAPIError`](app.domains.teal_sync.services.md#app.domains.teal_sync.services.TealAPIError)
  * [`TealSyncService`](app.domains.teal_sync.services.md#app.domains.teal_sync.services.TealSyncService)
    * [`TealSyncService.create_job()`](app.domains.teal_sync.services.md#app.domains.teal_sync.services.TealSyncService.create_job)
    * [`TealSyncService.get_job()`](app.domains.teal_sync.services.md#app.domains.teal_sync.services.TealSyncService.get_job)
    * [`TealSyncService.list_jobs()`](app.domains.teal_sync.services.md#app.domains.teal_sync.services.TealSyncService.list_jobs)
    * [`TealSyncService.sync_batch()`](app.domains.teal_sync.services.md#app.domains.teal_sync.services.TealSyncService.sync_batch)
    * [`TealSyncService.update_job_status()`](app.domains.teal_sync.services.md#app.domains.teal_sync.services.TealSyncService.update_job_status)

<a id="module-app.domains.teal_sync"></a>

<a id="module-contents"></a>

## Module contents
