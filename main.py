import os
import resend
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from app.services.scorer import LeakAnalyzer
from app.services.pdf_reporter import PDFReporter

app = FastAPI(title="Audit Scanner API")

# Enable CORS so your frontend can talk to the backend smoothly
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

resend.api_key = os.environ.get("RESEND_API_KEY")

@app.get("/")
def home():
    return {"status": "Audit Scanner API is running live!"}

@app.get("/api/v1/payment-options")
def get_payment_options():
    # Return your payment tiers/options if your frontend looks for this
    return {
        "tiers": [
            {"id": "growth", "name": "Growth Tier", "price": 49},
            {"id": "scale", "name": "Scale Tier", "price": 99}
        ]
    }

@app.post("/api/v1/scan")
async def scan_website(data: dict):
    try:
        target_features = data.get("target_features", {})
        competitor_features = data.get("competitor_features", {})
        business_type = data.get("business_type", "general")
        is_local = data.get("is_local", True)
        tier = data.get("tier", "growth")
        recipient_email = data.get("email")

        # 1. Generate the audit report payload and PDF
        analyzer = LeakAnalyzer(target_features, competitor_features, business_type, is_local)
        report_payload = analyzer.get_tier_report(tier)

        output_filename = "client_audit_report.pdf"
        pdf_path = await PDFReporter.generate_pdf(report_payload, output_filename)

        # 2. Send email via Resend if email is provided
        if recipient_email:
            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()

            params = {
                "from": "onboarding@resend.dev", # Change to your verified domain email later if needed
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