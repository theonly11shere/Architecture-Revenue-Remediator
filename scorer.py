import math
from typing import Any, Dict, List, Optional


class RevenueLeakScorer:
    """
    Analyzes scraped website data and calculates revenue leak scores,
    prioritized risk factors, and actionable recommendations.
    """

    def __init__(self):
        # Weight distributions across key audit pillars (must total 100)
        self.PILLAR_WEIGHTS = {
            "technical_performance": 25,
            "seo_meta": 20,
            "conversion_optimization": 25,
            "trust_and_security": 15,
            "social_presence": 15,
        }

    def evaluate(self, scraped_data: Dict[str, Any], business_type: str = "General") -> Dict[str, Any]:
        """
        Evaluates scraped data and returns a comprehensive score and audit breakdown.
        """
        # If scraper encountered a fatal error, return a zeroed out failure report
        if not scraped_data.get("is_success", True) or "error" in scraped_data:
            return self._build_error_score_response(scraped_data.get("error", "Crawl failed"))

        # Score individual pillars (0 to 100 scale)
        tech_score = self._score_technical(scraped_data)
        seo_score = self._score_seo(scraped_data)
        conversion_score = self._score_conversion(scraped_data)
        security_score = self._score_security(scraped_data)
        social_score = self._score_social(scraped_data)

        # Calculate weighted overall score
        overall_score = round(
            (tech_score * self.PILLAR_WEIGHTS["technical_performance"] / 100) +
            (seo_score * self.PILLAR_WEIGHTS["seo_meta"] / 100) +
            (conversion_score * self.PILLAR_WEIGHTS["conversion_optimization"] / 100) +
            (security_score * self.PILLAR_WEIGHTS["trust_and_security"] / 100) +
            (social_score * self.PILLAR_WEIGHTS["social_presence"] / 100),
            1
        )

        # Identify leaks and generate actionable recommendations
        leaks = self._detect_revenue_leaks(scraped_data, tech_score, seo_score, conversion_score, security_score, social_score)
        recommendations = self._generate_recommendations(leaks)

        return {
            "overall_score": overall_score,
            "rating_label": self._get_rating_label(overall_score),
            "pillar_scores": {
                "technical_performance": tech_score,
                "seo_meta": seo_score,
                "conversion_optimization": conversion_score,
                "trust_and_security": security_score,
                "social_presence": social_score,
            },
            "revenue_leaks_detected": leaks,
            "actionable_recommendations": recommendations,
            "audit_metadata": {
                "business_type": business_type,
                "target_url": scraped_data.get("url"),
                "load_time_ms": scraped_data.get("load_time_ms", 0),
            }
        }

    def _score_technical(self, data: Dict[str, Any]) -> float:
        score = 100.0
        load_time = data.get("load_time_ms", 0)

        # Penalize slow load times (> 2000ms starts losing points, > 5000ms heavily penalized)
        if load_time > 2000:
            excess = load_time - 2000
            penalty = min(40, (excess / 100) * 1.2)
            score -= penalty

        # Penalize missing viewport tag (mobile responsiveness risk)
        meta = data.get("meta", {})
        if not meta.get("has_viewport", True):
            score -= 30.0

        return max(0.0, round(score, 1))

    def _score_seo(self, data: Dict[str, Any]) -> float:
        score = 100.0
        meta = data.get("meta", {})
        headings = data.get("headings", {})

        # Title checks
        title = meta.get("title")
        if not title:
            score -= 35.0
        elif len(title) < 10 or len(title) > 70:
            score -= 15.0

        # Description checks
        desc = meta.get("description")
        if not desc:
            score -= 30.0
        elif len(desc) < 50 or len(desc) > 160:
            score -= 10.0

        # H1 checks
        h1_count = headings.get("h1_count", 0)
        if h1_count == 0:
            score -= 25.0
        elif h1_count > 1:
            score -= 10.0  # Multiple H1 tags dilute SEO focus

        return max(0.0, round(score, 1))

    def _score_conversion(self, data: Dict[str, Any]) -> float:
        score = 100.0
        cta = data.get("cta_elements", {})
        images = data.get("images", {})

        # Check for CTAs & forms
        if not cta.get("has_cta_buttons", False) and cta.get("form_count", 0) == 0:
            score -= 50.0
        elif cta.get("cta_count", 0) == 0:
            score -= 25.0

        # Image accessibility & optimization
        alt_pct = images.get("alt_coverage_pct", 100.0)
        if alt_pct < 80.0:
            score -= 20.0

        return max(0.0, round(score, 1))

    def _score_security(self, data: Dict[str, Any]) -> float:
        score = 100.0

        if not data.get("ssl_enabled", True):
            score -= 60.0  # Massive risk factor

        sec_headers = data.get("security_headers", {})
        missing_headers_count = sum(1 for v in sec_headers.values() if not v)
        score -= (missing_headers_count * 10.0)

        return max(0.0, round(score, 1))

    def _score_social(self, data: Dict[str, Any]) -> float:
        social = data.get("social_signals", {})
        if not social.get("has_social_presence", False):
            return 30.0  # Base penalty for zero connected social footprint
        
        channel_count = social.get("total_social_channels", 0)
        if channel_count >= 3:
            return 100.0
        elif channel_count == 2:
            return 80.0
        return 60.0

    def _detect_revenue_leaks(self, data: Dict[str, Any], tech: float, seo: float, conv: float, sec: float, soc: float) -> List[Dict[str, Any]]:
        leaks = []

        if data.get("load_time_ms", 0) > 3000:
            leaks.append({
                "category": "Performance",
                "severity": "High",
                "issue": f"Slow page load time ({data.get('load_time_ms')}ms)",
                "impact": "High bounce rates and cart abandonment before content even renders."
            })

        if not data.get("ssl_enabled", True):
            leaks.append({
                "category": "Security",
                "severity": "Critical",
                "issue": "HTTPS / SSL Encryption missing or misconfigured",
                "impact": "Browsers flag site as 'Not Secure', instantly destroying visitor trust."
            })

        meta = data.get("meta", {})
        if not meta.get("title") or not meta.get("description"):
            leaks.append({
                "category": "SEO",
                "severity": "Medium",
                "issue": "Missing or incomplete Meta Title / Description",
                "impact": "Reduced organic click-through rates from search engine result pages."
            })

        cta = data.get("cta_elements", {})
        if not cta.get("has_cta_buttons", False) and cta.get("form_count", 0) == 0:
            leaks.append({
                "category": "Conversion",
                "severity": "High",
                "issue": "No clear Call-to-Action (CTA) or conversion funnel detected",
                "impact": "Visitors land on the page with nowhere obvious to convert, leading to silent drop-offs."
            })

        return leaks

    def _generate_recommendations(self, leaks: List[Dict[str, Any]]) -> List[str]:
        recs = []
        for leak in leaks:
            cat = leak["category"]
            if cat == "Performance":
                recs.append("Optimize and compress heavy images, leverage browser caching, and upgrade hosting infrastructure.")
            elif cat == "Security":
                recs.append("Install an active SSL/TLS certificate and enforce secure HTTPS routing across all pages.")
            elif cat == "SEO":
                recs.append("Craft a compelling descriptive Meta Title (under 60 chars) and Meta Description (under 160 chars) containing primary keywords.")
            elif cat == "Conversion":
                recs.append("Add prominent, high-contrast Call-to-Action buttons above the fold (e.g., 'Get Started', 'Book a Call') to guide user actions.")
        
        if not recs:
            recs.append("Your digital storefront is well-optimized! Focus on continuous A/B testing and expanding your inbound acquisition channels.")
        
        return recs

    def _get_rating_label(self, score: float) -> str:
        if score >= 85:
            return "Excellent"
        elif score >= 70:
            return "Good"
        elif score >= 50:
            return "Needs Improvement"
        return "Critical Revenue Leak"

    def _build_error_score_response(self, error_msg: str) -> Dict[str, Any]:
        return {
            "overall_score": 0.0,
            "rating_label": "Audit Failed",
            "pillar_scores": {"technical_performance": 0, "seo_meta": 0, "conversion_optimization": 0, "trust_and_security": 0, "social_presence": 0},
            "revenue_leaks_descriptors": [],
            "actionable_recommendations": [f"Could not complete audit scan: {error_msg}. Please check the URL and try again."],
            "audit_metadata": {"error": error_msg}
        }


# Compatibility wrapper function for main.py imports
def score_audit(scraped_data: Dict[str, Any], business_type: str = "General") -> Dict[str, Any]:
    scorer = RevenueLeakScorer()
    return scorer.evaluate(scraped_data, business_type)