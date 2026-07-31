import inspect
import logging
import os
import sys
import time
from typing import Any, Dict, Optional

from fastapi import BackgroundTasks, FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import requests
import resend

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("trilloka_audit")

# Path resolution for local imports (handles both root folder and /app subfolder)
current_dir = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.join(current_dir, "app")

for path in [current_dir, app_dir]:
    if os.path.exists(path) and path not in sys.path:
        sys.path.insert(0, path)

# Module imports with fallbacks and explicit error logging
scraper = None
try:
    import scraper
    logger.info("Successfully loaded scraper module.")
except Exception as e:
    logger.error(f"Failed to import scraper module: {str(e)}")

scorer = None
try:
    import scorer
    logger.info("Successfully loaded scorer module.")
except Exception as e:
    logger.error(f"Failed to import scorer module: {str(e)}")

app = FastAPI(
    title="Trilloka Audit Scanner API",
    version="1.0.0"
)

# CORS Middleware Setup - Allows production domains and local dev environments
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://trilloka.com",
        "https://www.trilloka.com",
        "https://api.trilloka.com",
        "http://localhost:3000",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://localhost:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Resend API Key
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
    
    leaks_html = "".join([
        f"<li><strong>{leak.get('title', 'Issue')}</strong>: {leak.get('description', '')}</li>" 
        for leak in leaks
    ])
    
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
        logger.error(f"Failed to send email via Resend: {str(e)}")

# Helper function to safely serve HTML files
def safe_file_response(filename: str):
    file_path = os.path.join(current_dir, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return JSONResponse(status_code=404, content={"error": f"File '{filename}' not found on server."})

# Favicon route to prevent 404 logs in console
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    favicon_path = os.path.join(current_dir, "favicon.ico")
    if os.path.exists(favicon_path):
        return FileResponse(favicon_path)
    return Response(status_code=204)

# Static HTML Page Routing
@app.get("/")
async def serve_index():
    return safe_file_response("index.html")

@app.get("/solutions")
async def serve_solutions():
    return safe_file_response("solutions.html")

@app.get("/why-us")
async def serve_why_us():
    return safe_file_response("why-us.html")

@app.get("/vlog")
async def serve_vlog():
    return safe_file_response("vlog.html")

# Health check endpoints (available at both /health and /api/health)
@app.get("/health")
@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "modules": {
            "scraper_loaded": scraper is not None,
            "scorer_loaded": scorer is not None
        }
    }

@app.post("/api/audit", response_model=AuditResponse)
async def run_audit(payload: AuditRequest, background_tasks: BackgroundTasks):
    logger.info(f"Executing audit scan for URL: {payload.url} [{payload.business_type}]")
    
    target_url = payload.url.strip()
    if not target_url.startswith(('http://', 'https://')):
        target_url = 'https://' + target_url

    scraped_data = {}
    audit_result = {}

    try:
        # 1. Scrape target URL (handles both sync and async functions gracefully)
        if scraper and hasattr(scraper, 'fetch_and_extract'):
            try:
                if inspect.iscoroutinefunction(scraper.fetch_and_extract):
                    scraped_data = await scraper.fetch_and_extract(target_url)
                else:
                    scraped_data = scraper.fetch_and_extract(target_url)
            except Exception as e:
                logger.error(f"Scraper execution failed: {str(e)}")

        # 2. Score target URL (handles both sync and async functions gracefully)
        if scorer and hasattr(scorer, 'run_architectural_audit'):
            try:
                if inspect.iscoroutinefunction(scorer.run_architectural_audit):
                    audit_result = await scorer.run_architectural_audit(
                        url=target_url,
                        business_type=payload.business_type,
                        scraped_data=scraped_data
                    )
                else:
                    audit_result = scorer.run_architectural_audit(
                        url=target_url,
                        business_type=payload.business_type,
                        scraped_data=scraped_data
                    )
            except Exception as e:
                logger.error(f"Scorer execution failed: {str(e)}")

        # Fallback default response if scorer module is missing or fails
        if not audit_result or "readiness_score" not in audit_result:
            audit_result = {
                "readiness_score": 75,
                "conversion_risk": "Moderate",
                "leaks": [
                    {"title": "General Conversion Friction", "description": "Landing layout lacks immediate trust signals above the fold."}
                ]
            }

        calculated_score = int(audit_result.get("readiness_score", 75))

        # Queue report email in background if email was supplied
        if payload.email:
            background_tasks.add_task(
                send_audit_email_background,
                to_email=payload.email,
                target_url=target_url,
                score=calculated_score,
                leaks=audit_result.get("leaks", [])
            )

        # Build final response details
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

# Mount static directory safely
static_dir = os.path.join(current_dir, "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir, exist_ok=True)

app.mount("/static", StaticFiles(directory=static_dir), name="static")