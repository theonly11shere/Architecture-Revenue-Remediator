from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel, HttpUrl
from app.services.gap_analyzer import CompetitorGapAnalyzer
from app.services.pdf_reporter import PDFReporter

router = APIRouter()

class AuditRequest(BaseModel):
    target_url: HttpUrl
    competitor_url: HttpUrl
    user_email: str
    tier: str = "basic" # 'basic' ($150) or 'pro' ($300)
    business_type: str = "local_service"
    is_local: bool = True

@router.post("/api/v1/report-request")
async def generate_gap_report(request: AuditRequest, background_tasks: BackgroundTasks):
    # In production, replace these with actual data from your scraper.py
    mock_target_data = {"mobile_sticky_cta": False, "exit_intent_capture": False}
    mock_competitor_data = {"mobile_sticky_cta": True, "exit_intent_capture": True}

    # 1. Analyze Gaps & Get Blueprints
    analyzer = CompetitorGapAnalyzer(
        mock_target_data, 
        mock_competitor_data, 
        request.tier, 
        request.business_type, 
        request.is_local
    )
    report_payload = analyzer.generate_full_report_data()

    # 2. Generate PDF
    pdf_filename = f"report_{request.user_email.replace('@', '_')}.pdf"
    await PDFReporter.generate_pdf(report_payload, output_path=pdf_filename)

    # 3. (Optional) Here is where you would call your mailer.py to send via Resend

    return {
        "status": "success",
        "message": f"{request.tier.upper()} Report generated successfully",
        "pdf_path": pdf_filename
    }