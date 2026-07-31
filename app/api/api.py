"""
Trilloka Revenue Readiness & Audit API
FastAPI backend handling Pass ID authentication, tier limits, URL normalization,
Architect guardrails, automated scoring, and email report delivery.
"""

import os
import json
import asyncio
import time
from typing import Optional, List
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from bs4 import BeautifulSoup
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ── Trilloka Services & Core Imports ───────────────────────────────────────
from app.services.tier_manager import TierManager, normalize_url
from app.services.email_sender import send_audit_email
from app.services.scraper import SiteScraper
from app.services.scorer import ExternalScorer
from app.core.blueprints import SolutionBlueprintEngine
from app.services.report_generator import ReportGenerator

# ── Security: API Key for admin endpoints ──────────────────────────────────
ADMIN_API_KEY = os.environ.get("ADMIN_API_KEY", "")
if not ADMIN_API_KEY:
    import secrets
    ADMIN_API_KEY = secrets.token_urlsafe(32)
    print(f"[SECURITY] Generated temporary ADMIN_API_KEY: {ADMIN_API_KEY}")

security_bearer = HTTPBearer(auto_error=False)

async def verify_admin(credentials: HTTPAuthorizationCredentials = Depends(security_bearer)):
    """Require Bearer token matching ADMIN_API_KEY for admin endpoints."""
    if not credentials:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    if credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid auth scheme. Use Bearer.")
    if credentials.credentials != ADMIN_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return credentials.credentials

# ── Simple in-memory rate limiter ────────────────────────────────────────────
_rate_limit_store = {}
RATE_LIMIT_WINDOW = 60  # seconds

async def rate_limit(request: Request, max_requests: int = 10):
    """Basic IP-based rate limiting."""
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    window = _rate_limit_store.get(client_ip, [])
    window = [t for t in window if now - t < RATE_LIMIT_WINDOW]
    if len(window) >= max_requests:
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again in a minute.")
    window.append(now)
    _rate_limit_store[client_ip] = window

# ── Guardrail: Intercept Self-Scans of The Architect / Master Domain ────────
RESTRICTED_DOMAINS = ["trilloka.com", "thearchitect.io", "localhost", "127.0.0.1"]

def check_architect_guardrail(target_url: str):
    clean_url = target_url.lower().replace("https://", "").replace("http://", "").split("/")[0]
    if any(domain in clean_url for domain in RESTRICTED_DOMAINS):
        raise HTTPException(
            status_code=403,
            detail=(
                "🛑 SECURITY EXCEPTION: EGO OVERFLOW DETECTED. "
                "Nice try attempting to audit perfection. We scanned your URL, "
                "found an absolute masterclass of engineering, and decided to spare "
                "you the existential crisis. Go fix your client's conversion funnel instead."
            )
        )

app = FastAPI(title="Trilloka Revenue Leak & Audit Scanner", version="5.0.0")

# CORS Configuration
_origins = [
    "https://trilloka.com",
    "https://www.trilloka.com",
    "https://api.trilloka.com",
]
if os.environ.get("ENV", "dev").lower() == "dev":
    _origins.extend([
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000",
    ])

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.options("/{path:path}")
async def options_handler(path: str):
    return JSONResponse(content={"ok": True})


# ── Request Models ──────────────────────────────────────────────────────────

class ScanRequest(BaseModel):
    url: str
    pass_id: Optional[str] = None  # If provided, authenticates against TierManager CSV
    email: Optional[str] = None    # Recipient for instant report delivery
    business_type: str = "local"   # local, ecommerce, saas, agency, b2b, creator
    competitor_url: Optional[str] = "Not Provided"
    location: Optional[str] = "Global"


class HealthResponse(BaseModel):
    status: str
    version: str


# ── Endpoints ───────────────────────────────────────────────────────────────

@app.get("/api/health", response_model=HealthResponse)
async def health():
    return {"status": "ok", "version": "5.0.0"}


@app.post("/api/v1/scan")
async def scan(request: ScanRequest, background_tasks: BackgroundTasks, http_request: Request):
    """
    Main Scan Endpoint:
    - Normalizes URLs
    - Triggers Architect Guardrail
    - Validates Pass ID & Tier limits (or defaults to Free preview tier 3)
    - Executes headless scraper & external scorer
    - Generates solution blueprint report
    - Automatically emails report to client in background
    """
    # 1. Normalize and check guardrail
    target_url = normalize_url(request.url)
    if not target_url:
        raise HTTPException(status_code=400, detail="Invalid target URL provided.")
    
    check_architect_guardrail(target_url)
    await rate_limit(http_request, max_requests=10)

    # 2. Authenticate Pass ID or assign Free tier preview
    client_tier = 3  # Default preview tier for free scans
    if request.pass_id:
        manager = TierManager()
        authorized, client_tier, auth_message = manager.authorize_scan(request.pass_id, target_url)
        if not authorized:
            raise HTTPException(status_code=403, detail=f"Pass Authorization Failed: {auth_message}")
    
    # 3. Execute Scraper
    scraper = SiteScraper(headless=True)
    raw_results = scraper.scrape_url(target_url)

    # 4. Score External Metrics
    scorer = ExternalScorer()
    final_checkpoint_results = scorer.enhance_checkpoint_results(raw_results, target_url)

    # 5. Dynamic Matrix Blueprint Calculation
    engine = SolutionBlueprintEngine()
    report_payload = engine.process_and_generate_report(
        checkpoint_results=final_checkpoint_results,
        client_tier=client_tier,
        business_type=request.business_type
    )

    if report_payload.get("status") != "CALCULATIONS_COMPLETE":
        raise HTTPException(status_code=500, detail=report_payload.get("message", "Calculation error."))

    # 6. Generate Master Markdown Report
    generator = ReportGenerator(
        target_url=target_url,
        competitor_url=request.competitor_url or "Not Provided",
        location=request.location or "Global"
    )
    markdown_output = generator.build_markdown_report(report_payload)

    # Append free upsell banner if scanning without an elite pass
    if not request.pass_id:
        markdown_output += "\n\n---\n"
        markdown_output += "### 💎 Want Access to the Elite Architect Class?\n"
        markdown_output += "You are currently viewing a complimentary public preview. To unlock full competitor gap matrices, deep audits, and direct team implementation, acquire a client pass at Trilloka."

    # Save local report copy
    filename_slug = target_url.replace('https://','').replace('http://','').replace('/','_')
    output_filename = f"audit_report_{filename_slug}.md"
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(markdown_output)

    # 7. Background task: Dispatch Email Report
    if request.email:
        background_tasks.add_task(
            send_audit_email,
            recipient_email=request.email,
            target_url=target_url,
            report_filepath=output_filename,
            markdown_content=markdown_output
        )

    return {
        "status": "SUCCESS",
        "target_url": target_url,
        "client_tier": client_tier,
        "report_file": output_filename,
        "report_data": report_payload
    }


# ── Main Entrypoint ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", "8000"))
    host = os.environ.get("HOST", "0.0.0.0")
    uvicorn.run("api:app", host=host, port=port, reload=False)