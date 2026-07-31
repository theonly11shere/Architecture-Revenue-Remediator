"""
Blueprint Calculation & Matrix Scoring Engine
Applies tailored business matrix scoring, evaluates all 35 checks, borrows solutions cross-industry,
filters by client tier, and outputs the Master Report payload.
"""

from typing import Dict, Any, Optional
from .config import (
    CHECKPOINTS,
    CATEGORY_WEIGHTS,
    BUSINESS_CONTEXT_MULTIPLIERS,
    BUSINESS_TYPE_ALIASES,
    TOTAL_CHECKS
)

VALID_BUSINESS_TYPES = ["ecommerce", "local", "agency", "saas", "b2b", "creator"]


class SolutionBlueprintEngine:

    def __init__(self):
        self.blueprint_db = self._initialize_solution_matrix()

    def process_and_generate_report(
        self,
        checkpoint_results: Dict[str, bool],
        client_tier: int,
        business_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calculates financial leak rankings based on business type,
        borrows solutions cross-industry if necessary, and truncates to the client's tier limit.
        """
        resolved_type = self._resolve_business_type(business_type)

        if not resolved_type:
            return {
                "status": "REQUIRES_USER_SELECTION",
                "message": "Business type uncertain. Please select your business model.",
                "available_types": VALID_BUSINESS_TYPES
            }

        # Step 1: Detect and calculate severity for ALL failed checks dynamically
        failed_leaks = []
        for check_key, passed in checkpoint_results.items():
            if not passed and check_key in CHECKPOINTS:
                meta = CHECKPOINTS[check_key]
                category = meta["category"]
                base_impact = meta["impact_weight"]

                # Apply sorting formula: Base * CategoryWeight * ContextMultiplier
                cat_weight = CATEGORY_WEIGHTS.get(category, 1.0)
                context_mult = BUSINESS_CONTEXT_MULTIPLIERS.get(resolved_type, {}).get(category, 1.0)
                
                severity_score = round(base_impact * cat_weight * context_mult, 2)

                failed_leaks.append({
                    "leak_key": check_key,
                    "label": meta["label"],
                    "category": category,
                    "severity_score": severity_score,
                    "base_impact": base_impact
                })

        # Step 2: Rank leaks by calculated severity score descending
        ranked_leaks = sorted(failed_leaks, key=lambda x: x["severity_score"], reverse=True)

        # Step 3: Attach solutions, borrow from other business types if missing, and flag Top 6 gaps
        processed_leaks = []
        manual_action_notices = []

        for index, leak in enumerate(ranked_leaks):
            rank = index + 1
            leak_key = leak["leak_key"]

            solutions, borrowed_from = self._get_or_borrow_solution(leak_key, resolved_type)

            leak["rank"] = rank
            leak["solutions"] = solutions
            leak["borrowed_from_business_type"] = borrowed_from

            if not solutions and rank <= 6:
                manual_action_notices.append({
                    "rank": rank,
                    "leak_key": leak_key,
                    "label": leak["label"],
                    "message": f"Critical Leak #{rank} ({leak['label']}) has no blueprint in DB. Manual strategy required."
                })

            processed_leaks.append(leak)

        # Step 4: Truncate output precisely to the client's purchased tier limit (3, 6, 8, or 10)
        tier_locked_leaks = processed_leaks[:client_tier]

        return {
            "status": "CALCULATIONS_COMPLETE",
            "business_type": resolved_type,
            "client_tier": client_tier,
            "total_checks_scanned": TOTAL_CHECKS,
            "master_report": {
                "leaks": tier_locked_leaks,
                "has_manual_action_notices": len(manual_action_notices) > 0,
                "manual_action_notices": manual_action_notices
            }
        }

    def _resolve_business_type(self, business_type: Optional[str]) -> Optional[str]:
        if not business_type:
            return None
        clean_input = business_type.lower().strip().replace(" ", "_")
        if clean_input in VALID_BUSINESS_TYPES:
            return clean_input
        return BUSINESS_TYPE_ALIASES.get(clean_input, None)

    def _get_or_borrow_solution(
        self,
        leak_key: str,
        target_business_type: str
    ) -> tuple[Optional[Dict[str, str]], Optional[str]]:
        target_db = self.blueprint_db.get(target_business_type, {})
        if leak_key in target_db:
            return target_db[leak_key], None

        for other_type, leaks in self.blueprint_db.items():
            if other_type != target_business_type and leak_key in leaks:
                return leaks[leak_key], other_type

        return None, None

    def _initialize_solution_matrix(self) -> Dict[str, Dict[str, Dict[str, str]]]:
        """Comprehensive solution database across core checkpoints."""
        return {
            "local": {
                "contact_info_visible": {
                    "quick_win": "Add phone number and service area prominently in the top navigation banner.",
                    "strategic_fix": "Embed an interactive Google Map showing active service coverage zip codes.",
                    "tech_ux": "Implement a prominent 'Tap to Call' floating action button for mobile visitors.",
                    "copy_conversion": "Add headline microcopy: 'Fast Response — Call or Text Us Now'.",
                    "trust_eeat": "Display local business license, bond number, and physical office address."
                },
                "clear_cta_above_fold": {
                    "quick_win": "Place 'Get Free Instant Quote' button directly above the main hero image.",
                    "strategic_fix": "Deploy a 3-step online booking form that estimates service pricing.",
                    "tech_ux": "Ensure call button target is large (min 48px) for thumb interaction on phones.",
                    "copy_conversion": "Use 'Claim Your Free Estimate' instead of generic 'Submit'.",
                    "trust_eeat": "Display '5-Star Rated Local Provider' directly below the CTA."
                },
                "social_proof_elements": {
                    "quick_win": "Add Google Review star rating summary in the site header.",
                    "strategic_fix": "Embed video testimonials from recent local neighborhood customers.",
                    "tech_ux": "Integrate auto-syncing Google / Yelp review carousel widget.",
                    "copy_conversion": "Quote specific customer praise regarding punctuality and thoroughness.",
                    "trust_eeat": "Include full customer names and specific neighborhood locations."
                },
                "phone_or_chat_option": {
                    "quick_win": "Add click-to-SMS text messaging button for quick inquiries.",
                    "strategic_fix": "Set up automated after-hours call routing and instant SMS response.",
                    "tech_ux": "Keep click-to-call icon persistent at the bottom of mobile screens.",
                    "copy_conversion": "Promote 'Speak With a Local Expert in 30 Seconds'.",
                    "trust_eeat": "State clear operating hours and emergency service availability."
                },
                "trust_badges": {
                    "quick_win": "Display BBB accreditation and background-checked employee seals.",
                    "strategic_fix": "Add verified insurance and bonding certification badges.",
                    "tech_ux": "Use crisp SVG graphics for trust badges to ensure fast loading.",
                    "copy_conversion": "Add '100% Satisfaction Guarantee or We Reclean for Free' badge text.",
                    "trust_eeat": "Link badges to official third-party verification profiles."
                },
                "form_fields_count_ok": {
                    "quick_win": "Reduce initial lead estimate form to 3 fields: Name, Phone, Zip Code.",
                    "strategic_fix": "Use progressive multi-step form to collect job details post-contact.",
                    "tech_ux": "Set numeric keypad default on mobile phone entry fields.",
                    "copy_conversion": "Add reassurance microcopy: 'No hidden fees. Free estimates.'",
                    "trust_eeat": "Include explicit privacy promise that phone numbers will not be spammed."
                },
                "ssl_valid": {
                    "quick_win": "Install an active SSL certificate to convert browser warning states.",
                    "strategic_fix": "Enforce strict HTTPS redirection across all site endpoints.",
                    "tech_ux": "Audit asset paths to prevent insecure content blocks.",
                    "copy_conversion": "Display secure connection indicators next to form entry points.",
                    "trust_eeat": "Ensure domain registration and contact ownership details are verified."
                }
            },
            "ecommerce": {
                "clear_cta_above_fold": {
                    "quick_win": "Add 'Add to Cart' button visible without scrolling on product pages.",
                    "strategic_fix": "Deploy a persistent sticky checkout bar on long product detail pages.",
                    "tech_ux": "Ensure purchase touch target is at least 48px tall on mobile viewports.",
                    "copy_conversion": "Change CTA copy to 'Claim Yours Now' or 'Buy Now — Free Shipping'.",
                    "trust_eeat": "Display accepted payment method icons directly beneath the CTA."
                },
                "ssl_valid": {
                    "quick_win": "Enforce HTTPS redirects across all checkout and account pages.",
                    "strategic_fix": "Upgrade to high-assurance EV SSL certificate.",
                    "tech_ux": "Fix mixed-content HTTP script calls on cart and checkout templates.",
                    "copy_conversion": "Add '256-Bit Encrypted Checkout' text near purchase forms.",
                    "trust_eeat": "Display verified SSL security badges on cart pages."
                }
            }
        }