#!/usr/bin/env python3
"""RRS API — FastAPI app with competitor support, admin reports, and email delivery."""
import os
import json
import asyncio
import time
from typing import Optional, List
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, Depends, Header
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from bs4 import BeautifulSoup
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl

# ── Security: API Key for admin endpoints ──────────────────────────────────
ADMIN_API_KEY = os.environ.get("ADMIN_API_KEY", "")
if not ADMIN_API_KEY:
    # Generate a random one if not set — log it so you can copy it
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
    # Filter to current window
    window = [t for t in window if now - t < RATE_LIMIT_WINDOW]
    if len(window) >= max_requests:
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again in a minute.")
    window.append(now)
    _rate_limit_store[client_ip] = window

# IP Geolocation for auto-detecting location
try:
    from ip_geolocation import get_location_from_ip, get_client_ip
    IP_GEO_AVAILABLE = True
except ImportError:
    IP_GEO_AVAILABLE = False

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

# ── In-memory fallback for admin reports (when Redis is unavailable) ───────
_in_memory_reports = {}      # key -> json data
_in_memory_forwardable = {}  # key -> markdown string
_MAX_MEMORY_REPORTS = 100

app = FastAPI(title="Revenue Readiness Scanner", version="4.1.1")

# CORS — allow requests from your website ONLY in production
_origins = [
    "https://trilloka.com",
    "https://www.trilloka.com",
]
# Add localhost only in dev mode
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
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
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


# ── Helper: store report (Redis if available, else in-memory) ───────────────

def _store_report(scan_id: str, admin_report: dict, forwardable_md: str):
    """Save report to Redis if available, otherwise in-memory dict."""
    if REDIS_AVAILABLE:
        try:
            r = redis.from_url(REDIS_URL)
            r.setex(f"rrs:admin:{scan_id}", 86400 * 7, json.dumps(admin_report))
            r.setex(f"rrs:forwardable:{scan_id}", 86400 * 7, forwardable_md)
            return "redis"
        except Exception as e:
            print(f"[Redis save failed, falling back to memory] {e}")

    # In-memory fallback
    if len(_in_memory_reports) >= _MAX_MEMORY_REPORTS:
        # Evict oldest
        oldest = next(iter(_in_memory_reports))
        _in_memory_reports.pop(oldest, None)
        _in_memory_forwardable.pop(oldest, None)

    _in_memory_reports[scan_id] = admin_report
    _in_memory_forwardable[scan_id] = forwardable_md
    return "memory"


def _get_report(scan_id: str):
    """Retrieve admin report from Redis or memory."""
    if REDIS_AVAILABLE:
        try:
            r = redis.from_url(REDIS_URL)
            data = r.get(f"rrs:admin:{scan_id}")
            if data:
                return json.loads(data), "redis"
        except Exception:
            pass

    if scan_id in _in_memory_reports:
        return _in_memory_reports[scan_id], "memory"

    return None, None


def _get_forwardable(scan_id: str):
    """Retrieve forwardable markdown from Redis or memory."""
    if REDIS_AVAILABLE:
        try:
            r = redis.from_url(REDIS_URL)
            data = r.get(f"rrs:forwardable:{scan_id}")
            if data:
                return data.decode() if isinstance(data, bytes) else data, "redis"
        except Exception:
            pass

    if scan_id in _in_memory_forwardable:
        return _in_memory_forwardable[scan_id], "memory"

    return None, None


def _list_reports(limit: int = 20):
    """List report IDs from Redis or memory."""
    reports = []

    if REDIS_AVAILABLE:
        try:
            r = redis.from_url(REDIS_URL)
            keys = r.keys("rrs:admin:*")
            keys = keys[:limit]
            for key in keys:
                key_str = key.decode() if isinstance(key, bytes) else key
                data = r.get(key_str)
                if data:
                    reports.append({
                        "id": key_str.replace("rrs:admin:", ""),
                        "key": key_str,
                        "size": len(data),
                        "source": "redis",
                    })
            return reports
        except Exception:
            pass

    # Memory fallback
    for scan_id, data in list(_in_memory_reports.items())[:limit]:
        reports.append({
            "id": scan_id,
            "key": f"rrs:admin:{scan_id}",
            "size": len(json.dumps(data)),
            "source": "memory",
        })
    return reports


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
    return {"status": "ok", "version": "4.1.1", "redis": redis_ok}


