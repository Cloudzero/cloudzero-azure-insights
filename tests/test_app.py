# SPDX-FileCopyrightText: Copyright (c) 2016-2023, CloudZero, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import pytest
from unittest.mock import Mock, patch
from argparse import Namespace

from app.app import transmit_azure_insights, main
from app.clients import CloudZeroClient


class TestTransmitAzureInsights:
    """Tests for transmit_azure_insights orchestration function."""

    @patch('app.app.get_cloudzero_insights_list')
    @patch('app.app.filter_azure_advisor_recs')
    @patch('app.app.create_individual_insight')
    @patch('app.app.create_cloudzero_insight')
    def test_transmits_filtered_recommendations_with_one_to_one_mapping(
        self, mock_create, mock_create_individual, mock_filter, mock_get_insights
    ):
        """Should fetch, filter, and transmit recommendations using 1:1 mapping."""
        # Arrange
        mock_client = Mock(spec=CloudZeroClient)
        mock_get_insights.return_value = []
        mock_filter.return_value = [{
            "name": "rec-1",
            "id": "/subscriptions/sub-123/providers/...",
            "short_description": {"problem": "Test problem"},
            "extended_properties": {"savingsAmount": "100"}
        }]
        mock_create_individual.return_value = {
            "title": "Test",
            "cost_impact": "100",
            "category": "cost",
            "effort": "medium",
            "status": "new",
            "source": "Azure Advisor",
            "description": "Test description"
        }
        mock_create.return_value = {"insight": {"title": "Test"}}

        recommendations = [{
            "name": "rec-1",
            "id": "/subscriptions/sub-123/providers/...",
            "short_description": {"problem": "Test problem"},
            "extended_properties": {"savingsAmount": "100"}
        }]

        # Act
        transmit_azure_insights(mock_client, recommendations)

        # Assert
        mock_get_insights.assert_called_once_with(mock_client)
        mock_filter.assert_called_once()
        mock_create_individual.assert_called_once()
        mock_create.assert_called_once()

    @patch('app.app.get_cloudzero_insights_list')
    @patch('app.app.filter_azure_advisor_recs')
    @patch('app.app.create_individual_insight')
    @patch('app.app.create_cloudzero_insight')
    def test_dry_run_does_not_create_insights(
        self, mock_create, mock_create_individual, mock_filter, mock_get_insights
    ):
        """Should not create insights when dry_run is True."""
        # Arrange
        mock_client = Mock(spec=CloudZeroClient)
        mock_get_insights.return_value = []
        mock_filter.return_value = [{
            "name": "rec-1",
            "id": "/subscriptions/sub-123/providers/...",
            "short_description": {"problem": "Test problem"},
            "extended_properties": {"savingsAmount": "100"}
        }]
        mock_create_individual.return_value = {
            "title": "Test",
            "cost_impact": "100",
            "description": "Test description",
            "category": "cost",
            "effort": "medium",
            "status": "new",
            "source": "Azure Advisor"
        }

        recommendations = [{
            "name": "rec-1",
            "id": "/subscriptions/sub-123/providers/...",
            "short_description": {"problem": "Test problem"},
            "extended_properties": {"savingsAmount": "100"}
        }]

        # Act
        transmit_azure_insights(mock_client, recommendations, dry_run=True)

        # Assert
        mock_create.assert_not_called()

    @patch('app.app.get_cloudzero_insights_list')
    @patch('app.app.filter_azure_advisor_recs')
    @patch('app.app.create_individual_insight')
    @patch('app.app.create_cloudzero_insight')
    def test_handles_failed_insight_creation(
        self, mock_create, mock_create_individual, mock_filter, mock_get_insights
    ):
        """Should track failed insights when API returns error."""
        # Arrange
        mock_client = Mock(spec=CloudZeroClient)
        mock_get_insights.return_value = []
        mock_filter.return_value = [{
            "name": "rec-1",
            "id": "/subscriptions/sub-123/providers/...",
            "short_description": {"problem": "Test problem"},
            "extended_properties": {"savingsAmount": "100"}
        }]
        mock_create_individual.return_value = {
            "title": "Test",
            "cost_impact": "100",
            "category": "cost",
            "effort": "medium",
            "status": "new",
            "source": "Azure Advisor",
            "description": "Test description"
        }
        mock_create.return_value = {"error": "API Error"}

        recommendations = [{
            "name": "rec-1",
            "id": "/subscriptions/sub-123/providers/...",
            "short_description": {"problem": "Test problem"},
            "extended_properties": {"savingsAmount": "100"}
        }]

        # Act
        transmit_azure_insights(mock_client, recommendations)

        # Assert
        mock_create.assert_called_once()


