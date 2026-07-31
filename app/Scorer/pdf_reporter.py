from jinja2 import Template
from playwright.async_api import async_playwright

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; color: #1e293b; margin: 40px; line-height: 1.4; }
        h1 { font-size: 22px; color: #0f172a; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px; }
        h2 { font-size: 16px; color: #334155; margin-top: 25px; }
        .leak-card { background: #fff; border: 1px solid #e2e8f0; border-radius: 6px; padding: 14px; margin-bottom: 12px; }
        .leak-title { font-weight: bold; color: #b91c1c; font-size: 14px; }
        .leak-desc { font-size: 13px; color: #475569; margin-top: 4px; }
    </style>
</head>
<body>
    <h1>Audit & Competitor Gap Analysis</h1>
    <p><strong>Tier Applied:</strong> {{ tier_applied | upper }}</p>

    <h2>Top Revenue Leaks Found</h2>
    {% for leak in unlocked_leaks %}
    <div class="leak-card">
        <div class="leak-title">{{ leak.issue }} (Severity: {{ leak.severity_score }}/10)</div>
        <div class="leak-desc">{{ leak.explanation }}</div>
    </div>
    {% endfor %}

    {% if roadmap_included %}
    <div style="margin-top: 30px; page-break-inside: avoid;">
        <h2>1-Week Growth Executive Roadmap</h2>
        {% for phase, description in roadmap_timeline.items() %}
        <div style="background: #f8fafc; border-left: 4px solid #2563eb; padding: 14px 18px; margin-bottom: 15px; border-radius: 4px;">
             <strong style="font-size: 14px; color: #1e293b; display: block; margin-bottom: 6px;">{{ phase }}</strong>
             <p style="margin: 0; font-size: 13px; color: #334155; line-height: 1.5;">
                 {{ description }}
             </p>
        </div>
        {% endfor %}
    </div>
    {% endif %}
</body>
</html>
"""

class PDFReporter:
    @staticmethod
    async def generate_pdf(report_payload: dict, output_path: str = "report.pdf") -> str:
        template = Template(HTML_TEMPLATE)
        rendered_html = template.render(
            tier_applied=report_payload.get("tier_applied"),
            unlocked_leaks=report_payload.get("unlocked_leaks"),
            roadmap_included=report_payload.get("roadmap_included"),
            roadmap_timeline=report_payload.get("roadmap_timeline")
        )

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.set_content(rendered_html)
            await page.pdf(path=output_path, format="A4", print_background=True, margin={"top": "20px", "bottom": "20px", "left": "20px", "right": "20px"})
            await browser.close()

        return output_path