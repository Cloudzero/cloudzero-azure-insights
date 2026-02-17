# SPDX-FileCopyrightText: Copyright (c) 2016-2023, CloudZero, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Client modules for external services (Azure, CloudZero)."""

from app.clients.azure_client import (
    AzureClientFactory,
    list_azure_subscription_ids,
    get_advisor_recommendations
)
from app.clients.cloudzero_client import (
    CloudZeroClient,
    get_cloudzero_insights_list,
    create_cloudzero_insight,
    display_insights,
    delete_insights
)

__all__ = [
    "AzureClientFactory",
    "list_azure_subscription_ids",
    "get_advisor_recommendations",
    "CloudZeroClient",
    "get_cloudzero_insights_list",
    "create_cloudzero_insight",
    "display_insights",
    "delete_insights",
]
