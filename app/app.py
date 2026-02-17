# SPDX-FileCopyrightText: Copyright (c) 2016-2023, CloudZero, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import argparse
import csv
import logging
import os
import requests
import urllib.parse
from typing import List, Dict, Any, Optional

from azure.identity import ClientSecretCredential
from azure.mgmt.resource import SubscriptionClient
from azure.mgmt.advisor import AdvisorManagementClient


# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


class AzureClientFactory:
    """Factory for creating Azure clients with shared credentials."""

    def __init__(self, client_id: str, client_secret: str, tenant_id: str) -> None:
        """Initialize factory with Azure credentials.

        Args:
            client_id: Azure application client ID
            client_secret: Azure application client secret
            tenant_id: Azure tenant ID
        """
        self.credentials = ClientSecretCredential(
            client_id=client_id,
            client_secret=client_secret,
            tenant_id=tenant_id
        )

    def create_subscription_client(self) -> SubscriptionClient:
        """Create an Azure SubscriptionClient."""
        return SubscriptionClient(self.credentials)

    def create_advisor_client(self, subscription_id: str) -> AdvisorManagementClient:
        """Create an Azure AdvisorManagementClient for a subscription."""
        return AdvisorManagementClient(self.credentials, subscription_id)


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

    def get_insights(self, source: str = "azure advisor", limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve insights from CloudZero filtered by source.

        Args:
            source: Source filter for insights (default: "azure advisor")
            limit: Items per page (default: 100)

        Returns:
            List of insight dictionaries or dict with error key
        """
        logging.info(f"Fetching CloudZero insights with source={source}...")

        insights = []
        next_cursor = None
        base_url = f"{self.BASE_URL}?source={urllib.parse.quote(source)}&limit={limit}"
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


def create_directory_if_not_exists(directory_name: str) -> None:
    """Create a directory if it does not exist.

    Args:
        directory_name: Name of the directory to create

    Raises:
        OSError: If directory creation fails due to permissions or disk space
    """
    # Check if directory exists
    if not os.path.exists(directory_name):
        # Create directory
        os.makedirs(directory_name)
        logging.info(f"Directory '{directory_name}' created.")
    else:
        logging.info(f"Directory '{directory_name}' already exists.")


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


def list_azure_subscription_ids(subscription_client: SubscriptionClient) -> List[str]:
    """List all Azure subscription IDs accessible by the client.

    Args:
        subscription_client: Authenticated Azure subscription client

    Returns:
        List of subscription ID strings, empty list if error occurs

    Raises:
        azure.core.exceptions.AzureError: If Azure API call fails
    """

    logging.info("Listing Azure subscription IDs...")

    try:
        subscriptions = subscription_client.subscriptions.list()
        subscription_ids = [
            subscription.subscription_id for subscription in subscriptions
        ]
        logging.info(f"Retrieved {len(subscription_ids)} Azure subscription IDs.")

        return subscription_ids

    except Exception as e:
        logging.error(f"Error occurred while fetching Azure subscription IDs: {e}")
        return []


def get_advisor_recommendations(
    azure_factory: AzureClientFactory,
    subscriptions: List[str]
) -> List[Dict[str, Any]]:
    """Fetch Azure Advisor cost recommendations for all subscriptions.

    Args:
        azure_factory: Factory for creating Azure Advisor clients
        subscriptions: List of Azure subscription IDs

    Returns:
        List of recommendation dictionaries from Azure Advisor

    Raises:
        azure.core.exceptions.AzureError: If Azure API call fails for any subscription
    """

    logging.info(
        "Fetching Azure Advisor cost recommendations for provided subscriptions."
    )

    all_recommendations = []

    for subscription_id in subscriptions:
        try:
            advisor_client = azure_factory.create_advisor_client(subscription_id)
            recommendations = advisor_client.recommendations.list(
                filter="Category eq 'Cost'"
            )

            all_recommendations.extend([rec.as_dict() for rec in recommendations])
            logging.info(
                f"Retrieved Azure Advisor cost recommendations for subscription ID: {subscription_id}"
            )

        except Exception as e:
            logging.error(
                f"Failed to fetch Azure Advisor cost recommendations for subscription ID {subscription_id}: {e}"
            )

    return all_recommendations


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


def _get_savings_amount(rec: Dict[str, Any]) -> str:
    """Extract savings amount from recommendation safely."""
    if "extended_properties" in rec and "savingsAmount" in rec["extended_properties"]:
        return rec["extended_properties"]["savingsAmount"]
    return "0"


def _format_recommendation_details(rec: Dict[str, Any]) -> str:
    """Format extended properties or short description for display."""
    details = rec.get("extended_properties", rec.get("short_description", {}))
    if isinstance(details, dict):
        details = details.copy()

    return (
        str(details)
        .replace("'", "")
        .replace("{", "")
        .replace("}", "")
        .replace(",", "\n\n")
    )


def _build_description_header(rec: Dict[str, Any]) -> str:
    """Build description header with subscription ID and recommendation ID."""
    subscription_id = rec["id"].split("/")[2] if "/" in rec.get("id", "") else "unknown"
    rec_id = rec.get("name", "unknown")
    return f"Azure Subscription ID: {subscription_id}\n\nAzure Advisor Recommendation ID: {rec_id}\n\n"


def _create_collapsed_entry(rec: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new collapsed recommendation entry."""
    title = rec["short_description"]["problem"]
    return {
        "title": title,
        "cost_impact": _get_savings_amount(rec),
        "description": _build_description_header(rec) + _format_recommendation_details(rec),
        "effort": "medium",
        "category": "optimization",
        "status": "new",
        "source": "Azure Advisor",
    }


def _merge_into_collapsed(collapsed: Dict[str, Dict[str, Any]], title: str, rec: Dict[str, Any]) -> None:
    """Merge recommendation into existing collapsed entry."""
    # Add to cost impact
    current_cost = float(collapsed[title]["cost_impact"])
    additional_cost = float(_get_savings_amount(rec))
    collapsed[title]["cost_impact"] = str(current_cost + additional_cost)

    # Append to description
    separator = "\n\n---\n\n"
    collapsed[title]["description"] += separator + _build_description_header(rec) + _format_recommendation_details(rec)


def collapse_recommendations(recs: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Collapse recommendations with identical titles into single records.

    Combines recommendations by title, aggregating cost impacts and
    concatenating descriptions. Empty input returns empty dict.

    Args:
        recs: List of Azure Advisor recommendation dictionaries

    Returns:
        Dictionary mapping recommendation titles to collapsed entries

    Raises:
        KeyError: If recommendation missing required fields
        ValueError: If cost calculation fails due to invalid data
    """

    collapsed = {}

    if not recs:
        logging.info("No Azure Advisor recommendations available to collapse.")
        return collapsed

    logging.info(f"Starting to collapse {len(recs)} Azure Advisor recommendations.")

    for rec in recs:
        try:
            title = rec["short_description"]["problem"]

            if title not in collapsed:
                collapsed[title] = _create_collapsed_entry(rec)
            else:
                _merge_into_collapsed(collapsed, title, rec)

        except KeyError as ke:
            logging.warning(f"Key error encountered in recommendation: {ke}")
            logging.info(f"Available keys: {rec.keys()}")
        except (ValueError, TypeError) as e:
            logging.error(f"Error processing recommendation: {e}")

    logging.info(
        f"Successfully collapsed {len(recs)} Azure Advisor recommendations to {len(collapsed)}."
    )
    return collapsed


def filter_azure_advisor_recs(
    cz_insights: List[Dict[str, Any]],
    azure_advisor_recs: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Filter out Azure Advisor recommendations already in CloudZero.

    Prevents duplicate insights by checking recommendation IDs against
    existing CloudZero insights. If no existing insights, returns all recs.

    Args:
        cz_insights: List of existing CloudZero insight dictionaries
        azure_advisor_recs: List of Azure Advisor recommendation dictionaries

    Returns:
        Filtered list of recommendations not yet in CloudZero

    Raises:
        AttributeError: If insight structure is invalid
    """
    try:
        logging.info(
            f"Starting to filter {len(azure_advisor_recs)} Azure Advisor recommendations based on existing Azure Advisor CloudZero insights to prevent duplicates."
        )

        if not cz_insights:
            logging.info("No existing Azure Advisor CloudZero insights.")
            return azure_advisor_recs

        # Extract recommendation IDs from CloudZero insights
        cz_recommendation_ids = set()
        for insight in cz_insights:
            description = insight.get("description", "")
            lines = description.split("\n")
            for line in lines:
                if "Azure Advisor Recommendation ID:" in line:
                    _, rec_id = line.split(": ", 1)
                    cz_recommendation_ids.add(rec_id.strip())

        # Filter Azure Advisor recommendations
        filtered_recs = [
            rec
            for rec in azure_advisor_recs
            if rec.get("name") not in cz_recommendation_ids
        ]

        logging.info(f"Remaining recommendations: {len(filtered_recs)}.")
        return filtered_recs

    except Exception as e:
        logging.error(
            f"An error occurred while filtering Azure Advisor recommendations: {e}"
        )
        return []


def transmit_azure_insights(
    cz_client: CloudZeroClient,
    recommendations: List[Dict[str, Any]],
    dry_run: bool = False
) -> None:
    """Transmit Azure Advisor insights to CloudZero.

    Args:
        cz_client: Authenticated CloudZero API client
        recommendations: List of Azure Advisor recommendations
        dry_run: If True, preview without actually uploading

    Raises:
        requests.HTTPError: If CloudZero API call fails
    """
    mode = "DRY RUN - Previewing" if dry_run else "Transmitting"
    logging.info(f"{mode} Azure Advisor insights to CloudZero...")

    logging.info("Fetching existing CloudZero Azure insights...")
    cz_insights = get_cloudzero_insights_list(cz_client)

    logging.info("Filtering Azure Advisor recommendations...")
    filtered_recs = filter_azure_advisor_recs(cz_insights, recommendations)

    insights_created = 0
    insights_failed = 0

    for rec in collapse_recommendations(filtered_recs).values():
        if dry_run:
            # Preview mode: just log what would be uploaded
            desc_preview = rec['description'][:100] + "..." if len(rec['description']) > 100 else rec['description']
            print(f"\n[DRY RUN] Would upload:")
            print(f"  Title: {rec['title']}")
            print(f"  Cost Impact: ${rec['cost_impact']}")
            print(f"  Category: {rec['category']} | Effort: {rec['effort']}")
            print(f"  Description: {desc_preview}")
            insights_created += 1
        else:
            # Actually upload
            response = create_cloudzero_insight(cz_client, rec)

            if "error" in response:
                logging.info(f"Insight NOT transmitted: {rec['title']}")
                insights_failed += 1
            else:
                logging.info(
                    f"Insight transmitted to CloudZero: {response['insight']['title']}"
                )
                insights_created += 1

    summary = f"[DRY RUN] Would upload" if dry_run else "Insights transmitted to CloudZero"
    logging.info(f"{summary}: {insights_created}/{insights_created + insights_failed}")


def convert_to_csv(data: List[Dict[str, Any]]) -> tuple[List[str], List[Dict[str, Any]]]:
    logging.info("Converting data to CSV format")
    extended_properties_keys = set()
    for record in data:
        if "extended_properties" in record and isinstance(
            record["extended_properties"], dict
        ):
            extended_properties_keys.update(record["extended_properties"].keys())

    csv_columns = [
        "id",
        "subscription_id",
        "recommendation_id",
        "short_description",
    ] + list(extended_properties_keys)
    csv_data = []

    for record in data:
        try:
            id = record.get("id", "")
            sub_id = id.split("/")[2] if "/" in id else "unknown"
            row = {
                "id": id,
                "subscription_id": sub_id,
                "recommendation_id": record.get("name", ""),
                "short_description": record.get("short_description", {}).get(
                    "solution", ""
                ),
            }

            for key in extended_properties_keys:
                row[key] = record.get("extended_properties", {}).get(key, "")

            csv_data.append(row)
        except Exception as e:
            logging.error(f"Error processing record: {e}")

    return csv_columns, csv_data


def export_to_csv(recommendations: List[Dict[str, Any]]) -> None:
    logging.info("Exporting recommendations to CSV")
    csv_columns, csv_data = convert_to_csv(recommendations)

    target_directory = "output"
    create_directory_if_not_exists(target_directory)

    csv_file = f"./{target_directory}/azure_advisor_recommendations.csv"
    try:
        with open(csv_file, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
            writer.writeheader()
            for data in csv_data:
                writer.writerow(data)
        logging.info(f"Data successfully exported to {csv_file}")
    except IOError as e:
        logging.error(f"IOError while writing to CSV: {e}")


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


def display_insights(cz_client: CloudZeroClient) -> None:
    """Display existing CloudZero insights in a formatted list.

    Args:
        cz_client: Authenticated CloudZero API client

    Raises:
        requests.HTTPError: If API returns error status
    """
    logging.info("Fetching insights from CloudZero...")
    insights = get_cloudzero_insights_list(cz_client)

    if "error" in insights:
        logging.error(f"Failed to fetch insights: {insights['error']}")
        return

    if not insights:
        print("\n✓ No insights found in CloudZero")
        return

    print(f"\n✓ Found {len(insights)} insights in CloudZero:\n")
    print("-" * 80)

    for idx, insight in enumerate(insights, 1):
        title = insight.get("title", "No title")
        status = insight.get("status", "unknown")
        cost_impact = insight.get("cost_impact", "N/A")
        source = insight.get("source", "unknown")
        created = insight.get("created_at", "unknown")

        print(f"{idx}. {title}")
        print(f"   Status: {status} | Cost Impact: ${cost_impact} | Source: {source}")
        print(f"   Created: {created}")
        print("-" * 80)

    print(f"\nTotal: {len(insights)} insights")


def main(args: argparse.Namespace) -> None:
    logging.info("Starting application...")

    client_id = os.environ.get("AZURE_CLIENT_ID")
    client_secret = os.environ.get("AZURE_CLIENT_SECRET")
    tenant_id = os.environ.get("AZURE_TENANT_ID")
    cz_api_key = os.environ.get("CLOUDZERO_API_KEY")

    if not all([client_id, client_secret, tenant_id, cz_api_key]):
        raise ValueError(
            "Environment variables for Azure and CloudZero are not set correctly."
        )

    # Create clients
    cz_client = CloudZeroClient(cz_api_key)

    # Handle list-insights (CloudZero only, no Azure needed)
    if args.list_insights:
        display_insights(cz_client)
        logging.info("Application finished.")
        return

    # For other operations, need Azure clients
    azure_factory = AzureClientFactory(client_id, client_secret, tenant_id)
    subscription_client = azure_factory.create_subscription_client()

    logging.info("Fetching Azure subscription IDs...")
    subscriptions = list_azure_subscription_ids(subscription_client)

    logging.info("Fetching Azure Advisor cost recommendations...")
    recommendations = get_advisor_recommendations(azure_factory, subscriptions)

    if args.transmit and args.export_csv:
        # Code to transmit to CloudZero and export to CSV
        transmit_azure_insights(cz_client, recommendations, dry_run=args.dry_run)
        export_to_csv(recommendations)

    elif args.transmit:
        # Code to only transmit to CloudZero
        transmit_azure_insights(cz_client, recommendations, dry_run=args.dry_run)

    elif args.export_csv:
        # Code to only export to CSV
        export_to_csv(recommendations)

    logging.info("Application finished.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CloudZero Azure Insights")
    parser.add_argument(
        "--transmit", action="store_true", help="Transmit Azure Insights to CloudZero"
    )
    parser.add_argument(
        "--export-csv", action="store_true", help="Export Azure Insights to a CSV file"
    )
    parser.add_argument(
        "--list-insights", action="store_true", help="List existing insights from CloudZero"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview what would be uploaded without actually uploading"
    )

    args = parser.parse_args()
    main(args)
