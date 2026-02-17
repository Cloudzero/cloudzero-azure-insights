#!/usr/bin/env python3
"""Check the actual JSON structure of CloudZero insights."""

import os
import sys
import json
import requests
from dotenv import load_dotenv

load_dotenv()

CLOUDZERO_API_KEY = os.environ.get("CLOUDZERO_API_KEY")
if not CLOUDZERO_API_KEY:
    print("❌ CLOUDZERO_API_KEY not set")
    sys.exit(1)

BASE_URL = "https://api.cloudzero.com/v2/insights"
HEADERS = {
    "Authorization": CLOUDZERO_API_KEY,
    "Content-Type": "application/json"
}
TIMEOUT = 45

print("🔍 Checking CloudZero API response structure\n")

# Fetch without source filter
url = f"{BASE_URL}?limit=5"
print(f"Fetching 5 insights...")

try:
    response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)

    if response.status_code != 200:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)
        sys.exit(1)

    data = response.json()

    # Show full response structure
    print("="*80)
    print("FULL RESPONSE STRUCTURE")
    print("="*80)
    print(json.dumps(data, indent=2)[:2000])  # First 2000 chars
    print("\n... (truncated for readability)\n")

    # Check insights
    insights = data.get("insights", [])
    print("="*80)
    print(f"INSIGHTS ({len(insights)} found)")
    print("="*80)

    for idx, insight in enumerate(insights, 1):
        print(f"\nInsight {idx}:")
        print(f"  Keys: {list(insight.keys())}")
        print(f"  ID: {insight.get('id', 'N/A')}")
        print(f"  Title: {insight.get('title', 'N/A')[:60]}...")
        print(f"  Source: {insight.get('source', 'MISSING!')}")
        print(f"  Status: {insight.get('status', 'N/A')}")
        print(f"  Cost Impact: ${insight.get('cost_impact', 'N/A')}")

    # Check if 'source' field exists
    print("\n" + "="*80)
    print("SOURCE FIELD CHECK")
    print("="*80)

    has_source = [i for i in insights if "source" in i]
    missing_source = [i for i in insights if "source" not in i]

    print(f"✅ Insights WITH 'source' field: {len(has_source)}/{len(insights)}")
    print(f"❌ Insights WITHOUT 'source' field: {len(missing_source)}/{len(insights)}")

    if has_source:
        sources = set(i.get("source") for i in has_source)
        print(f"\n📋 Source values found:")
        for source in sorted(sources):
            count = sum(1 for i in has_source if i.get("source") == source)
            print(f"   - '{source}': {count}")

    # Show one full insight
    if insights:
        print("\n" + "="*80)
        print("FULL INSIGHT EXAMPLE")
        print("="*80)
        print(json.dumps(insights[0], indent=2))

except requests.Timeout:
    print(f"❌ Request timed out after {TIMEOUT}s")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
