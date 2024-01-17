# SPDX-FileCopyrightText: Copyright (c) 2016-2023, CloudZero, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import argparse
import csv
import logging
import os
import requests

from azure.identity import ClientSecretCredential
from azure.mgmt.resource import SubscriptionClient
from azure.mgmt.advisor import AdvisorManagementClient


# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def create_directory_if_not_exists(directory_name):
    """
    Creates a directory if it does not exist.

    Args:
    - directory_name (str): Name of the directory to be created.

    Returns:
    - None
    """
    # Check if directory exists
    if not os.path.exists(directory_name):
        # Create directory
        os.makedirs(directory_name)
        print(f"Directory '{directory_name}' created.")
    else:
        print(f"Directory '{directory_name}' already exists.")


def get_cloudzero_insights_list(api_key):
    """
    Retrieve a list of insights from CloudZero.

    Args:
    - api_key (str): The API key for authenticating with CloudZero.

    Returns:
    - dict: The list of insights or error message.
    """

    logging.info("Fetching CloudZero insights list...")

    base_url = "https://api.cloudzero.com/v2/insights?source=azure%20advisor"
    headers = {"Authorization": api_key, "Content-Type": "application/json"}

    insights = []
    next_cursor = None

    try:
        while True:
            url = base_url + (f"?cursor={next_cursor}" if next_cursor else "")
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                data = response.json()
                insights.extend(data.get("insights", []))
                logging.info(f"Retrieved {len(data.get('insights', []))} insights.")

                pagination_info = data.get("pagination", {})
                if pagination_info.get("has_next"):
                    next_cursor = pagination_info["cursor"]["next_cursor"]
                else:
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


def list_azure_subscription_ids(client_id, client_secret, tenant_id):
    """
    Lists the IDs of all Azure subscriptions associated with the given credentials.

    Args:
    - client_id (str): The Azure client ID.
    - client_secret (str): The Azure client secret.
    - tenant_id (str): The Azure tenant ID.

    Returns:
    - list: A list of strings, where each string is an Azure subscription ID.
    """

    logging.info("Listing Azure subscription IDs...")

    try:
        credentials = ClientSecretCredential(
            client_id=client_id, client_secret=client_secret, tenant_id=tenant_id
        )

        subscription_client = SubscriptionClient(credentials)

        subscriptions = subscription_client.subscriptions.list()
        subscription_ids = [
            subscription.subscription_id for subscription in subscriptions
        ]
        logging.info(f"Retrieved {len(subscription_ids)} Azure subscription IDs.")

        return subscription_ids

    except Exception as e:
        logging.error(f"Error occurred while fetching Azure subscription IDs: {e}")
        return []


def get_advisor_recommendations(client_id, client_secret, tenant_id, subscriptions):
    """
    Fetches Azure Advisor recommendations for all subscriptions in the account.

    Args:
    - client_id (str): Azure client ID.
    - client_secret (str): Azure client secret.
    - tenant_id (str): Azure tenant ID.

    Returns:
    - list: A list Azure Advisor recommendations.
    """

    logging.info(
        "Fetching Azure Advisor cost recommendations for provided subscriptions."
    )

    try:
        credentials = ClientSecretCredential(
            client_id=client_id, client_secret=client_secret, tenant_id=tenant_id
        )

        all_recommendations = []

        for subscription_id in subscriptions:
            try:
                advisor_client = AdvisorManagementClient(credentials, subscription_id)
                recommendations = advisor_client.recommendations.list(
                    filter="Category eq 'Cost'"
                )

                all_recommendations.extend([rec.as_dict() for rec in recommendations])
                logging.info(
                    f"Retrieved Azure Advistor cost recommendations for subscription ID: {subscription_id}"
                )

            except Exception as e:
                logging.error(
                    f"Failed to fetch Azure Advistor cost recommendations for subscription ID {subscription_id}: {e}"
                )

        return all_recommendations

    except Exception as e:
        logging.error(
            f"An error occurred while fetching Azure Advisor cost recommendations: {e}"
        )
        return []


def create_cloudzero_insight(api_key, data):
    """
    Sends a POST request to create an insight in CloudZero.

    Args:
    - api_key (str): API key for authentication with CloudZero.
    - data (dict): The data payload for creating an insight.

    Returns:
    - dict: The response from the CloudZero API.
    """
    url = "https://api.cloudzero.com/v2/insights"
    headers = {"authorization": f"{api_key}", "accept": "application/json"}

    try:
        logging.info("Attempting to create a new CloudZero insight.")
        response = requests.post(url, json=data, headers=headers)

        if response.status_code == 200:
            logging.info("CloudZero insight created successfully.")
            return response.json()
        else:
            logging.error(
                f"Failed to create CloudZero insight. Status code: {response.status_code}, Response: {response.text}"
            )
            return {"error": response.text}

    except Exception as e:
        logging.error(f"An error occurred while creating CloudZero insight: {e}")
        return {"error": str(e)}


