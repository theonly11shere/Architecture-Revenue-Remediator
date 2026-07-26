"""Revenue Readiness Scorer — Configuration"""
import os
from typing import List, Dict, Any, Set

TOTAL_CHECKS: int = 40
CATEGORY_COUNT: int = 5
CATEGORY_NAMES: List[str] = ["trust_signals","conversion_ready","seo_foundation","content_quality","technical_health"]
TIER_NAMES: List[str] = ["free", "paid", "admin"]
DELIVERY_TIME_FREE: str = "10 seconds"
DELIVERY_TIME_PAID: str = "24 hours"
PRICING: Dict[str, int] = {"free": 0, "paid": 149, "roadmap": 299, "retainer": 997}
MAX_PAGES_FREE: int = 8
MAX_PAGES_PAID: int = 30
MIN_PAGES_PER_TEMPLATE_PAID: int = 3
REQUEST_TIMEOUT: int = 15
MAX_DOWNLOAD_SIZE: int = 10 * 1024 * 1024
PLAYWRIGHT_TIMEOUT: int = 30
BLOCKED_PORTS: List[int] = [22, 25, 3306, 5432, 6379, 27017, 3389, 5900]
PRIVATE_IP_RANGES: List[str] = [
    "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16",
    "127.0.0.0/8", "169.254.0.0/16", "0.0.0.0/32",
    "::1/128", "fc00::/7", "fe80::/10",
]
RATE_LIMIT_FREE: str = "10/minute"
RATE_LIMIT_PAID: str = "100/minute"
REDIS_URL: str = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
STRIPE_WEBHOOK_SECRET: str = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
SMTP_HOST: str = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT: int = int(os.environ.get("SMTP_PORT", "465"))
SMTP_USER: str = os.environ.get("SMTP_USER", "")
SMTP_PASS: str = os.environ.get("SMTP_PASS", "")
ALERT_EMAIL: str = os.environ.get("ALERT_EMAIL", "onlyonearpit@gmail.com")
RESEND_API_KEY: str = os.environ.get("RESEND_API_KEY", "")
EMAIL_FROM: str = os.environ.get("EMAIL_FROM", "RRS Alerts <onboarding@resend.dev>")
SESSION_SECRET: str = os.environ.get("SESSION_SECRET", "")
if not SESSION_SECRET:
    import secrets as _secrets
    SESSION_SECRET = _secrets.token_urlsafe(64)
SCAN_PASS_SECRET: str = os.environ.get("SCAN_PASS_SECRET", "")
OWN_DOMAINS: Set[str] = {d.strip().lower() for d in os.environ.get("OWN_DOMAINS", "trilloka.com,www.trilloka.com").split(",") if d.strip()}

# ── NEW: The 6 Unified Score Names ────────────────────────────────────────
SCORE_NAMES: List[str] = [
    "differentiation",
    "trust_credibility",
    "conversion_friction",
    "ai_copy_cliche",
    "tech_stack_impact",
    "revenue_leak",
]

# ── NEW: AI-Generated Copy Detection Patterns ──────────────────────────────
AI_GENERATED_PATTERNS: List[str] = [
    # Hedging / uncertainty patterns common in AI text
    "it is important to note", "it\'s important to note", "worth noting",
    "delve into", "dig deeper", "in conclusion", "in summary",
    "let\'s explore", "let us explore", "we will explore",
    "navigate the", "landscape of", "ever-evolving", "rapidly changing",
    "in today\'s", "in the world of", "in an era of",
    "not only.*but also", "both.*and.*while", "whether you\'re.*or",
    "look no further", "your one-stop", "end-to-end solution",
    "seamless experience", "streamlined process", "robust framework",
    "leverage our", "unlock the power", "harness the power",
    "empowering businesses", "driving innovation", "fostering growth",
    "at the forefront", "pioneering", "groundbreaking",
    "unparalleled", "unmatched", "unrivaled", "best-in-class",
    "tailored solutions", "bespoke solutions", "customized approach",
    "our mission is to", "we pride ourselves on", "committed to delivering",
    "dedicated to providing", "passionate about", "excellence in everything",
    "transform your", "elevate your", "revolutionize your",
    "discover how", "learn why", "find out how",
]

