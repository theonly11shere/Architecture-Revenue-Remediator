from typing import Dict, List, Any

REVENUE_LEAKS: Dict[str, Dict[str, Any]] = {
    "mobile_sticky_cta": {"title": "Missing Mobile Sticky CTA", "base_weight": 9, "leak_msg": "Mobile users lose the buy button on scroll, causing high drop-off."},
    "exit_intent_capture": {"title": "Missing Exit-Intent Lead Capture", "base_weight": 8, "leak_msg": "95% of non-converting visitors leave with zero retargeting info."},
    "social_proof_above_fold": {"title": "Zero Above-the-Fold Social Proof", "base_weight": 9, "leak_msg": "No trust signals visible within 3 seconds of landing."},
    "no_click_to_call": {"title": "No Click-to-Call / Instant Contact", "base_weight": 8, "leak_msg": "High-intent phone leads drop off on mobile browsers."},
    "local_seo_schema": {"title": "Missing Local Business Schema", "base_weight": 7, "leak_msg": "Missing out on Google rich snippets and Map Pack rankings."},
    "lcp_speed_lag": {"title": "LCP Speed Lag (> 2.5s)", "base_weight": 8, "leak_msg": "Every second of load delay reduces conversions by ~7%."},
    "missing_ssl": {"title": "Missing SSL / Security Badges", "base_weight": 9, "leak_msg": "Form abandonment spikes when checkouts lack trust anchors."},
    "broken_meta": {"title": "Broken Social Share Meta", "base_weight": 5, "leak_msg": "Shared links look unprofessional on messaging apps."},
    "no_secondary_cta": {"title": "No Secondary Call-to-Action", "base_weight": 6, "leak_msg": "Only asking for immediate sales with no low-commitment alternative."},
    "competitor_feature_gap": {"title": "Competitor Exclusive Feature Advantage", "base_weight": 7, "leak_msg": "Competitors offer native features your site lacks."}
}

class LeakAnalyzer:
    def __init__(self, target_features: dict, competitor_features: dict, business_type: str, is_local: bool):
        self.target = target_features
        self.competitor = competitor_features
        self.business_type = business_type
        self.is_local = is_local

    def get_tier_report(self, tier: str = "entry") -> Dict[str, Any]:
        detected_leaks = []

        for feature_key, rule in REVENUE_LEAKS.items():
            if not self.target.get(feature_key, False):
                severity_score = rule["base_weight"]
                if self.competitor.get(feature_key, False):
                    severity_score += 3  
                if self.is_local and feature_key in ["local_seo_schema", "no_click_to_call"]:
                    severity_score += 4  
                if self.business_type == "ecommerce" and feature_key in ["exit_intent_capture", "mobile_sticky_cta"]:
                    severity_score += 3

                detected_leaks.append({
                    "leak_key": feature_key,
                    "issue": rule["title"],
                    "severity_score": severity_score,
                    "explanation": rule["leak_msg"]
                })

        sorted_leaks = sorted(detected_leaks, key=lambda x: x["severity_score"], reverse=True)
        
        if tier == "entry":
            selected_leaks = sorted_leaks[:3]
            roadmap = None
        elif tier == "growth":
            selected_leaks = sorted_leaks[:6]
            
            def get_leak(idx, default_title="General Optimization", default_expl="improving site conversion metrics"):
                if idx < len(selected_leaks):
                    return selected_leaks[idx]
                return {"issue": default_title, "explanation": default_expl}

            l0 = get_leak(0)
            l1 = get_leak(1)
            l2 = get_leak(2)
            l3 = get_leak(3)
            l4 = get_leak(4)
            l5 = get_leak(5)

            roadmap = {
                "Days 1-2: Trust & Mobile Foundation": (
                    f"Begin by resolving {l0['issue'].lower()} ({l0['explanation'].lower()}) "
                    f"alongside {l1['issue'].lower()} to instantly secure mobile traffic and local visibility."
                ),
                "Days 3-5: Conversion & Lead Capture": (
                    f"Focus on implementing {l2['issue'].lower()} and {l3['issue'].lower()} "
                    f"to actively convert high-intent visitors before they abandon the page."
                ),
                "Days 6-7: Performance & Security Polish": (
                    f"Finalize the sprint by addressing {l4['issue'].lower()} and {l5['issue'].lower()} "
                    f"to ensure maximum trust and technical readiness."
                )
            }
        else: # enterprise
            selected_leaks = sorted_leaks[:10]
            roadmap = {
                "Week 1 (Immediate Patches)": [f"Fix {l['issue']}" for l in selected_leaks[:3]],
                "Week 2 (Trust & Conversion)": [f"Implement {l['issue']}" for l in selected_leaks[3:6]],
                "Week 3-4 (Full Optimization & Secret Leaks)": [f"Optimize {l['issue']}" for l in selected_leaks[6:]]
            }
        
        # Controlled scaling to sit precisely around your 53 baseline target
        if selected_leaks:
            raw_template_score = sum(l["severity_score"] for l in selected_leaks)
            template_score = min(max(int(raw_template_score * 0.35), 20), 55)
        else:
            template_score = 53

        return {
            "tier_applied": tier,
            "unlocked_leaks": selected_leaks,
            "roadmap_included": tier != "entry",
            "roadmap_timeline": roadmap,
            "template_score": template_score,
            "visual_score": 10,
            "sameness_score": 5,
            "presence_score": 0
        }