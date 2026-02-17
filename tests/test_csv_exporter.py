# SPDX-FileCopyrightText: Copyright (c) 2016-2023, CloudZero, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import pytest
from unittest.mock import Mock, patch, mock_open

from app.exporters import export_to_csv
from app.exporters.csv_exporter import convert_to_csv


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
        assert "short_description" in columns
        assert "savingsAmount" in columns
        assert "savingsCurrency" in columns
        assert len(csv_data) == 1
        assert csv_data[0]["subscription_id"] == "sub-1"
        assert csv_data[0]["recommendation_id"] == "rec-1"

    def test_handles_multiple_records(self):
        """Should handle multiple recommendation records."""
        # Arrange
        data = [
            {
                "id": "/subscriptions/sub-1/...",
                "name": "rec-1",
                "short_description": {"solution": "Solution 1"},
                "extended_properties": {"savingsAmount": "100"}
            },
            {
                "id": "/subscriptions/sub-2/...",
                "name": "rec-2",
                "short_description": {"solution": "Solution 2"},
                "extended_properties": {"savingsAmount": "200"}
            }
        ]

        # Act
        columns, csv_data = convert_to_csv(data)

        # Assert
        assert len(csv_data) == 2
        assert csv_data[0]["subscription_id"] == "sub-1"
        assert csv_data[1]["subscription_id"] == "sub-2"

    def test_handles_missing_extended_properties(self):
        """Should handle records without extended_properties."""
        # Arrange
        data = [
            {
                "id": "/subscriptions/sub-1/...",
                "name": "rec-1",
                "short_description": {"solution": "Test"}
            }
        ]

        # Act
        columns, csv_data = convert_to_csv(data)

        # Assert
        assert len(csv_data) == 1
        assert csv_data[0]["subscription_id"] == "sub-1"

    def test_handles_missing_short_description(self):
        """Should handle records without short_description."""
        # Arrange
        data = [
            {
                "id": "/subscriptions/sub-1/...",
                "name": "rec-1",
                "extended_properties": {"savingsAmount": "100"}
            }
        ]

        # Act
        columns, csv_data = convert_to_csv(data)

        # Assert
        assert len(csv_data) == 1
        assert csv_data[0]["short_description"] == ""

    def test_handles_malformed_id(self):
        """Should handle IDs that don't follow expected format."""
        # Arrange
        data = [
            {
                "id": "malformed-id",
                "name": "rec-1",
                "short_description": {"solution": "Test"}
            }
        ]

        # Act
        columns, csv_data = convert_to_csv(data)

        # Assert
        assert csv_data[0]["subscription_id"] == "unknown"

    def test_handles_empty_data(self):
        """Should handle empty data list."""
        # Arrange
        data = []

        # Act
        columns, csv_data = convert_to_csv(data)

        # Assert
        assert "id" in columns
        assert len(csv_data) == 0

    def test_aggregates_all_extended_properties(self):
        """Should aggregate all unique extended properties across records."""
        # Arrange
        data = [
            {
                "id": "/subscriptions/sub-1/...",
                "name": "rec-1",
                "short_description": {"solution": "Test"},
                "extended_properties": {"savingsAmount": "100", "propA": "valueA"}
            },
            {
                "id": "/subscriptions/sub-2/...",
                "name": "rec-2",
                "short_description": {"solution": "Test"},
                "extended_properties": {"savingsAmount": "200", "propB": "valueB"}
            }
        ]

        # Act
        columns, csv_data = convert_to_csv(data)

        # Assert
        assert "propA" in columns
        assert "propB" in columns
        assert csv_data[0]["propA"] == "valueA"
        assert csv_data[0]["propB"] == ""  # Not present in first record
        assert csv_data[1]["propA"] == ""  # Not present in second record
        assert csv_data[1]["propB"] == "valueB"


class TestExportToCSV:
    """Tests for export_to_csv function."""

    @patch('app.exporters.csv_exporter.create_directory_if_not_exists')
    @patch('app.exporters.csv_exporter.convert_to_csv')
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
        assert "./output/azure_advisor_recommendations.csv" in str(mock_file.call_args)

    @patch('app.exporters.csv_exporter.create_directory_if_not_exists')
    @patch('app.exporters.csv_exporter.convert_to_csv')
    @patch('builtins.open', new_callable=mock_open)
    def test_creates_output_directory(self, mock_file, mock_convert, mock_create_dir):
        """Should create output directory before writing."""
        # Arrange
        mock_convert.return_value = ([], [])

        # Act
        export_to_csv([])

        # Assert
        mock_create_dir.assert_called_once_with("output")

    @patch('app.exporters.csv_exporter.create_directory_if_not_exists')
    @patch('app.exporters.csv_exporter.convert_to_csv')
    @patch('builtins.open')
    @patch('app.exporters.csv_exporter.logging')
    def test_logs_error_on_io_error(self, mock_logging, mock_file, mock_convert, mock_create_dir):
        """Should log error when file write fails."""
        # Arrange
        mock_convert.return_value = (["id"], [{"id": "1"}])
        mock_file.side_effect = IOError("Disk full")

        # Act
        export_to_csv([{"id": "1"}])

        # Assert
        mock_logging.error.assert_called()
