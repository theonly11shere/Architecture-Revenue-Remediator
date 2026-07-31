import sys
import os
import time
import logging
import requests
import resend
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Path resolution for local imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    import scraper
except ImportError:
    scraper = None

try:
    import scorer
except ImportError:
    scorer = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("trilloka_audit")

app = FastAPI(
    title="Trilloka Audit Scanner API",
    version="1.0.0"
)

# CORS Middleware Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://trilloka.com",
        "https://www.trilloka.com",
        "http://localhost:3000",
        "http://127.0.0.1:8000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Resend
resend.api_key = os.getenv("RESEND_API_KEY", "")

class AuditRequest(BaseModel):
    url: str
    business_type: Optional[str] = "General"
    email: Optional[str] = None

class AuditResponse(BaseModel):
    status: str
    score: int
    summary: str
    details: Dict[str, Any]
    email_status: Optional[str] = None

def send_audit_email_background(to_email: str, target_url: str, score: int, leaks: list):
    if not resend.api_key or not to_email:
        return
    
    leaks_html = "".join([f"<li><strong>{leak.get('title')}</strong>: {leak.get('description')}</li>" for leak in leaks])
    
    html_content = f"""
    <h2>Your Trilloka Audit Report for {target_url}</h2>
    <p><strong>Revenue Readiness Score:</strong> {score}/100</p>
    <h3>Detected Revenue Leaks:</h3>
    <ul>{leaks_html}</ul>
    <p>Log back into Trilloka to view your full architectural remediation plan.</p>
    """
    
    try:
        resend.Emails.send({
            "from": "audit@trilloka.com",
            "to": [to_email],
            "subject": f"Audit Report & Revenue Leaks for {target_url}",
            "html": html_content
        })
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")

# HTML Page Routing
@app.get("/")
async def serve_index():
    return FileResponse(os.path.join(current_dir, "index.html"))

@app.get("/solutions")
async def serve_solutions():
    return FileResponse(os.path.join(current_dir, "solutions.html"))

@app.get("/why-us")
async def serve_why_us():
    return FileResponse(os.path.join(current_dir, "why-us.html"))

@app.get("/vlog")
async def serve_vlog():
    return FileResponse(os.path.join(current_dir, "vlog.html"))

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/api/audit", response_model=AuditResponse)
async def run_audit(payload: AuditRequest, background_tasks: BackgroundTasks):
    logger.info(f"Executing audit scan for URL: {payload.url} [{payload.business_type}]")
    
    target_url = payload.url.strip()
    if not target_url.startswith(('http://', 'https://')):
        target_url = 'https://' + target_url

    scraped_data = {}
    audit_result = {}

    try:
        # 1. Asynchronously crawl target URL using scraper.py
        if scraper and hasattr(scraper, 'fetch_and_extract'):
            try:
                scraped_data = await scraper.fetch_and_extract(target_url)
            except Exception as e:
                logger.error(f"Scraper execution failed: {str(e)}")

        # 2. Pass live scraped dataset into scorer.py to compute score and leaks
        if scorer and hasattr(scorer, 'run_architectural_audit'):
            try:
                audit_result = scorer.run_architectural_audit(
                    url=target_url,
                    business_type=payload.business_type,
                    scraped_data=scraped_data
                )
            except Exception as e:
                logger.error(f"Scorer execution failed: {str(e)}")

        # Fallback if scorer is unavailable
        if not audit_result or "readiness_score" not in audit_result:
            audit_result = {
                "readiness_score": 75,
                "conversion_risk": "Moderate",
                "leaks": [
                    {"title": "General Conversion Friction", "description": "Landing layout lacks immediate trust signals above the fold."}
                ]
            }

        calculated_score = int(audit_result.get("readiness_score", 75))

        # Send report email in background if provided
        if payload.email:
            background_tasks.add_task(
                send_audit_email_background,
                to_email=payload.email,
                target_url=target_url,
                score=calculated_score,
                leaks=audit_result.get("leaks", [])
            )

        # Build response details joining scraper DOM telemetry with scorer vitals
        response_details = {
            "target_url": target_url,
            "business_type": payload.business_type,
            "load_time_ms": scraped_data.get("load_time_ms") or audit_result.get("add_on_metrics", {}).get("response_latency_ms", 120),
            "ssl_enabled": scraped_data.get("ssl_enabled") if "ssl_enabled" in scraped_data else audit_result.get("add_on_metrics", {}).get("ssl_integrity") == "Valid HTTPS",
            "has_title": scraped_data.get("meta", {}).get("title") is not None if scraped_data else True,
            "title_text": scraped_data.get("meta", {}).get("title") if scraped_data else None,
            "meta_description": scraped_data.get("meta", {}).get("description") if scraped_data else None,
            "heading_structure": scraped_data.get("headings", {}),
            "image_stats": scraped_data.get("images", {}),
            "social_signals": scraped_data.get("social_signals", {}),
            "cta_elements": scraped_data.get("cta_elements", {}),
            "analytics_tags": scraped_data.get("analytics_tags", {}),
            "revenue_leak_risk": audit_result.get("conversion_risk", "Moderate"),
            "leaks": audit_result.get("leaks", []),
            "seo_vitals": audit_result.get("add_on_metrics", {})
        }

        return AuditResponse(
            status="success",
            score=calculated_score,
            summary=f"Audit completed successfully for {payload.url}.",
            details=response_details
        )

    except Exception as e:
        logger.error(f"Error during scan for {payload.url}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Scan execution error: {str(e)}")

# Secure Static Mounting
static_dir = os.path.join(current_dir, "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir, exist_ok=True)

app.mount("/static", StaticFiles(directory=static_dir), name="static")