class TestMain:
    """Tests for main function."""

    @patch('app.app.display_insights')
    @patch('app.app.os.environ.get')
    def test_list_insights_mode_only_requires_cz_api_key(self, mock_env_get, mock_display):
        """Should only require CloudZero API key for list-insights mode."""
        # Arrange
        mock_env_get.return_value = "test-api-key"
        args = Namespace(list_insights=True, limit=10)

        # Act
        main(args)

        # Assert
        mock_display.assert_called_once()

    @patch('app.app.os.environ.get')
    def test_raises_error_when_cz_api_key_missing_for_list_insights(self, mock_env_get):
        """Should raise ValueError when CloudZero API key is missing."""
        # Arrange
        mock_env_get.return_value = None
        args = Namespace(list_insights=True, limit=10)

        # Act & Assert
        with pytest.raises(ValueError, match="CLOUDZERO_API_KEY"):
            main(args)

    @patch('app.app.transmit_azure_insights')
    @patch('app.app.export_to_csv')
    @patch('app.app.get_advisor_recommendations')
    @patch('app.app.list_azure_subscription_ids')
    @patch('app.app.AzureClientFactory')
    @patch('app.app.CloudZeroClient')
    @patch('app.app.os.environ.get')
    def test_transmit_and_export_calls_both_functions(
        self, mock_env_get, mock_cz_client, mock_azure_factory,
        mock_list_subs, mock_get_recs, mock_export, mock_transmit
    ):
        """Should call both transmit and export when both flags are set."""
        # Arrange
        mock_env_get.side_effect = lambda key: "test-value"
        mock_list_subs.return_value = ["sub-1"]
        mock_get_recs.return_value = [{"name": "rec-1"}]

        args = Namespace(
            list_insights=False,
            transmit=True,
            export_csv=True,
            dry_run=False
        )

        # Act
        main(args)

        # Assert
        mock_transmit.assert_called_once()
        mock_export.assert_called_once()

    @patch('app.app.transmit_azure_insights')
    @patch('app.app.get_advisor_recommendations')
    @patch('app.app.list_azure_subscription_ids')
    @patch('app.app.AzureClientFactory')
    @patch('app.app.CloudZeroClient')
    @patch('app.app.os.environ.get')
    def test_transmit_only_does_not_export(
        self, mock_env_get, mock_cz_client, mock_azure_factory,
        mock_list_subs, mock_get_recs, mock_transmit
    ):
        """Should only transmit when only transmit flag is set."""
        # Arrange
        mock_env_get.side_effect = lambda key: "test-value"
        mock_list_subs.return_value = ["sub-1"]
        mock_get_recs.return_value = [{"name": "rec-1"}]

        args = Namespace(
            list_insights=False,
            transmit=True,
            export_csv=False,
            dry_run=False
        )

        # Act
        main(args)

        # Assert
        mock_transmit.assert_called_once()

    @patch('app.app.export_to_csv')
    @patch('app.app.get_advisor_recommendations')
    @patch('app.app.list_azure_subscription_ids')
    @patch('app.app.AzureClientFactory')
    @patch('app.app.CloudZeroClient')
    @patch('app.app.os.environ.get')
    def test_export_only_does_not_transmit(
        self, mock_env_get, mock_cz_client, mock_azure_factory,
        mock_list_subs, mock_get_recs, mock_export
    ):
        """Should only export when only export flag is set."""
        # Arrange
        mock_env_get.side_effect = lambda key: "test-value"
        mock_list_subs.return_value = ["sub-1"]
        mock_get_recs.return_value = [{"name": "rec-1"}]

        args = Namespace(
            list_insights=False,
            transmit=False,
            export_csv=True,
            dry_run=False
        )

        # Act
        main(args)

        # Assert
        mock_export.assert_called_once()
