import asyncio
import re
import time
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup


class WebScraper:
    """
    Asynchronous web scraper for the Trilloka Revenue Leak & Audit Scanner.
    Extracts technical, structural, social, and conversion data from a target URL
    to feed directly into scorer.py.
    """

    DEFAULT_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/126.0.0.0 Safari/537.36 AuditScanner/2.0"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }

    SOCIAL_DOMAINS = {
        "facebook": "facebook.com",
        "instagram": "instagram.com",
        "twitter": "twitter.com",
        "x": "x.com",
        "linkedin": "linkedin.com",
        "youtube": "youtube.com",
        "tiktok": "tiktok.com",
    }

    ANALYTICS_PATTERNS = {
        "google_analytics": [r"googletagmanager\.com/gtag/js", r"google-analytics\.com/analytics\.js", r"GA_MEASUREMENT_ID"],
        "google_tag_manager": [r"googletagmanager\.com/gtm\.js"],
        "facebook_pixel": [r"connect\.facebook\.net/.*fbevents\.js", r"fbq\("],
        "hotjar": [r"static\.hotjar\.com"],
        "klaviyo": [r"static\.klaviyo\.com"],
        "hubspot": [r"js\.hs-scripts\.com"],
    }

    def __init__(self, timeout: float = 12.0):
        self.timeout = timeout

    async def scrape(self, url: str) -> Dict[str, Any]:
        """
        Scrapes a target URL and returns a structured dictionary for scorer.py.
        """
        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"

        start_time = time.time()
        
        try:
            async with httpx.AsyncClient(
                headers=self.DEFAULT_HEADERS,
                follow_redirects=True,
                timeout=self.timeout,
                verify=False  # Allows auditing sites with self-signed or invalid SSL without crashing
            ) as client:
                response = await client.get(url)
                load_time_ms = round((time.time() - start_time) * 1000, 2)
                
                html_content = response.text
                status_code = response.status_code
                final_url = str(response.url)
                headers = dict(response.headers)

            # Parse DOM safely with BeautifulSoup
            soup = BeautifulSoup(html_content, "html.parser")

            return {
                "url": final_url,
                "original_url": url,
                "status_code": status_code,
                "is_success": 200 <= status_code < 300,
                "load_time_ms": load_time_ms,
                "ssl_enabled": final_url.startswith("https://"),
                "security_headers": self._extract_security_headers(headers),
                "meta": self._extract_meta_data(soup),
                "headings": self._extract_headings(soup),
                "images": self._extract_image_stats(soup),
                "social_signals": self._extract_social_signals(soup),
                "cta_elements": self._extract_cta_elements(soup),
                "analytics_tags": self._extract_analytics_tags(html_content),
                "schema_markup": self._extract_schema_markup(soup),
                "html_length": len(html_content),
            }

        except Exception as exc:
            # Catch all network & parsing exceptions cleanly
            return self._build_error_response(url, f"Audit crawl failed: {str(exc)}")

    def _extract_meta_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
        title_tag = soup.find("title")
        meta_desc = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", attrs={"property": "og:description"})
        viewport = soup.find("meta", attrs={"name": "viewport"})
        canonical = soup.find("link", attrs={"rel": "canonical"})

        og_title = soup.find("meta", attrs={"property": "og:title"})
        og_image = soup.find("meta", attrs={"property": "og:image"})
        twitter_card = soup.find("meta", attrs={"name": "twitter:card"}) or soup.find("meta", attrs={"property": "twitter:card"})

        # Safe text extraction to prevent AttributeError on empty or nested tags
        title_str = title_tag.get_text(strip=True) if title_tag else None
        
        desc_str = None
        if meta_desc and meta_desc.get("content"):
            desc_str = str(meta_desc["content"]).strip() or None

        return {
            "title": title_str,
            "title_length": len(title_str) if title_str else 0,
            "description": desc_str,
            "description_length": len(desc_str) if desc_str else 0,
            "has_viewport": bool(viewport),
            "canonical_url": canonical.get("href") if canonical and canonical.get("href") else None,
            "has_og_tags": bool(og_title or og_image),
            "has_twitter_card": bool(twitter_card),
        }

    def _extract_headings(self, soup: BeautifulSoup) -> Dict[str, Any]:
        h1s = [h.get_text(strip=True) for h in soup.find_all("h1") if h.get_text(strip=True)]
        h2s = [h.get_text(strip=True) for h in soup.find_all("h2") if h.get_text(strip=True)]
        return {
            "h1_count": len(h1s),
            "h2_count": len(h2s),
            "h1_texts": h1s,
        }

    def _extract_image_stats(self, soup: BeautifulSoup) -> Dict[str, Any]:
        images = soup.find_all("img")
        total_images = len(images)
        missing_alt = sum(1 for img in images if not img.get("alt") or not str(img.get("alt")).strip())
        return {
            "total_images": total_images,
            "missing_alt_count": missing_alt,
            "alt_coverage_pct": round(((total_images - missing_alt) / total_images * 100), 2) if total_images > 0 else 100.0,
        }

    def _extract_social_signals(self, soup: BeautifulSoup) -> Dict[str, Any]:
        found_links = {}
        all_links = [str(a.get("href")) for a in soup.find_all("a", href=True)]

        for platform, domain in self.SOCIAL_DOMAINS.items():
            matching_links = [link for link in all_links if domain in link.lower()]
            found_links[platform] = matching_links[0] if matching_links else None

        active_channels = {k: v for k, v in found_links.items() if v}
        return {
            "detected_links": active_channels,
            "has_social_presence": len(active_channels) > 0,
            "total_social_channels": len(active_channels),
        }

    def _extract_cta_elements(self, soup: BeautifulSoup) -> Dict[str, Any]:
        cta_keywords = re.compile(
            r"(buy|order|get started|book|schedule|contact|subscribe|sign up|try free|demo|cart|checkout)",
            re.IGNORECASE,
        )

        buttons = soup.find_all(["button", "a"])
        matching_ctas = []

        for btn in buttons:
            text = btn.get_text(strip=True)
            if text and cta_keywords.search(text):
                matching_ctas.append(text[:50])

        forms = soup.find_all("form")
        phone_links = [a.get("href") for a in soup.find_all("a", href=True) if str(a.get("href")).startswith("tel:")]

        return {
            "has_cta_buttons": len(matching_ctas) > 0,
            "cta_count": len(matching_ctas),
            "cta_sample_texts": matching_ctas[:5],
            "form_count": len(forms),
            "phone_link_count": len(phone_links),
        }

    def _extract_analytics_tags(self, html_content: str) -> Dict[str, bool]:
        analytics_detected = {}
        for tool, patterns in self.ANALYTICS_PATTERNS.items():
            analytics_detected[tool] = any(re.search(pattern, html_content, re.IGNORECASE) for pattern in patterns)
        return analytics_detected

    def _extract_schema_markup(self, soup: BeautifulSoup) -> Dict[str, Any]:
        json_ld_scripts = soup.find_all("script", attrs={"type": "application/ld+json"})
        return {
            "has_schema": len(json_ld_scripts) > 0,
            "schema_script_count": len(json_ld_scripts),
        }

    def _extract_security_headers(self, headers: Dict[str, str]) -> Dict[str, bool]:
        headers_lower = {k.lower(): v for k, v in headers.items()}
        return {
            "strict_transport_security": "strict-transport-security" in headers_lower,
            "content_security_policy": "content-security-policy" in headers_lower,
            "x_frame_options": "x-frame-options" in headers_lower,
            "x_content_type_options": "x-content-type-options" in headers_lower,
        }

    def _build_error_response(self, url: str, error_msg: str) -> Dict[str, Any]:
        return {
            "url": url,
            "original_url": url,
            "status_code": 0,
            "is_success": False,
            "error": error_msg,
            "load_time_ms": 0,
            "ssl_enabled": url.startswith("https://"),
            "security_headers": {
                "strict_transport_security": False,
                "content_security_policy": False,
                "x_frame_options": False,
                "x_content_type_options": False,
            },
            "meta": {
                "title": None,
                "title_length": 0,
                "description": None,
                "description_length": 0,
                "has_viewport": False,
                "canonical_url": None,
                "has_og_tags": False,
                "has_twitter_card": False,
            },
            "headings": {"h1_count": 0, "h2_count": 0, "h1_texts": []},
            "images": {"total_images": 0, "missing_alt_count": 0, "alt_coverage_pct": 0.0},
            "social_signals": {"detected_links": {}, "has_social_presence": False, "total_social_channels": 0},
            "cta_elements": {"has_cta_buttons": False, "cta_count": 0, "cta_sample_texts": [], "form_count": 0, "phone_link_count": 0},
            "analytics_tags": {tool: False for tool in self.ANALYTICS_PATTERNS},
            "schema_markup": {"has_schema": False, "schema_script_count": 0},
            "html_length": 0,
        }


# Compatibility wrappers matching main.py imports
async def scrape_website(url: str) -> Dict[str, Any]:
    scraper = WebScraper()
    return await scraper.scrape(url)

async def fetch_and_extract(url: str) -> Dict[str, Any]:
    scraper = WebScraper()
    return await scraper.scrape(url)