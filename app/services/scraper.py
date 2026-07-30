import requests
from bs4 import BeautifulSoup
import re
from typing import Dict, Any

class WebsiteScraper:
    @staticmethod
    def scrape_url(url: str) -> Dict[str, Any]:
        """
        Scrapes a target website and extracts structural, trust, 
        and conversion features to evaluate against revenue leaks.
        """
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url

        features = {
            "mobile_sticky_cta": False,
            "exit_intent_capture": False,
            "social_proof_above_fold": False,
            "no_click_to_call": True,
            "local_seo_schema": False,
            "lcp_speed_lag": False,
            "missing_ssl": not url.startswith("https://"),
            "broken_meta": True,
            "no_secondary_cta": True,
            "competitor_feature_gap": False
        }

        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            response = requests.get(url, headers=headers, timeout=10)
            html_content = response.text
            soup = BeautifulSoup(html_content, 'html.parser')

            # 1. Check for Click-to-Call (tel: links)
            tel_links = soup.find_all('a', href=re.compile(r'^tel:'))
            if tel_links:
                features["no_click_to_call"] = False

            # 2. Check for Local Business / Organization JSON-LD Schema
            json_ld_tags = soup.find_all('script', type='application/ld+json')
            for tag in json_ld_tags:
                text_content = tag.string or ""
                if any(schema_type in text_content for schema_type in ["LocalBusiness", "Organization", "Restaurant", "Store", "Service"]):
                    features["local_seo_schema"] = True
                    break

            # 3. Check for Above-the-Fold Social Proof
            body_text = soup.get_text().lower()
            social_proof_keywords = ["review", "testimonial", "stars", "rated", "trusted by", "clients", "customer"]
            if any(kw in body_text[:2500] for kw in social_proof_keywords):
                features["social_proof_above_fold"] = True

            # 4. Check for OpenGraph Meta Tags
            og_title = soup.find('meta', property='og:title')
            og_image = soup.find('meta', property='og:image')
            if og_title and og_image:
                features["broken_meta"] = False

            # 5. Check for Secondary Call-to-Action
            buttons = soup.find_all(['button', 'a'], class_=re.compile(r'btn|button|cta|action|order|book', re.I))
            if len(buttons) > 1:
                features["no_secondary_cta"] = False

            # 6. Heuristic check for Exit-Intent or Mobile Sticky CTA
            script_text = "".join([s.get_text() for s in soup.find_all('script')])
            if any(term in script_text.lower() for term in ["exit", "ouibounce", "popup", "modal", "lead-capture"]):
                features["exit_intent_capture"] = True

            if any(term in html_content.lower() for term in ["sticky", "fixed-bottom", "floating-cta"]):
                features["mobile_sticky_cta"] = True

        except Exception as e:
            print(f"Error scraping target URL {url}: {e}")

        return features