# ── NEW: Tech Stack UX Impact Matrix (framework -> impact score 0-100) ──────
# Higher = better for UX out-of-the-box
TECH_STACK_IMPACT: Dict[str, Dict[str, Any]] = {
    "Next.js": {"ux_score": 88, "seo_score": 92, "speed_score": 85, "notes": "SSR/SSG, excellent Core Web Vitals"},
    "React": {"ux_score": 75, "seo_score": 65, "speed_score": 70, "notes": "Client-side rendering can hurt initial load"},
    "Vue": {"ux_score": 78, "seo_score": 70, "speed_score": 75, "notes": "Lighter than React, good performance"},
    "Angular": {"ux_score": 65, "seo_score": 60, "speed_score": 60, "notes": "Heavy bundle, slower initial load"},
    "Svelte": {"ux_score": 90, "seo_score": 85, "speed_score": 90, "notes": "Compiled, minimal runtime, very fast"},
    "Gatsby": {"ux_score": 85, "seo_score": 90, "speed_score": 85, "notes": "SSG, image optimization built-in"},
    "Shopify": {"ux_score": 82, "seo_score": 80, "speed_score": 78, "notes": "Hosted, CDN included, theme-dependent"},
    "WordPress": {"ux_score": 60, "seo_score": 75, "speed_score": 55, "notes": "Plugin bloat common, needs optimization"},
    "Wix": {"ux_score": 55, "seo_score": 50, "speed_score": 50, "notes": "Limited control, slower TTFB"},
    "Squarespace": {"ux_score": 65, "seo_score": 60, "speed_score": 62, "notes": "Pretty but limited performance tuning"},
    "Webflow": {"ux_score": 78, "seo_score": 75, "speed_score": 80, "notes": "Clean code export, good animations"},
    "Django": {"ux_score": 70, "seo_score": 80, "speed_score": 72, "notes": "Server-rendered, developer-dependent"},
    "Rails": {"ux_score": 68, "seo_score": 78, "speed_score": 70, "notes": "Server-rendered, asset pipeline helps"},
    "Framer": {"ux_score": 80, "seo_score": 70, "speed_score": 75, "notes": "Great animations, export can be heavy"},
    "Bootstrap": {"ux_score": 50, "seo_score": 60, "speed_score": 55, "notes": "Generic look, heavy CSS/JS"},
    "Tailwind": {"ux_score": 85, "seo_score": 80, "speed_score": 88, "notes": "PurgeCSS, minimal bundle, fast"},
    "Unknown / Custom": {"ux_score": 50, "seo_score": 50, "speed_score": 50, "notes": "Unknown impact"},
}

# ── NEW: Revenue Leak Calculation Weights ────────────────────────────────────
REVENUE_LEAK_WEIGHTS: Dict[str, float] = {
    "trust_gap": 0.30,      # Missing trust signals = 30% of leak
    "conversion_gap": 0.35,  # Friction = 35% of leak
    "differentiation_gap": 0.20,  # Looking generic = 20% of leak
    "content_gap": 0.15,     # Weak content = 15% of leak
}

