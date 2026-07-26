"""
Demo script — shows all 3 report types with the new six-score system,
content evidence signals, and transparent failure reporting.
"""

import os
import sys

from config import TOTAL_CHECKS, TIER_NAMES, PRICING, SCORE_NAMES
from scraper import WebsiteScraper
from scorer import RevenueScorer
from content_evidence_signals import ContentEvidenceSignals
from reporter import ReportGenerator


# Configurable admin unlock code. Change the default here or set env var RRS_ADMIN_CODE.
ADMIN_CODE = os.environ.get("RRS_ADMIN_CODE", "TheOne1sHere")


def run_demo():
    args = sys.argv[1:]
    test_url = args[0] if args else "https://example.com"
    admin_mode = ADMIN_CODE in args

    print(f"Demo URL: {test_url}")
    print(f"Admin mode: {'ON' if admin_mode else 'OFF'} (code: {ADMIN_CODE})")

    print("=" * 70)
    print("REVENUE READINESS SCORER — DEMO (v4.0 with 6 Unified Scores)")
    print("=" * 70)

    # Scrape
    scraper = WebsiteScraper(test_url, tier="free")
    data = scraper.scrape()

    if "error" in data:
        print(f"\n❌ SCRAPE FAILED: {data['error']}")
        return

    # Score
    revenue_scorer = RevenueScorer(data)
    revenue_scorer.calculate_scores()

    content_evidence = ContentEvidenceSignals(data)
    content_evidence.analyze()

    top_failures = revenue_scorer.get_top_failures(10)
    reporter = ReportGenerator(
        test_url,
        revenue_scorer,
        content_evidence,
        data,
        top_failures,
    )

    # Free report
    print("\n" + "=" * 70)
    print("FREE REPORT (what customer sees)")
    print("=" * 70)
    free = reporter.generate_free()

    print(f"\n📊 LEGACY SCORES:")
    print(f"   Readiness:      {free['scores']['readiness_score']}/100")
    print(f"   Evidence:       {free['scores']['evidence_coverage']}/100")
    print(f"   Confidence:     {free['scores']['confidence_score']}/100")

    print(f"\n🎯 6 UNIFIED SCORES:")
    for name, info in free['six_scores'].items():
        label = info['label']
        score = info['score']
        status = info['status']
        icon = "🟢" if status == "excellent" else "🟡" if status == "good" else "🟠" if status == "fair" else "🔴"
        print(f"   {icon} {label:<25} {score:>3}/100  ({status})")

    print(f"\n💰 REVENUE LEAK ESTIMATE:")
    leak = free['revenue_leak_estimate']
    print(f"   Monthly leak:   ${leak['monthly_leak_estimate']:,.2f}")
    print(f"   Annual leak:    ${leak['annual_leak_estimate']:,.2f}")
    print(f"   Current revenue: ${leak['current_monthly_revenue']:,.2f}/mo")
    print(f"   Potential:      ${leak['potential_monthly_revenue']:,.2f}/mo")

    print(f"\n📋 SCAN QUALITY: {free['scan_quality']}")
    print(f"   Severity:       {free['severity']['label']} ({free['severity']['key']})")
    print(f"   Pages sampled:   {free['pages_sampled']}")
    print(f"   Business type:   {free['business_type'].get('detected_type', 'unknown')} ({free['business_type'].get('confidence', 0)}% confidence)")
    print(f"   Framework:       {free['tech_stack_impact'].get('detected_framework', 'Unknown')}")
    print(f"   Visible failures: {len(free['visible_failures'])}")
    print(f"   Hidden failures: {free['hidden_failure_count']}")

    print(f"\n🤖 AI COPY ANALYSIS:")
    ai = free['ai_copy_analysis']
    print(f"   AI score:        {ai.get('ai_score', 0)}/100 (badness)")
    print(f"   Cliché score:    {ai.get('cliche_score', 0)}/100 (badness)")
    print(f"   Assessment:      {ai.get('assessment', 'N/A')}")

    print(f"\n📝 FORM FRICTION:")
    form = free['form_friction']
    print(f"   Forms found:     {form.get('forms_found', 0)}")
    print(f"   Avg fields:      {form.get('avg_fields', 0)}")
    print(f"   Friction score:  {form.get('friction_score', 0)}/100 (higher = less friction)")
    print(f"   Assessment:      {form.get('assessment', 'N/A')}")

    print(f"\n📡 SOCIAL SIGNALS:")
    social = data.get('social_signals_enhanced', {})
    print(f"   Mentions found:  {social.get('mentions_found', 0)}")
    print(f"   Verdict:         {social.get('verdict_label', 'N/A')}")
    sources = social.get('sources', {})
    print(f"   Sources:         Reddit:{sources.get('reddit',0)} Trustpilot:{sources.get('trustpilot',0)} Yelp:{sources.get('yelp',0)} Google:{sources.get('google',0)} News:{sources.get('news',0)}")

    print(f"\n📄 Content Evidence Signals: {len(free['content_evidence_signals'])} checks")
    for s in free['content_evidence_signals']:
        print(f"   [{s['status'].upper()}] {s['name']}: {s['detail'][:80]}...")

    print(f"\n🔧 TOP FAILURES:")
    for f in free['visible_failures']:
        print(f"   [{f['severity'].upper()}] {f['category']}: {f['item']} — {f['one_liner']}")

    print(f"\n🚀 CTA: {free['upgrade_cta']}")

    if admin_mode:
        # Paid report
        print("\n" + "=" * 70)
        print(f"PAID REPORT (${PRICING['paid']} — what customer gets)")
        print("=" * 70)
        paid = reporter.generate_paid()
        print(f"Scores: {paid['scores']}")
        print(f"Fix steps: {len(paid.get('fix_steps', []))}")
print(f"Revenue leak estimate: ${paid.get('revenue_leak_estimate', {}).get('monthly_leak_estimate', 0):,.2f}/mo")

        # Admin report
        print("\n" + "=" * 70)
        print("ADMIN REPORT (locked — owner only)")
        print("=" * 70)
        admin = reporter.generate_admin()
        print(f"Scores: {admin['scores']}")
        print(f"Threats: {len(admin['threat_analysis'])}")
        print(f"Human gist: {admin['human_gist']}")
        print(f"Research time: {admin['estimated_research_time']}")
        print(f"\nAdmin report contains complete sources and methods.")
        print("Only the owner can access this.")
    else:
        print("\n[Provide the admin code to unlock paid + admin reports]")


if __name__ == "__main__":
    run_demo()