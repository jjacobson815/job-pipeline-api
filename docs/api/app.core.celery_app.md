<a id="module-app.core.celery_app"></a>

<a id="app-core-celery-app-module"></a>

# app.core.celery_app module

Celery application factory.

Creates a single Celery instance wired to the Redis broker defined in
Settings.  Task autodiscovery scans the `app.tasks` package so new
task modules are picked up automatically.

### app.core.celery_app.create_celery_app() → Celery

Build and configure the Celery application.
