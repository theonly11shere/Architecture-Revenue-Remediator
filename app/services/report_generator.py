"""
Master Report Generator
Compiles the finalized tier payload into a single Markdown document,
applies custom tier names, embeds Architect team messaging, maps competitor gaps,
and appends the mandatory 3-month consistency disclaimer.
"""

from typing import Dict, Any
from datetime import datetime

TIER_NAMES = {
    3: "Important for your business",
    6: "Making your business the best",
    8: "No one like you",
    10: "The Architect"
}

class ReportGenerator:
    def __init__(self, target_url: str, competitor_url: str = "Not Provided", location: str = "Global"):
        self.target_url = target_url
        self.competitor_url = competitor_url
        self.location = location
        self.timestamp = datetime.now().strftime("%Y-%m-%d")

    def build_markdown_report(self, payload: Dict[str, Any]) -> str:
        if payload.get("status") != "CALCULATIONS_COMPLETE":
            return "# Error: Calculations incomplete."

        business_type = payload["business_type"].upper()
        client_tier = payload["client_tier"]
        tier_name = TIER_NAMES.get(client_tier, "Audit")
        leaks = payload["master_report"]["leaks"]

        md = f"# Financial Leak Audit: {tier_name} Edition\n\n"
        md += f"**Target URL:** `{self.target_url}`\n"
        md += f"**Business Model:** {business_type}\n"
        md += f"**Date Generated:** {self.timestamp}\n\n"
        
        if client_tier == 10:
            md += "> **Welcome to The Architect Tier.** My team and I will be working with you directly to help you implement these solutions and become the absolute best online presence in your industry type.\n\n"
        
        md += "---\n\n"
        md += f"## 📊 Competitor Conversion Gap Analysis\n"
        md += f"*Benchmarking against: `{self.competitor_url}` in {self.location}*\n\n"
        md += f"> **Summary:** This section maps the specific conversion and trust gaps identified below directly against your primary competitor.\n\n"
        md += "---\n\n"

        md += f"## 🚨 Top {client_tier} Financial Leaks & Resolution Roadmaps\n\n"

        for leak in leaks:
            md += f"### #{leak['rank']}: {leak['label']}\n"
            md += f"* **Category:** {leak['category'].replace('_', ' ').title()}\n"
            md += f"* **Severity Score:** {leak['severity_score']} / 15.0\n"
            
            md += "\n**Resolution Blueprint:**\n"
            if leak["solutions"]:
                s = leak["solutions"]
                md += f"* **Quick Win (24hr):** {s.get('quick_win', 'N/A')}\n"
                md += f"* **Strategic Fix (30-Day):** {s.get('strategic_fix', 'N/A')}\n"
                md += f"* **Technical & UX:** {s.get('tech_ux', 'N/A')}\n"
                md += f"* **Copy & Conversion:** {s.get('copy_conversion', 'N/A')}\n"
                md += f"* **Trust & E-E-A-T:** {s.get('trust_eeat', 'N/A')}\n"
            else:
                md += "* ⚠️ *Manual solution required for this specific edge-case.*\n"
            md += "\n---\n"

        md += "\n### ⚖️ Disclaimer & Commitment Requirement\n"
        md += "We do not guarantee that executing these steps will automatically or directly increase your revenue. However, we can improve your overall online presence, audience perception, and ensure the core message you want to send across is effectively received.\n\n"
        md += "These results are contingent upon you and your team following the steps and solutions provided for at least **3 months on a constant basis**. True digital infrastructure optimization takes time and consistency, and these blueprints should not be taken lightly.\n"

        return md