# SPDX-FileCopyrightText: Copyright (c) 2016-2023, CloudZero, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import os
import pytest
from unittest.mock import Mock, patch, MagicMock, mock_open
from app.app import (
    AzureClientFactory,
    CloudZeroClient,
    create_directory_if_not_exists,
    get_cloudzero_insights_list,
    list_azure_subscription_ids,
    get_advisor_recommendations,
    create_cloudzero_insight,
    collapse_recommendations,
    filter_azure_advisor_recs,
    transmit_azure_insights,
    convert_to_csv,
    export_to_csv,
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


class TestCloudZeroClient:
    """Tests for CloudZeroClient class."""

    def test_init_sets_api_key_and_headers(self):
        """CloudZeroClient init should set API key and headers."""
        client = CloudZeroClient("test-api-key")

        assert client.api_key == "test-api-key"
        assert "Authorization" in client.headers
        assert client.headers["Authorization"] == "test-api-key"

    @patch('app.app.requests.get')
    def test_get_insights_returns_list_when_successful(self, mock_get):
        """get_insights should return list of insights when API succeeds."""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "insights": [{"id": "1", "title": "Test"}],
            "pagination": {"has_next": False}
        }
        mock_get.return_value = mock_response

        client = CloudZeroClient("test-api-key")

        # Act
        result = client.get_insights()

        # Assert
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["id"] == "1"

    @patch('app.app.requests.get')
    def test_get_insights_handles_pagination(self, mock_get):
        """get_insights should handle paginated responses."""
        # Arrange
        mock_response1 = Mock()
        mock_response1.status_code = 200
        mock_response1.json.return_value = {
            "insights": [{"id": "1"}],
            "pagination": {"has_next": True, "cursor": {"next_cursor": "cursor-2"}}
        }

        mock_response2 = Mock()
        mock_response2.status_code = 200
        mock_response2.json.return_value = {
            "insights": [{"id": "2"}],
            "pagination": {"has_next": False}
        }

        mock_get.side_effect = [mock_response1, mock_response2]

        client = CloudZeroClient("test-api-key")

        # Act
        result = client.get_insights()

        # Assert
        assert len(result) == 2
        assert result[0]["id"] == "1"
        assert result[1]["id"] == "2"
        assert mock_get.call_count == 2

    @patch('app.app.requests.get')
    def test_get_insights_returns_error_on_non_200_status(self, mock_get):
        """get_insights should return error dict when API returns non-200 status."""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_get.return_value = mock_response

        client = CloudZeroClient("test-api-key")

        # Act
        result = client.get_insights()

        # Assert
        assert "error" in result
        assert result["error"] == "Unauthorized"

    @patch('app.app.requests.post')
    def test_create_insight_returns_json_when_successful(self, mock_post):
        """create_insight should return response JSON when API succeeds."""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"insight": {"id": "123", "title": "Test"}}
        mock_post.return_value = mock_response

        client = CloudZeroClient("test-api-key")
        data = {"title": "Test", "description": "Test insight"}

        # Act
        result = client.create_insight(data)

        # Assert
        assert "insight" in result
        assert result["insight"]["id"] == "123"
        mock_post.assert_called_once()

    @patch('app.app.requests.post')
    def test_create_insight_returns_error_on_failure(self, mock_post):
        """create_insight should return error dict when API fails."""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_post.return_value = mock_response

        client = CloudZeroClient("test-api-key")
        data = {"title": "Test"}

        # Act
        result = client.create_insight(data)

        # Assert
        assert "error" in result
        assert result["error"] == "Bad Request"


class TestCreateDirectoryIfNotExists:
    """Tests for create_directory_if_not_exists function."""

    @patch('app.app.os.path.exists')
    @patch('app.app.os.makedirs')
    @patch('builtins.print')
    def test_creates_directory_when_not_exists(self, mock_print, mock_makedirs, mock_exists):
        """Should create directory when it doesn't exist."""
        # Arrange
        mock_exists.return_value = False

        # Act
        create_directory_if_not_exists("test_dir")

        # Assert
        mock_makedirs.assert_called_once_with("test_dir")
        mock_print.assert_called_once()

    @patch('app.app.os.path.exists')
    @patch('app.app.os.makedirs')
    @patch('builtins.print')
    def test_does_not_create_when_exists(self, mock_print, mock_makedirs, mock_exists):
        """Should not create directory when it already exists."""
        # Arrange
        mock_exists.return_value = True

        # Act
        create_directory_if_not_exists("test_dir")

        # Assert
        mock_makedirs.assert_not_called()
        mock_print.assert_called_once()


class TestGetCloudZeroInsightsList:
    """Tests for get_cloudzero_insights_list function."""

    def test_returns_insights_from_client(self):
        """Should return insights from CloudZero client."""
        # Arrange
        mock_client = Mock(spec=CloudZeroClient)
        mock_client.get_insights.return_value = [{"id": "1"}, {"id": "2"}]

        # Act
        result = get_cloudzero_insights_list(mock_client)

        # Assert
        assert len(result) == 2
        mock_client.get_insights.assert_called_once()


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


class TestCreateCloudZeroInsight:
    """Tests for create_cloudzero_insight function."""

    def test_calls_client_create_insight(self):
        """Should call CloudZeroClient.create_insight with data."""
        # Arrange
        mock_client = Mock(spec=CloudZeroClient)
        mock_client.create_insight.return_value = {"insight": {"id": "123"}}
        data = {"title": "Test"}

        # Act
        result = create_cloudzero_insight(mock_client, data)

        # Assert
        mock_client.create_insight.assert_called_once_with(data)
        assert result["insight"]["id"] == "123"


