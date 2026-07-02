import asyncio
import os
import sys

# Ensure stdout/stderr use UTF-8 encoding on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.domains.job_ingestion.models import JobBoardSource, ScrapeTarget
from app.domains.job_ingestion.services import JobIngestionService
from app.domains.llm_analysis.models import AnalysisKind, AnalysisRequest
from app.domains.llm_analysis.services import LLMAnalysisService
from app.domains.teal_sync.models import TealJobPayload, TealSyncRequest
from app.domains.teal_sync.services import TealSyncService

async def main():
    resume_path = "resume.txt"
    jobs_path = "jobs.txt"

    if not os.path.exists(resume_path):
        print(f"❌ Error: '{resume_path}' not found in project root.")
        return 1
    if not os.path.exists(jobs_path):
        print(f"❌ Error: '{jobs_path}' not found in project root.")
        return 1

    with open(resume_path, "r", encoding="utf-8") as f:
        resume_text = f.read().strip()
    with open(jobs_path, "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]

    if not urls:
        print("❌ Error: No URLs found in 'jobs.txt'.")
        return 1

    print(f"🚀 Running pipeline locally for {len(urls)} job URLs...")

    # Stage 1: Ingest
    print("\n🔄 Stage 1: Ingesting Job Postings...")
    ingestion_service = JobIngestionService()
    targets = [ScrapeTarget(url=u, source=JobBoardSource.CUSTOM) for u in urls]
    ingestion_result = await ingestion_service.ingest_batch(targets)
    print(f"✅ Ingestion complete: {len(ingestion_result.succeeded)} succeeded, {len(ingestion_result.failed)} failed.")

    if not ingestion_result.succeeded:
        print("⚠️ No jobs were successfully ingested. Exiting.")
        return 0

    # Stage 2: Analyse
    print("\n🔄 Stage 2: Matching Résumé with LLM (using Gemini)...")
    analysis_service = LLMAnalysisService()
    for i, job in enumerate(ingestion_result.succeeded):
        print(f"   Analyzing job {i+1}: '{job.title}' at '{job.company}'...")
        request = AnalysisRequest(
            kind=AnalysisKind.FIT_SCORE,
            job_description=job.description,
            resume_text=resume_text,
        )
        response = await analysis_service.analyse(request)
        if hasattr(response, "fit_score") and response.fit_score:
            score = response.fit_score.overall_score
            rec = response.fit_score.recommendation
            print(f"   📊 Fit Score: {score}%")
            print(f"   💡 Recommendation: {rec}\n")
        else:
            print(f"   ❌ Analysis failed or returned error: {response}\n")

    # Stage 3: Sync to Teal
    print("\n🔄 Stage 3: Syncing to Teal...")
    teal_payloads = [
        TealJobPayload(
            title=job.title,
            company=job.company,
            url=job.source_url,
            location=job.location or "Remote",
            description=job.description[:10000],
            status="bookmarked"
        )
        for job in ingestion_result.succeeded
    ]
    teal_service = TealSyncService()
    sync_request = TealSyncRequest(jobs=teal_payloads, dry_run=True)
    teal_result = await teal_service.sync_batch(sync_request)
    print(f"✅ Sync complete (Dry Run): {teal_result.synced_count} jobs processed.")
    return 0

if __name__ == "__main__":
    # Handle event loop policies for Windows asyncio loop
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    sys.exit(asyncio.run(main()))
