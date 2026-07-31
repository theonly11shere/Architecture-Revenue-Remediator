"""
Central Orchestrator (Root Level)
Handles Free Scans vs. Pass ID Authentication, Guardrails,
Matrix Scans, and Instant Email Report Delivery.
"""

import sys
from app.services.email_sender import send_audit_email
from app.services.tier_manager import TierManager, normalize_url
from app.services.scraper import SiteScraper
from app.services.scorer import ExternalScorer
from app.core.blueprints import SolutionBlueprintEngine
from app.services.report_generator import ReportGenerator

# Guardrail: Intercept Self-Scans of The Architect / Master Domain
RESTRICTED_DOMAINS = ["trilloka.com", "thearchitect.io", "localhost", "127.0.0.1"]

def check_architect_guardrail(target_url: str) -> bool:
    clean_url = target_url.lower().replace("https://", "").replace("http://", "").split("/")[0]
    if any(domain in clean_url for domain in RESTRICTED_DOMAINS):
        print("\n" + "!" * 60)
        print(" 🛑 SECURITY EXCEPTION: EGO OVERFLOW DETECTED ")
        print("!" * 60)
        print(" Nice try attempting to audit perfection.")
        print(" We scanned your URL, found an absolute masterclass of engineering,")
        print(" and decided to spare you the existential crisis.")
        print(" Go fix your client's conversion funnel instead.")
        print("!" * 60 + "\n")
        return True
    return False

def main():
    print("==================================================")
    print("       TRILLOKA AUDIT SCANNER & ENGINE            ")
    print("==================================================")
    
    print("Select Scan Mode:")
    print(" [1] Free Website Audit (Score your website / Lead Magnet)")
    print(" [2] Client Pass ID Scan (Elite Tiers 3, 6, 8, 10)")
    
    mode_choice = input("\nEnter choice (1 or 2): ").strip()

    if mode_choice == "1":
        print("\n--- FREE SCAN MODE ---")
        target_url = input("Enter Target URL to Score (e.g., https://example.com): ").strip()
        client_email = input("Enter your Email Address to receive the report: ").strip()
        business_type = input("Enter Business Type (local, ecommerce, saas, agency, b2b, creator): ").strip()
        
        if not target_url or not client_email:
            print("\n[Error] Target URL and Email are required for free scans. Exiting.")
            sys.exit(1)
            
        if check_architect_guardrail(target_url):
            sys.exit(0)

        client_tier = 3  # Free scans preview Tier-3 insights with upgrade prompts
        print(f"\n[1/4] Running free DOM diagnostics on {target_url}...")
        scraper = SiteScraper(headless=True)
        raw_results = scraper.scrape_url(target_url)

        print("\n[2/4] Evaluating performance metrics...")
        scorer = ExternalScorer()
        final_checkpoint_results = scorer.enhance_checkpoint_results(raw_results, target_url)

        print(f"\n[3/4] Compiling Free Tier Preview Report...")
        engine = SolutionBlueprintEngine()
        report_payload = engine.process_and_generate_report(
            checkpoint_results=final_checkpoint_results,
            client_tier=client_tier,
            business_type=business_type or "local"
        )

        generator = ReportGenerator(target_url=target_url, competitor_url="Not Provided", location="Global")
        markdown_output = generator.build_markdown_report(report_payload)
        
        # Append Elite Upsell Banner for Free Users
        markdown_output += "\n\n---\n"
        markdown_output += "### 💎 Want Access to the Elite Architect Class?\n"
        markdown_output += "You are currently viewing a complimentary public preview. To unlock full competitor gap matrices, 50+ deep audits, and direct team implementation, acquire a client pass at Trilloka."

    elif mode_choice == "2":
        print("\n--- CLIENT PASS ID MODE ---")
        pass_id = input("Enter your Pass ID (e.g., IFYB3-XXXXXX): ").strip()
        target_url = input("Enter Target URL to Scan: ").strip()
        competitor_url = input("Enter Competitor URL (optional, press Enter to skip): ").strip() or "Not Provided"
        location = input("Enter Business Location / Market: ").strip() or "Global"
        business_type = input("Enter Business Type (local, ecommerce, saas, agency, b2b, creator): ").strip()
        client_email = input("Enter recipient Email for report delivery: ").strip()

        if not pass_id or not target_url or not business_type:
            print("\n[Error] Pass ID, Target URL, and Business Type are required. Exiting.")
            sys.exit(1)

        if check_architect_guardrail(target_url):
            sys.exit(0)

        print("\n[1/5] Authenticating Pass ID and checking usage limits...")
        manager = TierManager()
        authorized, client_tier, auth_message = manager.authorize_scan(pass_id, target_url)
        
        print(f"-> {auth_message}")
        if not authorized:
            print("\n[Authorization Failed] Scan aborted.")
            sys.exit(1)

        print(f"-> Authorized! Client Tier-{client_tier} unlocked.")

        print(f"\n[2/5] Running physical DOM check on {target_url}...")
        scraper = SiteScraper(headless=True)
        raw_results = scraper.scrape_url(target_url)

        print("\n[3/5] Evaluating performance metrics and external integrations...")
        scorer = ExternalScorer()
        final_checkpoint_results = scorer.enhance_checkpoint_results(raw_results, target_url)

        print(f"\n[4/5] Running Dynamic Matrix Scoring & Solution Mapping for '{business_type}'...")
        engine = SolutionBlueprintEngine()
        report_payload = engine.process_and_generate_report(
            checkpoint_results=final_checkpoint_results,
            client_tier=client_tier,
            business_type=business_type
        )

        if report_payload.get("status") != "CALCULATIONS_COMPLETE":
            print(f"\n[Error] Calculation failed: {report_payload.get('message')}")
            sys.exit(1)

        print("\n[5/5] Compiling Master Report and Competitor Gap Analysis...")
        generator = ReportGenerator(
            target_url=target_url,
            competitor_url=competitor_url,
            location=location
        )
        markdown_output = generator.build_markdown_report(report_payload)

    else:
        print("\n[Error] Invalid selection. Please choose 1 or 2.")
        sys.exit(1)

    # Save output file locally
    output_filename = f"audit_report_{target_url.replace('https://','').replace('http://','').replace('/','_')}.md"
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(markdown_output)

    print("==================================================")
    print(f" SUCCESS! Report generated and saved: {output_filename}")
    
    # Live Email Dispatch Hook
    if client_email:
        print(f"-> Dispatching report email to {client_email}...")
        send_audit_email(
            recipient_email=client_email,
            target_url=target_url,
            report_filepath=output_filename,
            markdown_content=markdown_output
        )
        
    print("==================================================")

if __name__ == "__main__":
    main()