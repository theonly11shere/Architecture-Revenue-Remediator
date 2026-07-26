#!/usr/bin/env python3
"""Report Generator — builds free, paid, admin, and forwardable customer reports.

PRIVACY RULES:
- Free report: 6 scores, basic scan info, top 5 failures ONLY
- Paid report: Everything in free + fix steps + competitor analysis + roadmap
- Admin report: EVERYTHING (full raw data, all checkpoints, competitor gaps, roadmap)
- Forwardable report: Polished markdown derived from admin data
"""
from typing import Any, Dict, List, Optional
from datetime import datetime

from config import (
    TOTAL_CHECKS, SEVERITY, FUTURE_PREDICTIONS,
    DEFAULT_TRAFFIC, DEFAULT_CONVERSION_RATE, DEFAULT_AOV, DEFAULT_PROFIT_MARGIN,
    CALCULATOR_LABEL, FREE_REPORT_CTA, BUSINESS_TYPE_CHECKS, SCORE_NAMES,
    ADMIN_REPORT_BRANDING, FORWARDABLE_REPORT_FOOTER,
    ADMIN_REPORT_INCLUDE_ROADMAP, ADMIN_REPORT_INCLUDE_COMPETITOR,
)
from scorer import RevenueScorer
from content_evidence_signals import ContentEvidenceSignals


