# SPDX-FileCopyrightText: Copyright (c) 2016-2023, CloudZero, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import pytest
from unittest.mock import Mock, patch

from app.clients import (
    CloudZeroClient,
    get_cloudzero_insights_list,
    create_cloudzero_insight
)


class TestCloudZeroClient:
    """Tests for CloudZeroClient class."""

    def test_init_sets_api_key_and_headers(self):
        """CloudZeroClient init should set API key and headers."""
        client = CloudZeroClient("test-api-key")

        assert client.api_key == "test-api-key"
        assert "Authorization" in client.headers
        assert client.headers["Authorization"] == "test-api-key"
        assert client.headers["Content-Type"] == "application/json"

    @patch('app.clients.cloudzero_client.requests.get')
    def test_get_insights_returns_list_when_successful(self, mock_get):
        """get_insights should return list of insights when API succeeds."""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "insights": [{"id": "1", "title": "Test", "source": "azure advisor"}],
            "pagination": {"cursor": {"has_next": False}}
        }
        mock_get.return_value = mock_response

        client = CloudZeroClient("test-api-key")

        # Act
        result = client.get_insights()

        # Assert
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["id"] == "1"

    @patch('app.clients.cloudzero_client.requests.get')
    def test_get_insights_handles_pagination(self, mock_get):
        """get_insights should handle paginated responses."""
        # Arrange
        mock_response1 = Mock()
        mock_response1.status_code = 200
        mock_response1.json.return_value = {
            "insights": [{"id": "1", "source": "azure advisor"}],
            "pagination": {"cursor": {"has_next": True, "next_cursor": "cursor-2"}}
        }

        mock_response2 = Mock()
        mock_response2.status_code = 200
        mock_response2.json.return_value = {
            "insights": [{"id": "2", "source": "azure advisor"}],
            "pagination": {"cursor": {"has_next": False}}
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

    @patch('app.clients.cloudzero_client.requests.get')
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
        assert isinstance(result, dict)
        assert "error" in result
        assert result["error"] == "Unauthorized"

    @patch('app.clients.cloudzero_client.requests.get')
    def test_get_insights_respects_max_total_limit(self, mock_get):
        """get_insights should stop fetching when max_total Azure Advisor insights is reached."""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "insights": [{"id": str(i), "source": "azure advisor"} for i in range(150)],
            "pagination": {"cursor": {"has_next": True, "next_cursor": "cursor-2"}}
        }
        mock_get.return_value = mock_response

        client = CloudZeroClient("test-api-key")

        # Act
        result = client.get_insights(max_total=100)

        # Assert
        assert len(result) == 100
        assert mock_get.call_count == 1

    @patch('app.clients.cloudzero_client.requests.post')
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

    @patch('app.clients.cloudzero_client.requests.post')
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

    @patch('app.clients.cloudzero_client.requests.delete')
    def test_delete_insight_returns_success_on_200(self, mock_delete):
        """delete_insight should return success dict when API returns 200."""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 200
        mock_delete.return_value = mock_response

        client = CloudZeroClient("test-api-key")

        # Act
        result = client.delete_insight("insight-123")

        # Assert
        assert result["success"] is True
        assert result["insight_id"] == "insight-123"

    @patch('app.clients.cloudzero_client.requests.delete')
    def test_delete_insight_returns_success_on_204(self, mock_delete):
        """delete_insight should return success dict when API returns 204."""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 204
        mock_delete.return_value = mock_response

        client = CloudZeroClient("test-api-key")

        # Act
        result = client.delete_insight("insight-123")

        # Assert
        assert result["success"] is True

    @patch('app.clients.cloudzero_client.requests.delete')
    def test_delete_insight_returns_error_on_failure(self, mock_delete):
        """delete_insight should return error dict when API fails."""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_delete.return_value = mock_response

        client = CloudZeroClient("test-api-key")

        # Act
        result = client.delete_insight("insight-123")

        # Assert
        assert "error" in result
        assert result["error"] == "Not Found"


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
