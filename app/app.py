# SPDX-FileCopyrightText: Copyright (c) 2016-2023, CloudZero, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import argparse
import logging
import os
from typing import List, Dict, Any

from app.clients import (
    AzureClientFactory,
    CloudZeroClient,
    list_azure_subscription_ids,
    get_advisor_recommendations,
    get_cloudzero_insights_list,
    create_cloudzero_insight,
    display_insights
)
from app.transformers import collapse_recommendations, filter_azure_advisor_recs
from app.exporters import export_to_csv


# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


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


def main(args: argparse.Namespace) -> None:
    """Main entry point for CloudZero Azure Insights application.

    Args:
        args: Parsed command-line arguments

    Raises:
        ValueError: If required environment variables are missing
    """
    logging.info("Starting application...")

    cz_api_key = os.environ.get("CLOUDZERO_API_KEY")

    # Handle list-insights (CloudZero only, no Azure needed)
    if args.list_insights:
        if not cz_api_key:
            raise ValueError("CLOUDZERO_API_KEY environment variable is required.")
        cz_client = CloudZeroClient(cz_api_key)
        display_insights(cz_client, limit=args.limit)
        logging.info("Application finished.")
        return

    # For other operations, need all credentials
    client_id = os.environ.get("AZURE_CLIENT_ID")
    client_secret = os.environ.get("AZURE_CLIENT_SECRET")
    tenant_id = os.environ.get("AZURE_TENANT_ID")

    if not all([client_id, client_secret, tenant_id, cz_api_key]):
        raise ValueError(
            "Environment variables for Azure and CloudZero are not set correctly."
        )

    # Create clients
    cz_client = CloudZeroClient(cz_api_key)

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
        "--limit", type=int, default=10, help="Number of insights to display with --list-insights (0=all, default=10)"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview what would be uploaded without actually uploading"
    )

    args = parser.parse_args()
    main(args)
