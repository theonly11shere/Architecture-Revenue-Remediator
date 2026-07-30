import os
import resend
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.services.scorer import LeakAnalyzer
from app.services.pdf_reporter import PDFReporter
from app.services.scraper import WebsiteScraper

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
            {"id": "entry", "name": "Entry Tier", "price": 0},
            {"id": "growth", "name": "Growth Tier", "price": 49},
            {"id": "scale", "name": "Scale Tier", "price": 99}
        ]
    }

@app.post("/api/v1/scan")
async def scan_website(data: dict):
    try:
        # Extract URL from frontend request
        url = data.get("url") or data.get("target_url") or "karakoramrestaurant.com"
        
        # 1. Live scrape the website features using your scraper service
        target_features = data.get("target_features")
        if not target_features or len(target_features) == 0:
            target_features = WebsiteScraper.scrape_url(url)

        competitor_features = data.get("competitor_features", {})
        business_type = data.get("business_type", "general")
        is_local = data.get("is_local", True)
        tier = data.get("tier", "growth")
        recipient_email = data.get("email")

        # 2. Run leak analysis and scoring
        analyzer = LeakAnalyzer(target_features, competitor_features, business_type, is_local)
        report_payload = analyzer.get_tier_report(tier)

        # 3. Generate PDF & send email via Resend if email is provided
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

        # 4. Return JSON payload so frontend UI dials render correctly
        return report_payload

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))