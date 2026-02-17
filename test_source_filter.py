#!/usr/bin/env python3
"""Test CloudZero API source filter behavior.

Compare:
1. Fetching WITH source filter (current approach)
2. Fetching WITHOUT source filter, then filtering client-side
"""

import os
import sys
import time
import requests
from dotenv import load_dotenv

# Load environment
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


def test_with_source_filter():
    """Test current approach: source filter in query string."""
    print("\n" + "="*80)
    print("TEST 1: WITH source filter (current approach)")
    print("="*80)

    url = f"{BASE_URL}?source=azure%20advisor&limit=10"
    print(f"URL: {url}")

    start = time.time()
    try:
        response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        elapsed = time.time() - start

        print(f"⏱️  Time: {elapsed:.2f}s")
        print(f"📊 Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            insights = data.get("insights", [])
            print(f"✅ Success: Retrieved {len(insights)} insights")

            # Check sources
            sources = set(i.get("source", "unknown") for i in insights)
            print(f"📋 Sources found: {sources}")

            # Count by source
            azure_count = sum(1 for i in insights if i.get("source", "").lower() == "azure advisor")
            print(f"   - azure advisor: {azure_count}")

            return insights
        elif response.status_code == 504:
            print(f"❌ FAILED: 504 Gateway Timeout")
            return None
        else:
            print(f"❌ FAILED: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return None

    except requests.Timeout:
        elapsed = time.time() - start
        print(f"⏱️  Time: {elapsed:.2f}s")
        print(f"❌ FAILED: Request timeout ({TIMEOUT}s)")
        return None
    except Exception as e:
        elapsed = time.time() - start
        print(f"⏱️  Time: {elapsed:.2f}s")
        print(f"❌ FAILED: {e}")
        return None


def test_without_source_filter():
    """Test alternative: no source filter, filter client-side."""
    print("\n" + "="*80)
    print("TEST 2: WITHOUT source filter (filter client-side)")
    print("="*80)

    url = f"{BASE_URL}?limit=10"
    print(f"URL: {url}")

    start = time.time()
    try:
        response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        elapsed = time.time() - start

        print(f"⏱️  Time: {elapsed:.2f}s")
        print(f"📊 Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            all_insights = data.get("insights", [])
            print(f"✅ Success: Retrieved {len(all_insights)} insights (all sources)")

            # Check all sources
            sources = {}
            for insight in all_insights:
                source = insight.get("source", "unknown")
                sources[source] = sources.get(source, 0) + 1

            print(f"📋 Sources breakdown:")
            for source, count in sorted(sources.items()):
                print(f"   - {source}: {count}")

            # Filter for azure advisor
            azure_insights = [
                i for i in all_insights
                if i.get("source", "").lower() == "azure advisor"
            ]
            print(f"\n🔍 After client-side filtering:")
            print(f"   - Azure Advisor insights: {len(azure_insights)}")

            return azure_insights
        elif response.status_code == 504:
            print(f"❌ FAILED: 504 Gateway Timeout")
            return None
        else:
            print(f"❌ FAILED: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return None

    except requests.Timeout:
        elapsed = time.time() - start
        print(f"⏱️  Time: {elapsed:.2f}s")
        print(f"❌ FAILED: Request timeout ({TIMEOUT}s)")
        return None
    except Exception as e:
        elapsed = time.time() - start
        print(f"⏱️  Time: {elapsed:.2f}s")
        print(f"❌ FAILED: {e}")
        return None


def test_larger_limit_with_filter():
    """Test with larger limit (100) and source filter."""
    print("\n" + "="*80)
    print("TEST 3: WITH source filter + larger limit (100)")
    print("="*80)

    url = f"{BASE_URL}?source=azure%20advisor&limit=100"
    print(f"URL: {url}")

    start = time.time()
    try:
        response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        elapsed = time.time() - start

        print(f"⏱️  Time: {elapsed:.2f}s")
        print(f"📊 Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            insights = data.get("insights", [])
            print(f"✅ Success: Retrieved {len(insights)} insights")

            # Check sources
            sources = set(i.get("source", "unknown") for i in insights)
            print(f"📋 Sources found: {sources}")

            return insights
        elif response.status_code == 504:
            print(f"❌ FAILED: 504 Gateway Timeout")
            return None
        else:
            print(f"❌ FAILED: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return None

    except requests.Timeout:
        elapsed = time.time() - start
        print(f"⏱️  Time: {elapsed:.2f}s")
        print(f"❌ FAILED: Request timeout ({TIMEOUT}s)")
        return None
    except Exception as e:
        elapsed = time.time() - start
        print(f"⏱️  Time: {elapsed:.2f}s")
        print(f"❌ FAILED: {e}")
        return None


if __name__ == "__main__":
    print("🧪 Testing CloudZero API source filter behavior")
    print(f"📍 Endpoint: {BASE_URL}")
    print(f"⏱️  Timeout: {TIMEOUT}s")

    # Test 1: Current approach (small limit + source filter)
    result1 = test_with_source_filter()
    time.sleep(2)  # Brief pause between tests

    # Test 2: No source filter (client-side filtering)
    result2 = test_without_source_filter()
    time.sleep(2)

    # Test 3: Large limit + source filter
    result3 = test_larger_limit_with_filter()

    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Test 1 (source filter, limit=10):  {'✅ SUCCESS' if result1 is not None else '❌ FAILED'}")
    print(f"Test 2 (no filter, limit=10):      {'✅ SUCCESS' if result2 is not None else '❌ FAILED'}")
    print(f"Test 3 (source filter, limit=100): {'✅ SUCCESS' if result3 is not None else '❌ FAILED'}")

    if result2 is not None:
        print("\n💡 RECOMMENDATION:")
        print("   Client-side filtering (Test 2) is viable and may be more reliable.")
        print("   This avoids the CloudZero API source filter bug entirely.")
    else:
        print("\n⚠️  WARNING:")
        print("   All approaches may be experiencing issues.")
        print("   CloudZero API may be having broader performance problems.")
