import asyncio
from app.services.gap_analyzer import CompetitorGapAnalyzer
from app.services.pdf_reporter import PDFReporter

async def test_pipeline():
    print("--- STARTING LOCAL AUDIT TEST ---")
    
    # Mock data representing a target site missing critical elements vs a competitor who has them
    target_site_features = {
        "mobile_sticky_cta": False,
        "exit_intent_capture": False,
        "social_proof_above_fold": False,
        "no_click_to_call": False,
        "local_seo_schema": False
    }
    
    competitor_site_features = {
        "mobile_sticky_cta": True,
        "exit_intent_capture": True,
        "social_proof_above_fold": True,
        "no_click_to_call": True,
        "local_seo_schema": True
    }

    # Test the $550 Growth Tier
    tier_to_test = "growth"
    business_vertical = "local_service"
    
    print(f"Analyzing gaps for Tier: {tier_to_test.upper()} | Business: {business_vertical}...")
    
    analyzer = CompetitorGapAnalyzer(
        target_data=target_site_features,
        competitor_data=competitor_site_features,
        tier=tier_to_test,
        business_type=business_vertical,
        is_local=True
    )
    
    report_payload = analyzer.generate_full_report_data()
    print(f"Scorer complete. Found {len(report_payload['unlocked_leaks'])} leaks.")

    print("Rendering Playwright PDF report...")
    output_pdf = "vancouver_client_audit.pdf"
    await PDFReporter.generate_pdf(report_payload, output_path=output_pdf)
    
    print(f"SUCCESS! PDF generated successfully at: {output_pdf}")
    print("--- TEST COMPLETE ---")

if __name__ == "__main__":
    asyncio.run(test_pipeline())