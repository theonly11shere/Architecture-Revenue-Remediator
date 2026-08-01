import os
import logging
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from scraper import scrape_website
from scorer import score_audit

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


class AuditRequest(BaseModel):
    url: str
    email: str
    business_type: str = "general"


def send_admin_notification(prospect_email: str, prospect_url: str, audit_data: dict):
    print("==================================================")
    print("🔥 NEW LEAD AUDIT CAPTURED")
    print(f"SENDING DIRECTLY TO ADMIN: {ADMIN_EMAIL}")
    print(f"Prospect Email: {prospect_email}")
    print(f"Prospect Target URL: {prospect_url}")
    print(f"Score: {audit_data.get('overall_score')}")
    # Print the exact scraper error if score is 0.0
    if audit_data.get("audit_metadata", {}).get("error"):
        print(f"⚠️ SCRAPE ERROR: {audit_data['audit_metadata']['error']}")
    print("==================================================")


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/api/audit")
async def run_audit(payload: AuditRequest):
    try:
        url = payload.url.strip()
        user_email = payload.email.strip()
        b_type = payload.business_type.strip()

        # 1. Execute Scraper & Scorer
        scraped_data = await scrape_website(url)
        score_results = score_audit(scraped_data, b_type)

        # 2. Clean Domain String
        clean_domain = url.replace("https://", "").replace("http://", "").split("/")[0]

        # 3. Log / Notify Admin
        send_admin_notification(user_email, url, score_results)

        # 4. Return Formatted Results
        return {
            "domain": clean_domain,
            "prospect_email": user_email,
            "overall_score": score_results.get("overall_score", 0),
            "rating_label": score_results.get("rating_label", "Critical Risk"),
            "pillar_scores": score_results.get("pillar_scores", {}),
            "revenue_leaks_detected": score_results.get("revenue_leaks_detected", []),
            "actionable_recommendations": score_results.get("actionable_recommendations", []),
            "audit_metadata": score_results.get("audit_metadata", {})
        }

    except Exception as e:
        logger.error(f"Audit failed for URL {payload.url}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Audit execution failed: {str(e)}")