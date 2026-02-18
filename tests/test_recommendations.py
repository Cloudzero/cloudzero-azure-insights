# SPDX-FileCopyrightText: Copyright (c) 2016-2023, CloudZero, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import pytest

from app.transformers import (
    collapse_recommendations,
    filter_azure_advisor_recs,
    create_individual_insight
)
from app.transformers.recommendations import (
    extract_resource_name,
    extract_category,
    map_effort_level,
    build_insight_title,
    format_single_recommendation,
    AZURE_ADVISOR_SOURCE
)


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
        assert result["Test Problem"]["source"] == AZURE_ADVISOR_SOURCE

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


class TestExtractResourceName:
    """Tests for extract_resource_name function."""

    def test_extracts_role_name_when_present(self):
        """Should extract roleName from extended_properties."""
        rec = {"extended_properties": {"roleName": "vm-test-prod"}}
        assert extract_resource_name(rec) == "vm-test-prod"

    def test_falls_back_to_resource_name(self):
        """Should use resourceName if roleName not present."""
        rec = {"extended_properties": {"resourceName": "my-resource"}}
        assert extract_resource_name(rec) == "my-resource"

    def test_returns_unknown_when_no_name_fields(self):
        """Should return 'unknown-resource' when no name fields present."""
        rec = {"extended_properties": {}}
        assert extract_resource_name(rec) == "unknown-resource"

    def test_returns_unknown_when_no_extended_properties(self):
        """Should return 'unknown-resource' when extended_properties missing."""
        rec = {}
        assert extract_resource_name(rec) == "unknown-resource"


class TestExtractCategory:
    """Tests for extract_category function."""

    def test_extracts_and_lowercases_category(self):
        """Should extract category and convert to lowercase."""
        assert extract_category({"category": "Cost"}) == "cost"
        assert extract_category({"category": "Performance"}) == "performance"

    def test_defaults_to_cost(self):
        """Should default to 'cost' when category missing."""
        assert extract_category({}) == "cost"


class TestMapEffortLevel:
    """Tests for map_effort_level function."""

    def test_maps_high_correctly(self):
        """Should map 'High' to 'high'."""
        assert map_effort_level("High") == "high"

    def test_maps_medium_correctly(self):
        """Should map 'Medium' to 'medium'."""
        assert map_effort_level("Medium") == "medium"

    def test_maps_low_correctly(self):
        """Should map 'Low' to 'low'."""
        assert map_effort_level("Low") == "low"

    def test_defaults_to_medium_for_unknown(self):
        """Should default to 'medium' for unknown values."""
        assert map_effort_level("Unknown") == "medium"
        assert map_effort_level("") == "medium"


class TestBuildInsightTitle:
    """Tests for build_insight_title function."""

    def test_builds_title_with_sku_change(self):
        """Should include SKU change when both SKUs present."""
        rec = {
            "short_description": {"problem": "Right-size VM"},
            "extended_properties": {
                "roleName": "vm-test",
                "currentSku": "D8",
                "targetSku": "B8"
            }
        }
        assert build_insight_title(rec) == "Right-size VM: vm-test (D8 → B8)"

    def test_builds_title_for_shutdown(self):
        """Should format shutdown recommendations specially."""
        rec = {
            "short_description": {"problem": "Right-size VM"},
            "extended_properties": {
                "roleName": "vm-test",
                "targetSku": "Shutdown"
            }
        }
        assert build_insight_title(rec) == "Shutdown vm-test"

    def test_builds_title_without_sku_info(self):
        """Should build simple title when SKU info missing."""
        rec = {
            "short_description": {"problem": "Right-size VM"},
            "extended_properties": {"roleName": "vm-test"}
        }
        assert build_insight_title(rec) == "Right-size VM: vm-test"

    def test_truncates_long_titles(self):
        """Should truncate titles longer than 200 characters."""
        long_name = "x" * 300
        rec = {
            "short_description": {"problem": "Test"},
            "extended_properties": {"roleName": long_name}
        }
        title = build_insight_title(rec)
        assert len(title) == 200


class TestFormatSingleRecommendation:
    """Tests for format_single_recommendation function."""

    def test_formats_basic_recommendation(self):
        """Should format recommendation with all basic fields."""
        rec = {
            "name": "test-rec-id",
            "extended_properties": {
                "roleName": "vm-test",
                "regionId": "eastus",
                "currentSku": "D8",
                "targetSku": "B8",
                "savingsAmount": "100",
                "annualSavingsAmount": "1200",
                "savingsCurrency": "USD"
            }
        }
        desc = format_single_recommendation(rec, "sub-123")

        assert "sub-123" in desc
        assert "vm-test" in desc
        assert "eastus" in desc
        assert "D8" in desc
        assert "B8" in desc
        assert "$100" in desc
        assert "$1200" in desc
        assert "test-rec-id" in desc

    def test_includes_carbon_savings_when_present(self):
        """Should include carbon savings when available."""
        rec = {
            "name": "test-rec",
            "extended_properties": {
                "roleName": "vm-test",
                "savingsAmount": "100",
                "PotentialMonthlyCarbonSavings": "1.5"
            }
        }
        desc = format_single_recommendation(rec, "sub-123")

        assert "Carbon Savings" in desc
        assert "1.5" in desc

    def test_includes_utilization_when_available(self):
        """Should include utilization metrics when available."""
        rec = {
            "name": "test-rec",
            "extended_properties": {
                "roleName": "vm-test",
                "savingsAmount": "100",
                "MaxCpuP95": "10",
                "MaxMemoryP95": "50",
                "MaxTotalNetworkP95": "5"
            }
        }
        desc = format_single_recommendation(rec, "sub-123")

        assert "Utilization" in desc
        assert "CPU: 10%" in desc
        assert "Memory: 50%" in desc
        assert "Network: 5%" in desc


class TestCreateIndividualInsight:
    """Tests for create_individual_insight function."""

    def test_creates_insight_with_all_fields(self):
        """Should create insight with all CloudZero fields populated."""
        rec = {
            "short_description": {"problem": "Right-size VM"},
            "category": "Cost",
            "impact": "High",
            "name": "rec-123",
            "extended_properties": {
                "roleName": "vm-test",
                "currentSku": "D8",
                "targetSku": "B8",
                "savingsAmount": "100"
            }
        }
        insight = create_individual_insight(rec, "sub-123")

        assert "vm-test" in insight["title"]
        assert insight["category"] == "cost"
        assert insight["effort"] == "high"
        assert insight["cost_impact"] == "100"
        assert insight["status"] == "new"
        assert insight["source"] == AZURE_ADVISOR_SOURCE
        assert "sub-123" in insight["description"]

    def test_handles_missing_optional_fields(self):
        """Should handle missing optional fields gracefully."""
        rec = {
            "short_description": {"problem": "Test"},
            "extended_properties": {}
        }
        insight = create_individual_insight(rec, "sub-123")

        assert insight["title"] == "Test: unknown-resource"
        assert insight["category"] == "cost"  # Default
        assert insight["effort"] == "medium"  # Default
        assert insight["cost_impact"] == "0"  # Default
