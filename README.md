# Career Alignment Engine & Job Pipeline

An automated, asynchronous pipeline to ingest job listings, analyze them against a candidate's résumé using LLM capabilities (Google Gemini or OpenAI), and synchronize matched positions to the Teal Job Tracker.

This application is built with a highly scalable, multi-tenant architecture designed for performance and security.

---

## 🚀 Key Features

* **Multi-Tenant Accounts & Data Isolation**: Full user registration and OAuth2 JWT session management. Users have personal profiles that store custom `gemini_api_key` and `teal_api_key` overrides. All analysis run histories and results are strictly isolated by account.
* **Relational Database**: Powered by SQLAlchemy. Defaults to a frictionless local `SQLite` database (`jobs.db`) for local testing, seamlessly switching to serverless `PostgreSQL` in production environments via environment variables.
* **Dual-Lane Task Queuing**: Leverages a highly-optimized dual-worker strategy orchestrated by Celery:
  * **I/O Lane**: A highly concurrent `gevent` pool strictly processes network-bound tasks (scraping boards, pushing to Teal).
  * **CPU Lane**: A `prefork` pool dedicated to computing-heavy tasks (LLM evaluations).
* **Zero-Discard Real-Time Telemetry**: Custom Celery signal hooks track precise task execution latencies in real-time, backing metrics into isolated Redis Sorted Sets by queue namespace.
* **Multi-Source Job Ingestion**: Scrapes job details from various platforms, normalizes fields (Title, Company, Description), and filters out boilerplate HTML junk with built-in SSRF protections.
* **LLM Fit Evaluation (Google Gemini / OpenAI)**: Analyzes the job description against a provided résumé. Computes a percentage fit score, extracts key matching and missing keywords, lists strengths and gaps, and delivers actionable resume-tailoring recommendations.
* **Interactive Glassmorphism Dashboard**: Modern dark-mode interface featuring a visual login overlay, real-time fetching of isolated pipeline execution histories, dynamic resume autosaving, and settings management.

---

## 🔒 Security Architecture

* **SSRF Protection**: Restricts the ingestion scraper from accessing internal, private IP addresses (e.g. `127.0.0.1`, `169.254.169.254`).
* **OAuth2 JWT Bearer Tokens**: All API endpoints require an active, validated Bearer token.
* **Zero-Passlib Crypto**: Core password hashing strictly relies directly on `bcrypt`, evading legacy library compatibility bugs and fully supporting Python 3.14+ architectures.

---

## 🛠️ Setup & Prerequisites

### 1. Configure the Environment
Copy the example environment file and add your default keys:
```powershell
cp .env.example .env
```
Inside your `.env` file, configure your settings:
```env
# Optional: Production Postgres URL (Will default to local SQLite `sqlite:///./jobs.db` if empty)
DATABASE_URL=

# Default Google Gemini Key (Users can override this in their dashboard profile)
GEMINI_API_KEY=your-gemini-key-here

# Redis Connection (Defaults to local container, or Upstash in production)
REDIS_URL=redis://:redis-secure-password-789@redis:6379/0

# Optional: Teal credentials
TEAL_API_KEY=
```

---

## 💻 How to Run

### Full Asynchronous Services (Docker)
To start the FastAPI web server, dual-lane Celery workers, and Redis broker:
```powershell
docker-compose up --build
```
Once active:
* **Interactive Dashboard**: View the UI at `http://localhost:8000/dashboard/`.
* **Swagger Documentation**: View endpoints at `http://localhost:8000/docs` (Authentication required).

---

## ☁️ Production Deployment

The containerized API is fully compatible with **Google Cloud Run** for serverless hosting:

1. **Configure Serverless Redis**: Set up a serverless Redis database on [Upstash](https://upstash.com/) and copy the `rediss://...` connection URL.
2. **Configure Serverless DB**: Provision a serverless PostgreSQL database (e.g. Supabase, Neon) and copy the connection string.
3. **Build and Push**:
   ```powershell
   docker build -t us-central1-docker.pkg.dev/YOUR_PROJECT_ID/job-pipeline/api:latest .
   docker push us-central1-docker.pkg.dev/YOUR_PROJECT_ID/job-pipeline/api:latest
   ```
4. **Deploy to Cloud Run**:
   ```powershell
   gcloud run deploy job-pipeline-api `
     --image us-central1-docker.pkg.dev/YOUR_PROJECT_ID/job-pipeline/api:latest `
     --region us-central1 `
     --platform managed `
     --allow-unauthenticated `
     --set-env-vars="DATABASE_URL=your-postgres-url,REDIS_URL=your-upstash-redis-url"
   ```

---

## 🧪 Testing
Run the comprehensive mocked unit testing suite (verifying auth, isolation, and routing structures) directly via `pytest`. (Note: The `email-validator` and `bcrypt` Python 3.14 compliant requirements are installed).
```powershell
python -m pytest
```
