# SPDX-FileCopyrightText: Copyright (c) 2016-2023, CloudZero, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import logging
import requests
import urllib.parse
from typing import List, Dict, Any

# Source filter constant - ensures tool ONLY touches Azure Advisor insights
AZURE_ADVISOR_SOURCE = "azure advisor"


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
        source: str = AZURE_ADVISOR_SOURCE,
        page_size: int = 100,
        max_total: int = 0
    ) -> List[Dict[str, Any]]:
        """Retrieve insights from CloudZero filtered by source.

        **SAFETY**: This tool should ONLY access Azure Advisor insights.
        The source parameter is locked to "azure advisor" by default.

        Args:
            source: Source filter for insights (default: "azure advisor", DO NOT CHANGE)
            page_size: Items per API page (default: 100)
            max_total: Maximum total insights to fetch, 0=all (default: 0)

        Returns:
            List of insight dictionaries or dict with error key

        Raises:
            ValueError: If source is not "azure advisor"
        """
        # Safety check: Only allow Azure Advisor insights
        if source.lower() != AZURE_ADVISOR_SOURCE.lower():
            raise ValueError(
                f"This tool only operates on Azure Advisor insights. "
                f"Attempted to access source='{source}' which is not allowed."
            )

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
    """Retrieve Azure Advisor insights from CloudZero API.

    **SAFETY**: This function ONLY retrieves Azure Advisor insights.
    It explicitly filters by source="azure advisor" to prevent
    accidental modification of other CloudZero insights.

    Args:
        cz_client: Authenticated CloudZero API client

    Returns:
        List of Azure Advisor insight dictionaries from CloudZero

    Raises:
        requests.HTTPError: If API returns error status code
        requests.RequestException: If network error occurs
    """
    # Explicitly pass source to ensure safety
    return cz_client.get_insights(source=AZURE_ADVISOR_SOURCE)


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
    """Display existing Azure Advisor insights in a formatted list.

    **SAFETY**: Only displays Azure Advisor insights, not other CloudZero insights.

    Args:
        cz_client: Authenticated CloudZero API client
        limit: Maximum number of insights to fetch and display (0 = all)

    Raises:
        requests.HTTPError: If API returns error status
    """
    if limit == 0:
        logging.warning("Fetching ALL Azure Advisor insights - this may take ~70 minutes for 13K+ insights!")
        confirm = input("Continue? (yes/no): ")
        if confirm.lower() != "yes":
            print("Cancelled")
            return

    logging.info(f"Fetching up to {limit if limit > 0 else 'ALL'} Azure Advisor insights from CloudZero...")

    # Fetch Azure Advisor insights only (source filter enforced in get_insights)
    insights = cz_client.get_insights(source=AZURE_ADVISOR_SOURCE, page_size=100, max_total=limit)

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


def delete_insights(cz_client: CloudZeroClient, force: bool = False) -> None:
    """Delete Azure Advisor insights from CloudZero with confirmation.

    **SAFETY**: This function ONLY deletes Azure Advisor insights.
    It cannot access or delete other CloudZero insights.

    Args:
        cz_client: Authenticated CloudZero API client
        force: Skip confirmation prompt if True (USE WITH CAUTION)

    Raises:
        requests.HTTPError: If API returns error status
    """
    logging.info(f"Fetching Azure Advisor insights to delete...")
    insights = get_cloudzero_insights_list(cz_client)

    if isinstance(insights, dict) and "error" in insights:
        logging.error(f"Failed to fetch insights: {insights['error']}")
        return

    if not insights:
        print("\n✓ No Azure Advisor insights found to delete")
        return

    # Verify all insights are Azure Advisor (safety check)
    non_azure = [i for i in insights if i.get("source", "").lower() != AZURE_ADVISOR_SOURCE.lower()]
    if non_azure:
        logging.error(
            f"SAFETY ERROR: Found {len(non_azure)} non-Azure Advisor insights! "
            "This should never happen. Aborting deletion."
        )
        print(f"\n❌ ERROR: Found non-Azure Advisor insights. Aborting for safety.")
        return

    print(f"\n⚠️  Found {len(insights)} Azure Advisor insights to delete:")
    for idx, insight in enumerate(insights[:5], 1):
        print(f"  {idx}. {insight.get('title', 'No title')} (${insight.get('cost_impact', 'N/A')})")
    if len(insights) > 5:
        print(f"  ... and {len(insights) - 5} more")

    # Confirmation prompt (unless forced)
    if not force:
        print(f"\n⚠️  WARNING: This will delete {len(insights)} Azure Advisor insights from CloudZero!")
        print("⚠️  Other CloudZero insights will NOT be affected.")
        confirm = input("Type 'DELETE' to confirm: ")
        if confirm != "DELETE":
            print("❌ Deletion cancelled")
            return

    print(f"\n🗑️  Deleting {len(insights)} Azure Advisor insights...")
    deleted = 0
    failed = 0

    for insight in insights:
        insight_id = insight.get("id")
        insight_source = insight.get("source", "")

        # Double-check source before deletion (paranoid safety check)
        if insight_source.lower() != AZURE_ADVISOR_SOURCE.lower():
            logging.error(f"SAFETY: Skipping {insight_id} - source is '{insight_source}', not Azure Advisor")
            failed += 1
            continue

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

    print(f"\n✓ Deleted {deleted}/{deleted + failed} Azure Advisor insights")
    if failed > 0:
        print(f"⚠️  Failed to delete {failed} insights (check logs)")