class TestCollapseRecommendations:
    """Tests for collapse_recommendations function."""

    def test_returns_empty_dict_when_no_recommendations(self):
        """Should return empty dict when recommendations list is empty."""
        # Act
        result = collapse_recommendations([])

        # Assert
        assert result == {}

    def test_collapses_recommendations_with_same_title(self):
        """Should collapse recommendations with identical titles."""
        # Arrange
        recs = [
            {
                "short_description": {"problem": "Test Problem"},
                "extended_properties": {"savingsAmount": "100"},
                "id": "/subscriptions/sub-1/...",
                "name": "rec-1"
            },
            {
                "short_description": {"problem": "Test Problem"},
                "extended_properties": {"savingsAmount": "50"},
                "id": "/subscriptions/sub-2/...",
                "name": "rec-2"
            }
        ]

        # Act
        result = collapse_recommendations(recs)

        # Assert
        assert len(result) == 1
        assert "Test Problem" in result
        assert result["Test Problem"]["cost_impact"] == "150.0"

    def test_keeps_separate_recommendations_with_different_titles(self):
        """Should keep recommendations with different titles separate."""
        # Arrange
        recs = [
            {
                "short_description": {"problem": "Problem A"},
                "extended_properties": {"savingsAmount": "100"},
                "id": "/subscriptions/sub-1/...",
                "name": "rec-1"
            },
            {
                "short_description": {"problem": "Problem B"},
                "extended_properties": {"savingsAmount": "50"},
                "id": "/subscriptions/sub-2/...",
                "name": "rec-2"
            }
        ]

        # Act
        result = collapse_recommendations(recs)

        # Assert
        assert len(result) == 2
        assert "Problem A" in result
        assert "Problem B" in result


class TestFilterAzureAdvisorRecs:
    """Tests for filter_azure_advisor_recs function."""

    def test_returns_all_recs_when_no_cz_insights(self):
        """Should return all recommendations when no CloudZero insights exist."""
        # Arrange
        azure_recs = [{"name": "rec-1"}, {"name": "rec-2"}]

        # Act
        result = filter_azure_advisor_recs([], azure_recs)

        # Assert
        assert len(result) == 2

    def test_filters_out_existing_recommendations(self):
        """Should filter out recommendations that already exist in CloudZero."""
        # Arrange
        cz_insights = [
            {"description": "Azure Advisor Recommendation ID: rec-1\nSome text"}
        ]
        azure_recs = [
            {"name": "rec-1"},
            {"name": "rec-2"}
        ]

        # Act
        result = filter_azure_advisor_recs(cz_insights, azure_recs)

        # Assert
        assert len(result) == 1
        assert result[0]["name"] == "rec-2"

    def test_handles_invalid_cz_insights_gracefully(self):
        """Should return all recs when cz_insights is None (treated as no insights)."""
        # Arrange
        cz_insights = None
        azure_recs = [{"name": "rec-1"}]

        # Act
        result = filter_azure_advisor_recs(cz_insights, azure_recs)

        # Assert
        # When cz_insights is None/empty, function returns all azure_recs (no filtering)
        assert result == azure_recs


class TestTransmitAzureInsights:
    """Tests for transmit_azure_insights function."""

    @patch('app.app.get_cloudzero_insights_list')
    @patch('app.app.filter_azure_advisor_recs')
    @patch('app.app.collapse_recommendations')
    @patch('app.app.create_cloudzero_insight')
    def test_transmits_filtered_and_collapsed_recommendations(
        self, mock_create, mock_collapse, mock_filter, mock_get_insights
    ):
        """Should fetch, filter, collapse, and transmit recommendations."""
        # Arrange
        mock_client = Mock(spec=CloudZeroClient)
        mock_get_insights.return_value = []
        mock_filter.return_value = [{"name": "rec-1"}]
        mock_collapse.return_value = {
            "title1": {"title": "Test", "cost_impact": "100"}
        }
        mock_create.return_value = {"insight": {"title": "Test"}}

        recommendations = [{"name": "rec-1"}]

        # Act
        transmit_azure_insights(mock_client, recommendations)

        # Assert
        mock_get_insights.assert_called_once_with(mock_client)
        mock_create.assert_called_once()


class TestConvertToCSV:
    """Tests for convert_to_csv function."""

    def test_extracts_columns_and_converts_data(self):
        """Should extract CSV columns and convert data to CSV format."""
        # Arrange
        data = [
            {
                "id": "/subscriptions/sub-1/...",
                "name": "rec-1",
                "short_description": {"solution": "Test solution"},
                "extended_properties": {"savingsAmount": "100", "savingsCurrency": "USD"}
            }
        ]

        # Act
        columns, csv_data = convert_to_csv(data)

        # Assert
        assert "id" in columns
        assert "subscription_id" in columns
        assert "recommendation_id" in columns
        assert "savingsAmount" in columns
        assert len(csv_data) == 1
        assert csv_data[0]["subscription_id"] == "sub-1"


class TestExportToCSV:
    """Tests for export_to_csv function."""

    @patch('app.app.create_directory_if_not_exists')
    @patch('app.app.convert_to_csv')
    @patch('builtins.open', new_callable=mock_open)
    def test_exports_recommendations_to_csv_file(self, mock_file, mock_convert, mock_create_dir):
        """Should export recommendations to CSV file."""
        # Arrange
        mock_convert.return_value = (
            ["id", "title"],
            [{"id": "1", "title": "Test"}]
        )
        recommendations = [{"id": "1"}]

        # Act
        export_to_csv(recommendations)

        # Assert
        mock_create_dir.assert_called_once_with("output")
        mock_file.assert_called_once()
