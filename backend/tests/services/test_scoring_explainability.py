"""
Unit tests for scoring service explainability functions.

Tests:
- get_top_posts(): Social post retrieval and formatting
- get_competitors(): Business retrieval with distance calculations
- generate_rationale(): Threshold-based explanations
- _haversine_distance(): Distance calculation accuracy

Usage:
    pytest tests/services/test_scoring_explainability.py -v
"""

import pytest
from src.services.scoring_service import (
    get_top_posts, 
    get_competitors, 
    generate_rationale,
    _haversine_distance
)


# ============================================================================
# Test Haversine Distance Function
# ============================================================================

class TestHaversineDistance:
    """Test distance calculations."""
    
    def test_zero_distance(self):
        """Same point should return 0 distance."""
        lat, lon = 24.8607, 67.0011  # Karachi
        distance = _haversine_distance(lat, lon, lat, lon)
        assert distance == 0.0, "Same point should have zero distance"
    
    def test_known_distance_karachi_lahore(self):
        """Test known distance between Karachi and Lahore (~990 km)."""
        karachi_lat, karachi_lon = 24.8607, 67.0011
        lahore_lat, lahore_lon = 31.5497, 74.3436
        
        distance = _haversine_distance(karachi_lat, karachi_lon, lahore_lat, lahore_lon)
        
        # Allow 10% tolerance for spherical approximation
        assert 890 <= distance <= 1090, f"Karachi-Lahore should be ~990km, got {distance:.2f}km"
    
    def test_small_distance_within_city(self):
        """Test small distance within DHA Phase 2 (~1 km)."""
        # Two points ~1 km apart in DHA
        lat1, lon1 = 24.8157, 67.0605
        lat2, lon2 = 24.8248, 67.0605
        
        distance = _haversine_distance(lat1, lon1, lat2, lon2)
        
        assert 0.9 <= distance <= 1.1, f"Distance should be ~1 km, got {distance:.2f}km"
    
    def test_negative_coordinates(self):
        """Test with negative coordinates (southern/western hemisphere)."""
        # Sydney to Melbourne (~714 km)
        sydney_lat, sydney_lon = -33.8688, 151.2093
        melbourne_lat, melbourne_lon = -37.8136, 144.9631
        
        distance = _haversine_distance(sydney_lat, sydney_lon, melbourne_lat, melbourne_lon)
        
        assert 640 <= distance <= 790, f"Sydney-Melbourne should be ~714km, got {distance:.2f}km"
    
    def test_distance_is_symmetric(self):
        """Distance A→B should equal distance B→A."""
        lat1, lon1 = 24.8157, 67.0605
        lat2, lon2 = 24.8248, 67.0712
        
        dist_ab = _haversine_distance(lat1, lon1, lat2, lon2)
        dist_ba = _haversine_distance(lat2, lon2, lat1, lon1)
        
        assert abs(dist_ab - dist_ba) < 0.001, "Distance should be symmetric"


# ============================================================================
# Test get_top_posts Function
# ============================================================================

