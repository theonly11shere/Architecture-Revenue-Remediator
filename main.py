# ==========================================
# main.py (FastAPI Backend with Real WebScraper)
# ==========================================

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os
from pydantic import BaseModel

# Import your real WebScraper class from scraper.py
from scraper import WebScraper

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")


# Root directory for HTML files
FRONTEND_DIR = os.path.dirname(os.path.abspath(__file__))

class ScanRequest(BaseModel):
    url: str
    tier: str = "free"

@app.post("/api/v1/scan")
async def api_scan(payload: ScanRequest):
    # Initialize the real scraper
    scraper = WebScraper()
    crawl_result = await scraper.scrape(payload.url)
    
    print("CRAWL RESULT:", crawl_result)
    
    if not crawl_result.get("is_success"):
        return {
            "domain": payload.url,
            "status": "Crawl Failed: " + crawl_result.get("error", "Unknown"),
            "scores": {"template": 0, "visual-twin": 0, "sameness": 0, "presence": 0},
            "leaks": "$0/mo",
            "score": "0%",
        }

    # Extract real metrics to drive your 3D scoring system
    images_info = crawl_result.get("images", {})
    social_info = crawl_result.get("social_signals", {})
    cta_info = crawl_result.get("cta_elements", {})
    
    # Calculate dynamic scores based on actual scanned site data
    alt_coverage = images_info.get("alt_coverage_pct", 100)
    template_score = int(100 - alt_coverage)
    presence_score = 80 if social_info.get("has_social_presence") else 20
    sameness_score = 45 if cta_info.get("has_cta_buttons") else 85
    visual_twin_score = 30  # Baseline metric for twin detection

    return {
        "domain": crawl_result.get("url"),
        "status": "Custom Architecture" if crawl_result.get("ssl_enabled") else "Standard Template",
        "scores": {
            "template": template_score,
            "visual-twin": visual_twin_score,
            "sameness": sameness_score,
            "presence": presence_score
        },
        "leaks": "$14,200/mo",
        "score": f"{100 - template_score}%"
    }

@app.get("/", response_class=HTMLResponse)
async def read_index(request: Request):
    path = os.path.join(FRONTEND_DIR, "index.html")
    return HTMLResponse(content=open(path, "r", encoding="utf-8").read(), status_code=200)

@app.get("/results", response_class=HTMLResponse)
async def read_results(request: Request, domain: str = None):
    path = os.path.join(FRONTEND_DIR, "results.html")
    return HTMLResponse(content=open(path, "r", encoding="utf-8").read(), status_code=200)

@app.get("/vlog", response_class=HTMLResponse)
async def read_vlog(request: Request):
    path = os.path.join(FRONTEND_DIR, "vlog.html")
    return HTMLResponse(content=open(path, "r", encoding="utf-8").read(), status_code=200)

@app.get("/contact", response_class=HTMLResponse)
async def read_contact(request: Request):
    path = os.path.join(FRONTEND_DIR, "contact.html")
    return HTMLResponse(content=open(path, "r", encoding="utf-8").read(), status_code=200)