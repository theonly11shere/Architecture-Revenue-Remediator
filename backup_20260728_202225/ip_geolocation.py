#!/usr/bin/env python3
"""IP Geolocation — Auto-detects city/region from IP address using ip-api.com (free, no API key)."""
import requests
from typing import Optional, Dict


def get_location_from_ip(ip_address: str = "") -> Optional[str]:
    """
    Detect city and region from IP address.

    Args:
        ip_address: Client IP. If empty, uses the request IP (ip-api detects automatically).

    Returns:
        String like "Chicago IL" or "New York NY" or None if detection fails.
    """
    try:
        # ip-api.com is free, no API key needed, 45 requests/minute limit
        # Use fields=city,region,country to minimize response size
        url = f"http://ip-api.com/json/{ip_address}?fields=city,regionName,country,status,message"
        response = requests.get(url, timeout=5)
        data = response.json()

        if data.get("status") != "success":
            print(f"[IP Geo] Detection failed: {data.get('message', 'Unknown error')}")
            return None

        city = data.get("city", "").strip()
        region = data.get("regionName", "").strip()
        country = data.get("country", "").strip()

        # Build location string
        parts = []
        if city:
            parts.append(city)
        if region:
            parts.append(region)

        location = " ".join(parts) if parts else None

        if location:
            print(f"[IP Geo] Detected location from IP: {location} ({country})")

        return location

    except Exception as e:
        print(f"[IP Geo] Error: {e}")
        return None


def get_client_ip(request_headers: Dict[str, str]) -> str:
    """
    Extract real client IP from request headers, handling proxies/CDNs.

    Checks in order:
    1. X-Forwarded-For (most common via proxy/CDN)
    2. X-Real-IP (Nginx proxy)
    3. CF-Connecting-IP (Cloudflare)
    4. True-Client-IP (Akamai/Cloudflare enterprise)
    5. Remote-Addr (direct connection)

    Returns:
        Client IP address string, or empty string if not found.
    """
    # X-Forwarded-For can contain multiple IPs: "client, proxy1, proxy2"
    x_forwarded = request_headers.get("x-forwarded-for", "")
    if x_forwarded:
        # First IP is the real client
        return x_forwarded.split(",")[0].strip()

    # Check other proxy headers
    for header in ["x-real-ip", "cf-connecting-ip", "true-client-ip"]:
        ip = request_headers.get(header, "")
        if ip:
            return ip.strip()

    return ""