class TestGetTopPosts:
    """Test social post retrieval."""
    
    def test_returns_list(self):
        """Should return a list (empty or populated)."""
        result = get_top_posts("DHA-Phase2-Cell-01", "Gym", limit=3)
        assert isinstance(result, list), "Should return a list"
    
    def test_respects_limit(self):
        """Should not exceed requested limit."""
        result = get_top_posts("DHA-Phase2-Cell-01", "Gym", limit=2)
        assert len(result) <= 2, "Should respect limit parameter"
    
    def test_post_structure(self):
        """Posts should have required fields."""
        result = get_top_posts("DHA-Phase2-Cell-01", "Gym", limit=1)
        
        if result:
            post = result[0]
            assert "source" in post, "Post should have 'source' field"
            assert "text" in post, "Post should have 'text' field"
            assert "timestamp" in post, "Post should have 'timestamp' field"
            assert "link" in post, "Post should have 'link' field"
    
    def test_text_truncation(self):
        """Text should be truncated to 200 characters if longer."""
        result = get_top_posts("DHA-Phase2-Cell-01", "Gym", limit=10)
        
        for post in result:
            # Check that text ends with ... if it was truncated
            if post["text"].endswith("..."):
                # The stored text was longer than 200 chars
                assert len(post["text"]) <= 203, "Truncated text should be ≤200 chars + '...'"
            else:
                # The stored text was ≤200 chars
                assert len(post["text"]) <= 200, "Non-truncated text should be ≤200 chars"
    
    def test_timestamp_format(self):
        """Timestamp should be ISO format string."""
        result = get_top_posts("DHA-Phase2-Cell-01", "Gym", limit=1)
        
        if result and result[0]["timestamp"]:
            ts = result[0]["timestamp"]
            # Should be ISO format like "2025-10-05T17:44:48"
            assert "T" in ts, "Timestamp should be ISO format with 'T' separator"
            assert len(ts) >= 19, "Timestamp should be at least 19 chars (YYYY-MM-DDTHH:MM:SS)"
    
    def test_nonexistent_grid(self):
        """Non-existent grid should return empty list."""
        result = get_top_posts("NonExistent-Cell-99", "Gym", limit=3)
        assert result == [], "Non-existent grid should return empty list"
    
    def test_default_limit(self):
        """Default limit should be 3."""
        # This test validates the function signature
        result = get_top_posts("DHA-Phase2-Cell-01", "Gym")
        assert isinstance(result, list), "Should work with default limit"
        assert len(result) <= 3, "Default limit should be 3"


# ============================================================================
# Test get_competitors Function
# ============================================================================

class TestGetCompetitors:
    """Test competitor retrieval with distances."""
    
    def test_returns_list(self):
        """Should return a list (empty or populated)."""
        result = get_competitors("DHA-Phase2-Cell-03", "Gym", limit=5)
        assert isinstance(result, list), "Should return a list"
    
    def test_respects_limit(self):
        """Should not exceed requested limit."""
        result = get_competitors("DHA-Phase2-Cell-03", "Gym", limit=2)
        assert len(result) <= 2, "Should respect limit parameter"
    
    def test_competitor_structure(self):
        """Competitors should have required fields."""
        result = get_competitors("DHA-Phase2-Cell-03", "Gym", limit=1)
        
        if result:
            comp = result[0]
            assert "name" in comp, "Competitor should have 'name' field"
            assert "distance_km" in comp, "Competitor should have 'distance_km' field"
            assert "rating" in comp, "Competitor should have 'rating' field"
    
    def test_distance_is_reasonable(self):
        """Distance should be reasonable for same grid (~0-1 km)."""
        result = get_competitors("DHA-Phase2-Cell-03", "Gym", limit=5)
        
        for comp in result:
            # Businesses in same grid should be within ~1 km of center
            assert 0 <= comp["distance_km"] <= 2.0, \
                f"Distance {comp['distance_km']}km seems unreasonable for same grid"
    
    def test_distance_precision(self):
        """Distance should be rounded to 2 decimals."""
        result = get_competitors("DHA-Phase2-Cell-03", "Gym", limit=1)
        
        if result:
            distance_str = str(result[0]["distance_km"])
            if "." in distance_str:
                decimals = len(distance_str.split(".")[1])
                assert decimals <= 2, "Distance should be rounded to 2 decimals"
    
    def test_rating_can_be_none(self):
        """Rating can be None for businesses without ratings."""
        result = get_competitors("DHA-Phase2-Cell-03", "Gym", limit=10)
        
        # At least one business should have a rating (given real data)
        has_rating = any(comp["rating"] is not None for comp in result)
        assert has_rating or len(result) == 0, "Should have at least one rated business"
    
    def test_nonexistent_grid(self):
        """Non-existent grid should return empty list."""
        result = get_competitors("NonExistent-Cell-99", "Gym", limit=5)
        assert result == [], "Non-existent grid should return empty list"
    
    def test_empty_grid(self):
        """Grid with no businesses should return empty list."""
        # Cell-01 has 0 businesses
        result = get_competitors("DHA-Phase2-Cell-01", "Gym", limit=5)
        assert result == [], "Empty grid should return empty list"
    
    def test_default_limit(self):
        """Default limit should be 5."""
        result = get_competitors("DHA-Phase2-Cell-03", "Gym")
        assert isinstance(result, list), "Should work with default limit"
        assert len(result) <= 5, "Default limit should be 5"


