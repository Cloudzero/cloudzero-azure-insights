# SPDX-FileCopyrightText: Copyright (c) 2016-2023, CloudZero, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""
Modern CLI for CloudZero Azure Insights using Click framework.

This module provides a clean subcommand-based interface:
    cz-azure sync [--dry-run]
    cz-azure export {csv|json}
    cz-azure list [--limit N]
    cz-azure delete --filter EXPR
    cz-azure validate
"""

import click
import logging
import os
import sys
from typing import Optional

from app.clients import (
    AzureClientFactory,
    CloudZeroClient,
    list_azure_subscription_ids,
    get_advisor_recommendations,
    get_cloudzero_insights_list,
    create_cloudzero_insight,
    display_insights,
    delete_insights
)
from app.transformers import (
    filter_azure_advisor_recs,
    create_individual_insight
)
from app.exporters import export_to_csv


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# ============================================================================
# CLI Group (Entry Point)
# ============================================================================

@click.group()
@click.version_option(version="2.0.0", prog_name="cz-azure")
def cli():
    """CloudZero Azure Advisor Integration

    Sync Azure Advisor cost recommendations to CloudZero as insights.

    \b
    Common workflows:
      cz-azure validate              # Check credentials
      cz-azure sync --dry-run        # Preview sync
      cz-azure sync                  # Full sync
      cz-azure list --limit 20       # View insights
      cz-azure export csv            # Export to CSV

    For detailed help on any command:
      cz-azure <command> --help
    """
    pass


# ============================================================================
# Helper Functions
# ============================================================================

def get_required_env(var_name: str) -> str:
    """Get required environment variable or exit with error."""
    value = os.environ.get(var_name)
    if not value:
        click.secho(f"❌ Error: {var_name} environment variable is required.", fg="red", err=True)
        click.echo(f"Please set {var_name} in your .env file or environment.", err=True)
        sys.exit(1)
    return value


def create_azure_factory() -> AzureClientFactory:
    """Create Azure client factory from environment variables."""
    return AzureClientFactory(
        client_id=get_required_env("AZURE_CLIENT_ID"),
        client_secret=get_required_env("AZURE_CLIENT_SECRET"),
        tenant_id=get_required_env("AZURE_TENANT_ID")
    )


def create_cloudzero_client() -> CloudZeroClient:
    """Create CloudZero client from environment variables."""
    return CloudZeroClient(api_key=get_required_env("CLOUDZERO_API_KEY"))


# ============================================================================
# Sync Command
# ============================================================================

@cli.command()
@click.option(
    "--dry-run",
    is_flag=True,
    help="Preview what would be synced without actually uploading"
)
@click.option(
    "--delete-duplicates",
    is_flag=True,
    help="Remove duplicate insights before syncing (future feature)"
)
def sync(dry_run: bool, delete_duplicates: bool):
    """Sync Azure Advisor recommendations to CloudZero

    Fetches cost recommendations from Azure Advisor and uploads them to
    CloudZero as insights. Each Azure recommendation becomes one CloudZero
    insight for better tracking and filtering.

    \b
    Examples:
      cz-azure sync --dry-run    # Preview without uploading
      cz-azure sync              # Full sync

    Note: First run may take 60-120 minutes for large deployments.
    """
    if dry_run:
        click.secho("🔍 DRY RUN MODE", fg="yellow", bold=True)
        click.echo("Previewing what would be uploaded (no actual changes)\n")

    try:
        # Create clients
        click.echo("Initializing Azure and CloudZero clients...")
        azure_factory = create_azure_factory()
        cz_client = create_cloudzero_client()

        # Get Azure subscriptions
        click.echo("Fetching Azure subscriptions...")
        subscription_client = azure_factory.create_subscription_client()
        subscriptions = list_azure_subscription_ids(subscription_client)

        if not subscriptions:
            click.secho("❌ No Azure subscriptions found", fg="red")
            sys.exit(1)

        click.secho(f"✓ Found {len(subscriptions)} subscription(s)", fg="green")

        # Get Azure Advisor recommendations
        click.echo("Fetching Azure Advisor recommendations...")
        recommendations = get_advisor_recommendations(azure_factory, subscriptions)
        click.secho(f"✓ Retrieved {len(recommendations)} recommendation(s)", fg="green")

        if not recommendations:
            click.secho("ℹ No recommendations to sync", fg="blue")
            return

        # Filter out duplicates
        click.echo("Checking for existing insights in CloudZero...")
        cz_insights = get_cloudzero_insights_list(cz_client)
        filtered_recs = filter_azure_advisor_recs(cz_insights, recommendations)
        click.secho(f"✓ {len(filtered_recs)} new recommendation(s) to sync", fg="green")

        if not filtered_recs:
            click.secho("ℹ All recommendations already exist in CloudZero", fg="blue")
            return

        # Sync recommendations
        insights_created = 0
        insights_failed = 0

        with click.progressbar(
            filtered_recs,
            label="Syncing recommendations",
            show_pos=True
        ) as recs:
            for rec in recs:
                try:
                    # Extract subscription ID from recommendation
                    subscription_id = rec["id"].split("/")[2] if "/" in rec.get("id", "") else "unknown"

                    # Create insight
                    insight_data = create_individual_insight(rec, subscription_id)

                    if dry_run:
                        # Just count in dry-run mode
                        insights_created += 1
                    else:
                        # Actually upload
                        response = create_cloudzero_insight(cz_client, insight_data)
                        if "error" in response:
                            insights_failed += 1
                            logger.error(f"Failed to create insight: {response['error']}")
                        else:
                            insights_created += 1

                except Exception as e:
                    insights_failed += 1
                    logger.error(f"Error processing recommendation: {e}")

        # Summary
        click.echo()
        if dry_run:
            click.secho(f"✓ [DRY RUN] Would create {insights_created} insight(s)", fg="yellow", bold=True)
        else:
            click.secho(f"✓ Successfully created {insights_created} insight(s)", fg="green", bold=True)

        if insights_failed > 0:
            click.secho(f"⚠ {insights_failed} insight(s) failed", fg="red")

    except Exception as e:
        click.secho(f"❌ Error: {e}", fg="red", err=True)
        if "--debug" in sys.argv:
            raise
        sys.exit(1)


# ============================================================================
# Export Command
# ============================================================================

@cli.command()
@click.argument("format", type=click.Choice(["csv", "json"], case_sensitive=False))
@click.option(
    "--output",
    "-o",
    default="output/",
    help="Output directory (default: output/)",
    show_default=True
)
def export(format: str, output: str):
    """Export Azure Advisor recommendations to file

    \b
    Supported formats:
      csv   CSV file with all recommendation details
      json  JSON file (future feature)

    \b
    Examples:
      cz-azure export csv
      cz-azure export csv --output ./reports/
    """
    try:
        # Create clients
        click.echo("Initializing Azure client...")
        azure_factory = create_azure_factory()

        # Get Azure subscriptions
        click.echo("Fetching Azure subscriptions...")
        subscription_client = azure_factory.create_subscription_client()
        subscriptions = list_azure_subscription_ids(subscription_client)

        if not subscriptions:
            click.secho("❌ No Azure subscriptions found", fg="red")
            sys.exit(1)

        click.secho(f"✓ Found {len(subscriptions)} subscription(s)", fg="green")

        # Get Azure Advisor recommendations
        click.echo("Fetching Azure Advisor recommendations...")
        recommendations = get_advisor_recommendations(azure_factory, subscriptions)
        click.secho(f"✓ Retrieved {len(recommendations)} recommendation(s)", fg="green")

        if not recommendations:
            click.secho("ℹ No recommendations to export", fg="blue")
            return

        # Export
        if format.lower() == "csv":
            click.echo(f"Exporting to CSV in {output}...")
            export_to_csv(recommendations)
            click.secho(f"✓ Successfully exported to {output}/azure_advisor_recommendations.csv", fg="green", bold=True)
        elif format.lower() == "json":
            click.secho("⚠ JSON export not yet implemented", fg="yellow")
            sys.exit(1)

    except Exception as e:
        click.secho(f"❌ Error: {e}", fg="red", err=True)
        if "--debug" in sys.argv:
            raise
        sys.exit(1)


# ============================================================================
# List Command
# ============================================================================

@cli.command()
@click.option(
    "--limit",
    type=int,
    default=10,
    help="Number of insights to display (0=all)",
    show_default=True
)
@click.option(
    "--filter",
    "filter_expr",
    help="Filter expression (future feature)"
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json"], case_sensitive=False),
    default="table",
    help="Output format",
    show_default=True
)
def list(limit: int, filter_expr: Optional[str], output_format: str):
    """List existing CloudZero insights

    \b
    Examples:
      cz-azure list                           # Show 10 insights
      cz-azure list --limit 20                # Show 20 insights
      cz-azure list --limit 0                 # Show all (slow!)
      cz-azure list --filter "source=azure"   # Filter (future)
    """
    try:
        if filter_expr:
            click.secho("⚠ Filtering not yet implemented", fg="yellow")

        # Create client
        cz_client = create_cloudzero_client()

        # Display insights
        click.echo(f"Fetching insights from CloudZero (limit={limit or 'all'})...")
        display_insights(cz_client, limit=limit)

    except Exception as e:
        click.secho(f"❌ Error: {e}", fg="red", err=True)
        if "--debug" in sys.argv:
            raise
        sys.exit(1)


# ============================================================================
# Delete Command
# ============================================================================

@cli.command()
@click.option(
    "--filter",
    "filter_expr",
    default="azure advisor",
    help="Source filter for insights to delete",
    show_default=True
)
@click.option(
    "--force",
    is_flag=True,
    help="Skip confirmation prompt"
)
@click.option(
    "--backup",
    is_flag=True,
    help="Backup insights before deletion (future feature)"
)
def delete(filter_expr: str, force: bool, backup: bool):
    """Delete insights from CloudZero

    ⚠️  DESTRUCTIVE OPERATION - Use with caution!

    \b
    Examples:
      cz-azure delete                         # Delete Azure Advisor insights (with confirmation)
      cz-azure delete --force                 # Skip confirmation
      cz-azure delete --filter "custom"       # Delete different source
    """
    try:
        if backup:
            click.secho("⚠ Backup feature not yet implemented", fg="yellow")

        # Create client
        cz_client = create_cloudzero_client()

        # Delete insights
        click.echo(f"Deleting insights from CloudZero (source={filter_expr})...")
        delete_insights(cz_client, source_filter=filter_expr, force=force)

    except Exception as e:
        click.secho(f"❌ Error: {e}", fg="red", err=True)
        if "--debug" in sys.argv:
            raise
        sys.exit(1)


# ============================================================================
# Validate Command
# ============================================================================

@cli.command()
@click.option("--azure", is_flag=True, help="Check Azure credentials only")
@click.option("--cloudzero", is_flag=True, help="Check CloudZero credentials only")
def validate(azure: bool, cloudzero: bool):
    """Validate Azure and CloudZero credentials

    Checks that all required environment variables are set and that
    API credentials are valid by making test API calls.

    \b
    Examples:
      cz-azure validate              # Check all credentials
      cz-azure validate --azure      # Check Azure only
      cz-azure validate --cloudzero  # Check CloudZero only
    """
    try:
        check_azure = azure or not cloudzero
        check_cloudzero = cloudzero or not azure

        all_valid = True

        if check_azure:
            click.echo("Validating Azure credentials...")
            try:
                azure_factory = create_azure_factory()
                subscription_client = azure_factory.create_subscription_client()
                subscriptions = list_azure_subscription_ids(subscription_client)
                click.secho(f"✓ Azure: Valid ({len(subscriptions)} subscription(s) found)", fg="green")
            except Exception as e:
                click.secho(f"❌ Azure: Invalid - {e}", fg="red")
                all_valid = False

        if check_cloudzero:
            click.echo("Validating CloudZero credentials...")
            try:
                cz_client = create_cloudzero_client()
                insights = cz_client.get_insights(page_size=1, max_total=1)
                if isinstance(insights, dict) and "error" in insights:
                    raise ValueError(insights["error"])
                click.secho("✓ CloudZero: Valid", fg="green")
            except Exception as e:
                click.secho(f"❌ CloudZero: Invalid - {e}", fg="red")
                all_valid = False

        if all_valid:
            click.echo()
            click.secho("✓ All credentials validated successfully", fg="green", bold=True)
        else:
            click.echo()
            click.secho("❌ Credential validation failed", fg="red", bold=True)
            sys.exit(1)

    except Exception as e:
        click.secho(f"❌ Error: {e}", fg="red", err=True)
        if "--debug" in sys.argv:
            raise
        sys.exit(1)


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    cli()
