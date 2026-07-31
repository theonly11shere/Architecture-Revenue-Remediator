import logging
import inspect
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.services.scraper import WebScraper, fetch_and_extract
import scorer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("trilloka_audit")

app = FastAPI(
    title="Trilloka Audit Scanner API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AuditRequest(BaseModel):
    url: str
    business_type: str
    email: Optional[str] = None

class AuditResponse(BaseModel):
    status: str
    score: int
    summary: str
    details: Dict[str, Any]
    email_status: Optional[str] = None

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/api/audit", response_model=AuditResponse)
async def run_audit(payload: AuditRequest, background_tasks: BackgroundTasks):
    logger.info(f"Executing live audit scan for URL: {payload.url} [{payload.business_type}]")
    
    try:
        # 1. Execute scraper using the correct WebScraper / fetch_and_extract implementation
        raw_crawl = None
        if fetch_and_extract and inspect.iscoroutinefunction(fetch_and_extract):
            raw_crawl = await fetch_and_extract(payload.url)
        else:
            scraper_instance = WebScraper()
            if inspect.iscoroutinefunction(scraper_instance.scrape):
                raw_crawl = await scraper_instance.scrape(payload.url)
            else:
                raw_crawl = scraper_instance.scrape(payload.url)

        if not raw_crawl:
            raise HTTPException(status_code=500, detail="Scraper returned empty data from target URL.")

        # 2. Execute Scorer
        audit_result = None
        if hasattr(scorer, 'calculate_scores'):
            audit_result = scorer.calculate_scores(raw_crawl, payload.business_type)
        elif hasattr(scorer, 'evaluate'):
            audit_result = scorer.evaluate(raw_crawl, payload.business_type)
        else:
            raise HTTPException(
                status_code=500, 
                detail="Critical Error: scorer.py is missing scoring functions."
            )

        if not audit_result or "overall_score" not in audit_result:
            raise HTTPException(
                status_code=500, 
                detail="Critical Error: scorer.py did not return a valid 'overall_score'."
            )

        calculated_score = int(audit_result["overall_score"])

        return AuditResponse(
            status="success",
            score=calculated_score,
            summary=f"Live audit completed successfully for {payload.url}.",
            details={
                "target_url": raw_crawl.get("url", payload.url),
                "business_type": payload.business_type,
                "load_time_ms": raw_crawl.get("load_time_ms", 0),
                "ssl_enabled": raw_crawl.get("ssl_enabled", False),
                "has_title": bool(raw_crawl.get("meta", {}).get("title")),
                "revenue_leak_risk": audit_result.get("conversion_risk", "High"),
                "leaks": audit_result.get("leaks", [])
            }
        )

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Unexpected error during audit scan for {payload.url}: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Audit execution failed: {str(e)}"
        )