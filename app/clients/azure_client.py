# SPDX-FileCopyrightText: Copyright (c) 2016-2023, CloudZero, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import logging
from typing import List, Dict, Any

from azure.identity import ClientSecretCredential
from azure.mgmt.resource import SubscriptionClient
from azure.mgmt.advisor import AdvisorManagementClient


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
