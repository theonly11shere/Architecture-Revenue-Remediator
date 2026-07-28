#!/usr/bin/env python3
"""RRS API — FastAPI app with competitor support, admin reports, and email delivery."""
import os
import json
import asyncio
from typing import Optional, List
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from bs4 import BeautifulSoup
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl

# RRS modules
from config import (
    PRICING, ADMIN_EMAIL, ADMIN_REPORT_AUTO_SEND, EMAIL_FROM, RESEND_API_KEY,
    ADMIN_REPORT_INCLUDE_ROADMAP, ADMIN_REPORT_INCLUDE_COMPETITOR,
    REDIS_URL, RATE_LIMIT_FREE, RATE_LIMIT_PAID,
)
from scraper import WebsiteScraper
from scorer import RevenueScorer
from content_evidence_signals import ContentEvidenceSignals
from reporter import ReportGenerator

# Optional: Resend for email
try:
    import resend
    RESEND_AVAILABLE = True
except ImportError:
    RESEND_AVAILABLE = False

# Optional: Redis for storing admin reports
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

app = FastAPI(title="Revenue Readiness Scanner", version="4.1.0")

# CORS — allow requests from your website
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://trilloka.com",
        "https://www.trilloka.com",
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


# ── Request Models ──────────────────────────────────────────────────────────

class ScanRequest(BaseModel):
    url: HttpUrl
    tier: str = "free"  # free | paid | roadmap | admin
    competitor_urls: Optional[List[HttpUrl]] = None
    location: Optional[str] = ""
    traffic: Optional[int] = None
    conversion_rate: Optional[float] = None
    aov: Optional[float] = None


class HealthResponse(BaseModel):
    status: str
    version: str
    redis: bool


# ── Endpoints ───────────────────────────────────────────────────────────────

@app.get("/api/health", response_model=HealthResponse)
async def health():
    redis_ok = False
    if REDIS_AVAILABLE:
        try:
            r = redis.from_url(REDIS_URL)
            redis_ok = r.ping()
        except Exception:
            pass
    return {"status": "ok", "version": "4.1.0", "redis": redis_ok}


@app.post("/api/v1/scan")
async def scan(request: ScanRequest, background_tasks: BackgroundTasks):
    url = str(request.url).rstrip("/")
    tier = request.tier.lower()
    competitor_urls = [str(u).rstrip("/") for u in (request.competitor_urls or [])]
    location = request.location or ""

    # Validate tier
    if tier not in ["free", "paid", "roadmap", "admin"]:
        raise HTTPException(status_code=400, detail="Invalid tier. Use: free, paid, roadmap, admin")

    # 1. Scrape
    scraper = WebsiteScraper(
        url=url,
        tier=tier,
        competitor_urls=competitor_urls,
        location=location,
    )
    data = await scraper._scrape_async()

    if "error" in data:
        raise HTTPException(status_code=500, detail=f"Scrape failed: {data['error']}")

    # 2. Score
    revenue_scorer = RevenueScorer(data)
    revenue_scorer.calculate_scores()

    # 3. Content evidence
    content_evidence = ContentEvidenceSignals(BeautifulSoup(data['raw_html'], 'html.parser'), data['url'])
    content_evidence.analyze()

    # 4. Top failures
    top_failures = revenue_scorer.get_top_failures(10)

    # 5. Calculator inputs (if provided)
    calc_inputs = {}
    if request.traffic:
        calc_inputs["traffic"] = request.traffic
    if request.conversion_rate:
        calc_inputs["conversion_rate"] = request.conversion_rate
    if request.aov:
        calc_inputs["aov"] = request.aov

    # 6. Reporter
    reporter = ReportGenerator(
        url,
        revenue_scorer,
        content_evidence,
        data,
        top_failures,
        calculator_inputs=calc_inputs if calc_inputs else None,
    )

    # 7. Generate public report (what the customer sees)
    if tier == "free":
        public_report = reporter.generate_free()
    elif tier == "paid":
        public_report = reporter.generate_paid()
    elif tier == "roadmap":
        public_report = reporter.generate_roadmap()
    else:  # admin
        public_report = reporter.generate_admin()

    # 8. ALWAYS generate admin report + forwardable markdown (in background)
    background_tasks.add_task(
        _process_admin_report,
        url=url,
        domain=data.get("domain", ""),
        reporter=reporter,
        data=data,
    )

    return JSONResponse(public_report)