# ── NEW: Competitor Analysis & Admin Delivery ──────────────────────────────
ADMIN_EMAIL: str = os.environ.get("ADMIN_EMAIL", ALERT_EMAIL)
COMPETITOR_SCAN_ENABLED: bool = os.environ.get("COMPETITOR_SCAN_ENABLED", "true").lower() == "true"
MAX_COMPETITORS: int = int(os.environ.get("MAX_COMPETITORS", "3"))
ADMIN_REPORT_BRANDING: str = os.environ.get("ADMIN_REPORT_BRANDING", "Trilloka Revenue Recovery Scanner")
FORWARDABLE_REPORT_FOOTER: str = (
    "Generated by Trilloka RRS | Confidential Revenue Analysis | "
    "This report contains actionable recommendations based on automated scanning."
)
# Feature signatures for competitor gap analysis (by business type)
COMPETITOR_FEATURE_SIGNATURES: Dict[str, Dict[str, List[str]]] = {
    "global": {
        "Trustpilot Widget": [r"trustpilot\.com/widget", r"trustpilot-widget"],
        "Sticky Header/CTA": [r"position:\s*(?:sticky|fixed)", r"sticky-header", r"is-sticky"],
        "Live Chat": [r"intercom", r"zendesk", r"tidio", r"tawk\.to", r"chat-widget"],
        "Email Capture Popup": [r"newsletter", r"subscribe", r"email-signup", r"popup"],
        "Video Content": [r"<video", r"youtube\.com/embed", r"vimeo\.com"],
    },
    "ecommerce": {
        "30-Day Money Back Guarantee": [r"30[- ]day", r"money[- ]back", r"guarantee"],
        "Express Checkout (Apple/Google Pay)": [r"apple pay", r"google pay", r"shop pay"],
        "Free Shipping Threshold": [r"free shipping over", r"ships free", r"free delivery"],
        "Product Reviews Widget": [r"reviews", r"rating", r"stars", r"yotpo", r"loox"],
        "Abandoned Cart Recovery": [r"cart recovery", r"abandoned cart"],
        "Size Guide": [r"size guide", r"size chart", r"fitting"],
    },
    "local_service": {
        "Google Maps Embed": [r"google\.com/maps/embed", r"iframe.*?maps"],
        "Click-to-Call Phone": [r"href=[\"']tel:"],
        "Online Booking System": [r"book now", r"schedule", r"appointment", r"calendly", r"acuity"],
        "Before/After Gallery": [r"before.*after", r"gallery", r"portfolio"],
        "Emergency Service Badge": [r"emergency", r"24/7", r"urgent", r"same day"],
    },
    "restaurant": {
        "Online Reservations": [r"reservation", r"book a table", r"opentable", r"resy"],
        "Full Menu Online": [r"menu", r"view menu", r"full menu"],
        "Dietary Labels": [r"vegan", r"vegetarian", r"gluten-free", r"allergen"],
        "Order Online/Delivery": [r"order online", r"delivery", r"doordash", r"ubereats"],
        "Chef/Team Photos": [r"chef", r"team", r"kitchen", r"staff"],
    },
    "saas": {
        "Free Trial CTA": [r"free trial", r"start free", r"try free"],
        "Pricing Calculator": [r"pricing", r"calculator", r"estimate"],
        "API Documentation": [r"api docs", r"documentation", r"developer"],
        "Security Badges (SOC2)": [r"soc 2", r"soc2", r"gdpr", r"hipaa", r"security"],
        "Integration Logos": [r"integrations", r"connect with", r"works with"],
    },
    "agency": {
        "Case Studies": [r"case stud", r"client story", r"success story"],
        "Awards/Recognition": [r"award", r"recognized", r"featured in", r"top agency"],
        "Process Diagram": [r"process", r"how we work", r"methodology"],
        "Team Bios": [r"team", r"meet the team", r"our people"],
        "Client Logos": [r"clients", r"trusted by", r"worked with"],
    },
    "personal_brand": {
        "Media Appearances": [r"as seen on", r"featured in", r"media", r"press"],
        "Speaking Topics": [r"speak", r"keynote", r"presentation", r"workshop"],
        "Book/Podcast Links": [r"book", r"podcast", r"episode", r"listen"],
        "Coaching Packages": [r"coaching", r"mentorship", r"program", r"package"],
        "Social Proof Counter": [r"followers", r"subscribers", r"students", r"clients served"],
    },
}

# ── NEW: Admin Report Delivery ───────────────────────────────────────────────
ADMIN_REPORT_AUTO_SEND: bool = os.environ.get("ADMIN_REPORT_AUTO_SEND", "true").lower() == "true"
ADMIN_REPORT_INCLUDE_ROADMAP: bool = True
ADMIN_REPORT_INCLUDE_COMPETITOR: bool = True
ADMIN_REPORT_FORMAT: str = os.environ.get("ADMIN_REPORT_FORMAT", "markdown")  # markdown | html | json

