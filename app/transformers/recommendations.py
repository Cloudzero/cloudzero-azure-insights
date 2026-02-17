# SPDX-FileCopyrightText: Copyright (c) 2016-2023, CloudZero, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import logging
from typing import List, Dict, Any


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
