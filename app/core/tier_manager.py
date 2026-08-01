"""
Backend Client Tier & Scan Tracker
Handles Pass ID generation, CSV database tracking, and normalized URL scan authorization.
"""

import csv
import os
import secrets
import string
from datetime import datetime
from typing import Tuple

DB_FILE = "client_tiers_backend.csv"

TIER_CONFIG = {
    3: {"name": "Important for your business", "prefix": "IFYB3", "scans_allowed": 5},
    6: {"name": "Making your business the best", "prefix": "MBTB6", "scans_allowed": 10},
    8: {"name": "No one like you", "prefix": "NOLY8", "scans_allowed": 15},
    10: {"name": "The Architect", "prefix": "ARCH10", "scans_allowed": 50}
}

def normalize_url(url: str) -> str:
    """Normalizes URLs to prevent mismatch errors (removes trailing slashes, enforces https, lowers)."""
    if not url:
        return ""
    url = url.strip().lower()
    if url.startswith("https://"):
        url = url[8:]
    elif url.startswith("http://"):
        url = url[7:]
    return "https://" + url.rstrip("/")

class TierManager:
    def __init__(self):
        self._initialize_db()

    def _initialize_db(self):
        if not os.path.exists(DB_FILE):
            with open(DB_FILE, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(["Pass_ID", "Target_URL", "Tier_Purchased", "Scans_Used", "Scans_Allowed", "Last_Scan_Date"])

    def _generate_pass_id(self, tier: int) -> str:
        prefix = TIER_CONFIG[tier]["prefix"]
        suffix = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
        return f"{prefix}-{suffix}"

    def add_new_client(self, target_url: str, tier: int) -> str:
        if tier not in TIER_CONFIG:
            return "Error: Invalid Tier. Choose 3, 6, 8, or 10."
        
        pass_id = self._generate_pass_id(tier)
        clean_url = normalize_url(target_url)
        
        with open(DB_FILE, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow([
                pass_id, 
                clean_url, 
                tier, 
                0, 
                TIER_CONFIG[tier]["scans_allowed"], 
                "Never"
            ])
            
        return pass_id

    def authorize_scan(self, pass_id: str, target_url: str) -> Tuple[bool, int, str]:
        client_data = []
        authorized = False
        client_tier = 0
        message = "Invalid Pass ID or URL mismatch. Please verify your credentials."
        clean_target = normalize_url(target_url)

        if not os.path.exists(DB_FILE):
            return False, 0, "Database error."

        with open(DB_FILE, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                stored_url = normalize_url(row["Target_URL"])
                if row["Pass_ID"].strip() == pass_id.strip() and stored_url == clean_target:
                    scans_used = int(row["Scans_Used"])
                    scans_allowed = int(row["Scans_Allowed"])
                    
                    if scans_used < scans_allowed:
                        authorized = True
                        client_tier = int(row["Tier_Purchased"])
                        row["Scans_Used"] = str(scans_used + 1)
                        row["Last_Scan_Date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        message = f"Scan authorized. {scans_allowed - (scans_used + 1)} scans remaining."
                    else:
                        message = f"Scan limit reached ({scans_used}/{scans_allowed})."
                
                client_data.append(row)

        if authorized:
            with open(DB_FILE, mode='w', newline='', encoding='utf-8') as file:
                fieldnames = ["Pass_ID", "Target_URL", "Tier_Purchased", "Scans_Used", "Scans_Allowed", "Last_Scan_Date"]
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(client_data)

        return authorized, client_tier, message