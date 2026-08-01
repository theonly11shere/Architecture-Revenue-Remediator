import logging
from typing import Any, Dict, List

logger = logging.getLogger("trilloka_scorer")


def score_audit(scraped_data: Dict[str, Any], business_type: str = "general") -> Dict[str, Any]:
    """
    Evaluates scraped website metrics and calculates pillar scores,
    revenue leaks, and actionable recommendations.
    """
    if not scraped_data.get("is_success", False):
        return _build_fallback_score(scraped_data, business_type)

    leaks: List[Dict[str, str]] = []
    recommendations: List[str] = []

    # Extract raw data blocks
    load_time = scraped_data.get("load_time_ms", 0)
    ssl_enabled = scraped_data.get("ssl_enabled", False)
    security_headers = scraped_data.get("security_headers", {})
    meta = scraped_data.get("meta", {})
    headings = scraped_data.get("headings", {})
    images = scraped_data.get("images", {})
    social = scraped_data.get("social_signals", {})
    cta = scraped_data.get("cta_elements", {})
    analytics = scraped_data.get("analytics_tags", {})
    schema = scraped_data.get("schema_markup", {})

    # ------------------------------------------------------------------
    # 1. Technical Performance Score (Weight: 20%)
    # ------------------------------------------------------------------
    tech_score = 100
    if load_time > 3000:
        tech_score -= 40
        leaks.append({
            "category": "Performance",
            "severity": "High",
            "issue": f"Slow site load time ({round(load_time/1000, 2)}s)",
            "impact": "High bounce rates—up to 40% of visitors leave if load takes over 3s."
        })
        recommendations.append("Optimize image assets and leverage server caching to reduce response time under 2 seconds.")
    elif load_time > 1500:
        tech_score -= 15

    # ------------------------------------------------------------------
    # 2. SEO & Meta Structure Score (Weight: 20%)
    # ------------------------------------------------------------------
    seo_score = 100
    
    # Meta Description Check
    if not meta.get("description"):
        seo_score -= 25
        leaks.append({
            "category": "SEO",
            "severity": "High",
            "issue": "Missing Meta Description",
            "impact": "Lower search engine click-through rates (CTR) from Google results."
        })
        recommendations.append("Add a compelling meta description containing primary target keywords.")

    # Image Alt Tag Check
    alt_coverage = images.get("alt_coverage_pct", 100)
    missing_alt = images.get("missing_alt_count", 0)
    if alt_coverage < 50 and missing_alt > 0:
        seo_score -= 20
        leaks.append({
            "category": "SEO",
            "severity": "Medium",
            "issue": f"Missing Alt text on {missing_alt} images",
            "impact": "Inadequate alt tags harm image search rankings and web accessibility compliance."
        })
        recommendations.append("Add descriptive alt attributes to all product and site images.")

    # Heading Hierarchy Check
    h1_count = headings.get("h1_count", 0)
    if h1_count == 0:
        seo_score -= 20
        leaks.append({
            "category": "SEO",
            "severity": "Medium",
            "issue": "Missing H1 Header",
            "impact": "Search engines struggle to identify the main topic of the page."
        })
    elif h1_count > 1:
        seo_score -= 10
        leaks.append({
            "category": "SEO",
            "severity": "Low",
            "issue": f"Multiple H1 Tags Detected ({h1_count} found)",
            "impact": "Dilutes search keyword focus across primary headers."
        })
        recommendations.append("Consolidate primary page titles into a single <h1> tag.")

    # ------------------------------------------------------------------
    # 3. Conversion & Analytics Optimization Score (Weight: 25%)
    # ------------------------------------------------------------------
    cro_score = 100

    # CTA Checks
    if not cta.get("has_cta_buttons"):
        cro_score -= 35
        leaks.append({
            "category": "Conversion",
            "severity": "Critical",
            "issue": "No Clear Call-To-Action (CTA) Found",
            "impact": "Visitors leave without purchasing or taking direct action."
        })
        recommendations.append("Add prominent, high-contrast CTA buttons above the fold.")

    # Analytics Tracking Checks (Crucial for E-commerce / Lead Gen)
    has_analytics = any(analytics.values())
    if not has_analytics:
        cro_score -= 30
        leaks.append({
            "category": "Analytics & Data",
            "severity": "High",
            "issue": "No Analytics or Conversion Tracking Detected",
            "impact": "Unable to track revenue attribution, customer journeys, or ad ROI."
        })
        recommendations.append("Install Google Tag Manager or GA4 to begin measuring traffic and conversions.")

    # ------------------------------------------------------------------
    # 4. Trust & Security Score (Weight: 20%)
    # ------------------------------------------------------------------
    trust_score = 100
    if not ssl_enabled:
        trust_score -= 50
        leaks.append({
            "category": "Security",
            "severity": "Critical",
            "issue": "Unsecured Connection (No HTTPS)",
            "impact": "Browsers label site 'Not Secure', scaring off buyers."
        })
        recommendations.append("Install an SSL certificate immediately.")

    sec_headers = sum(1 for v in security_headers.values() if v)
    if sec_headers < 2:
        trust_score -= 20

    # ------------------------------------------------------------------
    # 5. Social & Brand Signals Score (Weight: 15%)
    # ------------------------------------------------------------------
    social_score = 100
    channels_count = social.get("total_social_channels", 0)
    
    if channels_count == 0:
        social_score = 0
        leaks.append({
            "category": "Social Proof",
            "severity": "Medium",
            "issue": "No Linked Social Media Channels",
            "impact": "Modern shoppers expect active social proof to verify business legitimacy."
        })
        recommendations.append("Add visible links to official social profiles in the footer.")
    elif channels_count < 2:
        social_score = 50

    # Clamp scores between 0 and 100
    tech_score = max(0, min(100, tech_score))
    seo_score = max(0, min(100, seo_score))
    cro_score = max(0, min(100, cro_score))
    trust_score = max(0, min(100, trust_score))
    social_score = max(0, min(100, social_score))

    # Overall Weighted Score Calculation
    overall_score = round(
        (tech_score * 0.20) +
        (seo_score * 0.20) +
        (cro_score * 0.25) +
        (trust_score * 0.20) +
        (social_score * 0.15), 
        1
    )

    # Determine Rating Label
    if overall_score >= 85:
        rating_label = "Low Risk"
    elif overall_score >= 70:
        rating_label = "Moderate Risk"
    elif overall_score >= 50:
        rating_label = "High Risk"
    else:
        rating_label = "Critical Risk"

    # Identify Biggest Pain Point
    biggest_pain_point = {}
    critical_or_high_leaks = [l for l in leaks if l["severity"] in ["Critical", "High"]]
    if critical_or_high_leaks:
        biggest_pain_point = critical_or_high_leaks[0]
    elif leaks:
        biggest_pain_point = leaks[0]

    return {
        "overall_score": overall_score,
        "rating_label": rating_label,
        "pillar_scores": {
            "technical_performance": tech_score,
            "seo_meta": seo_score,
            "conversion_optimization": cro_score,
            "trust_and_security": trust_score,
            "social_presence": social_score
        },
        "revenue_leaks_detected": leaks,
        "biggest_pain_point": biggest_pain_point,
        "actionable_recommendations": list(set(recommendations)),
        "audit_metadata": {
            "business_type": business_type,
            "target_url": scraped_data.get("url"),
            "load_time_ms": load_time
        }
    }


def _build_fallback_score(scraped_data: Dict[str, Any], business_type: str) -> Dict[str, Any]:
    return {
        "overall_score": 0.0,
        "rating_label": "Critical Risk",
        "pillar_scores": {
            "technical_performance": 0,
            "seo_meta": 0,
            "conversion_optimization": 0,
            "trust_and_security": 0,
            "social_presence": 0
        },
        "revenue_leaks_detected": [{
            "category": "Crawl Error",
            "severity": "Critical",
            "issue": "Failed to connect or scrape target URL",
            "impact": "Site unreachable or blocking scanner."
        }],
        "biggest_pain_point": {
            "category": "Crawl Error",
            "severity": "Critical",
            "issue": "Failed to connect or scrape target URL",
            "impact": "Site unreachable or blocking scanner."
        },
        "actionable_recommendations": ["Ensure website URL is correct and server allows external traffic."],
        "audit_metadata": {
            "business_type": business_type,
            "error": scraped_data.get("error", "Unknown crawl failure")
        }
    }