#!/usr/bin/env python3
"""CompetitorFinder — Auto-discovers top competitors via DuckDuckGo."""
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, unquote


class CompetitorFinder:
    def __init__(self, user_url: str = ""):
        self.user_domain = self._extract_domain(user_url) if user_url else ""
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        self.ignored_domains = {
            "yelp.com", "tripadvisor.com", "doordash.com", "ubereats.com",
            "grubhub.com", "yellowpages.com", "google.com", "facebook.com",
            "instagram.com", "linkedin.com", "twitter.com", "x.com",
            "amazon.com", "wikipedia.org", "reddit.com", "pinterest.com",
            "youtube.com", "forbes.com", "medium.com", "glassdoor.com",
            "trustpilot.com", "g2.com", "capterra.com", "bbb.org",
            "apnews.com", "bloomberg.com", "cnn.com", "news.ycombinator.com",
        }

    def _extract_domain(self, url: str) -> str:
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        return domain.replace("www.", "")

    def _is_valid_competitor(self, domain: str) -> bool:
        if not domain or domain == self.user_domain:
            return False
        return not any(ignored in domain for ignored in self.ignored_domains)

    def find_competitors(self, business_type: str, location: str = "", niche: str = "", limit: int = 3) -> list:
        physical_types = ["restaurant", "shop", "store", "physical_store", "local_service", "cafe", "bakery", "bar", "salon", "clinic"]
        is_physical = any(pt in business_type.lower() for pt in physical_types) or bool(location and location.strip())

        if is_physical and location:
            query = f"best {business_type} in {location}"
        elif is_physical and not location:
            query = f"top {business_type} store"
        else:
            extra_niche = f" {niche}" if niche else ""
            query = f"best {business_type}{extra_niche} websites"

        search_url = f"https://html.duckduckgo.com/html/?q={requests.utils.quote(query)}"
        competitors = []
        try:
            response = requests.get(search_url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.text, "html.parser")
            for link in soup.find_all("a", class_="result__url"):
                raw_href = link.get("href", "").strip()
                if "/l/?" in raw_href:
                    match = re.search(r"uddg=([^&]+)", raw_href)
                    if match:
                        raw_href = unquote(match.group(1))
                domain = self._extract_domain(raw_href)
                clean_url = f"https://{domain}"
                if self._is_valid_competitor(domain) and clean_url not in competitors:
                    competitors.append(clean_url)
                    if len(competitors) >= limit:
                        break
        except Exception as e:
            print(f"[CompetitorFinder] Error: {e}")

        return competitors