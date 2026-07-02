<a id="module-app.main"></a>

<a id="app-main-module"></a>

# app.main module

FastAPI application entry point.

Headless API — no HTML templates, no static files.  Exposes REST
endpoints for triggering pipeline stages and checking task status.
Lifespan hook validates configuration at startup.

### app.main.create_app() → FastAPI

### app.main.lifespan(app: FastAPI) → AsyncIterator[None]

Validate configuration eagerly on startup.
