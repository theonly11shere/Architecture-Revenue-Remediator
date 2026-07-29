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

        # ── ALWAYS create 4 weeks, distribute evenly ────────────────────
        total = len(ordered)
        if total >= 4:
            per_week = total // 4
            remainder = total % 4
            buckets = []
            idx = 0
            for week_num in range(4):
                count = per_week + (1 if week_num < remainder else 0)
                buckets.append(ordered[idx:idx + count])
                idx += count
        elif total > 0:
            per_week = max(1, total // 4) if total >= 4 else 1
            buckets = [
                ordered[0:per_week],
                ordered[per_week:per_week*2] if total > per_week else [],
                ordered[per_week*2:per_week*3] if total > per_week*2 else [],
                ordered[per_week*3:] if total > per_week*3 else [],
            ]
        else:
            buckets = [[], [], [], []]

        week_configs = [
            ("Week 1", "Stop the bleeding — critical revenue blockers first"),
            ("Week 2", "Build trust and credibility — close the confidence gap"),
            ("Week 3", "Content depth & differentiation — stand out from competitors"),
            ("Week 4", "Polish, speed, and measurement — optimize and track"),
        ]

        weeks = []
        btype = self.data.get("business_type", {}).get("detected_type", "unknown")
        comp = self.data.get("competitor_analysis", {})
        comp_features = comp.get("aggregate_missing_features", []) if comp else []
        comp_results = comp.get("competitors", []) if comp else []

        for i, (name, focus) in enumerate(week_configs):
            items = buckets[i] if i < len(buckets) else []
            week_items = []

            # Add failure items with comprehensive fix steps
            for failure in items:
                week_items.append({
                    "item": failure.get("human_name", failure.get("item", "")).replace("_", " ").title(),
                    "severity": failure.get("severity", ""),
                    "steps": self._generate_fix_steps(failure, btype, comp_results, comp_features),
                })

            # Add competitor differentiation tasks if week is light
            if len(week_items) < 2 and comp_features:
                feat = comp_features.pop(0)
                week_items.append({
                    "item": 'Differentiate from competitors: add "' + feat + '"',
                    "severity": "medium",
                    "steps": [
                        "Research how top 3 competitors implement this feature",
                        "Identify 2 ways to do it DIFFERENTLY (not just copy)",
                        "Create a version that matches your brand voice and audience",
                        "A/B test your approach vs. a competitor-inspired version",
                        "Document what worked — build a playbook for future features",
                        "Share the win internally so the team learns from it",
                    ],
                })

            # Add continuous improvement if still empty
            if not week_items:
                week_items.append({
                    "item": "Continuous improvement & competitor monitoring",
                    "severity": "low",
                    "steps": [
                        "Review top 3 competitor sites for new trends and features",
                        "Run a fresh scan to benchmark your progress vs. last month",
                        "Update at least one page of content to stay fresh and relevant",
                        "Test one new conversion element (CTA color, headline, form field)",
                        "Check your site speed on mobile — aim for <2.5s LCP",
                        "Document 1 insight from competitor analysis in your strategy doc",
                    ],
                })

            weeks.append({
                "week": name,
                "focus": focus,
                "items": week_items,
            })

        report["roadmap"] = weeks
        return report

    def _generate_fix_steps(self, failure: Dict[str, Any], business_type: str = "unknown",
                            comp_results: List[Dict] = None, comp_features: List[str] = None) -> List[str]:
        """Generate 6-8 diverse, multi-angle fix steps for any failure.

        Each failure gets solutions covering:
        1. Technical implementation
        2. Content/copy improvements
        3. Design/UX enhancements
        4. Trust/social proof
        5. SEO/discoverability
        6. Competitor differentiation (what they do + alternative approaches)
        """
        item = failure.get("item", "").lower()
        human_name = failure.get("human_name", item.replace("_", " ").title())
        comp_results = comp_results or []
        comp_features = comp_features or []

        # Build competitor context
        comp_domains = [c.get("domain", "competitor") for c in comp_results[:2]]
        comp_note = " (vs. " + ", ".join(comp_domains) + ")" if comp_domains else ""

        if item == "check_ssl_valid":
            return [
                "Technical: Install a valid SSL certificate (Let\'s Encrypt is free and auto-renews)",
                "Technical: Force HTTPS redirect in your server config — no HTTP version should load",
                "Technical: Check for mixed-content warnings using browser dev tools",
                "Trust: Add a security badge or \'Secure Checkout\' message near forms and CTAs",
                "Trust: Display your SSL provider\'s seal (DigiCert, Sectigo) in the footer",
                "Competitor: Check if competitors show security indicators — match or exceed their visibility",
                "Differentiate: Instead of just an SSL badge, add a \'256-bit Encrypted\' callout near your primary CTA",
                "SEO: Submit your HTTPS sitemap to Google Search Console and request re-indexing",
            ]

        if item == "check_contact":
            return [
                "Technical: Add clickable phone (tel:) and mailto: links in header AND footer",
                "Content: Write a compelling \'Contact Us\' page with multiple methods (phone, email, form, chat)",
                "Design: Make contact info sticky on mobile so it\'s always one tap away",
                "Trust: Add a real physical address with embedded Google Maps",
                "Trust: Display business hours prominently — \'Open Now\' vs \'Closed\' builds instant credibility",
                "Competitor: See how competitors display contact info — if they hide it, make yours impossible to miss",
                "Differentiate: Add a \'Call Back in 15 Minutes\' promise instead of just a phone number",
                "UX: Use a floating \'Chat with us\' widget that appears after 10 seconds on page",
            ]

        if item == "check_about":
            return [
                "Content: Write an About page that tells YOUR story — founder journey, mission, why you started",
                "Content: Include 3 specific facts (year founded, customers served, cities covered)",
                "Trust: Add real team photos with names and roles — avoid stock images",
                "Trust: Embed a 60-second \'Meet the Team\' video — video builds 3x more trust than text",
                "SEO: Add Organization schema markup with logo, address, and social profiles",
                "Competitor: Read competitor About pages — find what they\'re missing and do THAT",
                "Differentiate: Create a \'Our Promise to You\' manifesto speaking directly to customer fears",
                "Design: Use a timeline layout showing key milestones — visual storytelling beats walls of text",
            ]

        if item == "check_team_photos":
            return [
                "Content: Hire a local photographer for 1 hour to shoot authentic team photos ($100-300)",
                "Trust: Add captions with names, roles, and one fun fact per person",
                "Design: Use consistent photo style (same background, lighting, crop) across all images",
                "Trust: Show the team IN ACTION — working, laughing, collaborating — not posed headshots",
                "Alternative: If solo founder, show yourself with clients, at work, or speaking at events",
                "Competitor: Check if competitors use stock photos — your real photos are an instant differentiator",
                "UX: Make team photos clickable to reveal short bios or LinkedIn profiles",
                "Content: Add a \'Join Our Team\' section — shows growth and attracts talent",
            ]

        if item == "check_reviews":
            return [
                "Technical: Embed Google Reviews widget directly on your homepage (free, auto-updates)",
                "Trust: Create a \'Wall of Love\' page with 10+ detailed testimonials including names and photos",
                "Content: Reach out to 5 past customers TODAY asking for a 2-sentence testimonial",
                "Trust: Add star ratings next to product/service names — even 4.2 stars beats no rating",
                "Design: Use testimonial cards with customer photos, not just text quotes",
                "Competitor: See which review platforms competitors use — dominate the ONE they ignore",
                "Differentiate: Instead of generic 5-star reviews, showcase \'before/after\' stories with metrics",
                "SEO: Add Review schema markup so stars appear in Google search results",
            ]

        if item == "check_privacy":
            return [
                "Technical: Generate a privacy policy using Termly or Iubenda (free tier available)",
                "Trust: Make the privacy policy link visible in footer AND checkout flow",
                "Content: Write a human-readable summary (\'Here\'s what we do with your data\') above legal text",
                "Trust: Add a \'We never sell your data\' badge near email capture forms",
                "Technical: Implement cookie consent that respects user choices (not just \'Accept All\')",
                "Competitor: Check if competitors have GDPR/CCPA compliance — being compliant is a trust advantage",
                "Differentiate: Publish a \'Data Transparency Report\' showing what you collect and why",
                "SEO: Link to privacy policy from every page footer",
            ]

        if item == "check_terms":
            return [
                "Technical: Generate Terms of Service via Termly or Rocket Lawyer tailored to your business",
                "Trust: Highlight key terms in plain English (\'No hidden fees, cancel anytime\') at the top",
                "Content: Add a FAQ section addressing common concerns (refunds, shipping, cancellations)",
                "Trust: Display a \'30-Day Money-Back Guarantee\' badge if applicable",
                "Design: Make Terms link easy to find in footer + checkout page",
                "Competitor: See if competitors bury unfair terms — being transparent builds loyalty",
                "Differentiate: Create a \'Fair Deal Guarantee\' that goes beyond legal terms",
                "SEO: Add FAQ schema to your terms page for rich snippets",
            ]

        if item == "check_domain_age":
            return [
                "Trust: If domain is new, prominently display \'Established [Year]\' or years in business",
                "Content: Create a \'Our Journey\' timeline showing milestones since launch",
                "Trust: Partner with an established brand or mention media coverage to borrow credibility",
                "Trust: Display \'As seen on...\' logos if you\'ve been featured anywhere",
                "Differentiate: If you\'re new, lean into it — \'Fresh approach, modern methods, no outdated baggage\'",
                "Competitor: Older competitors may look outdated — use your newness as a speed/agility advantage",
                "Content: Publish thought leadership to build authority faster than domain age alone",
                "SEO: Focus on long-tail keywords where domain age matters less than content quality",
            ]

        if item == "check_cta":
            return [
                "Design: Place PRIMARY CTA (\'Book Now\', \'Get Quote\') in hero section — above fold on ALL devices",
                "Content: Use action-oriented button text — \'Get My Free Estimate\' beats \'Submit\' by 30%+",
                "Design: Make CTA button a contrasting color — it should POP against your brand palette",
                "UX: Add a sticky CTA bar on mobile that follows the user as they scroll",
                "Trust: Place social proof (\'Join 500+ happy customers\') directly above or below the CTA",
                "Competitor: Count how many CTAs competitors have on their homepage — match or exceed",
                "Differentiate: Instead of one CTA, offer a CHOICE: \'Start Free Trial\' OR \'Watch 2-Min Demo\'",
                "A/B Test: Test CTA color, text, and placement weekly until conversion rate improves 15%+",
            ]

        if item == "check_mobile_real":
            return [
                "Technical: Add proper viewport meta tag: <meta name=\'viewport\' content=\'width=device-width, initial-scale=1\'>",
                "Design: Test EVERY page on actual iPhone and Android devices, not just browser resize",
                "UX: Ensure all tap targets are at least 44x44px (Apple HIG standard)",
                "Design: Use responsive breakpoints at 320px, 375px, 414px, and 768px",
                "Content: Keep mobile headlines under 40 characters so they don\'t wrap awkwardly",
                "Competitor: Load competitor sites on your phone — note what they do better on mobile",
                "Differentiate: Add mobile-exclusive features like \'Tap to Call\' or \'Add to Home Screen\' prompt",
                "Technical: Use Chrome DevTools Lighthouse mobile audit — fix every flagged issue",
            ]

        if item == "check_speed_lighthouse":
            return [
                "Technical: Compress all images to WebP format (aim <200KB each, use Squoosh.app)",
                "Technical: Implement lazy loading for below-fold images and videos",
                "Technical: Use a CDN (Cloudflare free tier, BunnyCDN, or AWS CloudFront) for static assets",
                "Technical: Minify CSS/JS and defer non-critical scripts using async/defer",
                "Technical: Enable browser caching with proper cache-control headers",
                "Design: Reduce hero image file sizes without sacrificing quality — use modern formats",
                "Competitor: Test competitor site speed on PageSpeed Insights — aim to beat their LCP by 20%",
                "Differentiate: If competitor uses heavy images, differentiate with optimized vector graphics and SVG",
            ]

        if item == "check_booking":
            return [
                "Technical: Integrate Calendly, Acuity, or SimplyBook.me for instant online scheduling",
                "Content: Write booking page copy that removes friction — \'Pick a time that works for you\'",
                "Design: Add a \'Book Now\' button in the header, hero, and footer — three chances to convert",
                "Trust: Show available slots in real-time — scarcity drives action (\'Only 3 slots left this week\')",
                "UX: Reduce booking form to 3 fields max: Name, Email, Phone — ask everything else later",
                "Competitor: Check if competitors require phone calls to book — online booking is your edge",
                "Differentiate: Offer \'Instant Confirmation\' vs. competitors\' \'We\'ll call you back\' approach",
                "SEO: Add BookAction schema markup so Google shows \'Book Online\' button in search results",
            ]

        if item == "check_phone":
            return [
                "Technical: Add tel: links to ALL phone numbers: <a href=\'tel:+1234567890\'>Call Us</a>",
                "Design: Make the phone number a prominent button on mobile (sticky header or floating action)",
                "Content: Add \'Call Now — We\'re Available\' with current hours next to the phone number",
                "Trust: Display \'Average answer time: under 30 seconds\' if true — sets expectation",
                "UX: Add a \'Request Callback\' form for visitors who can\'t call right now",
                "Competitor: Check if competitors hide their phone number — being accessible builds trust",
                "Differentiate: Offer a \'Text Us\' option (SMS) alongside calling — younger audiences prefer it",
                "SEO: Add LocalBusiness schema with phone number for rich results",
            ]

        if item == "check_email_capture":
            return [
                "Technical: Add an email capture form above the fold — not buried in the footer",
                "Content: Offer a compelling lead magnet: \'Free Guide\', \'10% Off\', \'Exclusive Tips\'",
                "Design: Use a two-step opt-in: click button → popup form (higher conversion than inline)",
                "Trust: Add \'Join 2,000+ subscribers\' or \'No spam, unsubscribe anytime\' below the form",
                "UX: Keep form to ONE field (email) initially — ask name later in the welcome sequence",
                "Competitor: See what lead magnets competitors offer — create something 10x more valuable",
                "Differentiate: Instead of a generic newsletter, offer a \'Weekly [Industry] Insider Report\'",
                "Technical: Set up automated welcome email sequence (3-5 emails) to nurture new subscribers",
            ]

        if item == "check_pricing":
            return [
                "Content: Create a clear pricing page with at least 3 tiers (Good/Better/Best strategy)",
                "Trust: Show pricing on the homepage or link prominently — hidden pricing kills trust",
                "Design: Use anchoring — show the most expensive plan first, then the popular middle plan",
                "Content: Add a \'Most Popular\' badge to the plan you want most customers to choose",
                "Trust: Include \'No hidden fees\', \'Cancel anytime\', \'Money-back guarantee\' near pricing",
                "Competitor: Mystery-shop competitors to see their pricing structure — match or undercut",
                "Differentiate: Offer a \'Pay What You Can\' or sliding scale option competitors don\'t have",
                "UX: Add a pricing calculator or \'Build Your Package\' interactive tool",
            ]

        if item == "check_testimonials":
            return [
                "Content: Reach out to 10 past customers this week asking for specific results-based testimonials",
                "Trust: Use video testimonials — 30-second clips on a \'Wall of Love\' page",
                "Design: Create testimonial cards with customer photo, name, company, and specific metric",
                "Content: Ask for testimonials that answer: \'What was the problem? What did we do? What was the result?\'",
                "Trust: Add industry-specific badges or certifications next to relevant testimonials",
                "Competitor: See if competitors use generic testimonials — yours should include specific numbers",
                "Differentiate: Create case studies (500+ words) for your top 3 success stories — deep beats wide",
                "SEO: Add Review and Testimonial schema markup for rich snippets in search",
            ]

        if item == "check_title":
            return [
                "Technical: Ensure every page has a unique <title> under 60 characters",
                "Content: Put primary keyword at the START of the title, not the end",
                "Content: Add a benefit or hook: \'Best Pizza in Chicago | Mario\'s — Fresh Daily\'",
                "SEO: Include brand name at the end of titles for recognition: \'... | YourBrand\'",
                "Technical: Use dynamic title tags for product/service pages: \'[Product] — [Category] | [Brand]\'",
                "Competitor: Search your target keyword on Google — see what titles rank top 3, then write better ones",
                "Differentiate: Use emotional triggers competitors ignore: \'Finally, a [service] that actually works\'",
                "A/B Test: Test title variations in Google Ads first, then apply the winner to organic titles",
            ]

        if item == "check_meta":
            return [
                "Technical: Write unique meta descriptions for EVERY page (150-160 characters)",
                "Content: Include a CTA in the meta description: \'Learn how...\', \'Discover...\', \'Get started today...\'",
                "Content: Mention a specific benefit or number: \'Save 20% on...\', \'Trusted by 500+...\'",
                "SEO: Include target keyword naturally — Google bolds it in search results",
                "Technical: Use dynamic meta descriptions for product pages with price and availability",
                "Competitor: Read competitor meta descriptions in search results — write ones that stand out",
                "Differentiate: Use curiosity gaps competitors don\'t: \'The [industry] secret most businesses miss...\'",
                "A/B Test: Track CTR in Google Search Console — rewrite descriptions under 2% CTR",
            ]

        if item == "check_h1":
            return [
                "Technical: Ensure EVERY page has exactly ONE <h1> tag — no more, no less",
                "Content: Make H1 descriptive and keyword-rich: \'Affordable Web Design for Small Business\'",
                "Design: Style H1 to be the largest text on the page — visual hierarchy matters",
                "Content: H1 should answer the visitor\'s question in 6-10 words max",
                "SEO: Include primary keyword in H1 but keep it natural and readable",
                "Competitor: Check competitor H1s — if they use generic \'Welcome\', you win with specificity",
                "Differentiate: Use a question H1 if competitors use statements: \'Need a [solution] that actually works?\'",
                "Technical: Ensure H1 is visible above the fold on mobile — not hidden behind images",
            ]

        if item == "check_alt":
            return [
                "Technical: Add descriptive alt text to ALL images: \'Chef Maria preparing handmade pasta\'",
                "Content: Include target keywords naturally in 2-3 image alt texts per page",
                "SEO: Use alt text to describe the image\'s PURPOSE, not just its appearance",
                "Design: Ensure decorative images have empty alt=\'\' so screen readers skip them",
                "Technical: Audit all images with Screaming Frog or Sitebulb to find missing alt text",
                "Competitor: Check if competitor images have alt text — accessible sites rank higher",
                "Differentiate: Use original photography with descriptive alt text vs. competitors\' stock images",
                "SEO: Add ImageObject schema markup for key product/service images",
            ]

        if item == "check_schema":
            return [
                "Technical: Add Organization schema with name, logo, URL, and social profiles",
                "Technical: Add LocalBusiness schema with address, phone, hours, and geo-coordinates",
                "Technical: Add FAQPage schema to your FAQ section for rich snippets",
                "Technical: Add Product schema with price, availability, and reviews for e-commerce",
                "SEO: Use Google\'s Rich Results Test to validate all schema markup",
                "Competitor: Check if competitors have rich snippets in search — schema is how you get them",
                "Differentiate: Add HowTo schema for tutorial content competitors don\'t have",
                "Technical: Implement breadcrumb schema for better navigation in search results",
            ]

        if item == "check_internal_links":
            return [
                "Technical: Add 3-5 contextual internal links per page to related content",
                "Content: Use descriptive anchor text — \'our pricing plans\' beats \'click here\'",
                "SEO: Create topic clusters — pillar page links to 5+ related subtopic pages",
                "Design: Add \'Related Articles\' or \'You Might Also Like\' sections at page bottom",
                "Technical: Ensure no orphan pages — every page should be reachable within 3 clicks from home",
                "Competitor: Map competitor site structure — find content gaps you can fill with internal links",
                "Differentiate: Create a \'Start Here\' page that links to your best content in logical order",
                "SEO: Use breadcrumb navigation to reinforce site structure and internal linking",
            ]

        if item == "check_sitemap":
            return [
                "Technical: Generate XML sitemap at /sitemap.xml using your CMS or a generator tool",
                "Technical: Submit sitemap to Google Search Console and Bing Webmaster Tools",
                "SEO: Include only canonical, indexable pages — exclude tags, archives, and thin content",
                "Technical: Update sitemap automatically when new pages are published",
                "SEO: Add image and video sitemaps if you have significant visual content",
                "Competitor: Check competitor sitemaps at theirdomain.com/sitemap.xml — see what they prioritize",
                "Differentiate: Create an HTML sitemap page for users (not just XML for bots)",
                "Technical: Keep sitemap under 50,000 URLs and 50MB — split if needed",
            ]

        if item == "check_robots":
            return [
                "Technical: Create robots.txt at domain root with clear allow/disallow rules",
                "SEO: Add Sitemap directive to robots.txt: \'Sitemap: https://yoursite.com/sitemap.xml\'",
                "Technical: Block admin pages, search results, and duplicate content from indexing",
                "SEO: Allow CSS and JS files so Google can render pages correctly",
                "Technical: Test robots.txt with Google\'s Robots Testing Tool before deploying",
                "Competitor: Check competitor robots.txt — see what they hide (might reveal strategy)",
                "Differentiate: Use robots.txt to guide crawlers to your most important pages first",
                "SEO: Add crawl-delay if your server struggles with bot traffic",
            ]

        if item == "check_unique":
            return [
                "Content: Write original page copy — aim for 300+ words per page minimum",
                "Content: Use your own data, case studies, and research — don\'t regurgitate industry stats",
                "Content: Add original images, infographics, or videos that no competitor has",
                "Technical: Check for duplicate content with Copyscape or Siteliner — fix or canonicalize",
                "Content: Create content that ONLY you can create — your unique process, methodology, or story",
                "Competitor: Read competitor content — find the gaps (depth, personality, specifics) and fill them",
                "Differentiate: Publish \'behind the scenes\' content showing your actual process — transparency wins",
                "SEO: Use canonical tags to consolidate duplicate pages and preserve link equity",
            ]

        if item == "check_readability":
            return [
                "Content: Break text into short paragraphs (2-3 sentences max) with plenty of white space",
                "Content: Use subheadings (H2, H3) every 200-300 words to guide scanning readers",
                "Content: Replace jargon with plain language — write for an 8th-grade reading level",
                "Design: Use bullet points and numbered lists for complex information",
                "Content: Add a \'TL;DR\' summary at the top of long pages for busy readers",
                "Competitor: Run competitor pages through Hemingway Editor — beat their readability score",
                "Differentiate: Use storytelling format (Problem → Agitation → Solution) vs. competitors\' dry lists",
                "Technical: Ensure font size is 16px+ on mobile — small text hurts readability AND conversions",
            ]

        if item == "check_services":
            return [
                "Content: Create a dedicated page for EACH service with 500+ words of specific detail",
                "Content: Include pricing ranges or \'Starting at\' numbers — specificity builds trust",
                "Content: Add a \'Who This Is For / Who This Is NOT For\' section to qualify leads",
                "Design: Use process diagrams showing exactly how your service works (3-5 steps)",
                "Trust: Add case studies or results metrics for each service — \'We helped X achieve Y\'",
                "Competitor: List competitor services — find the ONE they don\'t offer and make it your flagship",
                "Differentiate: Package services in a unique way competitors haven\'t thought of — bundles, tiers, or subscriptions",
                "SEO: Create service-area pages for each location you serve — \'Plumber in [City]\'",
            ]

        if item == "check_blog":
            return [
                "Content: Publish 1-2 blog posts per month targeting questions your customers actually ask",
                "Content: Write \'ultimate guides\' (2000+ words) that comprehensively cover one topic",
                "SEO: Target long-tail keywords with low competition — \'best [service] for [specific need]\'",
                "Content: Repurpose blog content into social posts, emails, and videos — maximize ROI",
                "Trust: Add author bios with credentials to every blog post — builds E-E-A-T",
                "Competitor: See what topics competitors rank for — create BETTER, deeper versions",
                "Differentiate: Interview customers for blog content — their words are more persuasive than yours",
                "Technical: Add \'Last Updated\' dates and refresh old posts quarterly to maintain rankings",
            ]

        if item == "check_faq":
            return [
                "Content: Create an FAQ page with 10-20 real questions from customers (check support emails)",
                "Content: Write answers that are specific, not generic — include numbers, timeframes, and examples",
                "SEO: Add FAQPage schema markup so questions appear directly in Google search results",
                "Design: Use accordion/collapsible format so the page doesn\'t feel overwhelming",
                "Trust: Include pricing-related FAQs — \'How much does it cost?\' should never be avoided",
                "Competitor: Check competitor FAQ pages — answer the questions THEY avoid",
                "Differentiate: Add video answers for your top 5 FAQs — multimedia content ranks better",
                "UX: Link FAQ answers to relevant product/service pages for deeper exploration",
            ]

        if item == "check_local":
            return [
                "Content: Mention your city/neighborhood naturally in page titles, H1s, and body copy",
                "Technical: Add NAP (Name, Address, Phone) in footer on EVERY page — consistency is critical",
                "SEO: Create location-specific landing pages for each area you serve",
                "Technical: Embed a Google Map with your business marked on contact and location pages",
                "Content: Add local landmarks, neighborhood names, and regional references in your copy",
                "Competitor: See which local keywords competitors rank for — target the ones they miss",
                "Differentiate: Sponsor or partner with local events and blog about it — local links boost rankings",
                "SEO: Ensure your Google Business Profile is fully optimized with photos, posts, and Q&A",
            ]

        if item == "check_broken":
            return [
                "Technical: Run a broken link check monthly using Screaming Frog, Ahrefs, or Dead Link Checker",
                "Technical: Set up 301 redirects for any deleted or moved pages — preserve link equity",
                "Technical: Create a custom 404 page that helps users find what they need (search box, popular links)",
                "SEO: Check for broken internal links especially — they waste crawl budget and hurt UX",
                "Content: Update old blog posts to remove dead external links and replace with current resources",
                "Competitor: Check if competitors have broken links pointing to them — reach out to those sites with YOUR link",
                "Differentiate: Turn your 404 page into a conversion opportunity — add a lead magnet or special offer",
                "Technical: Monitor for 404 errors in Google Search Console and fix them within 48 hours",
            ]

        if item == "check_redirects":
            return [
                "Technical: Force all HTTP traffic to HTTPS using 301 redirects in server config",
                "Technical: Redirect www to non-www (or vice versa) — pick ONE and stick to it",
                "SEO: Check for redirect chains (A→B→C) — they slow down page load and waste crawl budget",
                "Technical: Use 301 (permanent) not 302 (temporary) for permanent moves — preserves SEO value",
                "Technical: Update internal links to point directly to final URLs, not through redirects",
                "Competitor: Check if competitors have redirect issues — faster sites rank higher",
                "Differentiate: Use redirect opportunities to send users to optimized landing pages, not just home",
                "SEO: Audit redirects quarterly — remove loops and chains that hurt performance",
            ]

        if item == "check_canonical":
            return [
                "Technical: Add canonical tags to every page: <link rel=\'canonical\' href=\'https://yoursite.com/page\'>",
                "Technical: Use self-referencing canonicals even on original pages — prevents scraper issues",
                "SEO: For paginated content, use rel=\'next\' and rel=\'prev\' or proper canonical structure",
                "Technical: Ensure canonical URLs use HTTPS and match your preferred domain (www vs non-www)",
                "SEO: Check for canonicalized pages that shouldn\'t be — especially product variants and filters",
                "Competitor: See how competitors handle duplicate content (products, locations) — copy best practices",
                "Differentiate: Use canonical tags strategically to consolidate thin content into authoritative pages",
                "Technical: Validate canonicals with Screaming Frog — look for \'Canonicalised\' status codes",
            ]

        if item == "check_structured":
            return [
                "Technical: Add Organization schema with logo, URL, and sameAs links to social profiles",
                "Technical: Add LocalBusiness schema with full address, geo-coordinates, and opening hours",
                "Technical: Add BreadcrumbList schema for better navigation display in search results",
                "SEO: Use Product schema for e-commerce with price, availability, and aggregateRating",
                "Technical: Validate ALL schema with Google\'s Rich Results Test before deploying",
                "Competitor: Search your target keywords — see which rich snippets competitors have, then get them too",
                "Differentiate: Add HowTo or Recipe schema for tutorial content competitors don\'t have",
                "SEO: Monitor Search Console for structured data errors and fix within 7 days",
            ]

        if item == "check_security_headers":
            return [
                "Technical: Add Content-Security-Policy header to prevent XSS attacks",
                "Technical: Enable Strict-Transport-Security (HSTS) to force HTTPS connections",
                "Technical: Add X-Frame-Options: DENY to prevent clickjacking attacks",
                "Technical: Set X-Content-Type-Options: nosniff to prevent MIME-type sniffing",
                "Technical: Add Referrer-Policy to control what data is sent with outbound links",
                "Trust: Display a \'Secured by [Provider]\' badge if you have enterprise security",
                "Competitor: Check competitor security headers on securityheaders.com — beat their score",
                "Differentiate: Publish a security whitepaper or \'How We Protect Your Data\' page — transparency builds trust",
            ]

        if item == "check_favicon":
            return [
                "Technical: Create a favicon.ico (16x16, 32x32) and place it in the site root",
                "Technical: Add <link rel=\'icon\' type=\'image/png\' sizes=\'32x32\' href=\'/favicon-32x32.png\'>",
                "Design: Ensure favicon is recognizable at 16x16 — simplify your logo if needed",
                "Technical: Create Apple touch icons (180x180) for iOS home screen bookmarks",
                "Technical: Add manifest.json for Android/Chrome \'Add to Home Screen\' functionality",
                "Competitor: Check competitor favicons in browser tabs — a missing favicon looks unprofessional",
                "Differentiate: Use an animated favicon or dynamic favicon that changes based on page context",
                "Design: Test favicon visibility on both light and dark browser themes",
            ]

        # Fallback: generate comprehensive generic steps
        return [
            "Technical: Audit and fix " + human_name + " using industry best practices and current standards",
            "Content: Rewrite or expand content related to " + human_name + " — add specifics, examples, and data",
            "Design: Improve the visual presentation and user experience of " + human_name,
            "Trust: Add social proof, certifications, or guarantees that reinforce " + human_name,
            "SEO: Optimize " + human_name + " for search engines with proper markup and keywords",
            "Competitor: Research how top competitors handle " + human_name + " — identify gaps and opportunities",
            "Differentiate: Find ONE thing competitors do poorly regarding " + human_name + " and make it your strength",
            "A/B Test: Test 2-3 variations of " + human_name + " and implement the winner",
        ]