# SPDX-FileCopyrightText: Copyright (c) 2016-2023, CloudZero, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import logging
import requests
import urllib.parse
from typing import List, Dict, Any


class CloudZeroClient:
    """Client for interacting with CloudZero API."""

    BASE_URL = "https://api.cloudzero.com/v2/insights"

    def __init__(self, api_key: str) -> None:
        """Initialize client with API key.

        Args:
            api_key: CloudZero API key for authentication
        """
        self.api_key = api_key
        self.headers = {
            "Authorization": api_key,
            "Content-Type": "application/json"
        }

    def get_insights(
        self,
        source: str = "azure advisor",
        page_size: int = 100,
        max_total: int = 0
    ) -> List[Dict[str, Any]]:
        """Retrieve insights from CloudZero filtered by source.

        Args:
            source: Source filter for insights (default: "azure advisor")
            page_size: Items per API page (default: 100)
            max_total: Maximum total insights to fetch, 0=all (default: 0)

        Returns:
            List of insight dictionaries or dict with error key
        """
        logging.info(f"Fetching CloudZero insights (source={source}, max={max_total or 'all'})...")

        insights = []
        next_cursor = None
        base_url = f"{self.BASE_URL}?source={urllib.parse.quote(source)}&limit={page_size}"
        page_num = 0

        try:
            while True:
                page_num += 1

                # URL-encode the cursor as required by CloudZero API
                if next_cursor:
                    url = base_url + f"&cursor={urllib.parse.quote(next_cursor)}"
                else:
                    url = base_url

                response = requests.get(url, headers=self.headers)

                if response.status_code == 200:
                    data = response.json()
                    page_insights = data.get("insights", [])
                    insights.extend(page_insights)

                    pagination_info = data.get("pagination", {})
                    total_count = pagination_info.get("total_count", "unknown")

                    logging.info(
                        f"Page {page_num}: Retrieved {len(page_insights)} insights "
                        f"(total so far: {len(insights)}/{total_count})"
                    )

                    # Stop if we've reached max_total limit
                    if max_total > 0 and len(insights) >= max_total:
                        logging.info(f"Reached max limit ({max_total}), stopping.")
                        insights = insights[:max_total]  # Trim to exact limit
                        break

                    # Check if there are more pages
                    cursor_info = pagination_info.get("cursor", {})
                    has_next = cursor_info.get("has_next", False)

                    if has_next:
                        next_cursor = cursor_info.get("next_cursor")
                        if not next_cursor:
                            logging.warning("has_next is true but next_cursor is missing!")
                            break
                        logging.info(f"Fetching next page...")
                    else:
                        logging.info(f"All pages fetched. Total insights: {len(insights)}")
                        break
                else:
                    logging.error(f"Error fetching CloudZero insights: {response.text}")
                    return {"error": response.text}

        except requests.RequestException as e:
            logging.error(f"Request error occurred: {e}")
            return {"error": str(e)}
        except Exception as e:
            logging.error(f"Unexpected error occurred: {e}")
            return {"error": str(e)}

        return insights

    def create_insight(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new insight in CloudZero.

        Args:
            data: Dictionary containing insight data

        Returns:
            Response dictionary from API or dict with error key
        """
        try:
            logging.info("Attempting to create a new CloudZero insight.")
            response = requests.post(self.BASE_URL, json=data, headers=self.headers)

            if response.status_code == 200:
                logging.info("CloudZero insight created successfully.")
                return response.json()
            else:
                logging.error(
                    f"Failed to create CloudZero insight. "
                    f"Status code: {response.status_code}, Response: {response.text}"
                )
                return {"error": response.text}

        except Exception as e:
            logging.error(f"An error occurred while creating CloudZero insight: {e}")
            return {"error": str(e)}

    def delete_insight(self, insight_id: str) -> Dict[str, Any]:
        """Delete an insight from CloudZero.

        Args:
            insight_id: ID of the insight to delete

        Returns:
            Response dictionary from API or dict with error key
        """
        try:
            url = f"{self.BASE_URL}/{insight_id}"
            logging.info(f"Attempting to delete CloudZero insight: {insight_id}")
            response = requests.delete(url, headers=self.headers)

            if response.status_code in [200, 204]:
                logging.info(f"CloudZero insight {insight_id} deleted successfully.")
                return {"success": True, "insight_id": insight_id}
            else:
                logging.error(
                    f"Failed to delete CloudZero insight {insight_id}. "
                    f"Status code: {response.status_code}, Response: {response.text}"
                )
                return {"error": response.text}

        except Exception as e:
            logging.error(f"An error occurred while deleting CloudZero insight: {e}")
            return {"error": str(e)}


def get_cloudzero_insights_list(cz_client: CloudZeroClient) -> List[Dict[str, Any]]:
    """Retrieve insights from CloudZero API.

    Args:
        cz_client: Authenticated CloudZero API client

    Returns:
        List of insight dictionaries from CloudZero

    Raises:
        requests.HTTPError: If API returns error status code
        requests.RequestException: If network error occurs
    """
    return cz_client.get_insights()


def create_cloudzero_insight(
    cz_client: CloudZeroClient,
    data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Sends a POST request to create an insight in CloudZero.

    Args:
    - cz_client (CloudZeroClient): CloudZero API client
    - data (dict): The data payload for creating an insight.

    Returns:
    - dict: The response from the CloudZero API.
    """
    return cz_client.create_insight(data)


def display_insights(cz_client: CloudZeroClient, limit: int = 10) -> None:
    """Display existing CloudZero insights in a formatted list.

    Args:
        cz_client: Authenticated CloudZero API client
        limit: Maximum number of insights to fetch and display (0 = all)

    Raises:
        requests.HTTPError: If API returns error status
    """
    if limit == 0:
        logging.warning("Fetching ALL insights - this may take ~70 minutes for 13K+ insights!")
        confirm = input("Continue? (yes/no): ")
        if confirm.lower() != "yes":
            print("Cancelled")
            return

    logging.info(f"Fetching up to {limit if limit > 0 else 'ALL'} insights from CloudZero...")

    # Fetch insights with max_total limit
    insights = cz_client.get_insights(page_size=100, max_total=limit)

    if isinstance(insights, dict) and "error" in insights:
        logging.error(f"Failed to fetch insights: {insights['error']}")
        return

    if not insights:
        print("\n✓ No insights found in CloudZero")
        return

    # Display insights
    display_count = len(insights) if limit == 0 else min(len(insights), limit)
    total_available = len(insights)

    print(f"\n✓ Displaying {display_count} of {total_available}+ insights:\n")
    print("-" * 80)

    for idx, insight in enumerate(insights[:display_count], 1):
        title = insight.get("title", "No title")
        status = insight.get("status", "unknown")
        cost_impact = insight.get("cost_impact", "N/A")
        source = insight.get("source", "unknown")
        created = insight.get("created", "unknown")
        last_updated = insight.get("last_updated", "unknown")

        print(f"{idx}. {title}")
        print(f"   Status: {status} | Cost Impact: ${cost_impact} | Source: {source}")
        print(f"   Created: {created} | Updated: {last_updated}")
        print("-" * 80)

    if limit > 0 and total_available > display_count:
        print(f"\n... and {total_available - display_count} more (use --limit=0 to see all)")
    else:
        print(f"\nTotal: {display_count} insights displayed")


def delete_insights(cz_client: CloudZeroClient, source_filter: str = "azure advisor", force: bool = False) -> None:
    """Delete insights from CloudZero with confirmation.

    Args:
        cz_client: Authenticated CloudZero API client
        source_filter: Filter insights by source (default: "azure advisor")
        force: Skip confirmation prompt if True

    Raises:
        requests.HTTPError: If API returns error status
    """
    logging.info(f"Fetching insights to delete (source={source_filter})...")
    insights = get_cloudzero_insights_list(cz_client)

    if "error" in insights:
        logging.error(f"Failed to fetch insights: {insights['error']}")
        return

    if not insights:
        print("\n✓ No insights found to delete")
        return

    # Filter by source
    filtered = [i for i in insights if i.get("source", "").lower() == source_filter.lower()]

    if not filtered:
        print(f"\n✓ No insights found with source='{source_filter}'")
        return

    print(f"\n⚠️  Found {len(filtered)} insights to delete:")
    for idx, insight in enumerate(filtered[:5], 1):
        print(f"  {idx}. {insight.get('title', 'No title')} (${insight.get('cost_impact', 'N/A')})")
    if len(filtered) > 5:
        print(f"  ... and {len(filtered) - 5} more")

    # Confirmation prompt (unless forced)
    if not force:
        print(f"\n⚠️  WARNING: This will delete {len(filtered)} insights from CloudZero!")
        confirm = input("Type 'DELETE' to confirm: ")
        if confirm != "DELETE":
            print("❌ Deletion cancelled")
            return

    print(f"\n🗑️  Deleting {len(filtered)} insights...")
    deleted = 0
    failed = 0

    for insight in filtered:
        insight_id = insight.get("id")
        if not insight_id:
            logging.warning("Insight missing ID, skipping")
            failed += 1
            continue

        response = cz_client.delete_insight(insight_id)

        if "error" in response:
            logging.error(f"Failed to delete {insight_id}: {response['error']}")
            failed += 1
        else:
            deleted += 1

    print(f"\n✓ Deleted {deleted}/{deleted + failed} insights")
    if failed > 0:
        print(f"⚠️  Failed to delete {failed} insights (check logs)")
