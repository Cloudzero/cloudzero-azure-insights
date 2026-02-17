#!/usr/bin/env python3
"""Test if no-filter approach is more stable than source filter."""

import os
import sys
import time
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


def test_query(url, test_name):
    """Test a single query."""
    start = time.time()
    try:
        response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        elapsed = time.time() - start
        success = response.status_code == 200
        return {
            "success": success,
            "status": response.status_code,
            "time": elapsed
        }
    except requests.Timeout:
        elapsed = time.time() - start
        return {
            "success": False,
            "status": "TIMEOUT",
            "time": elapsed
        }
    except Exception as e:
        elapsed = time.time() - start
        return {
            "success": False,
            "status": f"ERROR: {e}",
            "time": elapsed
        }


print("🧪 Testing CloudZero API stability: 5 attempts each\n")

# Test 1: WITH source filter
print("="*80)
print("Test A: WITH source filter (limit=10)")
print("="*80)
url_with_filter = f"{BASE_URL}?source=azure%20advisor&limit=10"
results_with = []

for i in range(5):
    print(f"  Attempt {i+1}/5...", end=" ", flush=True)
    result = test_query(url_with_filter, f"with_filter_{i+1}")
    results_with.append(result)
    status_icon = "✅" if result["success"] else "❌"
    print(f"{status_icon} {result['status']} ({result['time']:.2f}s)")
    if i < 4:  # Don't sleep after last attempt
        time.sleep(2)

success_count_with = sum(1 for r in results_with if r["success"])
print(f"\n  Success rate: {success_count_with}/5 ({success_count_with*20}%)")
avg_time_with = sum(r["time"] for r in results_with) / len(results_with)
print(f"  Average time: {avg_time_with:.2f}s")

# Test 2: WITHOUT source filter
print("\n" + "="*80)
print("Test B: WITHOUT source filter (limit=10)")
print("="*80)
url_no_filter = f"{BASE_URL}?limit=10"
results_without = []

for i in range(5):
    print(f"  Attempt {i+1}/5...", end=" ", flush=True)
    result = test_query(url_no_filter, f"no_filter_{i+1}")
    results_without.append(result)
    status_icon = "✅" if result["success"] else "❌"
    print(f"{status_icon} {result['status']} ({result['time']:.2f}s)")
    if i < 4:
        time.sleep(2)

success_count_without = sum(1 for r in results_without if r["success"])
print(f"\n  Success rate: {success_count_without}/5 ({success_count_without*20}%)")
avg_time_without = sum(r["time"] for r in results_without) / len(results_without)
print(f"  Average time: {avg_time_without:.2f}s")

# Summary
print("\n" + "="*80)
print("SUMMARY")
print("="*80)
print(f"WITH source filter:    {success_count_with}/5 success ({success_count_with*20}%) - avg {avg_time_with:.2f}s")
print(f"WITHOUT source filter: {success_count_without}/5 success ({success_count_without*20}%) - avg {avg_time_without:.2f}s")

if success_count_without > success_count_with:
    print("\n💡 RECOMMENDATION: No-filter approach is MORE RELIABLE")
    print("   Consider removing source filter from API query and filtering client-side.")
elif success_count_with > success_count_without:
    print("\n💡 RECOMMENDATION: Source filter approach is MORE RELIABLE")
    print("   Current approach is better.")
else:
    print("\n⚠️  CONCLUSION: Both approaches have SIMILAR reliability")
    print("   CloudZero API has broader performance issues.")