@app.get("/api/v1/payment-options")
async def payment_options():
    """Return available pricing tiers."""
    return {
        "tiers": [
            {"id": "free", "name": "Free Scan", "price": 0, "features": ["6 revenue scores", "Top 5 issues", "Basic scan info"]},
            {"id": "paid", "name": "Full Report", "price": PRICING.get("paid", 29), "features": ["Everything in Free", "Fix steps", "Competitor analysis", "Revenue leak estimate"]},
            {"id": "roadmap", "name": "Roadmap", "price": PRICING.get("roadmap", 79), "features": ["Everything in Paid", "4-week action plan", "Week-by-week priorities"]},
        ]
    }


@app.post("/api/v1/scan")
async def scan(request: ScanRequest, background_tasks: BackgroundTasks, http_request: Request):
    url = str(request.url).rstrip("/")
    tier = request.tier.lower()
    competitor_urls = [str(u).rstrip("/") for u in (request.competitor_urls or [])]
    location = request.location or ""

    # ── Rate limiting ─────────────────────────────────────────────────────
    # FIX: cast to int because config values may be strings
    raw_limit = RATE_LIMIT_PAID if tier in ("paid", "roadmap", "admin") else RATE_LIMIT_FREE
    try:
        limit = int(raw_limit)
    except (TypeError, ValueError):
        limit = 10
    await rate_limit(http_request, max_requests=limit)

    # ── Auto-detect location from IP if not provided ──────────────────────
    if not location and IP_GEO_AVAILABLE:
        client_ip = get_client_ip(dict(http_request.headers))
        # Do not geolocate localhost/private IPs
        if client_ip and not client_ip.startswith(("127.", "10.", "192.168.", "172.")):
            detected = get_location_from_ip(client_ip)
            if detected:
                location = detected
                print(f"[Auto-Location] IP {client_ip} -> {location}")
        elif not client_ip:
            # Try without IP (ip-api will use the connection IP)
            detected = get_location_from_ip("")
            if detected:
                location = detected
                print(f"[Auto-Location] Connection IP -> {location}")

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
    """Generates admin report, saves to Redis/memory, emails pretty HTML to admin via Resend."""
    try:
        # Generate admin report
        admin_report = reporter.generate_admin()
        forwardable_md = reporter.generate_forwardable_report()

        # Save (Redis if available, else memory)
        scan_id = f"{datetime.utcnow().isoformat().replace(':', '-')}-{domain}"
        source = _store_report(scan_id, admin_report, forwardable_md)
        print(f"[Admin report saved] {scan_id} -> {source}")

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


# ── Admin Report Retrieval (PROTECTED — requires API key) ──────────────────

@app.get("/api/v1/admin/reports", dependencies=[Depends(verify_admin)])
async def list_admin_reports(limit: int = 20):
    """List recent admin reports from Redis or memory. Owner only."""
    try:
        reports = _list_reports(limit=limit)
        return {"reports": reports, "source": "redis" if REDIS_AVAILABLE else "memory"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/admin/report/{scan_id}", dependencies=[Depends(verify_admin)])
async def get_admin_report(scan_id: str):
    """Get a specific admin report. Owner only."""
    data, source = _get_report(scan_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return data


@app.get("/api/v1/admin/report/{scan_id}/forwardable", dependencies=[Depends(verify_admin)])
async def get_forwardable_report(scan_id: str):
    """Get the forwardable markdown report. Owner only."""
    data, source = _get_forwardable(scan_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return {"markdown": data, "source": source}


# ── Main entry ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", "8000"))
    host = os.environ.get("HOST", "127.0.0.1")
    uvicorn.run("api:app", host=host, port=port, reload=False)