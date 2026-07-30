import os
import resend
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.services.scorer import LeakAnalyzer
from app.services.pdf_reporter import PDFReporter

app = FastAPI(title="Audit Scanner API")

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

        # 1. Generate the audit scores and report payload for your UI
        analyzer = LeakAnalyzer(target_features, competitor_features, business_type, is_local)
        report_payload = analyzer.get_tier_report(tier)

        # 2. Optionally generate PDF & send email via Resend in the background
        if recipient_email:
            try:
                output_filename = "client_audit_report.pdf"
                pdf_path = await PDFReporter.generate_pdf(report_payload, output_filename)
                
                with open(pdf_path, "rb") as f:
                    pdf_bytes = f.read()

                params = {
                    "from": "onboarding@resend.dev",
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
            except Exception as email_err:
                print(f"Email/PDF background task error: {email_err}")

        # 3. Return JSON so your frontend UI can populate those dials and scores!
        return report_payload

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))