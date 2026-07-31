from typing import Dict, Any
from app.services.scorer import LeakAnalyzer
from app.core.blueprints import get_blueprint

class CompetitorGapAnalyzer:
    def __init__(self, target_data: dict, competitor_data: dict, tier: str, business_type: str, is_local: bool):
        self.target = target_data
        self.competitor = competitor_data
        self.tier = tier
        self.business_type = business_type
        self.is_local = is_local

    def generate_full_report_data(self) -> Dict[str, Any]:
        # 1. Get the Top Leaks (4 for basic, 10 for pro)
        analyzer = LeakAnalyzer(self.target, self.competitor, self.business_type, self.is_local)
        report_data = analyzer.get_tier_report(self.tier)
        
        # 2. Inject Blueprints into the found leaks
        for leak in report_data["unlocked_leaks"]:
            leak["blueprint_solution"] = get_blueprint(leak["leak_key"], self.business_type)
            
        return report_data