TEMPLATE_PATTERNS: Dict[str, str] = {
    r"^/$|^/index\.": "home",
    r"product|shop|item|sku|buy|store": "product",
    r"service|solution|offering|capabilities": "service",
    r"blog|article|news|post|story": "blog",
    r"location|near-me|city|branch|office|find-us": "location",
    r"contact|reach|get-in-touch|help": "contact",
    r"checkout|cart|payment|billing|order": "checkout",
    r"privacy|terms|policy|refund|shipping|legal|disclaimer": "policy",
}

CHECKPOINTS: Dict[str, Dict[str, Any]] = {
    "trust_signals": {
        "weight": 0.25,
        "items": [
            {"name": "SSL Certificate Valid", "weight": 2, "method": "check_ssl_valid"},
            {"name": "Contact Info Visible", "weight": 3, "method": "check_contact"},
            {"name": "About Page Exists", "weight": 2, "method": "check_about"},
            {"name": "Team Photos Real", "weight": 3, "method": "check_team_photos"},
            {"name": "Social Proof", "weight": 3, "method": "check_reviews"},
            {"name": "Privacy Policy", "weight": 2, "method": "check_privacy"},
            {"name": "Terms of Service", "weight": 2, "method": "check_terms"},
            {"name": "Domain Age", "weight": 3, "method": "check_domain_age"},
        ]
    },
    "conversion_ready": {
        "weight": 0.30,
        "items": [
            {"name": "Clear CTA Above Fold", "weight": 4, "method": "check_cta"},
            {"name": "Mobile Responsive (Real Test)", "weight": 5, "method": "check_mobile_real"},
            {"name": "Page Load Speed (Lighthouse)", "weight": 5, "method": "check_speed_lighthouse"},
            {"name": "Booking/Quote System", "weight": 4, "method": "check_booking"},
            {"name": "Phone Number Clickable", "weight": 3, "method": "check_phone"},
            {"name": "Email Capture Form", "weight": 3, "method": "check_email_capture"},
            {"name": "Pricing Visible", "weight": 3, "method": "check_pricing"},
            {"name": "Testimonials Section", "weight": 3, "method": "check_testimonials"},
        ]
    },
    "seo_foundation": {
        "weight": 0.20,
        "items": [
            {"name": "Title Tags Optimized", "weight": 3, "method": "check_title"},
            {"name": "Meta Descriptions", "weight": 3, "method": "check_meta"},
            {"name": "H1 Hierarchy", "weight": 2, "method": "check_h1"},
            {"name": "Image Alt Text", "weight": 2, "method": "check_alt"},
            {"name": "Schema Markup", "weight": 3, "method": "check_schema"},
            {"name": "Internal Linking", "weight": 2, "method": "check_internal_links"},
            {"name": "XML Sitemap", "weight": 2, "method": "check_sitemap"},
            {"name": "Robots.txt", "weight": 1, "method": "check_robots"},
        ]
    },
    "content_quality": {
        "weight": 0.15,
        "items": [
            {"name": "Unique Content", "weight": 3, "method": "check_unique"},
            {"name": "Readability Score", "weight": 4, "method": "check_readability"},
            {"name": "Service Descriptions", "weight": 3, "method": "check_services"},
            {"name": "Blog/Updates", "weight": 2, "method": "check_blog"},
            {"name": "FAQ Section", "weight": 2, "method": "check_faq"},
            {"name": "Local SEO Content", "weight": 2, "method": "check_local"},
        ]
    },
    "technical_health": {
        "weight": 0.10,
        "items": [
            {"name": "No Broken Links", "weight": 3, "method": "check_broken"},
            {"name": "HTTPS Redirects", "weight": 2, "method": "check_redirects"},
            {"name": "Canonical Tags", "weight": 2, "method": "check_canonical"},
            {"name": "Structured Data", "weight": 3, "method": "check_structured"},
            {"name": "Security Headers", "weight": 3, "method": "check_security_headers"},
            {"name": "Favicon Present", "weight": 1, "method": "check_favicon"},
        ]
    }
}

