# SPDX-FileCopyrightText: Copyright (c) 2016-2023, CloudZero, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import csv
import logging
from typing import List, Dict, Any

from app.utils import create_directory_if_not_exists


def convert_to_csv(data: List[Dict[str, Any]]) -> tuple[List[str], List[Dict[str, Any]]]:
    """Convert Azure Advisor recommendations to CSV format.

    Args:
        data: List of Azure Advisor recommendation dictionaries

    Returns:
        Tuple of (column names list, CSV row data list)

    Raises:
        KeyError: If recommendation missing expected fields
    """
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
    """Export Azure Advisor recommendations to CSV file.

    Args:
        recommendations: List of Azure Advisor recommendation dictionaries

    Raises:
        IOError: If file write operation fails
    """
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
