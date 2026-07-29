#!/usr/bin/env python3
"""Quick test to verify your SMTP email setup is working."""
import os
from email_sender import ReportEmailer

# Show what we detected
print("=" * 60)
print("RRS Email Sender — Connection Test")
print("=" * 60)

host = os.getenv("SMTP_HOST", "NOT SET")
port = os.getenv("SMTP_PORT", "NOT SET")
user = os.getenv("SMTP_USER", "NOT SET")
frm  = os.getenv("FROM_EMAIL", "NOT SET")
pw   = "SET" if os.getenv("SMTP_PASSWORD") else "NOT SET"

print(f"SMTP_HOST:     {host}")
print(f"SMTP_PORT:     {port}")
print(f"SMTP_USER:     {user}")
print(f"FROM_EMAIL:    {frm}")
print(f"SMTP_PASSWORD: {pw}")
print("=" * 60)

# Prompt for recipient
recipient = input("\nEnter the email address to send a test to: ").strip()
if not recipient:
    print("No email entered. Exiting.")
    exit(1)

# Build a fake minimal report generator for testing
class FakeReportGenerator:
    url = "https://example.com"
    def generate_free(self):
        return {
            "url": self.url,
            "six_scores": {
                "differentiation": {"score": 72, "label": "Differentiation", "status": "good"},
                "trust_credibility": {"score": 65, "label": "Trust & Credibility", "status": "good"},
                "conversion_friction": {"score": 45, "label": "Conversion Friction", "status": "fair"},
                "ai_copy_cliche": {"score": 80, "label": "AI Copy & Cliché", "status": "excellent"},
                "tech_stack_impact": {"score": 55, "label": "Tech Stack Impact", "status": "fair"},
                "revenue_leak": {"score": 30, "label": "Revenue Leak", "status": "poor"},
            },
            "severity": {"key": "warning", "label": "Needs Work", "desc": "Test scan."},
            "revenue_exposure_teaser": {
                "conservative_scenario": {
                    "monthly_revenue": 12500.00,
                    "monthly_profit": 3750.00,
                    "annual_exposure": 45000.00,
                },
                "assumptions_banner": "Test values.",
            },
            "visible_failures": [
                {"severity": "high", "item": "No clear CTA above the fold"},
                {"severity": "medium", "item": "Page load speed > 3s"},
            ],
            "upgrade_cta": "Upgrade for the full analysis.",
            "scores": {"readiness_score": 58},
        }

emailer = ReportEmailer()
fake_gen = FakeReportGenerator()

print(f"\nSending test email to: {recipient}...")
result = emailer.send_free_report(fake_gen, recipient)

print("\n" + "=" * 60)
if result.get("success"):
    if result.get("mode") == "smtp":
        print("✅ SUCCESS — Email sent via SMTP!")
        print(f"   Host: {result.get('host')}")
        print(f"   To:   {result.get('to')}")
        print("\nCheck the recipient's inbox (and spam folder).")
    else:
        print("⚠️  CONSOLE MODE — SMTP credentials are missing.")
        print(f"   Missing: {', '.join(result.get('missing_config', []))}")
        print("\nThe email was printed to your terminal instead.")
else:
    print("❌ FAILED — Could not send email.")
    print(f"   Error: {result.get('error')}")
print("=" * 60)
