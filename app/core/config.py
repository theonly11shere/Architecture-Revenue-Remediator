"""
Centralized Configuration & Business Signature Matrix
Contains category weights, dynamic multipliers for local vs online models,
aliases, and 35 core checkpoints.
"""

from typing import Dict, Any

TOTAL_CHECKS = 35

CATEGORY_WEIGHTS: Dict[str, float] = {
    "trust": 0.25,
    "conversion": 0.25,
    "seo": 0.20,
    "content_eeat": 0.15,
    "technical": 0.15,
}

BUSINESS_CONTEXT_MULTIPLIERS: Dict[str, Dict[str, float]] = {
    "local": {"trust": 1.5, "conversion": 1.5, "seo": 0.9, "technical": 0.8, "content_eeat": 0.7},
    "ecommerce": {"trust": 1.4, "conversion": 1.5, "seo": 1.2, "technical": 1.3, "content_eeat": 0.8},
    "saas": {"trust": 1.3, "conversion": 1.4, "seo": 1.1, "technical": 1.4, "content_eeat": 0.9},
    "agency": {"trust": 1.4, "conversion": 1.3, "seo": 1.0, "technical": 0.9, "content_eeat": 1.2},
    "b2b": {"trust": 1.4, "conversion": 1.2, "seo": 1.0, "technical": 0.9, "content_eeat": 1.3},
    "creator": {"trust": 1.0, "conversion": 1.1, "seo": 1.3, "technical": 0.9, "content_eeat": 1.5},
}

BUSINESS_TYPE_ALIASES: Dict[str, str] = {
    "cleaning": "local",
    "cleaning_business": "local",
    "house_cleaning": "local",
    "plumbing": "local",
    "hvac": "local",
    "electrician": "local",
    "local_service": "local",
    "storefront": "local",
    "shopify": "ecommerce",
    "woocommerce": "ecommerce",
    "store": "ecommerce",
    "e-commerce": "ecommerce",
    "marketing": "agency",
    "consulting": "agency",
    "saas": "saas",
    "software": "saas",
    "b2b": "b2b",
    "creator": "creator",
    "blog": "creator"
}

CHECKPOINTS: Dict[str, Dict[str, Any]] = {
    # Trust & Credibility
    "ssl_valid": {"category": "trust", "impact_weight": 10, "label": "Valid SSL Certificate"},
    "privacy_policy": {"category": "trust", "impact_weight": 6, "label": "Privacy Policy Present"},
    "terms_conditions": {"category": "trust", "impact_weight": 5, "label": "Terms & Conditions Present"},
    "contact_info_visible": {"category": "trust", "impact_weight": 9, "label": "Clear Contact Information & Address"},
    "trust_badges": {"category": "trust", "impact_weight": 7, "label": "Security & License Badges"},
    "social_proof_elements": {"category": "trust", "impact_weight": 9, "label": "Reviews & Client Testimonials"},
    "secure_checkout_http": {"category": "trust", "impact_weight": 10, "label": "Secure Form / Payment Transmission"},

    # Conversion Optimization
    "clear_cta_above_fold": {"category": "conversion", "impact_weight": 10, "label": "Primary Action CTA Above Fold"},
    "form_fields_count_ok": {"category": "conversion", "impact_weight": 8, "label": "Low-Friction Contact Form"},
    "phone_or_chat_option": {"category": "conversion", "impact_weight": 9, "label": "Click-to-Call / Direct Chat Button"},
    "value_prop_headline": {"category": "conversion", "impact_weight": 9, "label": "Clear H1 Service Value Headline"},
    "no_friction_navigation": {"category": "conversion", "impact_weight": 6, "label": "Simple Uncluttered Navigation"},
    "urgency_scarcity_cues": {"category": "conversion", "impact_weight": 6, "label": "Booking Availability Triggers"},
    "mobile_cta_sticky": {"category": "conversion", "impact_weight": 9, "label": "Sticky Mobile Call / Book Button"},

    # SEO & Search Visibility
    "has_title": {"category": "seo", "impact_weight": 8, "label": "Optimized Page Title"},
    "has_meta_description": {"category": "seo", "impact_weight": 7, "label": "Meta Description Present"},
    "has_h1": {"category": "seo", "impact_weight": 7, "label": "Single Primary H1 Tag"},
    "sitemap_present": {"category": "seo", "impact_weight": 6, "label": "XML Sitemap Accessible"},
    "robots_txt_present": {"category": "seo", "impact_weight": 5, "label": "Robots.txt Configured"},
    "canonical_tag_present": {"category": "seo", "impact_weight": 6, "label": "Canonical URL Specified"},
    "clean_url_structure": {"category": "seo", "impact_weight": 5, "label": "Clean Search URLs"},

    # Content & E-E-A-T
    "eeat_author_byline": {"category": "content_eeat", "impact_weight": 7, "label": "Explicit Business Owner / Author Bio"},
    "eeat_editorial_policy": {"category": "content_eeat", "impact_weight": 6, "label": "Service Transparency Policy"},
    "eeat_citations_present": {"category": "content_eeat", "impact_weight": 6, "label": "External Verification / Citations"},
    "readability_score_ok": {"category": "content_eeat", "impact_weight": 7, "label": "Clear Scannable Text Copy"},
    "min_word_count_met": {"category": "content_eeat", "impact_weight": 6, "label": "Substantive Service Description"},
    "eeat_overall_score_ok": {"category": "content_eeat", "impact_weight": 8, "label": "High Overall Credibility Index"},
    "fresh_content_date": {"category": "content_eeat", "impact_weight": 5, "label": "Updated Copyright & Active Hours"},

    # Technical & Performance
    "page_speed_fast": {"category": "technical", "impact_weight": 8, "label": "Fast Initial Load Speed"},
    "mobile_viewport_set": {"category": "technical", "impact_weight": 9, "label": "Responsive Mobile Layout"},
    "no_broken_links": {"category": "technical", "impact_weight": 7, "label": "Zero Broken Internal Links"},
    "no_mixed_content": {"category": "technical", "impact_weight": 8, "label": "No Mixed HTTP/HTTPS Assets"},
    "tech_impact_score_ok": {"category": "technical", "impact_weight": 6, "label": "Clean DOM / Minimal Script Delays"},
    "image_alt_tags_present": {"category": "technical", "impact_weight": 5, "label": "Image ALT Attributes"},
    "favicon_present": {"category": "technical", "impact_weight": 4, "label": "Favicon Configured"},
}