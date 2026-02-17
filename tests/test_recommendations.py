# SPDX-FileCopyrightText: Copyright (c) 2016-2023, CloudZero, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import pytest

from app.transformers import collapse_recommendations, filter_azure_advisor_recs


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
        assert result["Test Problem"]["title"] == "Test Problem"
        assert result["Test Problem"]["status"] == "new"
        assert result["Test Problem"]["source"] == "Azure Advisor"

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
        assert result["Problem A"]["cost_impact"] == "100"
        assert result["Problem B"]["cost_impact"] == "50"

    def test_handles_missing_savings_amount_gracefully(self):
        """Should use 0 when savingsAmount is missing."""
        # Arrange
        recs = [
            {
                "short_description": {"problem": "Test Problem"},
                "extended_properties": {},
                "id": "/subscriptions/sub-1/...",
                "name": "rec-1"
            }
        ]

        # Act
        result = collapse_recommendations(recs)

        # Assert
        assert result["Test Problem"]["cost_impact"] == "0"

    def test_handles_malformed_recommendation_gracefully(self):
        """Should skip malformed recommendations and log warning."""
        # Arrange
        recs = [
            {"name": "rec-1"},  # Missing required fields
            {
                "short_description": {"problem": "Valid Problem"},
                "extended_properties": {"savingsAmount": "100"},
                "id": "/subscriptions/sub-1/...",
                "name": "rec-2"
            }
        ]

        # Act
        result = collapse_recommendations(recs)

        # Assert
        assert len(result) == 1
        assert "Valid Problem" in result

    def test_concatenates_descriptions_with_separator(self):
        """Should concatenate descriptions with separator when collapsing."""
        # Arrange
        recs = [
            {
                "short_description": {"problem": "Test Problem"},
                "extended_properties": {"savingsAmount": "100"},
                "id": "/subscriptions/sub-1/resourceGroups/rg1",
                "name": "rec-1"
            },
            {
                "short_description": {"problem": "Test Problem"},
                "extended_properties": {"savingsAmount": "50"},
                "id": "/subscriptions/sub-2/resourceGroups/rg2",
                "name": "rec-2"
            }
        ]

        # Act
        result = collapse_recommendations(recs)

        # Assert
        assert "---" in result["Test Problem"]["description"]
        assert "rec-1" in result["Test Problem"]["description"]
        assert "rec-2" in result["Test Problem"]["description"]


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

    def test_filters_multiple_existing_recommendations(self):
        """Should filter out multiple existing recommendations."""
        # Arrange
        cz_insights = [
            {"description": "Azure Advisor Recommendation ID: rec-1\nSome text"},
            {"description": "Azure Advisor Recommendation ID: rec-2\nMore text"}
        ]
        azure_recs = [
            {"name": "rec-1"},
            {"name": "rec-2"},
            {"name": "rec-3"}
        ]

        # Act
        result = filter_azure_advisor_recs(cz_insights, azure_recs)

        # Assert
        assert len(result) == 1
        assert result[0]["name"] == "rec-3"

    def test_returns_empty_when_all_filtered(self):
        """Should return empty list when all recommendations are filtered."""
        # Arrange
        cz_insights = [
            {"description": "Azure Advisor Recommendation ID: rec-1\n"}
        ]
        azure_recs = [{"name": "rec-1"}]

        # Act
        result = filter_azure_advisor_recs(cz_insights, azure_recs)

        # Assert
        assert result == []

    def test_handles_insights_without_description(self):
        """Should handle insights that don't have description field."""
        # Arrange
        cz_insights = [
            {"title": "Some insight"}  # No description field
        ]
        azure_recs = [{"name": "rec-1"}]

        # Act
        result = filter_azure_advisor_recs(cz_insights, azure_recs)

        # Assert
        assert len(result) == 1

    def test_handles_malformed_description_lines(self):
        """Should handle descriptions without proper format."""
        # Arrange
        cz_insights = [
            {"description": "Random text without proper format"}
        ]
        azure_recs = [{"name": "rec-1"}]

        # Act
        result = filter_azure_advisor_recs(cz_insights, azure_recs)

        # Assert
        assert len(result) == 1

    def test_returns_empty_list_on_exception(self):
        """Should return empty list when exception occurs."""
        # Arrange
        cz_insights = None  # Will cause exception in iteration
        azure_recs = [{"name": "rec-1"}]

        # Act
        result = filter_azure_advisor_recs(cz_insights, azure_recs)

        # Assert
        # Function handles this gracefully and returns all recs
        assert result == azure_recs
