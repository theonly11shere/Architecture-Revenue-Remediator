#!/usr/bin/env python3
"""Email Sender for RRS Reports — sends free, paid, roadmap, admin, and forwardable reports via SMTP.

USAGE:
    from reporter import ReportGenerator
    from email_sender import ReportEmailer

    # After building your ReportGenerator instance...
    emailer = ReportEmailer()
    result = emailer.send_forwardable_report(report_generator, "customer@example.com")
    print(result)

ENVIRONMENT VARIABLES (optional):
    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, FROM_EMAIL

If SMTP is not configured, emails print to the console in "test mode" so you
never lose a report while debugging.
"""
import os
import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Any, Dict, List, Optional
from datetime import datetime

# Optional: pip install markdown for richer HTML conversion
try:
    import markdown
    HAS_MARKDOWN = True
except ImportError:
    HAS_MARKDOWN = False


class ReportEmailer:
    """Sends RRS reports via SMTP with rich HTML formatting."""

    def __init__(
        self,
        smtp_host: Optional[str] = None,
        smtp_port: Optional[int] = None,
        smtp_user: Optional[str] = None,
        smtp_password: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: str = "RRS Report Bot",
    ):
        self.smtp_host = smtp_host or os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = smtp_port or int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = smtp_user or os.getenv("SMTP_USER")
        self.smtp_password = smtp_password or os.getenv("SMTP_PASSWORD")
        self.from_email = from_email or os.getenv("FROM_EMAIL", self.smtp_user or "noreply@rrs.local")
        self.from_name = from_name

    # ──────────────────────────────────────────────────────────────────
    #  Markdown → HTML helpers
    # ──────────────────────────────────────────────────────────────────

    def _md_to_html(self, md_text: str) -> str:
        """Convert markdown report to HTML. Falls back to simple regex if `markdown` not installed."""
        if HAS_MARKDOWN:
            return markdown.markdown(md_text, extensions=["tables", "fenced_code"])

        # Simple fallback parser
        lines = md_text.split("\n")
        html_lines: List[str] = []
        in_list = False

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("# "):
                if in_list:
                    html_lines.append("</ul>")
                    in_list = False
                html_lines.append(f"<h1>{stripped[2:]}</h1>")
            elif stripped.startswith("## "):
                if in_list:
                    html_lines.append("</ul>")
                    in_list = False
                html_lines.append(f"<h2>{stripped[3:]}</h2>")
            elif stripped.startswith("### "):
                if in_list:
                    html_lines.append("</ul>")
                    in_list = False
                html_lines.append(f"<h3>{stripped[4:]}</h3>")
            elif stripped.startswith("- "):
                if not in_list:
                    html_lines.append("<ul>")
                    in_list = True
                html_lines.append(f"<li>{stripped[2:]}</li>")
            elif stripped == "---":
                html_lines.append("<hr>")
            else:
                if in_list:
                    html_lines.append("</ul>")
                    in_list = False
                if stripped:
                    html_lines.append(f"<p>{stripped}</p>")
                else:
                    html_lines.append("<br>")

        if in_list:
            html_lines.append("</ul>")
        return "\n".join(html_lines)

    def _build_html_wrapper(self, title: str, body_html: str) -> str:
        """Wraps body HTML in a clean, responsive email template."""
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
body {{ font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #2c3e50; max-width: 720px; margin: 0 auto; padding: 24px; background: #f8f9fa; }}
.container {{ background: #fff; padding: 32px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }}
h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 12px; font-size: 24px; }}
h2 {{ color: #34495e; margin-top: 32px; font-size: 20px; border-left: 4px solid #3498db; padding-left: 12px; }}
h3 {{ color: #7f8c8d; font-size: 16px; margin-top: 24px; }}
table {{ border-collapse: collapse; width: 100%; margin: 16px 0; font-size: 14px; }}
th, td {{ border: 1px solid #e1e4e8; padding: 10px 12px; text-align: left; }}
th {{ background: #3498db; color: #fff; font-weight: 600; }}
tr:nth-child(even) {{ background: #f6f8fa; }}
ul {{ margin: 8px 0; padding-left: 20px; }}
li {{ margin: 4px 0; }}
.score-excellent {{ color: #27ae60; font-weight: bold; }}
.score-good {{ color: #2ecc71; font-weight: bold; }}
.score-fair {{ color: #f39c12; font-weight: bold; }}
.score-poor {{ color: #e67e22; font-weight: bold; }}
.score-critical {{ color: #e74c3c; font-weight: bold; }}
.cta {{ display: inline-block; margin-top: 24px; padding: 12px 24px; background: #3498db; color: #fff; text-decoration: none; border-radius: 4px; font-weight: 600; }}
.footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #e1e4e8; font-size: 12px; color: #95a5a6; text-align: center; }}
</style>
</head>
<body>
<div class="container">
{body_html}
<div class="footer">
  Generated by RRS Report Generator &bull; {datetime.now().strftime("%Y-%m-%d %H:%M")}
</div>
</div>
</body>
</html>"""

    # ──────────────────────────────────────────────────────────────────
    #  Core send logic
    # ──────────────────────────────────────────────────────────────────

    def _send(self, to_email: str, subject: str, html_body: str, text_body: str = "") -> Dict[str, Any]:
        """Dispatch email via SMTP or console fallback."""
        missing = [k for k, v in {
            "SMTP_USER": self.smtp_user,
            "SMTP_PASSWORD": self.smtp_password,
            "FROM_EMAIL": self.from_email,
        }.items() if not v]

        if missing:
            # Console test mode — never silently drops a report
            print("\n" + "=" * 70)
            print("  EMAIL TEST MODE — SMTP not fully configured")
            print(f"  Missing: {', '.join(missing)}")
            print("=" * 70)
            print(f"  To:       {to_email}")
            print(f"  Subject:  {subject}")
            print(f"  From:     {self.from_name} <{self.from_email}>")
            print("-" * 70)
            print(text_body or html_body)
            print("=" * 70 + "\n")
            return {"success": True, "mode": "console", "to": to_email, "missing_config": missing}

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{self.from_name} <{self.from_email}>"
        msg["To"] = to_email

        msg.attach(MIMEText(text_body, "plain", _charset="utf-8"))
        msg.attach(MIMEText(html_body, "html", _charset="utf-8"))

        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=30) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.from_email, [to_email], msg.as_string())
            return {"success": True, "mode": "smtp", "to": to_email, "host": self.smtp_host}
        except Exception as e:
            return {"success": False, "error": str(e), "to": to_email}

    # ──────────────────────────────────────────────────────────────────
    #  Public API — one method per report tier
    # ──────────────────────────────────────────────────────────────────

    def send_free_report(self, report_generator, to_email: str) -> Dict[str, Any]:
        """Send the free-tier summary (lightweight HTML)."""
        free = report_generator.generate_free()
        html = self._render_free_html(free)
        full_html = self._build_html_wrapper("Your Free Revenue Readiness Scan", html)
        subject = f"Revenue Readiness Scan — {report_generator.url}"
        text = f"Free scan for {report_generator.url}. Readiness: {free.get('scores', {}).get('readiness_score', 0)}/100"
        return self._send(to_email, subject, full_html, text)

    def send_paid_report(self, report_generator, to_email: str) -> Dict[str, Any]:
        """Send the paid-tier report with fix steps."""
        paid = report_generator.generate_paid()
        html = self._render_paid_html(paid)
        full_html = self._build_html_wrapper("Your Full Revenue Readiness Report", html)
        subject = f"Full Revenue Analysis — {report_generator.url}"
        text = f"Paid report for {report_generator.url}. See HTML version for fix steps."
        return self._send(to_email, subject, full_html, text)

    def send_roadmap_report(self, report_generator, to_email: str) -> Dict[str, Any]:
        """Send the week-by-week 1-month roadmap."""
        roadmap = report_generator.generate_roadmap()
        html = self._render_roadmap_html(roadmap)
        full_html = self._build_html_wrapper("Your 1-Month Revenue Fix Roadmap", html)
        subject = f"1-Month Fix Roadmap — {report_generator.url}"
        text = f"Roadmap for {report_generator.url}. See HTML version for weekly tasks."
        return self._send(to_email, subject, full_html, text)

    def send_admin_report(self, report_generator, to_email: str) -> Dict[str, Any]:
        """Send the full admin dump (HTML summary + JSON attachment concept)."""
        admin = report_generator.generate_admin()
        html = self._render_admin_html(admin)
        full_html = self._build_html_wrapper("[ADMIN] Full Revenue Report", html)
        subject = f"[ADMIN] Revenue Readiness — {report_generator.url}"
        text = json.dumps(admin, indent=2, default=str)[:6000]
        return self._send(to_email, subject, full_html, text)

    def send_forwardable_report(self, report_generator, to_email: str) -> Dict[str, Any]:
        """Send the polished markdown report converted to HTML."""
        md = report_generator.generate_forwardable_report()
        html = self._md_to_html(md)
        full_html = self._build_html_wrapper("Revenue Readiness Analysis", html)
        subject = f"Revenue Readiness Analysis — {report_generator.url}"
        return self._send(to_email, subject, full_html, md)

    # ──────────────────────────────────────────────────────────────────
    #  HTML renderers for each report type
    # ──────────────────────────────────────────────────────────────────

    def _render_free_html(self, free: Dict[str, Any]) -> str:
        scores = free.get("six_scores", {})
        severity = free.get("severity", {})
        html = f"""
        <h1>Revenue Readiness Scan</h1>
        <p><strong>URL:</strong> {free.get('url', 'N/A')}<br>
        <strong>Status:</strong> <span class="score-{severity.get('key', 'unknown')}">{severity.get('label', 'Unknown')}</span></p>
        <p>{severity.get('desc', '')}</p>
        <h2>6 Unified Scores</h2>
        <table>
        <tr><th>Dimension</th><th>Score</th><th>Status</th></tr>
        """
        for name, data in scores.items():
            html += f"""<tr>
                <td>{data.get('label', name)}</td>
                <td>{data.get('score', 0)}/100</td>
                <td class="score-{data.get('status', 'unknown')}">{data.get('status', 'unknown').title()}</td>
            </tr>"""
        html += "</table>"

        teaser = free.get("revenue_exposure_teaser", {})
        cons = teaser.get("conservative_scenario", {})
        html += f"""
        <h2>Revenue Exposure (Conservative)</h2>
        <p>Monthly Revenue: <strong>${cons.get('monthly_revenue', 0):,.2f}</strong><br>
        Monthly Profit: <strong>${cons.get('monthly_profit', 0):,.2f}</strong><br>
        Annual Exposure: <strong>${cons.get('annual_exposure', 0):,.2f}</strong></p>
        <p style="color:#7f8c8d;font-size:12px;">{teaser.get('assumptions_banner', '')}</p>
        """

        failures = free.get("visible_failures", [])
        if failures:
            html += "<h2>Top Issues Found</h2><ul>"
            for f in failures:
                html += f"<li><strong>[{f.get('severity', '').upper()}]</strong> {f.get('item', '')}</li>"
            html += "</ul>"

        html += f"<p style='margin-top:24px;'><em>{free.get('upgrade_cta', '')}</em></p>"
        return html

    def _render_paid_html(self, paid: Dict[str, Any]) -> str:
        html = self._render_free_html(paid)
        fix_steps = paid.get("fix_steps", [])
        if fix_steps:
            html += "<h2>Recommended Fix Steps</h2>"
            for f in fix_steps[:10]:
                html += f"<h3>{f.get('item', '')} <span style='font-size:12px;color:#e74c3c;'>[{f.get('severity', '').upper()}]</span></h3><ul>"
                for step in f.get("fix_steps", []):
                    html += f"<li>{step}</li>"
                html += "</ul>"
        return html

    def _render_roadmap_html(self, roadmap: Dict[str, Any]) -> str:
        html = f"""
        <h1>1-Month Fix Roadmap</h1>
        <p><strong>URL:</strong> {roadmap.get('url', 'N/A')}</p>
        """
        for week in roadmap.get("roadmap", []):
            html += f"""
            <h2>{week.get('week', '')}: {week.get('focus', '')}</h2>
            <ul>
            """
            for item in week.get("items", []):
                html += f"<li><strong>[{item.get('severity', '').upper()}]</strong> {item.get('item', '')}</li>"
                for step in item.get("steps", []):
                    html += f"<li style='margin-left:20px;list-style-type:circle;'>→ {step}</li>"
            html += "</ul>"
        return html

    def _six_score_status(self, value: int) -> str:
        if value >= 80: return "excellent"
        if value >= 60: return "good"
        if value >= 40: return "fair"
        if value >= 20: return "poor"
        return "critical"

    def _six_score_status(self, value: int) -> str:
        if value >= 80: return "excellent"
        if value >= 60: return "good"
        if value >= 40: return "fair"
        if value >= 20: return "poor"
        return "critical"

    def _get_score_status(self, name: str, value: int) -> str:
        """Returns status label, handling badness scores (higher=worse) correctly."""
        badness = {"ai_copy_cliche", "revenue_leak"}
        if name in badness:
            if value >= 80: return "critical"
            if value >= 60: return "poor"
            if value >= 40: return "fair"
            if value >= 20: return "good"
            return "excellent"
        # Goodness scores (higher=better)
        if value >= 80: return "excellent"
        if value >= 60: return "good"
        if value >= 40: return "fair"
        if value >= 20: return "poor"
        return "critical"

    def _render_admin_html(self, admin: Dict[str, Any]) -> str:
        scores = admin.get("six_scores", {})
        html = f"""
        <h1>Admin Report</h1>
        <p><strong>URL:</strong> {admin.get('url', 'N/A')}<br>
        <strong>Scan Quality:</strong> {admin.get('scan_quality', 'unknown')}<br>
        <strong>Readiness:</strong> {admin.get('scores', {}).get('readiness_score', 0)}/100</p>

        <h2>6 Unified Scores</h2>
        <table>
        <tr><th>Dimension</th><th>Score</th><th>Status</th></tr>
        """
        for name, val in scores.items():
            status = self._get_score_status(name, val)
            html += f'<tr><td>{name.replace("_", " ").title()}</td><td>{val}/100</td><td class="score-{status}">{status.title()}</td></tr>'
        html += "</table>"

        leak = admin.get("revenue_leak_estimate", {})
        html += f"""
        <h2>Revenue Leak Estimate</h2>
        <table>
        <tr><th>Metric</th><th>Value</th></tr>
        <tr><td>Current Monthly Revenue</td><td>${leak.get('current_monthly_revenue', 0):,.2f}</td></tr>
        <tr><td>Potential Monthly Revenue</td><td>${leak.get('potential_monthly_revenue', 0):,.2f}</td></tr>
        <tr><td>Monthly Leak</td><td>${leak.get('monthly_leak_estimate', 0):,.2f}</td></tr>
        <tr><td>Annual Leak</td><td>${leak.get('annual_leak_estimate', 0):,.2f}</td></tr>
        </table>
        """

        # Competitor Gap Analysis
        comp = admin.get("competitor_analysis", {})
        if comp and comp.get("competitors"):
            html += f"""
            <h2>Competitor Gap Analysis</h2>
            <p><strong>Competitors analyzed:</strong> {comp.get('competitor_count', 0)}<br>
            <strong>Gap score:</strong> {comp.get('gap_score', 0)}/100</p>
            """
            if comp.get("aggregate_missing_features"):
                html += "<p><strong>Features your competitors have that you may be missing:</strong></p><ul>"
                for feat in comp["aggregate_missing_features"]:
                    html += f"<li>{feat}</li>"
                html += "</ul>"
            for c in comp.get("competitors", []):
                html += f"<h3>vs. {c.get('domain', 'Unknown')}</h3>"
                shared = c.get("shared_with_user", [])
                missing = c.get("user_missing", [])
                if shared:
                    html += f"<p><strong>You both have:</strong> {', '.join(shared)}</p>"
                if missing:
                    html += f"<p style='color:#e74c3c;'><strong>You're missing:</strong> {', '.join(missing)}</p>"
                else:
                    html += "<p style='color:#27ae60;'>You match or exceed this competitor.</p>"
        else:
            html += "<h2>Competitor Gap Analysis</h2><p>No competitor URLs provided for this scan.</p>"

        # 1-Month Fix Roadmap
        html += "<h2>1-Month Fix Roadmap</h2>"
        html += '''<p style="background:#fff3cd;padding:12px;border-left:4px solid #f39c12;">
        <strong>💡 Note:</strong> These are template recommendations. Customize the steps for each client.
        </p>'''

        expected_weeks = [
            ("Week 1", "Stop the bleeding — critical revenue blockers first"),
            ("Week 2", "Build trust and credibility — close the confidence gap"),
            ("Week 3", "Content depth & differentiation — stand out from competitors"),
            ("Week 4", "Polish, speed, and measurement — optimize and track"),
        ]
        roadmap_data = {w.get("week", ""): w for w in admin.get("roadmap", [])}

        for week_name, default_focus in expected_weeks:
            week = roadmap_data.get(week_name)
            if week:
                focus = week.get("focus", default_focus)
                html += f"<h3>{week_name}: {focus}</h3><ul>"
                for item in week.get("items", []):
                    html += f"<li><strong>[{item.get('severity', '').upper()}]</strong> {item.get('item', '')}</li>"
                    for step in item.get("steps", []):
                        html += f"<li style='margin-left:20px;list-style-type:circle;'>→ {step}</li>"
                html += "</ul>"
            else:
                html += f"<h3>{week_name}: {default_focus}</h3><p>No items assigned for this week.</p>"

        # All Checkpoints
        checkpoints = admin.get("all_checkpoints", {})
        if checkpoints:
            html += "<h2>All Checkpoints</h2>"
            for cat, items in checkpoints.items():
                html += f"<h3>{cat.title()}</h3><ul>"
                if isinstance(items, dict):
                    for k, v in items.items():
                        status_icon = "✅" if v else "❌"
                        html += f"<li>{status_icon} <strong>{k}:</strong> {v}</li>"
                html += "</ul>"

        # Professional Footer
        html += f"""
        <div class="footer">
        <hr>
        <p><strong>Generated by Trilloka RRS</strong> | Confidential Revenue Analysis</p>
        <p>This report contains actionable recommendations based on automated scanning.</p>
        <p>Scan ID: {admin.get('timestamp', 'N/A')} | Domain: {admin.get('url', 'N/A')}</p>
        </div>
        """
        return html