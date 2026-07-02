<a id="module-app.tasks.pipeline_tasks"></a>

<a id="app-tasks-pipeline-tasks-module"></a>

# app.tasks.pipeline_tasks module

Celery tasks that orchestrate the end-to-end job-application pipeline.

Each task is a thin shim that instantiates the relevant domain service,
runs the async logic via `asyncio.run`, and returns serialisable results.
