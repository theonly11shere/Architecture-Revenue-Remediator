import json
import logging
import os
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from scorer import score_audit
from scraper import scrape_website

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("trilloka_audit")

app = FastAPI(title="Trilloka Revenue Leak Audit API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ADMIN_EMAIL = "onlyonearpit@gmail.com"

# Ensure backup local reports directory exists
REPORTS_DIR = os.path.join(os.getcwd(), "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)


class AuditRequest(BaseModel):
  url: str
  email: str
  business_type: str = "general"


def save_report_backup(domain: str, full_report: dict) -> str:
  """Saves a JSON copy of the full audit report to the local file system."""
  timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
  clean_domain_name = (
      domain.replace(".", "_").replace("/", "_").replace(":", "_")
  )
  filename = f"report_{clean_domain_name}_{timestamp}.json"
  filepath = os.path.join(REPORTS_DIR, filename)

  try:
    with open(filepath, "w", encoding="utf-8") as f:
      json.dump(full_report, f, indent=4)
    print(f"📁 LOCAL BACKUP SAVED: {filepath}")
    return filename
  except Exception as e:
    print(f"⚠️ Failed to write local report file: {e}")
    return ""


def send_admin_notification(
    prospect_email: str, prospect_url: str, audit_data: dict, report_file: str
):
  print("==================================================")
  print("🔥 NEW LEAD AUDIT CAPTURED")
  print(f"SENDING DIRECTLY TO ADMIN: {ADMIN_EMAIL}")
  print(f"Prospect Email: {prospect_email}")
  print(f"Prospect Target URL: {prospect_url}")
  print(f"Score: {audit_data.get('overall_score')}")
  print(f"Local Backup Report File: {report_file}")
  if audit_data.get("audit_metadata", {}).get("error"):
    print(f"⚠️ SCRAPE ERROR: {audit_data['audit_metadata']['error']}")
  print("==================================================")


@app.get("/health")
async def health_check():
  return {"status": "healthy"}


# -------------------------------------------------------------------
# BACKUP ENDPOINTS TO ACCESS/DOWNLOAD GENERATED REPORTS
# -------------------------------------------------------------------


@app.get("/api/reports/latest")
async def get_latest_report():
  """Fetches the most recently generated audit report JSON directly."""
  files = [
      os.path.join(REPORTS_DIR, f)
      for f in os.listdir(REPORTS_DIR)
      if f.endswith(".json")
  ]
  if not files:
    raise HTTPException(status_code=404, detail="No reports generated yet.")

  latest_file = max(files, key=os.path.getmtime)
  with open(latest_file, "r", encoding="utf-8") as f:
    data = json.load(f)
  return JSONResponse(content=data)


@app.get("/api/reports/list")
async def list_all_reports():
  """Lists all audit reports saved on the server."""
  files = [f for f in os.listdir(REPORTS_DIR) if f.endswith(".json")]
  files.sort(
      key=lambda x: os.path.getmtime(os.path.join(REPORTS_DIR, x)), reverse=True
  )
  return {"total_reports": len(files), "reports": files}


@app.get("/api/reports/download/{filename}")
async def download_report(filename: str):
  """Downloads a specific report file from the server."""
  filepath = os.path.join(REPORTS_DIR, filename)
  if not os.path.exists(filepath):
    raise HTTPException(status_code=404, detail="Report file not found.")
  return FileResponse(
      filepath, media_type="application/json", filename=filename
  )


# -------------------------------------------------------------------
# MAIN AUDIT ROUTE
# -------------------------------------------------------------------


@app.post("/api/audit")
async def run_audit(payload: AuditRequest):
  try:
    url = payload.url.strip()
    user_email = payload.email.strip()
    b_type = payload.business_type.strip()

    # 1. Execute Scraper & Scorer
    scraped_data = await scrape_website(url)
    score_results = score_audit(scraped_data, b_type)

    # 2. Extract domain cleanly
    clean_domain = (
        url.replace("https://", "").replace("http://", "").split("/")[0]
    )

    final_score = score_results.get("overall_score", 0)
    leaks = score_results.get("revenue_leaks_detected", [])

    # 3. Build Full Response Payload
    response_payload = {
        "domain": clean_domain,
        "prospect_email": user_email,
        # Score Key Compatibility Wrappers:
        "score": final_score,
        "readiness": final_score,
        "overall_score": final_score,
        "rating_label": score_results.get("rating_label", "Critical Risk"),
        "pillar_scores": score_results.get("pillar_scores", {}),
        # Leak Key Compatibility Wrappers:
        "leaks": leaks,
        "revenue_leaks_detected": leaks,
        "top_seo_leaks": leaks,
        "biggest_pain_point": score_results.get("biggest_pain_point", {}),
        "actionable_recommendations": score_results.get(
            "actionable_recommendations", []
        ),
        "scraped_data_summary": scraped_data,
        "audit_metadata": score_results.get("audit_metadata", {}),
      }

    # 4. Save local JSON report contingency backup
    saved_filename = save_report_backup(clean_domain, response_payload)

    # 5. Log & Notify Admin
    send_admin_notification(
        user_email, url, score_results, report_file=saved_filename
    )

    return response_payload

  except Exception as e:
    logger.error(f"Audit failed for URL {payload.url}: {str(e)}")
    raise HTTPException(
        status_code=500, detail=f"Audit execution failed: {str(e)}"
    )