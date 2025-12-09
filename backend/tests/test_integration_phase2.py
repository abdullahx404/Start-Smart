"""
Phase 2 Integration Tests - Complete Scoring Flow

Tests the full scoring pipeline from aggregation to recommendations:
1. Aggregate raw metrics from database
2. Normalize and score all grids
3. Store results in grid_metrics table
4. Query top recommendations
5. Verify scoring logic correctness

Coverage: End-to-end workflow validation
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from src.services.aggregator import aggregate_all_grids, compute_max_values
from src.services.scoring_service import score_all_grids, get_top_recommendations
from src.database.connection import get_session
from src.database.models import GridCellModel, BusinessModel, SocialPostModel, GridMetricsModel


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture(scope="function")
def test_database():
    """Set up test database with sample data."""
    with get_session() as session:
        # Clean up existing test data
        session.query(GridMetricsModel).filter(
            GridMetricsModel.grid_id.like('Test-%')
        ).delete()
        session.query(SocialPostModel).filter(
            SocialPostModel.grid_id.like('Test-%')
        ).delete()
        session.query(BusinessModel).filter(
            BusinessModel.grid_id.like('Test-%')
        ).delete()
        session.query(GridCellModel).filter(
            GridCellModel.grid_id.like('Test-%')
        ).delete()
        session.commit()
        
        # Create 3 test grid cells
        grids = [
            GridCellModel(
                grid_id="Test-Grid-01",
                neighborhood="Test Neighborhood",
                lat_north=24.8200,
                lat_south=24.8150,
                lon_east=67.0600,
                lon_west=67.0550,
                lat_center=24.8175,
                lon_center=67.0575
            ),
            GridCellModel(
                grid_id="Test-Grid-02",
                neighborhood="Test Neighborhood",
                lat_north=24.8250,
                lat_south=24.8200,
                lon_east=67.0650,
                lon_west=67.0600,
                lat_center=24.8225,
                lon_center=67.0625
            ),
            GridCellModel(
                grid_id="Test-Grid-03",
                neighborhood="Test Neighborhood",
                lat_north=24.8300,
                lat_south=24.8250,
                lon_east=67.0700,
                lon_west=67.0650,
                lat_center=24.8275,
                lon_center=67.0675
            ),
        ]
        
        for grid in grids:
            session.add(grid)
        
        # Create businesses - distributed unevenly
        # Grid-01: 0 businesses (high opportunity)
        # Grid-02: 3 businesses (medium)
        # Grid-03: 10 businesses (saturated)
        
        businesses = []
        
        # Grid-02: 3 gyms
        for i in range(3):
            businesses.append(BusinessModel(
                business_id=f"test-biz-grid2-{i}",
                name=f"Gym {i+1} (Grid 2)",
                category="Gym",
                lat=24.8210 + (i * 0.001),
                lon=67.0610 + (i * 0.001),
                grid_id="Test-Grid-02",
                rating=4.0 + (i * 0.2),
                review_count=50 + (i * 10),
                source="google_places",
                fetched_at=datetime.now()
            ))
        
        # Grid-03: 10 gyms (saturated)
        for i in range(10):
            businesses.append(BusinessModel(
                business_id=f"test-biz-grid3-{i}",
                name=f"Gym {i+1} (Grid 3)",
                category="Gym",
                lat=24.8260 + (i * 0.001),
                lon=67.0660 + (i * 0.001),
                grid_id="Test-Grid-03",
                rating=4.0 + (i * 0.05) if i < 8 else None,  # 2 businesses without ratings
                review_count=30 + (i * 5),
                source="google_places",
                fetched_at=datetime.now()
            ))
        
        for biz in businesses:
            session.add(biz)
        
        # Create social posts - varied distribution
        # Grid-01: 30 posts (high demand)
        # Grid-02: 15 posts (medium demand)
        # Grid-03: 5 posts (low demand)
        
        posts = []
        
        # Grid-01: High demand (30 posts)
        for i in range(30):
            posts.append(SocialPostModel(
                post_id=f"test-post-grid1-{i}",
                text=f"Need a good gym in Test Grid 01 #{i}",
                source="simulated",
                post_type="demand" if i % 2 == 0 else "complaint",
                timestamp=datetime.now() - timedelta(days=i),
                lat=24.8160 + (i * 0.0001),
                lon=67.0560 + (i * 0.0001),
                grid_id="Test-Grid-01",
                engagement_score=100 - i,
                is_simulated=True
            ))
        
        # Grid-02: Medium demand (15 posts)
        for i in range(15):
            posts.append(SocialPostModel(
                post_id=f"test-post-grid2-{i}",
                text=f"Looking for gym options in Test Grid 02 #{i}",
                source="simulated",
                post_type="demand" if i % 3 == 0 else "mention",
                timestamp=datetime.now() - timedelta(days=i),
                lat=24.8210 + (i * 0.0001),
                lon=67.0610 + (i * 0.0001),
                grid_id="Test-Grid-02",
                engagement_score=80 - (i * 2),
                is_simulated=True
            ))
        
        # Grid-03: Low demand (5 posts)
        for i in range(5):
            posts.append(SocialPostModel(
                post_id=f"test-post-grid3-{i}",
                text=f"Gym mention in Test Grid 03 #{i}",
                source="simulated",
                post_type="mention",
                timestamp=datetime.now() - timedelta(days=i * 2),
                lat=24.8260 + (i * 0.0001),
                lon=67.0660 + (i * 0.0001),
                grid_id="Test-Grid-03",
                engagement_score=50 - (i * 5),
                is_simulated=True
            ))
        
        for post in posts:
            session.add(post)
        
        session.commit()
    
    # Yield to tests
    yield None
    
    # Cleanup after tests
    with get_session() as session:
        session.query(GridMetricsModel).filter(
            GridMetricsModel.grid_id.like('Test-%')
        ).delete()
        session.query(SocialPostModel).filter(
            SocialPostModel.grid_id.like('Test-%')
        ).delete()
        session.query(BusinessModel).filter(
            BusinessModel.grid_id.like('Test-%')
        ).delete()
        session.query(GridCellModel).filter(
            GridCellModel.grid_id.like('Test-%')
        ).delete()
        session.commit()



# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestPhase2Integration:
    """Test complete Phase 2 scoring flow."""
    
    def test_complete_scoring_pipeline(self, test_database):
        """Test full pipeline: aggregate → score → query recommendations."""
        # Step 1: Aggregate all grids
        all_metrics, max_values = aggregate_all_grids("Gym")
        
        # Filter to test grids only
        test_metrics = [m for m in all_metrics if m["grid_id"].startswith('Test-')]
        
        # Verify aggregation
        assert len(test_metrics) == 3, f"Should have metrics for 3 test grids, got {len(test_metrics)}"
        
        # Convert to dict for easier access
        test_metrics_dict = {m["grid_id"]: m for m in test_metrics}
        
        assert "Test-Grid-01" in test_metrics_dict
        assert "Test-Grid-02" in test_metrics_dict
        assert "Test-Grid-03" in test_metrics_dict
        
        # Verify raw metrics
        grid1 = test_metrics_dict["Test-Grid-01"]
        grid2 = test_metrics_dict["Test-Grid-02"]
        grid3 = test_metrics_dict["Test-Grid-03"]
        
        assert grid1["business_count"] == 0, "Grid 1 should have 0 businesses"
        assert grid2["business_count"] == 3, "Grid 2 should have 3 businesses"
        assert grid3["business_count"] == 10, "Grid 3 should have 10 businesses"
        
        assert grid1["instagram_volume"] + grid1["reddit_mentions"] == 30, "Grid 1 should have 30 total posts"
        assert grid2["instagram_volume"] + grid2["reddit_mentions"] == 15, "Grid 2 should have 15 total posts"
        assert grid3["instagram_volume"] + grid3["reddit_mentions"] == 5, "Grid 3 should have 5 total posts"
        
        # Verify max values (will include all grids, not just test ones)
        assert max_values["max_business_count"] >= 10.0  # At least from our test grid-03
        assert max_values["max_instagram_volume"] > 0
        assert max_values["max_reddit_mentions"] > 0
        
        # Step 2: Score all grids
        results = score_all_grids("Gym")
        
        # Filter to test grids only
        test_results = [r for r in results if r["grid_id"].startswith('Test-')]
        
        assert len(test_results) == 3, f"Should have scored 3 test grids, got {len(test_results)}"
        
        # Step 3: Verify database persistence
        with get_session() as session:
            scored_grids = session.query(GridMetricsModel).filter(
                GridMetricsModel.grid_id.like('Test-%'),
                GridMetricsModel.category == "Gym"
            ).all()
            
            assert len(scored_grids) == 3, f"Should have 3 test records in grid_metrics, got {len(scored_grids)}"
        
        # Step 4: Query top recommendations (use Test Neighborhood)
        recommendations = get_top_recommendations("Test Neighborhood", "Gym", limit=3)
        
        assert len(recommendations) == 3, f"Should return 3 recommendations, got {len(recommendations)}"
        
        # Verify ranking (highest GOS first)
        assert recommendations[0]["gos"] >= recommendations[1]["gos"]
        assert recommendations[1]["gos"] >= recommendations[2]["gos"]
        
        # Grid-01 should rank highest (0 businesses, 30 posts)
        assert recommendations[0]["grid_id"] == "Test-Grid-01", \
            f"Grid-01 should rank first, got {recommendations[0]['grid_id']}"
        
        # Grid-03 should rank lowest (10 businesses, 5 posts)
        assert recommendations[2]["grid_id"] == "Test-Grid-03", \
            f"Grid-03 should rank last, got {recommendations[2]['grid_id']}"
    
    def test_gos_score_validity(self, test_database):
        """Test that all GOS scores are in valid range."""
        results = score_all_grids("Gym")
        
        for result in results:
            assert 0.0 <= result["gos"] <= 1.0, \
                f"GOS for {result['grid_id']} out of range: {result['gos']}"
            assert 0.0 <= result["confidence"] <= 1.0, \
                f"Confidence for {result['grid_id']} out of range: {result['confidence']}"
    
    def test_high_opportunity_detection(self, test_database):
        """Test that high opportunity grid (low supply, high demand) scores highest."""
        results = score_all_grids("Gym")
        
        # Find Grid-01 (0 businesses, 30 posts)
        test_results = [r for r in results if r["grid_id"].startswith('Test-')]
        grid1_result = next(r for r in test_results if r["grid_id"] == "Test-Grid-01")
        grid3_result = next(r for r in test_results if r["grid_id"] == "Test-Grid-03")
        
        # Grid-01 should have higher GOS than Grid-03 (which is saturated)
        assert grid1_result["gos"] > grid3_result["gos"], \
            f"High opportunity grid (0 businesses) should score higher than saturated grid (10 businesses)"
        
        # Should have reasonable confidence (lots of data)
        assert grid1_result["confidence"] >= 0.5, \
            f"High data volume should give confidence >= 0.5, got {grid1_result['confidence']}"
    
    def test_saturated_market_detection(self, test_database):
        """Test that saturated market (high supply, low demand) scores lowest among test grids."""
        results = score_all_grids("Gym")
        
        # Find test grids
        test_results = [r for r in results if r["grid_id"].startswith('Test-')]
        grid1_result = next(r for r in test_results if r["grid_id"] == "Test-Grid-01")
        grid3_result = next(r for r in test_results if r["grid_id"] == "Test-Grid-03")
        
        # Grid-03 (10 businesses, 5 posts) should have lower GOS than Grid-01 (0 businesses, 30 posts)
        assert grid3_result["gos"] < grid1_result["gos"], \
            f"Saturated grid should score lower than high opportunity grid"
    
    def test_recommendation_structure(self, test_database):
        """Test that recommendations have all required fields."""
        score_all_grids("Gym")  # Ensure data is scored
        recommendations = get_top_recommendations("Test Neighborhood", "Gym", limit=1)
        
        assert len(recommendations) > 0, "Should return at least one recommendation"
        
        rec = recommendations[0]
        
        # Check required fields
        assert "grid_id" in rec
        assert "gos" in rec
        assert "confidence" in rec
        assert "rationale" in rec
        assert "lat_center" in rec
        assert "lon_center" in rec
        assert "business_count" in rec
        assert "instagram_volume" in rec
        assert "reddit_mentions" in rec
        assert "top_posts" in rec
        assert "competitors" in rec
        
        # Check nested structures
        assert isinstance(rec["top_posts"], list)
        assert isinstance(rec["competitors"], list)
    
    def test_edge_case_zero_businesses(self, test_database):
        """Test grid with zero businesses scores correctly."""
        results = score_all_grids("Gym")
        
        grid1_result = next(r for r in results if r["grid_id"] == "Test-Grid-01")
        
        # Should handle zero businesses gracefully
        assert grid1_result["gos"] >= 0.0
        assert grid1_result["confidence"] >= 0.0
        
        # Supply component should be maximum (1 - 0 = 1)
        # High demand should boost score
        assert grid1_result["gos"] > 0.5, "Zero businesses should indicate opportunity"
    
    def test_edge_case_zero_posts(self, test_database):
        """Test grid with businesses but minimal social posts."""
        results = score_all_grids("Gym")
        
        grid3_result = next(r for r in results if r["grid_id"] == "Test-Grid-03")
        
        # Should handle low post count gracefully
        assert grid3_result["confidence"] < 0.6, \
            "Low post count should result in lower confidence"
    
    def test_edge_case_missing_ratings(self, test_database):
        """Test that businesses without ratings don't break scoring."""
        # Grid-03 has 2 businesses with rating=None
        results = score_all_grids("Gym")
        
        grid3_result = next(r for r in results if r["grid_id"] == "Test-Grid-03")
        
        # Should compute successfully
        assert grid3_result is not None
        assert 0.0 <= grid3_result["gos"] <= 1.0
    
    def test_explainability_json_validity(self, test_database):
        """Test that explainability JSON (top posts, competitors) is valid."""
        score_all_grids("Gym")
        recommendations = get_top_recommendations("Test Neighborhood", "Gym", limit=3)
        
        for rec in recommendations:
            # Top posts should be a list
            assert isinstance(rec["top_posts"], list)
            
            if len(rec["top_posts"]) > 0:
                post = rec["top_posts"][0]
                assert "text" in post
                assert "source" in post
                assert "timestamp" in post
            
            # Competitors should be a list
            assert isinstance(rec["competitors"], list)
            
            if len(rec["competitors"]) > 0:
                comp = rec["competitors"][0]
                assert "name" in comp
                assert "distance_km" in comp
                assert comp["distance_km"] >= 0
    
    def test_rationale_generation(self, test_database):
        """Test that rationale text is generated for each recommendation."""
        score_all_grids("Gym")
        recommendations = get_top_recommendations("Test Neighborhood", "Gym", limit=3)
        
        for rec in recommendations:
            assert isinstance(rec["rationale"], str)
            assert len(rec["rationale"]) > 0, "Rationale should not be empty"
            
            # High GOS should mention opportunity/demand
            if rec["gos"] >= 0.7:
                rationale_lower = rec["rationale"].lower()
                assert any(word in rationale_lower for word in 
                          ["high", "strong", "opportunity", "demand", "0 businesses"]), \
                    f"High GOS rationale should mention opportunity: {rec['rationale']}"
    
    def test_performance_under_2_seconds(self, test_database):
        """Test that scoring completes in under 2 seconds (Phase 2 requirement)."""
        import time
        
        start = time.time()
        score_all_grids("Gym")
        recommendations = get_top_recommendations("Test Neighborhood", "Gym", limit=3)
        elapsed = time.time() - start
        
        assert elapsed < 2.0, \
            f"Scoring + query should complete in <2s, took {elapsed:.2f}s"
    
    def test_idempotency(self, test_database):
        """Test that re-running scoring produces same results."""
        # Run twice
        results1 = score_all_grids("Gym")
        results2 = score_all_grids("Gym")
        
        # Should have same number of results
        assert len(results1) == len(results2)
        
        # GOS scores should be identical
        for r1, r2 in zip(results1, results2):
            assert r1["grid_id"] == r2["grid_id"]
            assert abs(r1["gos"] - r2["gos"]) < 0.001, \
                f"GOS changed between runs for {r1['grid_id']}"


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
