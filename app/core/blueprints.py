import random

MASTER_BLUEPRINT_LIBRARY = {
    "mobile_sticky_cta": {
        "variations": [
            {"angle": "ecommerce", "solution": "**Action Plan:** Implement a persistent bottom-bar sticky CTA on mobile containing the product price and checkout button."},
            {"angle": "local_service", "solution": "**Action Plan:** Lock a 'Tap-to-Call' button to the bottom of the mobile screen. Format as `tel:+1-your-number`."},
            {"angle": "saas_b2b", "solution": "**Action Plan:** Add a mobile sticky banner offering a low-friction action, like 'Book a Demo' or 'Email me this guide.'"}
        ]
    },
    "exit_intent_capture": {
        "variations": [
            {"angle": "ecommerce", "solution": "**Action Plan:** Set up a pop-up offering a 10% discount when their mouse leaves the window."},
            {"angle": "local_service", "solution": "**Action Plan:** Trigger an exit popup offering a 'Free Hiring Guide' to capture the lead."},
            {"angle": "saas_b2b", "solution": "**Action Plan:** Catch their exit with an invite to a pre-recorded, on-demand webinar."}
        ]
    },
    "social_proof_above_fold": {
        "variations": [
            {"angle": "ecommerce", "solution": "**Action Plan:** Add a dynamic widget showing real-time recent purchases."},
            {"angle": "local_service", "solution": "**Action Plan:** Embed a live feed of your 5-star Google Business Profile reviews directly under your main headline."},
            {"angle": "saas_b2b", "solution": "**Action Plan:** Place a banner below your CTA featuring the logos of the top 5 biggest companies that use your service."}
        ]
    },
    "no_click_to_call": {
        "variations": [
            {"angle": "local_service", "solution": "**Action Plan:** Ensure your phone number in the header and footer uses an HTML link formatted as `tel:+15555555555`. This allows mobile users to tap and instantly dial your office."},
            {"angle": "ecommerce", "solution": "**Action Plan:** If phone support drives high-ticket sales, add a floating phone icon next to your cart icon for mobile visitors."},
            {"angle": "saas_b2b", "solution": "**Action Plan:** For enterprise software, replace raw phone numbers with a clean 'Schedule a Quick Call' calendar embed widget."}
        ]
    },
    "local_seo_schema": {
        "variations": [
            {"angle": "local_service", "solution": "**Action Plan:** Add LocalBusiness JSON-LD Schema markup to your site header. This tells Google your exact address, operating hours, and service coordinates to win local Map Pack rankings."},
            {"angle": "ecommerce", "solution": "**Action Plan:** Implement Organization and Product Schema so Google displays your ratings, price, and stock status directly in search results."},
            {"angle": "saas_b2b", "solution": "**Action Plan:** Deploy SoftwareApplication Schema markup to help search engines understand your product category and features."}
        ]
    },
    "lcp_speed_lag": {
        "variations": [
            {"angle": "ecommerce", "solution": "**Action Plan:** Compress your above-the-fold product images into WebP format and lazy-load all images below the fold. Every 1-second delay drops checkouts by 7%."},
            {"angle": "local_service", "solution": "**Action Plan:** Move your site to a faster managed host and disable heavy, unused WordPress plugins that block mobile rendering."},
            {"angle": "saas_b2b", "solution": "**Action Plan:** Implement a Content Delivery Network (CDN) like Cloudflare to cache static assets and speed up global delivery times."}
        ]
    },
    "missing_ssl": {
        "variations": [
            {"angle": "ecommerce", "solution": "**Action Plan:** Install an active SSL certificate immediately and force HTTPS. Browsers showing 'Not Secure' on checkout pages instantly destroy buyer trust."},
            {"angle": "local_service", "solution": "**Action Plan:** Ensure your contact form submission page runs securely over HTTPS so user data cannot be intercepted."},
            {"angle": "saas_b2b", "solution": "**Action Plan:** Add recognized security trust seals (e.g., SSL provider badges, SOC2 notices) next to your login and registration buttons."}
        ]
    },
    "broken_meta": {
        "variations": [
            {"angle": "ecommerce", "solution": "**Action Plan:** Update your OpenGraph (OG) image and description tags. When users share your product links on WhatsApp or iMessage, they currently show a broken preview."},
            {"angle": "local_service", "solution": "**Action Plan:** Write custom meta titles and descriptions for every core service page containing your city name and primary offer."},
            {"angle": "saas_b2b", "solution": "**Action Plan:** Fix your Twitter and LinkedIn card meta tags so shared blog posts display high-converting custom banners instead of random stock images."}
        ]
    },
    "no_secondary_cta": {
        "variations": [
            {"angle": "ecommerce", "solution": "**Action Plan:** Add an 'Add to Wishlist' or 'Email me when on sale' button for visitors who aren't ready to buy today."},
            {"angle": "local_service", "solution": "**Action Plan:** Provide a low-commitment secondary CTA like 'Get a Free Instant Estimate' alongside your main 'Book Now' button."},
            {"angle": "saas_b2b", "solution": "**Action Plan:** Offer a 'Free Self-Guided Tour' or documentation link for enterprise leads who want to research before talking to sales."}
        ]
    },
    "competitor_feature_gap": {
        "variations": [
            {"angle": "ecommerce", "solution": "**Action Plan:** Your competitor utilizes interactive feature tools (like a quiz or product finder) that keep users engaged longer. Implement a simple product filter widget."},
            {"angle": "local_service", "solution": "**Action Plan:** Your competitor features an online booking portal directly on their homepage. Add a tool like Calendly or Acuity to let clients book instantly."},
            {"angle": "saas_b2b", "solution": "**Action Plan:** Add an interactive ROI calculator to your landing page to match your competitor's feature set and prove value instantly."}
        ]
    }
}

def get_blueprint(leak_key: str, business_type: str = "local_service") -> str:
    """Fetches the right solution based on the business type, or picks randomly."""
    if leak_key not in MASTER_BLUEPRINT_LIBRARY:
        return "**Action Plan:** Consult your developer to implement this industry standard feature."
        
    variations = MASTER_BLUEPRINT_LIBRARY[leak_key]["variations"]
    for var in variations:
        if var["angle"] == business_type:
            return var["solution"]
            
    return random.choice(variations)["solution"]