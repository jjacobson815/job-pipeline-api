<a id="module-app.domains.teal_sync.models"></a>

<a id="app-domains-teal-sync-models-module"></a>

# app.domains.teal_sync.models module

Pydantic schemas for the Teal-sync domain.

Models the Teal job-tracker entities: jobs, applications, and the sync
lifecycle.

### *class* app.domains.teal_sync.models.TealApplicationStatus(\*values)

Bases: `StrEnum`

Application statuses recognised by Teal.

#### ACCEPTED *= 'accepted'*

#### APPLIED *= 'applied'*

#### APPLYING *= 'applying'*

#### BOOKMARKED *= 'bookmarked'*

#### INTERVIEWING *= 'interviewing'*

#### NEGOTIATING *= 'negotiating'*

#### REJECTED *= 'rejected'*

#### WITHDRAWN *= 'withdrawn'*

### *class* app.domains.teal_sync.models.TealJobPayload(\*, title: ~typing.Annotated[str, ~annotated_types.MinLen(min_length=1), ~annotated_types.MaxLen(max_length=512)], company: ~typing.Annotated[str, ~annotated_types.MinLen(min_length=1), ~annotated_types.MaxLen(max_length=256)], url: ~pydantic.networks.HttpUrl, location: ~typing.Annotated[str, ~annotated_types.MaxLen(max_length=256)] = 'Remote', description: ~typing.Annotated[str, ~annotated_types.MaxLen(max_length=10000)] = '', salary: ~typing.Annotated[str, ~annotated_types.MaxLen(max_length=128)] = '', status: ~app.domains.teal_sync.models.TealApplicationStatus = TealApplicationStatus.BOOKMARKED, notes: ~typing.Annotated[str, ~annotated_types.MaxLen(max_length=5000)] = '', tags: list[str] = <factory>)

Bases: `BaseModel`

Payload sent to Teal to create or update a tracked job.

#### company *: str*

#### description *: str*

#### location *: str*

#### model_config *= {'frozen': True}*

Configuration for the model, should be a dictionary conforming to [ConfigDict][pydantic.config.ConfigDict].

#### notes *: str*

#### salary *: str*

#### status *: [TealApplicationStatus](#app.domains.teal_sync.models.TealApplicationStatus)*

#### tags *: list[str]*

#### title *: str*

#### url *: HttpUrl*

### *class* app.domains.teal_sync.models.TealJobResponse(, teal_id: Annotated[str, MinLen(min_length=1)], title: str, company: str, status: [TealApplicationStatus](#app.domains.teal_sync.models.TealApplicationStatus), created_at: datetime, updated_at: datetime)

Bases: `BaseModel`

Response from the Teal API after creating/updating a job.

#### company *: str*

#### created_at *: datetime*

#### model_config *= {'frozen': True}*

Configuration for the model, should be a dictionary conforming to [ConfigDict][pydantic.config.ConfigDict].

#### status *: [TealApplicationStatus](#app.domains.teal_sync.models.TealApplicationStatus)*

#### teal_id *: str*

#### title *: str*

#### updated_at *: datetime*

### *class* app.domains.teal_sync.models.TealSyncItemResult(, title: str, company: str, teal_id: str | None = None, success: bool, error: str | None = None)

Bases: `BaseModel`

Outcome of syncing a single job to Teal.

#### company *: str*

#### error *: str | None*

#### model_config *= {'frozen': True}*

Configuration for the model, should be a dictionary conforming to [ConfigDict][pydantic.config.ConfigDict].

#### success *: bool*

#### teal_id *: str | None*

#### title *: str*

### *class* app.domains.teal_sync.models.TealSyncRequest(\*, sync_id: str = <factory>, jobs: ~typing.Annotated[list[~app.domains.teal_sync.models.TealJobPayload], ~annotated_types.MinLen(min_length=1)], dry_run: bool = False)

Bases: `BaseModel`

A batch of jobs to push to Teal.

#### dry_run *: bool*

#### jobs *: list[[TealJobPayload](#app.domains.teal_sync.models.TealJobPayload)]*

#### model_config *= {'frozen': True}*

Configuration for the model, should be a dictionary conforming to [ConfigDict][pydantic.config.ConfigDict].

#### sync_id *: str*

### *class* app.domains.teal_sync.models.TealSyncResult(\*, sync_id: str, items: list[[TealSyncItemResult](#app.domains.teal_sync.models.TealSyncItemResult)] = <factory>, synced_count: int = 0, failed_count: int = 0, started_at: datetime = <factory>, completed_at: datetime | None = None)

Bases: `BaseModel`

Aggregate outcome of a sync batch.

#### completed_at *: datetime | None*

#### failed_count *: int*

#### items *: list[[TealSyncItemResult](#app.domains.teal_sync.models.TealSyncItemResult)]*

#### model_config *= {'frozen': True}*

Configuration for the model, should be a dictionary conforming to [ConfigDict][pydantic.config.ConfigDict].

#### started_at *: datetime*

#### sync_id *: str*

#### synced_count *: int*
