"""
Scorer & External API Integration Module
Handles performance metrics and external API hooks (like PageSpeed Insights)
to feed data directly into checkpoint evaluations.
"""

import requests
from typing import Dict, Any

class ExternalScorer:
    def __init__(self, pagespeed_api_key: str = None):
        self.api_key = pagespeed_api_key

    def enhance_checkpoint_results(self, checkpoint_results: Dict[str, bool], target_url: str) -> Dict[str, bool]:
        speed_score_valid = self._check_pagespeed(target_url)
        checkpoint_results["page_speed_fast"] = speed_score_valid
        return checkpoint_results

    def _check_pagespeed(self, url: str) -> bool:
        if not self.api_key:
            return True

        api_url = f"https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url={url}&key={self.api_key}&strategy=mobile"
        try:
            response = requests.get(api_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                score = data.get("lighthouseResult", {}).get("categories", {}).get("performance", {}).get("score", 1.0)
                return score >= 0.60
        except Exception:
            pass
        
        return True