def collapse_recommendations(recs):
    """
    Collapses recommendations with the same title into a single record.

    Args:
    - recs (list of dict): List of recommendation records.

    Returns:
    - dict: A new list of collapsed recommendation records.
    """

    collapsed = {}

    if not recs:
        logging.info("No Azure Advisor recommendations available to collapse.")
        return collapsed

    try:
        logging.info(f"Starting to collapse {len(recs)} Azure Advisor recommendations.")

        for rec in recs:
            try:
                title = rec["short_description"]["problem"]
                if title not in collapsed:
                    collapsed[title] = {
                        "title": title,
                        "cost_impact": f"{rec['extended_properties']['savingsAmount'] if 'extended_properties' in rec and 'savingsAmount' in rec['extended_properties'] else '0'}",
                        "description": f"Azure Subscription ID: {rec['id'].split('/')[2]}\n\nAzure Advisor Recommendation ID: {rec['name']}\n\n"
                        + str(
                            rec["extended_properties"].copy()
                            if "extended_properties" in rec
                            else rec["short_description"]
                        )
                        .replace("'", "")
                        .replace("{", "")
                        .replace("}", "")
                        .replace(",", "\n\n"),
                        "effort": "medium",
                        "category": "optimization",
                        "status": "new",
                        "source": "Azure Advisor",
                    }
                else:
                    collapsed[title]["cost_impact"] = str(
                        float(collapsed[title]["cost_impact"])
                        + float(
                            rec["extended_properties"]["savingsAmount"]
                            if "extended_properties" in rec
                            and "savingsAmount" in rec["extended_properties"]
                            else "0"
                        )
                    )
                    collapsed[title]["description"] += (
                        f"\n\n---\n\nAzure Subscription ID: {rec['id'].split('/')[2]}\n\nAzure Advisor Recommendation ID: {rec['name']}\n\n"
                        + str(
                            rec["extended_properties"]
                            if "extended_properties" in rec
                            else rec["short_description"]
                        )
                        .replace("'", "")
                        .replace("{", "")
                        .replace("}", "")
                        .replace(",", "\n\n")
                    )
            except KeyError as ke:
                logging.warning(f"Key error encountered in recommendation: {ke}")
                logging.info(title)
                logging.info(
                    rec["extended_properties"].keys()
                    if "extended_properties" in rec
                    else rec.keys()
                )
            except Exception as e:
                logging.error(
                    f"Unexpected error during processing a recommendation: {e}"
                )

        logging.info(
            f"Successfully collapsed {len(recs)} Azure Advisor recommendations to {len(collapsed)}."
        )
        return collapsed

    except Exception as e:
        logging.error(
            f"An error occurred while collapsing Azure Advisor recommendations: {e}"
        )
        return {}


def filter_azure_advisor_recs(cz_insights, azure_advisor_recs):
    """
    Filters Azure Advisor recommendations based on CloudZero insights.

    Args:
    - cz_insights (list of dict): List of insights from CloudZero.
    - azure_advisor_recs (list of dict): List of recommendations from Azure Advisor.

    Returns:
    - list of dict: Filtered Azure Advisor recommendations.
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


def transmit_azure_insights(cz_api_key, recommendations):
    logging.info("Trasmitting Azure Advisor insights to CloudZero...")

    logging.info("Fetching existing CloudZero Azure insights...")
    cz_insights = get_cloudzero_insights_list(cz_api_key)

    logging.info("Filtering Azure Advisor recommendations...")
    filtered_recs = filter_azure_advisor_recs(cz_insights, recommendations)

    insights_created = 0
    insights_failed = 0
    for rec in collapse_recommendations(filtered_recs).values():
        response = create_cloudzero_insight(cz_api_key, rec)

        if "error" in response:
            logging.info(f"Insight NOT transmitted: {rec['title']}")
            insights_failed += 1

        else:
            logging.info(
                f"Insight trasmitted to CloudZero: {response['insight']['title']}"
            )
            insights_created += 1

    logging.info(
        f"Insights transmitted to CloudZero: {insights_created}/{insights_created + insights_failed}"
    )


def convert_to_csv(data):
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


def export_to_csv(recommendations):
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


def main(args):
    logging.info("Starting application...")

    client_id = os.environ.get("AZURE_CLIENT_ID")
    client_secret = os.environ.get("AZURE_CLIENT_SECRET")
    tenant_id = os.environ.get("AZURE_TENANT_ID")
    cz_api_key = os.environ.get("CLOUDZERO_API_KEY")

    if not all([client_id, client_secret, tenant_id, cz_api_key]):
        raise ValueError(
            "Environment variables for Azure and CloudZero are not set correctly."
        )

    logging.info("Fetching Azure subscription IDs...")
    subscriptions = list_azure_subscription_ids(client_id, client_secret, tenant_id)

    logging.info("Fetching Azure Advisor cost recommendations...")
    recommendations = get_advisor_recommendations(
        client_id, client_secret, tenant_id, subscriptions
    )

    if args.transmit and args.export_csv:
        # Code to transmit to CloudZero and export to CSV
        transmit_azure_insights(cz_api_key, recommendations)
        export_to_csv(recommendations)

    elif args.transmit:
        # Code to only transmit to CloudZero
        transmit_azure_insights(cz_api_key, recommendations)

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

    args = parser.parse_args()
    main(args)