SEVERITY: Dict[str, tuple] = {
    "critical": (0, 34, "Critical", "Your site is losing revenue every day. Immediate action required."),
    "poor": (35, 54, "Poor", "Major gaps exist. Competitors are capturing your leads."),
    "fair": (55, 74, "Fair", "Functional but not competitive. Room for significant improvement."),
    "good": (75, 89, "Good", "Solid foundation. Fine-tuning will unlock growth."),
    "excellent": (90, 100, "Excellent", "Industry-leading. Maintain and optimize."),
}

FUTURE_PREDICTIONS: Dict[str, Dict[int, int]] = {
    "critical": {3: 25, 6: 50, 12: 75},
    "poor": {3: 15, 6: 35, 12: 60},
    "fair": {3: 10, 6: 20, 12: 40},
    "good": {3: 5, 6: 10, 12: 20},
    "excellent": {3: 0, 6: 0, 12: 5},
}

CONTENT_EVIDENCE_CHECKS: List[Dict[str, Any]] = [
    {"name": "Author Byline / Authorship Schema", "weight": 3},
    {"name": "Original Images (not stock-only)", "weight": 3},
    {"name": "First-Hand Experience Language", "weight": 4},
    {"name": "Source Citations / Outbound Authority Links", "weight": 3},
    {"name": "Publication & Last-Modified Dates", "weight": 2},
    {"name": "Organization Info / About Page", "weight": 3},
    {"name": "Templated / Repetitive Passages", "weight": 3},
    {"name": "FAQ & Structured Data Accuracy", "weight": 2},
]

DEFAULT_TRAFFIC: int = 1000
DEFAULT_CONVERSION_RATE: float = 0.02
DEFAULT_AOV: float = 75.0
DEFAULT_PROFIT_MARGIN: float = 0.30
CALCULATOR_LABEL: str = "Illustrative Revenue Exposure — Not Measured Loss."
FREE_REPORT_CTA: str = "Upgrade for full evidence, root cause, and fix steps."
FAILURE_SEVERITY_BY_WEIGHT: Dict[int, str] = {1: "low", 2: "medium", 3: "high", 4: "critical", 5: "critical"}

JS_FRAMEWORK_SIGNATURES: Dict[str, str] = {
    "__NEXT_DATA__": "Next.js", "_next": "Next.js",
    "data-reactroot": "React", "react": "React",
    "vue": "Vue", "__VUE__": "Vue",
    "ng-app": "Angular", "angular": "Angular",
    "data-svelte": "Svelte", "svelte": "Svelte",
    "window.gatsby": "Gatsby", "___GATSBY": "Gatsby",
}

GENERIC_PHRASES: List[str] = [
    "leverage our", "synergy", "digital landscape", "unlock the power",
    "innovative solutions", "passionate about", "driven by excellence",
    "cutting-edge", "next-generation", "holistic approach",
    "best-in-class", "world-class", "industry-leading",
    "transform your", "empower your", "elevate your",
    "seamless experience", "end-to-end", "turnkey solution",
    "scalable platform", "robust framework", "streamlined process",
    "customer-centric", "data-driven", "results-oriented",
    "proven track record", "trusted by", "all-in-one",
    "ecosystem", "bandwidth", "our story", "mission is to",
    "committed to delivering", "dedicated to providing",
    "we pride ourselves", "excellence in everything",
]

TEMPLATE_SIGNATURES: List[tuple] = [
    ("WordPress Astra", "wordpress", ["ast-container", "ast-", "astra-"], 1_200_000),
    ("WordPress Elementor", "wordpress", ["elementor-", "elementor/"], 5_000_000),
    ("WordPress Divi", "wordpress", ["et_pb_", "divi-"], 800_000),
    ("WordPress Avada", "wordpress", ["avada-", "fusion-"], 700_000),
    ("Shopify Dawn", "shopify", ["shopify-section", "shopify-dawn"], 2_000_000),
    ("Shopify Prestige", "shopify", ["prestige-", "shopify-prestige"], 400_000),
    ("Wix", "wix", ["wix-", "static.wixstatic.com"], 3_000_000),
    ("Squarespace", "squarespace", ["squarespace-", "static1.squarespace.com"], 1_500_000),
    ("Webflow", "webflow", ["w-webflow-badge", "webflow-"], 600_000),
    ("Bootstrap", "framework", ["bootstrap", "container-fluid", "row", "col-"], 10_000_000),
    ("Tailwind", "framework", ["tailwind", "bg-", "text-", "flex", "grid-cols-"], 8_000_000),
    ("AI Builder / Generic", "ai", ["ai-generated", "auto-generated", "template-"], 500_000),
]