# ============================================================================
# Test generate_rationale Function
# ============================================================================

class TestGenerateRationale:
    """Test rationale generation logic."""
    
    def test_high_opportunity_threshold(self):
        """GOS ≥ 0.7 should trigger high opportunity rationale."""
        metrics = {"business_count": 0, "instagram_volume": 28, "reddit_mentions": 47}
        rationale = generate_rationale(metrics, 0.913)
        
        assert "High demand" in rationale, "Should mention high demand"
        assert "75 posts" in rationale, "Should show total posts (28+47)"
        assert "0 businesses" in rationale, "Should show business count"
    
    def test_medium_opportunity_threshold(self):
        """0.4 ≤ GOS < 0.7 should trigger medium opportunity rationale."""
        metrics = {"business_count": 1, "instagram_volume": 15, "reddit_mentions": 25}
        rationale = generate_rationale(metrics, 0.650)
        
        assert "Moderate opportunity" in rationale, "Should mention moderate opportunity"
        assert "1 competitors" in rationale or "1 competitor" in rationale, "Should show competitors"
        assert "40 demand signals" in rationale, "Should show total demand signals"
    
    def test_low_opportunity_threshold(self):
        """GOS < 0.4 should trigger low opportunity rationale."""
        metrics = {"business_count": 4, "instagram_volume": 12, "reddit_mentions": 38}
        rationale = generate_rationale(metrics, 0.339)
        
        assert "Saturated market" in rationale, "Should mention saturation"
        assert "4 businesses" in rationale, "Should show business count"
        assert "limited demand" in rationale, "Should mention limited demand"
    
    def test_edge_case_zero_posts(self):
        """Zero posts should still generate valid rationale."""
        metrics = {"business_count": 5, "instagram_volume": 0, "reddit_mentions": 0}
        rationale = generate_rationale(metrics, 0.2)
        
        assert isinstance(rationale, str), "Should return a string"
        assert len(rationale) > 0, "Should not be empty"
        assert "0" in rationale or "limited" in rationale, "Should reflect zero demand"
    
    def test_edge_case_zero_businesses(self):
        """Zero businesses should still generate valid rationale."""
        metrics = {"business_count": 0, "instagram_volume": 50, "reddit_mentions": 50}
        rationale = generate_rationale(metrics, 0.95)
        
        assert "0 businesses" in rationale, "Should show zero businesses"
        assert "100 posts" in rationale, "Should show total posts"
    
    def test_threshold_boundaries(self):
        """Test exact threshold values."""
        # Exactly 0.7 (should be high)
        r1 = generate_rationale({"business_count": 1, "instagram_volume": 10, "reddit_mentions": 10}, 0.7)
        assert "High demand" in r1, "GOS=0.7 should be high opportunity"
        
        # Exactly 0.4 (should be medium)
        r2 = generate_rationale({"business_count": 2, "instagram_volume": 5, "reddit_mentions": 5}, 0.4)
        assert "Moderate opportunity" in r2, "GOS=0.4 should be medium opportunity"
        
        # Just below 0.4 (should be low)
        r3 = generate_rationale({"business_count": 5, "instagram_volume": 5, "reddit_mentions": 5}, 0.39)
        assert "Saturated market" in r3, "GOS=0.39 should be low opportunity"
    
    def test_missing_metrics(self):
        """Should handle missing metric keys gracefully."""
        metrics = {}  # Empty dict
        rationale = generate_rationale(metrics, 0.5)
        
        assert isinstance(rationale, str), "Should return a string"
        assert len(rationale) > 0, "Should not be empty"
        # Should default to 0 for missing values
        assert "0" in rationale, "Should handle missing metrics with defaults"
    
    def test_returns_string(self):
        """All rationales should be strings."""
        test_cases = [
            ({"business_count": 0, "instagram_volume": 30, "reddit_mentions": 40}, 0.9),
            ({"business_count": 2, "instagram_volume": 15, "reddit_mentions": 20}, 0.6),
            ({"business_count": 5, "instagram_volume": 5, "reddit_mentions": 10}, 0.3),
        ]
        
        for metrics, gos in test_cases:
            rationale = generate_rationale(metrics, gos)
            assert isinstance(rationale, str), f"Should return string for GOS={gos}"
            assert len(rationale) > 10, f"Rationale too short for GOS={gos}"


