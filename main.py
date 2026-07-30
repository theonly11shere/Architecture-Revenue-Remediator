import os
import resend
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from app.services.scorer import LeakAnalyzer
from app.services.pdf_reporter import PDFReporter

app = FastAPI(title="Audit Scanner API")
resend.api_key = os.environ.get("RESEND_API_KEY")

@app.post("/generate-audit")
async def generate_audit(data: dict):
    try:
        target_features = data.get("target_features", {})
        competitor_features = data.get("competitor_features", {})
        business_type = data.get("business_type", "general")
        is_local = data.get("is_local", True)
        tier = data.get("tier", "growth")
        recipient_email = data.get("email") # Get client email from request

        # 1. Generate the audit report payload and PDF
        analyzer = LeakAnalyzer(target_features, competitor_features, business_type, is_local)
        report_payload = analyzer.get_tier_report(tier)

        output_filename = "client_audit_report.pdf"
        pdf_path = await PDFReporter.generate_pdf(report_payload, output_filename)

        # 2. If an email is provided, send it via Resend with the PDF attached
        if recipient_email:
            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()

            params = {
                "from": "audit@yourdomain.com", # Update with your verified Resend domain/email
                "to": [recipient_email],
                "subject": "Your Website Performance & Leak Audit",
                "html": "<p>Hi there! Attached is your comprehensive website audit report.</p>",
                "attachments": [
                    {
                        "filename": "audit_report.pdf",
                        "content": list(pdf_bytes)
                    }
                ]
            }
            resend.Emails.send(params)

        return FileResponse(pdf_path, media_type="application/pdf", filename="audit_report.pdf")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))