# ── Admin Report Background Task ────────────────────────────────────────────

async def _process_admin_report(url: str, domain: str, reporter: ReportGenerator, data: dict):
    """Generates admin report, saves to Redis, emails pretty HTML to admin via Resend."""
    try:
        # Generate admin report
        admin_report = reporter.generate_admin()
        forwardable_md = reporter.generate_forwardable_report()

        # Save to Redis (if available)
        scan_id = f"{datetime.utcnow().isoformat().replace(':', '-')}-{domain}"
        if REDIS_AVAILABLE:
            try:
                r = redis.from_url(REDIS_URL)
                r.setex(f"rrs:admin:{scan_id}", 86400 * 7, json.dumps(admin_report))
                r.setex(f"rrs:forwardable:{scan_id}", 86400 * 7, forwardable_md)
            except Exception as e:
                print(f"[Redis save failed] {e}")

        # Generate pretty HTML using email_sender
        from email_sender import ReportEmailer
        emailer = ReportEmailer()
        html_body = emailer._render_admin_html(admin_report)
        full_html = emailer._build_html_wrapper(f"[ADMIN] Revenue Readiness — {url}", html_body)

        # Email to admin via Resend (reliable delivery from Railway)
        if ADMIN_REPORT_AUTO_SEND and RESEND_API_KEY and RESEND_AVAILABLE:
            try:
                resend.api_key = RESEND_API_KEY
                resend.Emails.send({
                    "from": EMAIL_FROM,
                    "to": ADMIN_EMAIL,
                    "subject": f"[ADMIN] Revenue Readiness — {url}",
                    "html": full_html,
                    "text": forwardable_md,
                })
                print(f"[Admin email sent] {ADMIN_EMAIL} for {url}")
            except Exception as e:
                print(f"[Admin email failed] {e}")

        # Fallback: try SMTP (may be blocked by Gmail from cloud IPs)
        try:
            emailer.send_admin_report(reporter, ADMIN_EMAIL)
            print(f"[Admin SMTP email sent] {ADMIN_EMAIL} for {url}")
        except Exception as e:
            print(f"[Admin SMTP email failed — expected from cloud IPs] {e}")

    except Exception as e:
        print(f"[Admin report processing failed] {e}")


# ── Admin Report Retrieval (for your dashboard) ─────────────────────────────

@app.get("/api/v1/admin/reports")
async def list_admin_reports(limit: int = 20):
    """List recent admin reports from Redis. Owner only."""
    if not REDIS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Redis not available")
    try:
        r = redis.from_url(REDIS_URL)
        keys = r.keys("rrs:admin:*")[:limit]
        reports = []
        for key in keys:
            key_str = key.decode() if isinstance(key, bytes) else key
            data = r.get(key_str)
            if data:
                reports.append({
                    "id": key_str.replace("rrs:admin:", ""),
                    "key": key_str,
                    "size": len(data),
                })
        return {"reports": reports}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/admin/report/{scan_id}")
async def get_admin_report(scan_id: str):
    """Get a specific admin report. Owner only."""
    if not REDIS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Redis not available")
    try:
        r = redis.from_url(REDIS_URL)
        data = r.get(f"rrs:admin:{scan_id}")
        if not data:
            raise HTTPException(status_code=404, detail="Report not found")
        return json.loads(data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/admin/report/{scan_id}/forwardable")
async def get_forwardable_report(scan_id: str):
    """Get the forwardable markdown report. Owner only."""
    if not REDIS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Redis not available")
    try:
        r = redis.from_url(REDIS_URL)
        data = r.get(f"rrs:forwardable:{scan_id}")
        if not data:
            raise HTTPException(status_code=404, detail="Report not found")
        return {"markdown": data.decode() if isinstance(data, bytes) else data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Main entry ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run("api:app", host="0.0.0.0", port=port, reload=False)