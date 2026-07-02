import sys
import os
import time
import httpx

# Ensure stdout/stderr use UTF-8 encoding on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


API_BASE_URL = "http://localhost:8000"

def run_automation():
    resume_path = "resume.txt"
    jobs_path = "jobs.txt"

    if not os.path.exists(resume_path):
        print(f"❌ Error: '{resume_path}' not found in project root.")
        print("   Please create a 'resume.txt' file and paste your resume text there.")
        return 1

    if not os.path.exists(jobs_path):
        print(f"❌ Error: '{jobs_path}' not found in project root.")
        print("   Please create a 'jobs.txt' file with one job URL per line.")
        return 1

    with open(resume_path, "r", encoding="utf-8") as f:
        resume_text = f.read().strip()

    if not resume_text:
        print("❌ Error: 'resume.txt' is empty.")
        return 1

    with open(jobs_path, "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]

    if not urls:
        print("❌ Error: No URLs found in 'jobs.txt'.")
        return 1

    print(f"🚀 Triggering pipeline for {len(urls)} job URLs...")
    payload = {
        "urls": urls,
        "resume_text": resume_text,
        "source": "custom",
        "analysis_kind": "fit_score",
        "sync_to_teal": True
    }

    try:
        with httpx.Client(timeout=30.0) as client:
            # Trigger pipeline
            response = client.post(f"{API_BASE_URL}/api/v1/pipeline", json=payload)
            response.raise_for_status()
            task_id = response.json()["task_id"]
            print(f"✅ Background task successfully queued! Task ID: {task_id}")
            print("⏳ Polling task status (please make sure your API server & Celery workers are running)...")

            while True:
                status_resp = client.get(f"{API_BASE_URL}/api/v1/tasks/{task_id}")
                status_resp.raise_for_status()
                data = status_resp.json()
                status = data.get("status")

                if status == "success":
                    print("\n🎉 Pipeline completed successfully!")
                    result = data.get("result", {})
                    
                    ingest = result.get("ingestion", {})
                    succeeded = ingest.get("succeeded", [])
                    failed = ingest.get("failed", [])
                    print(f"\n📊 Ingestion: {len(succeeded)} succeeded, {len(failed)} failed.")
                    
                    # Print analysis results
                    analyses = result.get("analyses", [])
                    for i, analysis in enumerate(analyses):
                        fit = analysis.get("fit_score", {})
                        score = fit.get("overall_score", 0)
                        rec = fit.get("recommendation", "N/A")
                        print(f"\n📄 Job {i+1} Fit Match: {score}%")
                        print(f"   💡 Recommendation: {rec}")

                    # Teal sync results
                    teal = result.get("teal_sync", {})
                    if teal:
                        print(f"\n💼 Teal Sync: {teal.get('synced_count', 0)} jobs synced, {teal.get('failed_count', 0)} failed.")
                    break
                elif status == "failed":
                    print(f"\n❌ Pipeline task failed. Error: {data.get('error')}")
                    break
                else:
                    print(".", end="", flush=True)
                    time.sleep(2)

    except httpx.HTTPError as exc:
        print(f"\n❌ API request failed: {exc}")
        print("   Make sure the FastAPI server is running (e.g. uvicorn app.main:app or docker compose).")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(run_automation())