class ReportGenerator:
    def __init__(
        self,
        url: str,
        revenue_scorer: RevenueScorer,
        content_evidence: ContentEvidenceSignals,
        data: Dict[str, Any],
        top_failures: List[Dict[str, Any]],
        calculator_inputs: Optional[Dict[str, Any]] = None,
    ):
        self.url = url
        self.revenue_scorer = revenue_scorer
        self.content_evidence = content_evidence
        self.data = data
        self.top_failures = top_failures
        self.calculator_inputs = calculator_inputs

    def _scan_quality(self) -> str:
        pages_sampled = self.data.get("pages_sampled", 0)
        has_errors = "error" in self.data
        html_length = self.data.get("html_length", 0)
        raw_html = self.data.get("raw_html", "")
        if has_errors or pages_sampled < 1 or html_length < 3000 or len(raw_html) < 3000:
            return "insufficient"
        categories = ["trust", "conversion", "seo", "content", "technical"]
        total_signals = 0
        for cat in categories:
            cat_data = self.data.get(cat, {})
            if isinstance(cat_data, dict):
                total_signals += len([v for v in cat_data.values() if v is not None and v != ""])
        if total_signals < 3:
            return "insufficient"
        return "good"

    def _severity_label(self, readiness: int, quality: str) -> Dict[str, str]:
        if quality == "insufficient":
            return {
                "key": "unknown",
                "label": "Scan Limited",
                "desc": "We couldn't fully analyze this site. It may use enterprise bot protection. Try a small business site for full results.",
            }
        if readiness >= 75:
            return {"key": "good", "label": "Revenue Ready", "desc": "Your site has strong foundations. Minor tweaks can unlock more revenue."}
        elif readiness >= 50:
            return {"key": "warning", "label": "Needs Work", "desc": "Several revenue-critical elements are missing or weak. Fixes will improve conversions."}
        elif readiness >= 25:
            return {"key": "poor", "label": "At Risk", "desc": "Major revenue blockers detected. Immediate fixes recommended."}
        else:
            return {"key": "critical", "label": "Critical", "desc": "Your site is losing revenue every day. Immediate action required."}

    def _future_prediction(self, readiness: int) -> Dict[str, int]:
        return {"3": min(readiness + 25, 100), "6": min(readiness + 45, 100), "12": min(readiness + 60, 100)}

    def _revenue_teaser(self) -> Dict[str, Any]:
        traffic = self.calculator_inputs.get("traffic", DEFAULT_TRAFFIC) if self.calculator_inputs else DEFAULT_TRAFFIC
        conversion_rate = self.calculator_inputs.get("conversion_rate", DEFAULT_CONVERSION_RATE) if self.calculator_inputs else DEFAULT_CONVERSION_RATE
        aov = self.calculator_inputs.get("aov", DEFAULT_AOV) if self.calculator_inputs else DEFAULT_AOV
        profit_margin = self.calculator_inputs.get("profit_margin", DEFAULT_PROFIT_MARGIN) if self.calculator_inputs else DEFAULT_PROFIT_MARGIN
        monthly_revenue = traffic * conversion_rate * aov
        monthly_profit = monthly_revenue * profit_margin
        annual_exposure = monthly_profit * 12
        readiness_gap = 1.0 - (self.revenue_scorer.get_readiness_score() / 100.0)
        return {
            "label": CALCULATOR_LABEL,
            "assumptions_banner": "Values shown are conservative industry estimates. Provide your actual numbers for a personalized projection.",
            "conservative_scenario": {
                "traffic": traffic,
                "conversion_rate": conversion_rate,
                "aov": aov,
                "profit_margin": profit_margin,
                "monthly_revenue": round(monthly_revenue, 2),
                "monthly_profit": round(monthly_profit, 2),
                "annual_exposure": round(annual_exposure, 2),
                "readiness_gap": round(readiness_gap, 2),
            },
        }

    # ════════════════════════════════════════════════════════════════════════
    #  FREE REPORT — What the public/customer sees (NO competitor data)
    # ════════════════════════════════════════════════════════════════════════

    def generate_free(self) -> Dict[str, Any]:
        scores = self.revenue_scorer.get_scores()
        six_scores = self.revenue_scorer.get_six_scores()
        readiness = scores.get("readiness_score", 0)
        quality = self._scan_quality()
        severity = self._severity_label(readiness, quality)
        failure_summary = []
        for f in self.top_failures[:20]:
            failure_summary.append({
                "category": f.get("category", "unknown"),
                "item": f.get("item", "unknown"),
                "severity": f.get("severity", "medium"),
                "one_liner": f.get("one_liner", ""),
                "completed": False,
            })
        evidence_signals = []
        if hasattr(self.content_evidence, 'signals'):
            for sig in self.content_evidence.signals:
                evidence_signals.append({
                    "name": sig.get("name", ""),
                    "status": sig.get("status", "unknown"),
                    "detail": sig.get("detail", ""),
                })

        six_score_breakdown = {}
        for name, value in six_scores.items():
            six_score_breakdown[name] = {
                "score": value,
                "label": self._six_score_label(name),
                "status": self._six_score_status(value),
            }

        # FREE report: NO competitor data, NO fix steps, NO roadmap
        report = {
            "type": "free",
            "url": self.url,
            "timestamp": self.data.get("timestamp", ""),
            "scan_quality": quality,
            "scores": scores,
            "six_scores": six_score_breakdown,
            "severity": severity,
            "content_evidence_signals": evidence_signals,
            "future_prediction": self._future_prediction(readiness),
            "visible_failures": self.top_failures[:5],
            "failure_summary": failure_summary,
            "hidden_failure_count": max(0, TOTAL_CHECKS - len(failure_summary)),
            "upgrade_cta": FREE_REPORT_CTA,
            "pages_sampled": self.data.get("pages_sampled", 0),
            "template_breakdown": self.data.get("template_breakdown", {}),
            "template_fingerprint": self.data.get("template_fingerprint", {}),
            "content_sameness": self.data.get("content_sameness", {}),
            "visual_twin": self.data.get("visual_twin", {}),
            "revenue_exposure_teaser": self._revenue_teaser(),
            # Revenue leak teaser only (not full breakdown)
            "revenue_leak_teaser": {
                "gap_percentage": self.revenue_scorer.get_six_scores().get("revenue_leak", 0),
                "note": "Upgrade for full revenue leak analysis with dollar estimates.",
            },
            "business_type": self.data.get("business_type", {}),
            "performance": self.data.get("performance", {}),
            "ai_copy_analysis": self.data.get("ai_copy_analysis", {}),
            "form_friction": self.data.get("form_friction", {}),
            "tech_stack_impact": self.data.get("tech_stack_impact", {}),
            # Competitor data INTENTIONALLY OMITTED from free report
        }
        if quality == "insufficient":
            report["insufficient_scan_message"] = (
                "We couldn't fully analyze this website. It may use enterprise-grade bot protection. "
                "Try scanning a small business website instead for full results."
            )
            report["can_show_preview"] = False
        else:
            report["can_show_preview"] = True
        return report

    def _six_score_label(self, name: str) -> str:
        labels = {
            "differentiation": "Differentiation",
            "trust_credibility": "Trust & Credibility",
            "conversion_friction": "Conversion Friction",
            "ai_copy_cliche": "AI Copy & Cliché",
            "tech_stack_impact": "Tech Stack Impact",
            "revenue_leak": "Revenue Leak",
        }
        return labels.get(name, name.replace("_", " ").title())

    def _six_score_status(self, value: int) -> str:
        if value >= 80: return "excellent"
        if value >= 60: return "good"
        if value >= 40: return "fair"
        if value >= 20: return "poor"
        return "critical"

    # ════════════════════════════════════════════════════════════════════════
    #  PAID REPORT — Customer gets this after paying (includes competitor)
    # ════════════════════════════════════════════════════════════════════════

    def generate_paid(self) -> Dict[str, Any]:
        free_report = self.generate_free()
        free_report["type"] = "paid"
        free_report["upgrade_cta"] = "Full report with actionable fix steps and competitor analysis."

        # Add fix steps
        fix_steps = []
        btype = self.data.get("business_type", {}).get("detected_type", "unknown")
        for f in self.top_failures:
            fix_steps.append({
                "category": f.get("category", ""),
                "item": f.get("item", ""),
                "severity": f.get("severity", ""),
                "fix_steps": self._generate_fix_steps(f, btype),
            })
        free_report["fix_steps"] = fix_steps

        # Add full revenue leak estimate (was teaser only in free)
        free_report["revenue_leak_estimate"] = self.revenue_scorer.get_revenue_leak_estimate()
        # Remove the teaser
        free_report.pop("revenue_leak_teaser", None)

        # Add competitor analysis (PAID ONLY)
        comp = self.data.get("competitor_analysis", {})
        if comp:
            free_report["competitor_analysis"] = {
                "gap_score": comp.get("gap_score", 0),
                "competitor_count": comp.get("competitor_count", 0),
                "aggregate_missing_features": comp.get("aggregate_missing_features", []),
                "competitors": [
                    {
                        "domain": c.get("domain", ""),
                        "shared_with_user": c.get("shared_with_user", []),
                        "user_missing": c.get("user_missing", []),
                        "advantage_score": c.get("advantage_score", 0),
                    }
                    for c in comp.get("competitors", [])
                ],
            }

        return free_report

    # ════════════════════════════════════════════════════════════════════════
    #  ROADMAP REPORT — Week-by-week plan (paid upgrade)
    # ════════════════════════════════════════════════════════════════════════

    def generate_roadmap(self) -> Dict[str, Any]:
        report = self.generate_paid()
        report["type"] = "roadmap"
        report["upgrade_cta"] = "Full report with week-by-week fix roadmap."
        sev_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        ordered = sorted(self.top_failures, key=lambda f: sev_order.get(str(f.get("severity", "low")).lower(), 3))
        buckets = [
            ("Week 1", "Stop the bleeding - critical revenue blockers first", ordered[0:6]),
            ("Week 2", "Build trust and credibility", ordered[6:12]),
            ("Week 3", "Content and search depth", ordered[12:18]),
            ("Week 4", "Polish, speed, and measurement", ordered[18:]),
        ]
        weeks = []
        btype = self.data.get("business_type", {}).get("detected_type", "unknown")
        for name, focus, items in buckets:
            if not items:
                continue
            weeks.append({
                "week": name,
                "focus": focus,
                "items": [{"item": f.get("item", ""), "severity": f.get("severity", ""),
                           "steps": self._generate_fix_steps(f, btype)} for f in items],
            })
        report["roadmap"] = weeks
        return report

    # ════════════════════════════════════════════════════════════════════════
    #  ADMIN REPORT — EVERYTHING, for owner eyes only
    # ════════════════════════════════════════════════════════════════════════

    def generate_admin(self) -> Dict[str, Any]:
        """Admin report — generated for EVERY scan regardless of tier.
        Contains raw data, competitor gaps, full roadmap, everything."""
        roadmap = self.generate_roadmap()
        return {
            "type": "admin",
            "url": self.url,
            "timestamp": self.data.get("timestamp", ""),
            "scores": self.revenue_scorer.get_scores(),
            "six_scores": self.revenue_scorer.get_six_scores(),
            "all_checkpoints": {
                "trust": self.data.get("trust", {}),
                "conversion": self.data.get("conversion", {}),
                "seo": self.data.get("seo", {}),
                "content": self.data.get("content", {}),
                "technical": self.data.get("technical", {}),
            },
            "top_failures": self.top_failures,
            "fix_steps": roadmap.get("fix_steps", []),
            "roadmap": roadmap.get("roadmap", []),
            "revenue_leak_estimate": self.revenue_scorer.get_revenue_leak_estimate(),
            # FULL competitor data (admin only)
            "competitor_analysis": self.data.get("competitor_analysis", {}),
            "competitor_urls": self.data.get("competitor_urls", []),
            "ai_copy_analysis": self.data.get("ai_copy_analysis", {}),
            "form_friction": self.data.get("form_friction", {}),
            "tech_stack_impact": self.data.get("tech_stack_impact", {}),
            "social_signals": self.data.get("social_signals_enhanced", {}),
            "business_type": self.data.get("business_type", {}),
            "lighthouse": self.data.get("lighthouse", {}),
            "mobile_test": self.data.get("mobile_test", {}),
            "security_headers": self.data.get("security_headers", {}),
            "ssl_valid": self.data.get("ssl_valid", {}),
            "screenshot_path": self.data.get("screenshot_path"),
            "visual_twin": self.data.get("visual_twin", {}),
            "template_fingerprint": self.data.get("template_fingerprint", {}),
            "content_sameness": self.data.get("content_sameness", {}),
            "raw_html_length": self.data.get("html_length", 0),
            "scan_quality": self._scan_quality(),
        }

    # ════════════════════════════════════════════════════════════════════════
    #  FORWARDABLE REPORT — Polished markdown for customer (from admin data)
    # ════════════════════════════════════════════════════════════════════════

    def generate_forwardable_report(self) -> str:
        """Generates a polished markdown report you can forward to customers."""
        admin = self.generate_admin()
        six = admin["six_scores"]
        leak = admin["revenue_leak_estimate"]
        comp = admin.get("competitor_analysis", {})
        btype = admin.get("business_type", {}).get("detected_type", "unknown").title()

        md = f"""# {ADMIN_REPORT_BRANDING}
## Confidential Revenue Analysis — {self.url}
**Generated:** {admin.get('timestamp', datetime.now().isoformat())}  
**Business Type:** {btype}

---

### Executive Summary

| Score | Value | Status |
|-------|-------|--------|
| Readiness | {admin['scores']['readiness_score']}/100 | {self._six_score_status(admin['scores']['readiness_score'])} |
| Revenue Leak | ${leak['monthly_leak_estimate']:,.2f}/mo | {self._six_score_status(six.get('revenue_leak', 0))} |

### 6 Unified Scores

| Dimension | Score | Assessment |
|-----------|-------|------------|
| Differentiation | {six.get('differentiation', 0)}/100 | {self._six_score_status(six.get('differentiation', 0))} |
| Trust & Credibility | {six.get('trust_credibility', 0)}/100 | {self._six_score_status(six.get('trust_credibility', 0))} |
| Conversion Friction | {six.get('conversion_friction', 0)}/100 | {self._six_score_status(six.get('conversion_friction', 0))} |
| AI Copy & Cliché | {six.get('ai_copy_cliche', 0)}/100 | {self._six_score_status(six.get('ai_copy_cliche', 0))} |
| Tech Stack Impact | {six.get('tech_stack_impact', 0)}/100 | {self._six_score_status(six.get('tech_stack_impact', 0))} |
| Revenue Leak Exposure | {six.get('revenue_leak', 0)}/100 | {self._six_score_status(six.get('revenue_leak', 0))} |

### Revenue Impact
- **Current estimated monthly revenue:** ${leak['current_monthly_revenue']:,.2f}
- **Potential monthly revenue:** ${leak['potential_monthly_revenue']:,.2f}
- **Estimated monthly leak:** ${leak['monthly_leak_estimate']:,.2f}
- **Estimated annual leak:** ${leak['annual_leak_estimate']:,.2f}

"""

        if ADMIN_REPORT_INCLUDE_COMPETITOR and comp and comp.get("competitors"):
            md += "\n### Competitor Gap Analysis\n\n"
            md += f"**Competitors analyzed:** {comp.get('competitor_count', 0)}  \n"
            md += f"**Your gap score:** {comp.get('gap_score', 0)}/100 (higher = less gap)\n\n"
            if comp.get("aggregate_missing_features"):
                md += "**Features your competitors have that you may be missing:**\n\n"
                for feat in comp["aggregate_missing_features"]:
                    md += f"- {feat}\n"
                md += "\n"
            for c in comp.get("competitors", []):
                md += f"#### vs. {c['domain']}\n"
                if c.get("user_missing"):
                    md += f"Missing: {', '.join(c['user_missing'])}\n"
                else:
                    md += "You match or exceed this competitor's features.\n"
                md += "\n"

        if ADMIN_REPORT_INCLUDE_ROADMAP and admin.get("roadmap"):
            md += "\n### 1-Month Fix Roadmap\n\n"
            for week in admin["roadmap"]:
                md += f"#### {week['week']}: {week['focus']}\n"
                for item in week.get("items", []):
                    md += f"- **[{item['severity'].upper()}]** {item['item']}\n"
                    for step in item.get("steps", []):
                        md += f"  - {step}\n"
                md += "\n"

        md += f"\n---\n{FORWARDABLE_REPORT_FOOTER}\n"

        return md

    # ════════════════════════════════════════════════════════════════════════
    #  FIX STEPS GENERATOR
    # ════════════════════════════════════════════════════════════════════════

    def _generate_fix_steps(self, failure: Dict[str, Any], business_type: str = "unknown") -> List[str]:
        item = failure.get("item", "").lower()
        if business_type == "ecommerce":
            ecommerce_steps = {
                "page load speed": [
                    "Compress product images to WebP (aim <200KB each)",
                    "Enable lazy loading for below-fold product images",
                    "Use a CDN for static assets (Cloudflare, BunnyCDN)",
                    "Minify CSS/JS and defer non-critical scripts",
                ],
                "clear cta above fold": [
                    "Add 'Add to Cart' button visible without scrolling on product pages",
                    "Use sticky 'Buy Now' bar on mobile product pages",
                    "Highlight free shipping threshold above the fold",
                ],
                "mobile responsive": [
                    "Test checkout flow on actual iPhone/Android devices",
                    "Ensure product image zoom works with pinch gestures",
                    "Make filter/sort controls thumb-friendly (min 44px tap targets)",
                ],
            }
            if item in ecommerce_steps:
                return ecommerce_steps[item]
        elif business_type == "saas":
            saas_steps = {
                "page load speed": [
                    "Code-split your React/Vue bundle to reduce initial JS load",
                    "Use server-side rendering (SSR) for landing pages",
                    "Optimize hero LCP image (preload, proper sizing)",
                    "Implement edge caching for marketing pages",
                ],
                "clear cta above fold": [
                    "Replace 'Learn More' with 'Start Free Trial' or 'Get Demo'",
                    "Add social proof ( logos, G2/Capterra badges) next to CTA",
                    "Use contrasting color for primary CTA button",
                ],
                "mobile responsive": [
                    "Ensure pricing table is swipeable on mobile",
                    "Test signup form autofill on mobile keyboards",
                    "Verify video embeds don't break mobile layout",
                ],
            }
            if item in saas_steps:
                return saas_steps[item]
        elif business_type == "local_service":
            local_steps = {
                "page load speed": [
                    "Compress before/after gallery images",
                    "Embed Google Maps efficiently (static image fallback)",
                    "Minimize third-party booking widget scripts",
                ],
                "clear cta above fold": [
                    "Add 'Book Appointment' button with calendar integration",
                    "Display phone number as prominent click-to-call button",
                    "Show 'Accepting New Patients/Clients' badge",
                ],
                "mobile responsive": [
                    "Ensure click-to-call button is thumb-sized and sticky",
                    "Test online booking form on mobile (date picker, dropdowns)",
                    "Verify driving directions link opens native maps app",
                ],
            }
            if item in local_steps:
                return local_steps[item]
        elif business_type == "restaurant":
            restaurant_steps = {
                "page load speed": [
                    "Compress food photography to WebP (<300KB each)",
                    "Lazy-load menu images below the fold",
                    "Minimize third-party reservation widget scripts",
                ],
                "clear cta above fold": [
                    "Add 'Reserve a Table' button above the fold",
                    "Display phone number as click-to-call on mobile",
                    "Show hours and 'Open Now' status prominently",
                ],
                "mobile responsive": [
                    "Test menu readability on mobile (font size, contrast)",
                    "Ensure reservation form works with mobile keyboards",
                    "Verify 'Get Directions' opens native maps app",
                ],
                "contact info visible": [
                    "Add address with embedded map to footer",
                    "Display hours for each day of the week",
                    "Include dietary restriction info (vegan, gluten-free)",
                ],
            }
            if item in restaurant_steps:
                return restaurant_steps[item]
        steps = {
            "page load speed": [
                "Compress images using WebP format",
                "Enable browser caching via .htaccess or nginx config",
                "Use a CDN for static assets",
                "Minify CSS and JavaScript files",
            ],
            "clear cta above fold": [
                "Add a prominent call-to-action button in the hero section",
                "Use contrasting colors for the CTA button",
                "Keep CTA text action-oriented (e.g., 'Get Quote', 'Book Now')",
            ],
            "mobile responsive": [
                "Test site on actual mobile devices, not just browser resize",
                "Use responsive breakpoints for common screen sizes",
                "Ensure touch targets are at least 44px wide",
            ],
            "contact info visible": [
                "Add phone number and email to header or footer",
                "Include a contact page link in main navigation",
                "Display business hours prominently",
            ],
            "social proof": [
                "Add 3-5 customer testimonials to homepage",
                "Include client logos if B2B",
                "Display review counts from Google/Yelp",
            ],
            "title tags optimized": [
                "Keep titles under 60 characters",
                "Include primary keyword near the beginning",
                "Make each page title unique",
            ],
            "meta descriptions": [
                "Write compelling descriptions under 160 characters",
                "Include a call-to-action in the description",
                "Use unique descriptions for every page",
            ],
        }
        return steps.get(item, [
            f"Review and improve {item.replace('_', ' ')}",
            "Check competitor sites for best practices",
            "Implement changes and test conversion impact",
        ])