# SPDX-FileCopyrightText: Copyright (c) 2016-2023, CloudZero, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import pytest
from app.clients.cloudzero_client import apply_filters


class TestApplyFilters:
    """Tests for apply_filters function."""

    @pytest.fixture
    def sample_insights(self):
        """Sample insights for testing."""
        return [
            {
                "id": "1",
                "title": "Right-size VM: vm-prod (D8 → B8)",
                "description": "Subscription: sub-abc-123\nRegion: eastus",
                "status": "new",
                "cost_impact": "100",
                "created": "1705881600",  # Jan 22, 2024
                "source": "azure advisor"
            },
            {
                "id": "2",
                "title": "Shutdown vm-test-dev",
                "description": "Subscription: sub-xyz-456\nRegion: westus",
                "status": "ignored",
                "cost_impact": "50",
                "created": "1706486400",  # Jan 29, 2024
                "source": "azure advisor"
            },
            {
                "id": "3",
                "title": "Right-size VM: vm-staging (D4 → B2)",
                "description": "Subscription: sub-abc-123\nRegion: centralus",
                "status": "new",
                "cost_impact": "200",
                "created": "1707091200",  # Feb 5, 2024
                "source": "azure advisor"
            },
            {
                "id": "4",
                "title": "Configure reserved instances",
                "description": "Subscription: sub-xyz-456\nRegion: eastus",
                "status": "in_progress",
                "cost_impact": "500",
                "created": "1707696000",  # Feb 12, 2024
                "source": "azure advisor"
            },
            {
                "id": "5",
                "title": "Shutdown vm-temp",
                "description": "Subscription: sub-abc-123\nRegion: westus",
                "status": "completed",
                "cost_impact": "25",
                "created": "1708300800",  # Feb 19, 2024
                "source": "azure advisor"
            }
        ]

    def test_no_filters_returns_all(self, sample_insights):
        """Should return all insights when no filters applied."""
        result = apply_filters(sample_insights)
        assert len(result) == 5

    def test_filter_by_subscription_id(self, sample_insights):
        """Should filter by subscription ID substring."""
        result = apply_filters(sample_insights, subscription_id="sub-abc")
        assert len(result) == 3
        assert all("sub-abc" in i["description"].lower() for i in result)

    def test_filter_by_status(self, sample_insights):
        """Should filter by exact status match."""
        result = apply_filters(sample_insights, status="new")
        assert len(result) == 2
        assert all(i["status"] == "new" for i in result)

    def test_filter_by_status_case_insensitive(self, sample_insights):
        """Should handle status filter case-insensitively."""
        result = apply_filters(sample_insights, status="NEW")
        assert len(result) == 2
        assert all(i["status"] == "new" for i in result)

    def test_filter_by_min_cost(self, sample_insights):
        """Should filter by minimum cost impact."""
        result = apply_filters(sample_insights, min_cost_impact=100)
        assert len(result) == 3
        assert all(float(i["cost_impact"]) >= 100 for i in result)

    def test_filter_by_max_cost(self, sample_insights):
        """Should filter by maximum cost impact."""
        result = apply_filters(sample_insights, max_cost_impact=100)
        assert len(result) == 3
        assert all(float(i["cost_impact"]) <= 100 for i in result)

    def test_filter_by_cost_range(self, sample_insights):
        """Should filter by cost range (min and max)."""
        result = apply_filters(
            sample_insights,
            min_cost_impact=50,
            max_cost_impact=200
        )
        assert len(result) == 3
        for insight in result:
            cost = float(insight["cost_impact"])
            assert 50 <= cost <= 200

    def test_filter_by_title_substring(self, sample_insights):
        """Should filter by title substring case-insensitively."""
        result = apply_filters(sample_insights, title_contains="shutdown")
        assert len(result) == 2
        assert all("shutdown" in i["title"].lower() for i in result)

    def test_filter_by_title_case_insensitive(self, sample_insights):
        """Should handle title filter case-insensitively."""
        result = apply_filters(sample_insights, title_contains="RIGHT-SIZE")
        assert len(result) == 2
        assert all("right-size" in i["title"].lower() for i in result)

    def test_filter_by_created_before(self, sample_insights):
        """Should filter insights created before timestamp."""
        # Feb 1, 2024
        result = apply_filters(sample_insights, created_before=1706745600)
        assert len(result) == 2
        assert all(int(i["created"]) < 1706745600 for i in result)

    def test_filter_by_created_after(self, sample_insights):
        """Should filter insights created after timestamp."""
        # Feb 1, 2024
        result = apply_filters(sample_insights, created_after=1706745600)
        assert len(result) == 3
        assert all(int(i["created"]) > 1706745600 for i in result)

    def test_filter_by_created_range(self, sample_insights):
        """Should filter by created date range."""
        # Between Feb 1 and Feb 15, 2024
        result = apply_filters(
            sample_insights,
            created_after=1706745600,
            created_before=1707955200
        )
        assert len(result) == 2

    def test_combine_multiple_filters(self, sample_insights):
        """Should correctly combine multiple filters with AND logic."""
        result = apply_filters(
            sample_insights,
            status="new",
            min_cost_impact=150
        )
        assert len(result) == 1
        assert result[0]["id"] == "3"
        assert result[0]["status"] == "new"
        assert float(result[0]["cost_impact"]) >= 150

    def test_combine_all_filters(self, sample_insights):
        """Should handle all filters combined."""
        result = apply_filters(
            sample_insights,
            subscription_id="sub-abc",
            status="new",
            min_cost_impact=50,
            max_cost_impact=250,
            title_contains="vm",
            created_after=1705881600,
            created_before=1708300800
        )
        # Only insight #3 matches all filters:
        # - subscription: sub-abc-123 ✓
        # - status: new ✓
        # - cost: 200 (>= 50, <= 250) ✓
        # - title: contains "vm" ✓
        # - created: 1707091200 (> 1705881600, < 1708300800) ✓
        assert len(result) == 1
        assert result[0]["id"] == "3"

    def test_filters_resulting_in_empty_list(self, sample_insights):
        """Should return empty list when no insights match filters."""
        result = apply_filters(
            sample_insights,
            status="new",
            min_cost_impact=1000  # No insights with cost >= 1000
        )
        assert len(result) == 0

    def test_filter_with_zero_min_cost(self, sample_insights):
        """Should handle min_cost_impact=0 correctly."""
        result = apply_filters(sample_insights, min_cost_impact=0)
        assert len(result) == 5  # All insights have cost >= 0

    def test_filter_empty_insights_list(self):
        """Should handle empty insights list."""
        result = apply_filters([])
        assert len(result) == 0

    def test_filter_handles_missing_fields(self):
        """Should handle insights with missing fields gracefully."""
        insights = [
            {"id": "1", "title": "Test", "description": ""},  # Missing status, cost_impact
            {"id": "2", "title": "Test 2", "status": "new"}  # Missing cost_impact
        ]

        # Should not crash
        result = apply_filters(insights, status="new")
        assert len(result) == 1

    def test_subscription_filter_substring_match(self, sample_insights):
        """Should match subscription as substring, not exact match."""
        # Partial subscription ID
        result = apply_filters(sample_insights, subscription_id="abc")
        assert len(result) == 3

        # Different partial match
        result = apply_filters(sample_insights, subscription_id="xyz")
        assert len(result) == 2

    def test_rec_id_filter(self, sample_insights):
        """Should filter by recommendation ID in description."""
        # Add rec ID to one insight's description
        sample_insights[0]["description"] += "\n\nAzure Advisor Recommendation ID: rec-123-abc"

        result = apply_filters(sample_insights, rec_id="rec-123-abc")
        assert len(result) == 1
        assert result[0]["id"] == "1"

    def test_filter_preserves_order(self, sample_insights):
        """Should preserve original order of insights."""
        result = apply_filters(sample_insights, status="new")
        # Insights 1 and 3 are "new", should maintain order
        assert result[0]["id"] == "1"
        assert result[1]["id"] == "3"
