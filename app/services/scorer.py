import uuid
import time
import requests
from bs4 import BeautifulSoup
from typing import Dict, Any, List, Optional

INDUSTRY_PROBLEM_LIBRARY = {
    "ecommerce": {
        "name": "E-Commerce",
        "leaks": [
            {
                "title": "Friction-Heavy Product Page Checkout Path",
                "description": "Product pages lack immediate add-to-cart urgency and clear shipping/return guarantees above the fold, causing cart abandonment."
            },
            {
                "title": "Suboptimal Visual Proof & UGC Deficit",
                "description": "Absence of prominent customer photo reviews or unboxing proof near the primary purchase trigger."
            },
            {
                "title": "Generic Category Value Proposition",
                "description": "Storefront copy mirrors commodity retail competitors without highlighting a distinct product differentiation angle."
            }
        ]
    },
    "saas": {
        "name": "SaaS / Software",
        "leaks": [
            {
                "title": "Unclear Software Value Proposition",
                "description": "The primary hero headline focuses on product features rather than the immediate business transformation or time-saved metric."
            },
            {
                "title": "Friction in Free Trial or Demo Conversion",
                "description": "Call-to-action triggers are buried or require excessive cognitive load, stalling user sign-up velocity."
            },
            {
                "title": "Missing Enterprise Trust & Security Badges",
                "description": "Lack of compliance indicators (SOC2, GDPR, data encryption proofs) near conversion gates for high-value buyers."
            }
        ]
    },
    "agency": {
        "name": "Agency",
        "leaks": [
            {
                "title": "Commoditized Service Positioning",
                "description": "Your positioning sounds like every other marketing or development shop. Clients bounce when they don't see a proprietary framework or specific ROI mechanism."
            },
            {
                "title": "Case Study & Metrics Proof Deficit",
                "description": "Portfolio items lack verified, quantifiable client growth outcomes right on the landing page."
            },
            {
                "title": "Vague Consultation Booking Funnel",
                "description": "Call-to-actions ask users to 'Contact Us' instead of a low-friction, high-intent action like 'Book a 15-Minute Revenue Audit'."
            }
        ]
    },
    "local_services": {
        "name": "Local Services",
        "leaks": [
            {
                "title": "Invisible Local Authority & Review Signals",
                "description": "Google Review ratings, local licensing proofs, and service area coverage guarantees are missing above the fold."
            },
            {
                "title": "Hidden Emergency Contact Triggers",
                "description": "Click-to-call phone numbers or instant quote widgets are not instantly accessible for mobile visitors."
            },
            {
                "title": "Generic Trade Positioning",
                "description": "Website copy lacks specific guarantees on response times, workmanship warranties, or upfront pricing transparency."
            }
        ]
    },
    "b2b": {
        "name": "B2B",
        "leaks": [
            {
                "title": "Long-Cycle Enterprise Friction",
                "description": "The site layout lacks targeted buyer-persona paths, forcing different decision-makers through a single generic funnel."
            },
            {
                "title": "Absence of Institutional Risk Reversal",
                "description": "No clear implementation roadmap or risk mitigation framework is presented to comfort enterprise procurement committees."
            },
            {
                "title": "Weak Institutional Authority Proof",
                "description": "Client logos, industry analyst mentions, or verified corporate case studies are absent from the homepage."
            }
        ]
    },
    "healthcare": {
        "name": "Healthcare",
        "leaks": [
            {
                "title": "Patient Trust & Compliance Deficit",
                "description": "Medical credentials, practitioner board certifications, and privacy compliance statements are difficult for patients to verify immediately."
            },
            {
                "title": "High-Friction Appointment Scheduling",
                "description": "Booking a consultation requires navigating complex menus rather than a direct, streamlined patient intake trigger."
            },
            {
                "title": "Complex Clinical Jargon",
                "description": "Copy relies on medical terminology rather than patient-centric outcome language, increasing visitor hesitation."
            }
        ]
    }
}

BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

