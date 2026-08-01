# telemetry.py
import json
import os
from datetime import datetime

TELEMETRY_DB = "pattern_telemetry.json"
ADMIN_TOKEN_ENV_VAR = "TRILLOKA_ADMIN_TOKEN"

def _verify_admin_access(token_provided: str) -> bool:
    """Verifies master admin token against environment variables."""
    master_token = os.environ.get(ADMIN_TOKEN_ENV_VAR, "SM65J3J34H34I34B34U")
    return token_provided == master_token

def log_telemetry_async(domain: str, business_type: str, audit_data: dict, final_score: float, synthetic_index: float):
    """
    Receives scan payload asynchronously from scorer.py.
    Categorizes, routes, and archives pattern telemetry.
    """
    valid_categories = ["ecommerce", "saas", "agency", "local_services", "b2b"]
    primary_category = business_type if business_type in valid_categories else "uncategorized"

    sub_category = _infer_subcategory(primary_category, audit_data)

    # Synthetic Bucket Routing (>70% AI)
    if synthetic_index >= 70.0:
        bucket = "unrecognized_synthetic"
    else:
        bucket = f"{primary_category}.{sub_category}" if sub_category else primary_category

    record = {
        "timestamp": datetime.utcnow().isoformat(),
        "domain": domain,
        "bucket": bucket,
        "primary_category": primary_category,
        "sub_category": sub_category,
        "score_given": final_score,
        "synthetic_index": synthetic_index,
        "footprint_signatures": {
            "shadcn_tailwind": audit_data.get("is_shadcn_tailwind", False),
            "lucide_icon_density": audit_data.get("lucide_icon_count", 0),
            "unlinked_form": audit_data.get("unlinked_form", False),
            "generic_llm_headline": audit_data.get("generic_headline", False),
            "missing_pixel": not audit_data.get("has_retargeting_pixel", False)
        }
    }

    _write_to_db(bucket, record)

def _infer_subcategory(category: str, audit_data: dict) -> str:
    """Infers sub-categories based on DOM text tokens."""
    text = audit_data.get("raw_text_sample", "").lower()
    
    if category == "saas":
        if "api" in text or "developer" in text: return "dev_tools"
        if "crm" in text or "pipeline" in text: return "sales_tech"
    elif category == "ecommerce":
        if "apparel" in text or "clothing" in text: return "apparel"
        if "supplements" in text or "health" in text: return "wellness"
    elif category == "local_services":
        if "plumb" in text or "drain" in text: return "plumbing"
        if "hvac" in text or "air" in text: return "hvac"
        
    return "general"

def _write_to_db(bucket: str, record: dict):
    db_data = {"buckets": {}}
    if os.path.exists(TELEMETRY_DB):
        try:
            with open(TELEMETRY_DB, "r") as f:
                db_data = json.load(f)
        except (json.JSONDecodeError, IOError):
            pass

    if "buckets" not in db_data:
        db_data["buckets"] = {}

    if bucket not in db_data["buckets"]:
        db_data["buckets"][bucket] = []

    db_data["buckets"][bucket].append(record)

    try:
        with open(TELEMETRY_DB, "w") as f:
            json.dump(db_data, f, indent=2)
        print(f" [TELEMETRY LOGGED] {record['domain']} --> [{bucket}]")
    except IOError as e:
        print(f" [TELEMETRY ERROR] Failed writing to telemetry file: {e}")

# =====================================================================
#                 ADMIN BACKDOOR / EMERGENCY DATA ACCESS
# =====================================================================

def get_telemetry_dump_admin(admin_token: str) -> dict:
    """
    ADMIN BACKDOOR: Retrieve raw telemetry data.
    Requires master token verification.
    """
    if not _verify_admin_access(admin_token):
        print(" [SECURITY ALERT] Unauthorized access attempt to Telemetry Dump.")
        return {"error": "ACCESS_DENIED: Invalid Admin Verification Token"}

    if not os.path.exists(TELEMETRY_DB):
        return {"message": "Telemetry database is currently empty.", "buckets": {}}

    try:
        with open(TELEMETRY_DB, "r") as f:
            data = json.load(f)
        print(" [ADMIN ACCESS GRANTED] Telemetry data dumped successfully.")
        return data
    except Exception as e:
        return {"error": f"Failed to read database: {str(e)}"}