# SPDX-FileCopyrightText: Copyright (c) 2016-2023, CloudZero, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import logging
from typing import List, Dict, Any

# Import source constant for consistency and safety
from app.clients.cloudzero_client import AZURE_ADVISOR_SOURCE


# =============================================================================
# ONE-TO-ONE MAPPING FUNCTIONS (New Approach)
# =============================================================================

def extract_resource_name(rec: Dict[str, Any]) -> str:
    """Extract resource name from Azure recommendation.

    Args:
        rec: Azure Advisor recommendation dictionary

    Returns:
        Resource name or 'unknown-resource' if not found
    """
    extended = rec.get("extended_properties", {})
    return extended.get("roleName") or extended.get("resourceName") or "unknown-resource"


def extract_category(rec: Dict[str, Any]) -> str:
    """Extract and normalize category from Azure recommendation.

    Args:
        rec: Azure Advisor recommendation dictionary

    Returns:
        Lowercase category string, defaults to "cost"
    """
    category = rec.get("category", "Cost")
    return category.lower()


def map_effort_level(azure_impact: str) -> str:
    """Map Azure impact level to CloudZero effort level.

    Azure uses: High, Medium, Low
    CloudZero uses: high, medium, low, not_set

    Args:
        azure_impact: Impact level from Azure Advisor

    Returns:
        CloudZero effort level (lowercase)
    """
    impact_map = {
        "High": "high",
        "Medium": "medium",
        "Low": "low"
    }
    return impact_map.get(azure_impact, "medium")


def build_insight_title(rec: Dict[str, Any]) -> str:
    """Build specific insight title with resource details.

    Format: "{recommendation}: {resource} ({current_sku} → {target_sku})"
    Falls back to "{recommendation}: {resource}" if SKU info unavailable.

    Args:
        rec: Azure Advisor recommendation dictionary

    Returns:
        Formatted title string (truncated to 200 chars if needed)

    Raises:
        KeyError: If short_description.problem is missing
    """
    title = rec["short_description"]["problem"]
    resource = extract_resource_name(rec)
    extended = rec.get("extended_properties", {})

    current_sku = extended.get("currentSku", "")
    target_sku = extended.get("targetSku", "")

    if current_sku and target_sku and target_sku != "Shutdown":
        # Format: "Right-size VM: vm-name (D8 → B8)"
        specific = f"{title}: {resource} ({current_sku} → {target_sku})"
    elif target_sku == "Shutdown":
        # Format: "Shutdown VM: vm-name"
        specific = f"Shutdown {resource}"
    else:
        # Fallback: "Right-size VM: vm-name"
        specific = f"{title}: {resource}"

    # Truncate to CloudZero limit
    return specific[:200] if len(specific) > 200 else specific


def format_single_recommendation(rec: Dict[str, Any], subscription_id: str) -> str:
    """Format a single Azure recommendation as human-readable description.

    Creates structured description with sections:
    - Subscription and region info
    - Resource details
    - Current vs recommended configuration
    - Savings and impact
    - Utilization metrics (if available)
    - Azure Advisor recommendation ID

    Args:
        rec: Azure Advisor recommendation dictionary
        subscription_id: Azure subscription ID

    Returns:
        Formatted multi-line description string
    """
    extended = rec.get("extended_properties", {})

    # Basic info
    resource = extract_resource_name(rec)
    region = extended.get("regionId", "unknown")
    rec_id = rec.get("name", "unknown")

    # Configuration
    current_sku = extended.get("currentSku", "N/A")
    target_sku = extended.get("targetSku", "N/A")
    rec_message = extended.get("recommendationMessage", "")

    # Savings
    monthly_savings = extended.get("savingsAmount", "0")
    annual_savings = extended.get("annualSavingsAmount", "0")
    currency = extended.get("savingsCurrency", "USD")

    # Carbon impact
    carbon_savings = extended.get("PotentialMonthlyCarbonSavings", "0")

    # Utilization (if available)
    cpu = extended.get("MaxCpuP95", "N/A")
    memory = extended.get("MaxMemoryP95", "N/A")
    network = extended.get("MaxTotalNetworkP95", "N/A")

    # Build description (plain text - CloudZero does not support markdown)
    parts = [
        f"Subscription: {subscription_id}",
        f"Region: {region}",
        f"Resource: {resource}",
        "",
        f"Current SKU: {current_sku}",
        f"Recommended SKU: {target_sku}",
    ]

    if rec_message:
        parts.append(f"Reason: {rec_message}")

    parts.extend([
        "",
        f"Monthly Savings: {currency} ${monthly_savings}",
        f"Annual Savings: {currency} ${annual_savings}",
    ])

    if carbon_savings and carbon_savings != "0":
        parts.append(f"Carbon Savings: {carbon_savings} kg CO2/month")

    # Add utilization if available
    if cpu != "N/A" or memory != "N/A":
        parts.extend([
            "",
            f"Utilization: CPU: {cpu}%, Memory: {memory}%, Network: {network}%"
        ])

    parts.extend([
        "",
        f"Azure Advisor Recommendation ID: {rec_id}"
    ])

    return "\n".join(parts)


def create_individual_insight(
    rec: Dict[str, Any],
    subscription_id: str
) -> Dict[str, Any]:
    """Create a CloudZero insight for a single Azure Advisor recommendation.

    Maps Azure Advisor recommendation to CloudZero insight with enhanced
    field usage for better tracking and filtering.

    Args:
        rec: Azure Advisor recommendation dictionary
        subscription_id: Azure subscription ID

    Returns:
        Dictionary containing CloudZero insight data

    Raises:
        KeyError: If required fields missing from recommendation
    """
    return {
        "title": build_insight_title(rec),
        "description": format_single_recommendation(rec, subscription_id),
        "category": extract_category(rec),
        "status": "new",
        "effort": map_effort_level(rec.get("impact", "Medium")),
        "cost_impact": rec.get("extended_properties", {}).get("savingsAmount", "0"),
        "source": AZURE_ADVISOR_SOURCE
    }


# =============================================================================
# COLLAPSED MAPPING FUNCTIONS (Legacy Approach - To Be Deprecated)
# =============================================================================


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
        "source": AZURE_ADVISOR_SOURCE,
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