def run_architectural_audit(url: str, business_type: str, scraped_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    scan_id = f"scan_{uuid.uuid4().hex[:10]}"
    start_time = time.time()
    
    target = url if url.startswith(("http://", "https://")) else f"https://{url}"
    
    clean_type = (business_type or "b2b").lower().strip()
    if clean_type not in INDUSTRY_PROBLEM_LIBRARY:
        clean_type = "b2b"
        
    profile = INDUSTRY_PROBLEM_LIBRARY[clean_type]
    detected_leaks = list(profile["leaks"])

    status_code = 200
    response_time_ms = 0
    title_tag = ""
    meta_desc = ""
    has_ssl = target.startswith("https://")
    
    if scraped_data and scraped_data.get("is_success"):
        # Utilize pre-scraped data if provided by WebScraper
        response_time_ms = int(scraped_data.get("load_time_ms", 120))
        status_code = scraped_data.get("status_code", 200)
        has_ssl = scraped_data.get("ssl_enabled", True)
        title_tag = scraped_data.get("meta", {}).get("title") or ""
        meta_desc = scraped_data.get("meta", {}).get("description") or ""
    else:
        # Perform fallback direct HTTP fetch
        try:
            response = requests.get(
                target, 
                timeout=8, 
                headers=BROWSER_HEADERS
            )
            status_code = response.status_code
            response_time_ms = int((time.time() - start_time) * 1000)
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Safe title extraction
            if soup.title:
                title_tag = soup.title.get_text(strip=True)
            
            # Safe meta description extraction
            meta_tag = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", attrs={"property": "og:description"})
            if meta_tag and meta_tag.get("content"):
                meta_desc = str(meta_tag["content"]).strip()

        except Exception:
            response_time_ms = 450
            status_code = 500

    # Dynamic Scoring Penalty System
    score_deductions = 0

    if not has_ssl:
        score_deductions += 15
        detected_leaks.append({
            "title": "Insecure Connection (Missing SSL)",
            "description": "Your site is served over HTTP, triggering browser security warnings and destroying visitor trust."
        })

    if not title_tag:
        score_deductions += 10
        detected_leaks.append({
            "title": "Missing Primary Meta Title",
            "description": "The site lacks a defined HTML title tag, severely harming SEO positioning and search snippet CTR."
        })

    if not meta_desc:
        score_deductions += 10
        detected_leaks.append({
            "title": "Missing Search Meta Description",
            "description": "Search engines are forcing automated text snippets because no primary meta description is configured."
        })

    if response_time_ms > 2500:
        score_deductions += 15
        detected_leaks.append({
            "title": "High Server Response Latency",
            "description": f"Initial page load latency reached {response_time_ms}ms, exceeding the 1.5s mobile drop-off threshold."
        })

    base_score = 85 - (len(profile["leaks"]) * 5)
    readiness_score = max(30, min(98, base_score - score_deductions))

    # Determine risk category for main.py integration
    if readiness_score >= 80:
        conversion_risk = "Low"
    elif readiness_score >= 60:
        conversion_risk = "Moderate"
    else:
        conversion_risk = "High"

    seo_vitals = {
        "response_latency_ms": response_time_ms,
        "ssl_integrity": "Valid HTTPS" if has_ssl else "Insecure HTTP",
        "http_status": status_code,
        "title_tag_present": bool(title_tag),
        "title_tag_length": len(title_tag),
        "meta_description_present": bool(meta_desc),
        "technical_health_score": max(40, 100 - score_deductions)
    }

    return {
        "scan_id": scan_id,
        "target_url": target,
        "business_type": clean_type,
        "industry_name": profile["name"],
        "generic_score": 75,
        "sameness_score": 8,
        "presence_score": 20,
        "visual_twin_score": 10,
        "readiness_score": readiness_score,
        "conversion_risk": conversion_risk,  # Key required by main.py
        "evidence_score": 45,
        "confidence_score": 80,
        "ai_risk_score": 70,
        "leaks": detected_leaks,
        "add_on_metrics": seo_vitals
    }