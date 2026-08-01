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
        # If scraper encountered a fatal error, return a clear failure report
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

        if load_time == 0 or load_time > 2000:
            excess = max(load_time - 2000, 1000)
            penalty = min(50, (excess / 100) * 1.2)
            score -= penalty

        meta = data.get("meta", {})
        if not meta.get("has_viewport", True):
            score -= 30.0

        return max(0.0, round(score, 1))

    def _score_seo(self, data: Dict[str, Any]) -> float:
        score = 100.0
        meta = data.get("meta", {})
        headings = data.get("headings", {})

        title = meta.get("title")
        if not title:
            score -= 35.0
        elif len(title) < 10 or len(title) > 70:
            score -= 15.0

        desc = meta.get("description")
        if not desc:
            score -= 30.0
        elif len(desc) < 50 or len(desc) > 160:
            score -= 10.0

        h1_count = headings.get("h1_count", 0)
        if h1_count == 0:
            score -= 25.0
        elif h1_count > 1:
            score -= 10.0

        return max(0.0, round(score, 1))

    def _score_conversion(self, data: Dict[str, Any]) -> float:
        score = 100.0
        cta = data.get("cta_elements", {})
        images = data.get("images", {})

        if not cta.get("has_cta_buttons", False) and cta.get("form_count", 0) == 0:
            score -= 50.0
        elif cta.get("cta_count", 0) == 0:
            score -= 25.0

        alt_pct = images.get("alt_coverage_pct", 100.0)
        if alt_pct < 80.0:
            score -= 20.0

        return max(0.0, round(score, 1))

    def _score_security(self, data: Dict[str, Any]) -> float:
        score = 100.0

        if not data.get("ssl_enabled", False):
            score -= 60.0

        sec_headers = data.get("security_headers", {})
        missing_headers_count = sum(1 for v in sec_headers.values() if not v)
        score -= (missing_headers_count * 10.0)

        return max(0.0, round(score, 1))

    def _score_social(self, data: Dict[str, Any]) -> float:
        social = data.get("social_signals", {})
        if not social.get("has_social_presence", False):
            return 30.0
        
        channel_count = social.get("total_social_channels", 0)
        if channel_count >= 3:
            return 100.0
        elif channel_count == 2:
            return 80.0
        return 60.0

    def _detect_revenue_leaks(self, data: Dict[str, Any], tech: float, seo: float, conv: float, sec: float, soc: float) -> List[Dict[str, Any]]:
        leaks = []

        if tech < 70:
            leaks.append({
                "category": "Performance",
                "severity": "High",
                "issue": f"Suboptimal load performance ({data.get('load_time_ms', 0)}ms)",
                "impact": "Slow loading speeds cause potential customers to leave before viewing content."
            })

        if sec < 70 or not data.get("ssl_enabled", False):
            leaks.append({
                "category": "Security",
                "severity": "Critical",
                "issue": "HTTPS / SSL Encryption missing or security headers weak",
                "impact": "Browsers display security warnings, scaring away visitors."
            })

        if seo < 70:
            leaks.append({
                "category": "SEO",
                "severity": "Medium",
                "issue": "Missing or improperly formatted Meta Tags / Heading Structure",
                "impact": "Lower organic search visibility, leading to missed organic leads."
            })

        if conv < 70:
            leaks.append({
                "category": "Conversion",
                "severity": "High",
                "issue": "No prominent Call-to-Action (CTA) or conversion forms detected",
                "impact": "Landing page visitors lack a clear next step to purchase or inquire."
            })

        if soc < 70:
            leaks.append({
                "category": "Social Proof",
                "severity": "Low",
                "issue": "Limited or unlinked social channels",
                "impact": "Lacks trust signals required by modern consumers."
            })

        return leaks

    def _generate_recommendations(self, leaks: List[Dict[str, Any]]) -> List[str]:
        recs = []
        for leak in leaks:
            cat = leak["category"]
            if cat == "Performance":
                recs.append("Compress images, minimize JavaScript execution, and upgrade server infrastructure.")
            elif cat == "Security":
                recs.append("Enforce HTTPS with a valid SSL certificate and configure security headers.")
            elif cat == "SEO":
                recs.append("Add structured Meta Titles, Descriptions, and ensure a single proper H1 tag per page.")
            elif cat == "Conversion":
                recs.append("Add explicit, high-contrast Call-to-Action buttons above the fold.")
            elif cat == "Social Proof":
                recs.append("Link active social media channels in the footer or navigation.")
        
        if not recs:
            recs.append("Your website is highly optimized! Focus on conversion rate optimization and ongoing A/B testing.")
        
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
            "pillar_scores": {
                "technical_performance": 0,
                "seo_meta": 0,
                "conversion_optimization": 0,
                "trust_and_security": 0,
                "social_presence": 0
            },
            "revenue_leaks_detected": [
                {
                    "category": "Accessibility",
                    "severity": "Critical",
                    "issue": f"Target website unreachable: {error_msg}",
                    "impact": "Visitors and search engine crawlers cannot access your page."
                }
            ],
            "actionable_recommendations": [
                f"Could not complete audit scan: {error_msg}. Verify the website domain is live and accessible."
            ],
            "audit_metadata": {"error": error_msg}
        }


# Compatibility wrapper function for main.py imports
def score_audit(scraped_data: Dict[str, Any], business_type: str = "General") -> Dict[str, Any]:
    scorer = RevenueLeakScorer()
    return scorer.evaluate(scraped_data, business_type)