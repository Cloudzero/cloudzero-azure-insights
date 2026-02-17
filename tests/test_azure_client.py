# SPDX-FileCopyrightText: Copyright (c) 2016-2023, CloudZero, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import pytest
from unittest.mock import Mock

from app.clients import (
    AzureClientFactory,
    list_azure_subscription_ids,
    get_advisor_recommendations
)


class TestAzureClientFactory:
    """Tests for AzureClientFactory class."""

    def test_init_creates_credentials(self):
        """AzureClientFactory should create ClientSecretCredential with provided credentials."""
        factory = AzureClientFactory("client-id", "client-secret", "tenant-id")

        assert factory.credentials is not None
        assert hasattr(factory, 'credentials')

    def test_create_subscription_client(self):
        """create_subscription_client should return SubscriptionClient."""
        factory = AzureClientFactory("client-id", "client-secret", "tenant-id")

        client = factory.create_subscription_client()

        assert client is not None

    def test_create_advisor_client(self):
        """create_advisor_client should return AdvisorManagementClient for subscription."""
        factory = AzureClientFactory("client-id", "client-secret", "tenant-id")

        client = factory.create_advisor_client("subscription-id")

        assert client is not None


class TestListAzureSubscriptionIds:
    """Tests for list_azure_subscription_ids function."""

    def test_returns_list_of_subscription_ids(self):
        """Should return list of subscription IDs from SubscriptionClient."""
        # Arrange
        mock_client = Mock()
        mock_sub1 = Mock()
        mock_sub1.subscription_id = "sub-1"
        mock_sub2 = Mock()
        mock_sub2.subscription_id = "sub-2"
        mock_client.subscriptions.list.return_value = [mock_sub1, mock_sub2]

        # Act
        result = list_azure_subscription_ids(mock_client)

        # Assert
        assert result == ["sub-1", "sub-2"]

    def test_returns_empty_list_on_exception(self):
        """Should return empty list when Azure API raises exception."""
        # Arrange
        mock_client = Mock()
        mock_client.subscriptions.list.side_effect = Exception("Azure error")

        # Act
        result = list_azure_subscription_ids(mock_client)

        # Assert
        assert result == []


class TestGetAdvisorRecommendations:
    """Tests for get_advisor_recommendations function."""

    def test_returns_recommendations_from_multiple_subscriptions(self):
        """Should return aggregated recommendations from all subscriptions."""
        # Arrange
        mock_factory = Mock(spec=AzureClientFactory)
        mock_advisor_client = Mock()

        mock_rec1 = Mock()
        mock_rec1.as_dict.return_value = {"id": "rec-1", "name": "Recommendation 1"}
        mock_rec2 = Mock()
        mock_rec2.as_dict.return_value = {"id": "rec-2", "name": "Recommendation 2"}

        mock_advisor_client.recommendations.list.return_value = [mock_rec1, mock_rec2]
        mock_factory.create_advisor_client.return_value = mock_advisor_client

        subscriptions = ["sub-1", "sub-2"]

        # Act
        result = get_advisor_recommendations(mock_factory, subscriptions)

        # Assert
        assert len(result) == 4  # 2 recs per subscription * 2 subscriptions
        assert mock_factory.create_advisor_client.call_count == 2

    def test_continues_on_subscription_error(self):
        """Should continue processing other subscriptions when one fails."""
        # Arrange
        mock_factory = Mock(spec=AzureClientFactory)
        mock_advisor_client1 = Mock()
        mock_advisor_client1.recommendations.list.side_effect = Exception("Azure error")

        mock_advisor_client2 = Mock()
        mock_rec = Mock()
        mock_rec.as_dict.return_value = {"id": "rec-1"}
        mock_advisor_client2.recommendations.list.return_value = [mock_rec]

        mock_factory.create_advisor_client.side_effect = [mock_advisor_client1, mock_advisor_client2]

        subscriptions = ["sub-1", "sub-2"]

        # Act
        result = get_advisor_recommendations(mock_factory, subscriptions)

        # Assert
        assert len(result) == 1
        assert result[0]["id"] == "rec-1"

    def test_returns_empty_list_for_empty_subscriptions(self):
        """Should return empty list when no subscriptions provided."""
        # Arrange
        mock_factory = Mock(spec=AzureClientFactory)

        # Act
        result = get_advisor_recommendations(mock_factory, [])

        # Assert
        assert result == []
        mock_factory.create_advisor_client.assert_not_called()
