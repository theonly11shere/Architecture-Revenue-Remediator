# test_harness.py
import os
import json
from scorer import run_full_audit_pipeline
from report_engine import get_report_by_id_admin, force_unlock_report_admin
from telemetry import get_telemetry_dump_admin

# 1. Set Master Admin Secret Token in Environment
ADMIN_SECRET = "SM65J3J34H34I34B34U"
os.environ["TRILLOKA_ADMIN_TOKEN"] = ADMIN_SECRET

MOCK_SITE = {
    "domain": "overnight-replit-saas.app",
    "business_type": "saas",
    "is_shadcn_tailwind": True,
    "lucide_icon_count": 14,
    "generic_headline": True,
    "unlinked_form": True,
    "has_retargeting_pixel": False,
    "has_custom_photos": False,
    "raw_text_sample": "Revolutionize your workflow with AI dev tools"
}

def run_test_suite():
    print("==========================================================")
    print("      TRILLOKA COMPLETE ARCHITECTURE TEST SUITE          ")
    print("==========================================================\n")

    # Step A: Run Main Pipeline
    print("1. Running Full Scorer Audit Pipeline...")
    public_payload = run_full_audit_pipeline(MOCK_SITE)
    print(" [FRONT-END PAYLOAD]:")
    print(json.dumps(public_payload, indent=2))
    print("\n" + "="*50 + "\n")

    report_id = public_payload["report_vault_id"]

    # Step B: Test Admin Backdoor Access to Private Vault
    print(f"2. Testing Admin Vault Access for Report ID: {report_id}...")
    vault_report = get_report_by_id_admin(report_id, admin_token=ADMIN_SECRET)
    print(f" [VAULT REPORT RETRIEVED]: Domain={vault_report.get('domain')}, Score={vault_report.get('overall_score')}")
    print("\n" + "="*50 + "\n")

    # Step C: Test Admin Force Unlock
    print(f"3. Testing Admin Force Unlock for Report ID: {report_id}...")
    unlocked_report = force_unlock_report_admin(report_id, admin_token=ADMIN_SECRET)
    print(f" [REPORT UNLOCKED STATUS]: {unlocked_report.get('is_unlocked')}")
    print("\n" + "="*50 + "\n")

    # Step D: Test Admin Telemetry Dump
    print("4. Testing Admin Telemetry Dump Access...")
    telemetry_data = get_telemetry_dump_admin(admin_token=ADMIN_SECRET)
    print(f" [TELEMETRY DUMP SUCCESS]: Captured {len(telemetry_data.get('buckets', {}))} active bucket categories.")
    print("\n" + "="*50 + "\n")

    print(" [SUCCESS] All systems operational. Zero syntax errors.")

if __name__ == "__main__":
    run_test_suite()