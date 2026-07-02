# Career Alignment Engine & Job Pipeline

An automated, asynchronous pipeline to ingest job listings, analyze them against a candidate's résumé using LLM capabilities (Google Gemini or OpenAI), and synchronize matched positions to the Teal Job Tracker.

This application is built with a dual execution architecture:
1. **Local CLI Runner**: Run the full ingestion, match, and sync pipeline synchronously in a single command line process (no Docker or Celery/Redis dependencies required).
2. **FastAPI Web Service & Celery Task Queue**: A fully scalable asynchronous REST API with background queues backed by Redis, SQLite, and an interactive modern glassmorphism dashboard.

---

## 🚀 Key Features

* **Multi-Source Job Ingestion**: Scrapes job details from various platforms, normalizes fields (Title, Company, Description), and filters out boilerplate HTML junk with built-in SSRF protections.
* **LLM Fit Evaluation (Google Gemini / OpenAI)**: Analyzes the job description against a provided résumé. Computes a percentage fit score, extracts key matching and missing keywords, lists strengths and gaps, and delivers actionable resume-tailoring recommendations.
* **Rate-Limit Adaptability**: Automatically throttles Gemini API requests sequentially with a 4.2s delay to prevent 429 rate limit issues on the Free Tier.
* **Teal Tracker Syncing**: Simulates and pushes parsed job cards directly into your Teal platform boards. Includes a Mock dry-run mode when API keys are omitted.
* **Automated CI/CD**: Pushing changes runs a 30-test suite and auto-merges the `features` branch into `master` upon success.
* **Interactive Dashboard**: Modern dark-mode interface with a visual breakdown of match scores, direct Celery Flower log linking, and credential visibility toggles.

---

## 🔒 Security Architecture

* **SSRF Protection**: Restricts the ingestion scraper from accessing internal, private IP addresses (e.g. `127.0.0.1`, `169.254.169.254`).
* **Endpoint Authentication**: All pipeline, sync, and ingest endpoints require verification via the `X-API-Key` header.
* **Credential Protection**: Local dashboard secures storage of the local access key inside session memory and provides a visibility toggle for easy copy-pasting.

---

## 🛠️ Setup & Prerequisites

### 1. Configure the Environment
Copy the example environment file and add your Google Gemini API key:
```powershell
cp .env.example .env
```
Inside your `.env` file, configure your API keys:
```env
# Local access key for dashboard authentication
API_KEY=personal-secret-key-123

# Google Gemini Key (highly recommended)
GEMINI_API_KEY=your-gemini-key-here

# Redis Connection (Defaults to local container, or Upstash in production)
REDIS_URL=redis://:redis-secure-password-789@redis:6379/0

# Optional: OpenAI / Teal credentials (defaults to mock dry-runs if empty)
OPENAI_API_KEY=
TEAL_API_KEY=
```

### 2. Prepare Inputs
Create the template input files in the project root:
* **`resume.txt`**: Paste your full text résumé.
* **`jobs.txt`**: Add one job URL per line to analyze.

---

## 💻 How to Run

### Method A: Standalone Local CLI (Simplest)
To run the full ingestion and matching process locally without running Docker or database containers:
```powershell
python scripts/run-pipeline-cli.py
```
*(Alternative npm shortcut: `npm run pipeline:cli`)*

### Method B: Full Asynchronous Services (Docker)
To start the FastAPI web server, Celery worker, and Redis broker:
```powershell
docker-compose up --build
```
Once active:
* **Interactive Dashboard**: View the UI at `http://localhost:8000/dashboard/`.
* **Swagger Documentation**: View endpoints at `http://localhost:8000/docs` (requires `X-API-Key` authentication).
* **Trigger Background Pipeline**: Run the automation script to fire requests and poll status:
  ```powershell
  python scripts/auto-pipeline.py
  ```

---

## ☁️ Production Deployment

The containerized API is fully compatible with **Google Cloud Run** for serverless hosting:

1. **Configure Serverless Redis**: Set up a serverless Redis database on [Upstash](https://upstash.com/) and copy the `rediss://...` connection URL.
2. **Build and Push**:
   ```powershell
   docker build -t us-central1-docker.pkg.dev/YOUR_PROJECT_ID/job-pipeline/api:latest .
   docker push us-central1-docker.pkg.dev/YOUR_PROJECT_ID/job-pipeline/api:latest
   ```
3. **Deploy to Cloud Run**:
   ```powershell
   gcloud run deploy job-pipeline-api `
     --image us-central1-docker.pkg.dev/YOUR_PROJECT_ID/job-pipeline/api:latest `
     --region us-central1 `
     --platform managed `
     --allow-unauthenticated `
     --set-env-vars="GEMINI_API_KEY=your-gemini-key,API_KEY=your-dashboard-key,REDIS_URL=your-upstash-redis-url"
   ```

---

## 🧪 Testing
Run the mocked unit testing suite to verify ingestion, rate-limiting, and synchronization structures:
```powershell
py -m pytest
```