COMPLAINT_KEYWORDS: tuple = (
    "broken", "not working", "doesn't work", "slow", "scam", "ripoff",
    "terrible", "worst", "avoid", "awful", "useless", "never again",
    "down", "error", "complaint", "bad experience", "unresponsive",
)

SECURITY_HEADERS: List[str] = [
    "Content-Security-Policy", "Strict-Transport-Security", "X-Frame-Options",
    "X-Content-Type-Options", "Referrer-Policy", "Permissions-Policy",
]

# ── FIXED: Added restaurant, case-insensitive matching handled in scraper ─────
BUSINESS_TYPE_KEYWORDS: Dict[str, List[str]] = {
    "ecommerce": ["shop", "store", "cart", "checkout", "product", "buy", "order", "shipping", "payment"],
    "saas": ["signup", "free trial", "demo", "pricing plans", "api", "dashboard", "login", "app"],
    "local_service": ["book now", "schedule", "appointment", "location", "near me", "call us", "visit us", "hours"],
    "restaurant": ["menu", "reservation", "dine", "chef", "cuisine", "restaurant", "book a table", "order online", "delivery", "takeout"],
    "b2b": ["enterprise", "solution", "partners", "case study", "roi", "integration", "consultation"],
    "agency": ["portfolio", "clients", "work", "creative", "design", "marketing", "branding"],
    "personal_brand": ["about me", "my story", "coach", "consultant", "speaker", "author", "podcast"],
}

BUSINESS_TYPE_CHECKS: Dict[str, List[str]] = {
    "ecommerce": ["Add to Cart Button", "Product Reviews", "Secure Checkout Badge", "Return Policy", "Size/Variant Selector"],
    "saas": ["Free Trial CTA", "Feature Comparison Table", "API Documentation Link", "Onboarding Flow", "Changelog"],
    "local_service": ["Google Maps Embed", "Online Booking", "Service Area List", "Before/After Gallery", "Emergency Contact"],
    "restaurant": ["Online Reservations", "Menu PDF/Interactive", "Hours & Location", "Chef/Team Photos", "Dietary Info"],
    "b2b": ["Case Studies", "White Papers", "ROI Calculator", "Integration Partners", "Demo Request"],
    "agency": ["Portfolio Grid", "Client Logos", "Team Bios", "Process Diagram", "Awards/Recognition"],
    "personal_brand": ["Bio Video", "Media Appearances", "Speaking Topics", "Book/Podcast Links", "Coaching Packages"],
}

SCREENSHOT_DIR: str = os.environ.get("SCREENSHOT_DIR", "./screenshots")
VISUAL_TWIN_MIN_SIMILARITY: float = 0.65
LIGHTHOUSE_ENABLED: bool = os.environ.get("LIGHTHOUSE_ENABLED", "true").lower() == "true"
LIGHTHOUSE_TIMEOUT: int = 45

# ── NEW: Social signal sources ───────────────────────────────────────────────
SOCIAL_SIGNAL_SOURCES: List[str] = ["reddit", "trustpilot", "yelp", "google", "news"]

# ── NEW: Form friction thresholds ────────────────────────────────────────────
FORM_FRICTION_THRESHOLDS: Dict[str, Any] = {
    "ideal_fields": 3,
    "acceptable_fields": 6,
    "high_friction_fields": 10,
    "required_penalty": 1.5,  # each required field above ideal adds this
}

def get_total_checks() -> int:
    return sum(len(cfg["items"]) for cfg in CHECKPOINTS.values())

def get_category_check_count(category: str) -> int:
    return len(CHECKPOINTS.get(category, {}).get("items", []))

def get_failure_severity(weight: int) -> str:
    return FAILURE_SEVERITY_BY_WEIGHT.get(weight, "medium")