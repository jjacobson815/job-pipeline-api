# Job Pipeline API & CLI Tool

An automated, asynchronous pipeline to ingest job listings, analyze them against a candidate's résumé using LLM capabilities (Google Gemini Pro or OpenAI), and synchronize matched positions to the Teal Job Tracker.

This application is built with a dual execution architecture:
1. **Local CLI Runner**: Run the full ingestion, match, and sync pipeline synchronously in a single command line process (no Docker or Celery/Redis dependencies required).
2. **FastAPI Web Service & Celery Task Queue**: A fully scaleable asynchronous REST API with background queues backed by Redis and SQLite.

---

## 🚀 Key Features

* **Multi-Source Job Ingestion**: Scrapes job details from various platforms, normalizes fields (Title, Company, Description), and filters out boilerplate HTML junk.
* **LLM Fit Evaluation (Google Gemini / OpenAI)**: Analyzes the job description against a provided résumé. Computes a percentage fit score, extracts key matching and missing keywords, lists strengths and gaps, and delivers actionable resume-tailoring recommendations.
* **OpenAI-Compatible Gemini Integration**: Bridges Google Gemini API to the OpenAI client wrapper transparently to leverage models like `gemini-2.5-flash` or `gemini-2.5-pro`.
* **Teal Tracker Syncing**: Simulates and pushes parsed job cards directly into your Teal platform boards. Includes a Mock dry-run mode when API keys are omitted.
* **Sphinx & Obsidian Documentation**: Interactive project mapping layout that converts docstrings into markdown pages compatible with Sphinx and Obsidian canvases.

---

## 🛠️ Setup & Prerequisites

### 1. Configure the Environment
Copy the example environment file and add your Google Gemini API key:
```powershell
cp .env.example .env
```
Inside your `.env` file, configure your API keys:
```env
# Google Gemini Key (highly recommended)
GEMINI_API_KEY=your-gemini-key-here

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
python3 scripts/run-pipeline-cli.py
```
*(Alternative npm shortcut: `npm run pipeline:cli`)*

### Method B: Full Asynchronous Services (Docker)
To start the FastAPI web server, Celery worker, and Redis broker:
```powershell
docker-compose up --build
```
Once active:
* **Swagger Documentation**: View endpoints at `http://localhost:8000/docs`.
* **Trigger Background Pipeline**: Run `npm run pipeline:run` to fire requests asynchronously and poll task completion status in the terminal.

---

## 📂 Codebase Architecture

* `app/`
  * `core/` - Project settings, database session setup, and Pydantic validation schemas.
  * `domains/` - Core domain-driven layers:
    * `job_ingestion/` - HTML scraping, field parsing, and cleaning logic.
    * `llm_analysis/` - LLM prompting and robust JSON response cleaner.
    * `teal_sync/` - Payloads configuration and REST integrations to Teal.
* `scripts/`
  * `run-pipeline-cli.py` - Single-process runner script for local matches.
  * `auto-pipeline.py` - Script to trigger background tasks and poll web api.
  * `generate-docs.py` - Auto-generates Sphinx documentation.
* `tests/` - Fully mocked unit testing suites.

---

## 🧪 Testing
Run the pytest test suite to verify ingestion and synchronization structures:
```powershell
py -m pytest
```
