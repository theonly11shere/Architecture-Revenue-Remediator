from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from app.services.scorer import LeakAnalyzer
from app.services.pdf_reporter import PDFReporter

app = FastAPI(title="Audit Scanner API")

@app.get("/")
def home():
    return {"status": "Audit Scanner API is running live!"}

@app.post("/generate-audit")
async def generate_audit(data: dict):
    try:
        target_features = data.get("target_features", {})
        competitor_features = data.get("competitor_features", {})
        business_type = data.get("business_type", "general")
        is_local = data.get("is_local", True)
        tier = data.get("tier", "growth")

        analyzer = LeakAnalyzer(target_features, competitor_features, business_type, is_local)
        report_payload = analyzer.get_tier_report(tier)

        output_filename = "client_audit_report.pdf"
        pdf_path = await PDFReporter.generate_pdf(report_payload, output_filename)

        return FileResponse(pdf_path, media_type="application/pdf", filename="audit_report.pdf")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))