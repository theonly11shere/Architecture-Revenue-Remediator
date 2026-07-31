from bs4 import BeautifulSoup


class ExternalScorer:
  """Analyzes raw scraped page data and external metrics to compute

  real-time audit checkpoint statuses and a dynamic score.
  """

  def __init__(self):
    pass

  def enhance_checkpoint_results(self, raw_results: dict, target_url: str):
    """Parses HTML content from the scraper and calculates checkpoint metrics."""
    html_content = raw_results.get("html", "")
    soup = BeautifulSoup(html_content, "html.parser")

    # 1. Perform actual checks on the scraped DOM
    has_viewport = bool(soup.find("meta", attrs={"name": "viewport"}))
    has_analytics = any(
        tracker in html_content.lower()
        for tracker in ["google-analytics", "gtag.js", "gtm.js", "segment", "fbq"]
    )
    has_ssl = target_url.startswith("https")
    has_form = len(soup.find_all("form")) > 0
    
    # Check for sticky CTAs or chat widgets based on common class/id patterns
    has_sticky_cta = bool(
        soup.find(
            class_=lambda c: c
            and any(
                term in c.lower()
                for term in ["sticky", "fixed-bottom", "floating", "banner-cta"]
            )
        )
    )

    # 2. Compute dynamic score based on detected elements instead of a static number
    base_score = 40
    if has_viewport:
      base_score += 15
    if has_analytics:
      base_score += 15
    if has_ssl:
      base_score += 15
    if has_form:
      base_score += 10
    if has_sticky_cta:
      base_score += 5

    final_score = min(base_score, 100)

    # 3. Structure the payload required by the SolutionBlueprintEngine
    return {
        "url": target_url,
        "overall_score": final_score,
        "checkpoints": {
            "mobile_responsive_meta": has_viewport,
            "analytics_installed": has_analytics,
            "ssl_secure": has_ssl,
            "lead_capture_form": has_form,
            "mobile_sticky_cta": has_sticky_cta,
        },
        "raw_title": raw_results.get("title", ""),
        "text_length": raw_results.get("text_length", 0),
        "status": raw_results.get("status", "success"),
        "error": raw_results.get("error", None),
    }