# ============================================================================
# Integration Tests
# ============================================================================

class TestExplainabilityIntegration:
    """Integration tests using real database data."""
    
    def test_complete_explainability_for_high_opportunity_grid(self):
        """Test all explainability features for a high opportunity grid."""
        grid_id = "DHA-Phase2-Cell-01"
        category = "Gym"
        
        # Get top posts
        posts = get_top_posts(grid_id, category, limit=3)
        
        # Get competitors (should be empty for Cell-01)
        competitors = get_competitors(grid_id, category, limit=5)
        
        # Generate rationale
        metrics = {
            "business_count": len(competitors) if competitors else 0,
            "instagram_volume": 28,
            "reddit_mentions": 47
        }
        rationale = generate_rationale(metrics, 0.913)
        
        # Assertions
        assert len(posts) > 0, "High opportunity grid should have demand posts"
        assert len(competitors) == 0, "High opportunity grid should have no competitors"
        assert "High demand" in rationale, "Should identify as high opportunity"
        assert "0 businesses" in rationale, "Should mention zero competition"
    
    def test_complete_explainability_for_saturated_grid(self):
        """Test all explainability features for a saturated grid."""
        grid_id = "DHA-Phase2-Cell-03"
        category = "Gym"
        
        # Get top posts
        posts = get_top_posts(grid_id, category, limit=3)
        
        # Get competitors
        competitors = get_competitors(grid_id, category, limit=5)
        
        # Generate rationale
        metrics = {
            "business_count": 4,  # Known from database
            "instagram_volume": 12,
            "reddit_mentions": 38
        }
        rationale = generate_rationale(metrics, 0.339)
        
        # Assertions
        assert len(competitors) > 0, "Saturated grid should have competitors"
        assert len(competitors) <= 5, "Should respect limit"
        assert "Saturated market" in rationale, "Should identify as saturated"
        
        # Verify competitor details
        for comp in competitors:
            assert comp["name"], "Competitor should have a name"
            assert comp["distance_km"] >= 0, "Distance should be non-negative"
    
    def test_explainability_output_format(self):
        """Verify output format suitable for API response."""
        grid_id = "DHA-Phase2-Cell-02"
        category = "Gym"
        
        # Simulate API response structure
        explainability = {
            "top_posts": get_top_posts(grid_id, category, limit=3),
            "competitors": get_competitors(grid_id, category, limit=5),
            "rationale": generate_rationale(
                {"business_count": 0, "instagram_volume": 25, "reddit_mentions": 50},
                0.914
            )
        }
        
        # Verify structure
        assert isinstance(explainability["top_posts"], list), "Posts should be a list"
        assert isinstance(explainability["competitors"], list), "Competitors should be a list"
        assert isinstance(explainability["rationale"], str), "Rationale should be a string"
        
        # Verify non-empty rationale
        assert len(explainability["rationale"]) > 20, "Rationale should be meaningful"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
