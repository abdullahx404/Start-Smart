"""
Unit tests for aggregator normalization functions.

Tests edge cases for compute_max_values() and normalize_metrics().
"""

import pytest
from src.services.aggregator import compute_max_values, normalize_metrics


class TestComputeMaxValues:
    """Test compute_max_values function edge cases."""
    
    def test_normal_case(self):
        """Test with normal metrics."""
        metrics_list = [
            {"business_count": 4, "instagram_volume": 38, "reddit_mentions": 50},
            {"business_count": 1, "instagram_volume": 28, "reddit_mentions": 47},
            {"business_count": 0, "instagram_volume": 25, "reddit_mentions": 15}
        ]
        
        result = compute_max_values(metrics_list)
        
        assert result["max_business_count"] == 4.0
        assert result["max_instagram_volume"] == 38.0
        assert result["max_reddit_mentions"] == 50.0
    
    def test_all_zeros(self):
        """Test with all zero values - should return 1.0 to avoid division by zero."""
        metrics_list = [
            {"business_count": 0, "instagram_volume": 0, "reddit_mentions": 0},
            {"business_count": 0, "instagram_volume": 0, "reddit_mentions": 0}
        ]
        
        result = compute_max_values(metrics_list)
        
        assert result["max_business_count"] == 1.0
        assert result["max_instagram_volume"] == 1.0
        assert result["max_reddit_mentions"] == 1.0
    
    def test_empty_list(self):
        """Test with empty metrics list."""
        result = compute_max_values([])
        
        assert result["max_business_count"] == 1.0
        assert result["max_instagram_volume"] == 1.0
        assert result["max_reddit_mentions"] == 1.0
    
    def test_single_grid(self):
        """Test with single grid."""
        metrics_list = [
            {"business_count": 3, "instagram_volume": 20, "reddit_mentions": 15}
        ]
        
        result = compute_max_values(metrics_list)
        
        assert result["max_business_count"] == 3.0
        assert result["max_instagram_volume"] == 20.0
        assert result["max_reddit_mentions"] == 15.0
    
    def test_partial_zeros(self):
        """Test when some metrics are zero but not all."""
        metrics_list = [
            {"business_count": 0, "instagram_volume": 30, "reddit_mentions": 40},
            {"business_count": 2, "instagram_volume": 0, "reddit_mentions": 0}
        ]
        
        result = compute_max_values(metrics_list)
        
        assert result["max_business_count"] == 2.0
        assert result["max_instagram_volume"] == 30.0
        assert result["max_reddit_mentions"] == 40.0


class TestNormalizeMetrics:
    """Test normalize_metrics function edge cases."""
    
    def test_normal_case(self):
        """Test with normal metrics and max values."""
        metrics = {
            "grid_id": "Test-Cell-01",
            "business_count": 2,
            "instagram_volume": 19,
            "reddit_mentions": 25
        }
        max_values = {
            "max_business_count": 4.0,
            "max_instagram_volume": 38.0,
            "max_reddit_mentions": 50.0
        }
        
        result = normalize_metrics(metrics, max_values)
        
        assert result["supply_norm"] == pytest.approx(0.5)  # 2/4
        assert result["demand_instagram_norm"] == pytest.approx(0.5)  # 19/38
        assert result["demand_reddit_norm"] == pytest.approx(0.5)  # 25/50
    
    def test_zero_business_count(self):
        """Test high opportunity grid (zero businesses, high demand)."""
        metrics = {
            "grid_id": "Test-Cell-02",
            "business_count": 0,
            "instagram_volume": 28,
            "reddit_mentions": 47
        }
        max_values = {
            "max_business_count": 4.0,
            "max_instagram_volume": 38.0,
            "max_reddit_mentions": 50.0
        }
        
        result = normalize_metrics(metrics, max_values)
        
        assert result["supply_norm"] == 0.0  # 0/4
        assert result["demand_instagram_norm"] == pytest.approx(0.7368, rel=1e-3)  # 28/38
        assert result["demand_reddit_norm"] == pytest.approx(0.94, rel=1e-3)  # 47/50
    
    def test_saturated_grid(self):
        """Test saturated grid (max businesses, low demand)."""
        metrics = {
            "grid_id": "Test-Cell-03",
            "business_count": 4,
            "instagram_volume": 10,
            "reddit_mentions": 5
        }
        max_values = {
            "max_business_count": 4.0,
            "max_instagram_volume": 38.0,
            "max_reddit_mentions": 50.0
        }
        
        result = normalize_metrics(metrics, max_values)
        
        assert result["supply_norm"] == 1.0  # 4/4 (saturated)
        assert result["demand_instagram_norm"] == pytest.approx(0.2632, rel=1e-3)  # 10/38
        assert result["demand_reddit_norm"] == pytest.approx(0.1, rel=1e-3)  # 5/50
    
    def test_all_zeros(self):
        """Test grid with no data."""
        metrics = {
            "grid_id": "Test-Cell-04",
            "business_count": 0,
            "instagram_volume": 0,
            "reddit_mentions": 0
        }
        max_values = {
            "max_business_count": 1.0,  # Edge case fallback
            "max_instagram_volume": 1.0,
            "max_reddit_mentions": 1.0
        }
        
        result = normalize_metrics(metrics, max_values)
        
        assert result["supply_norm"] == 0.0
        assert result["demand_instagram_norm"] == 0.0
        assert result["demand_reddit_norm"] == 0.0
    
    def test_missing_keys(self):
        """Test with missing keys in metrics (should default to 0)."""
        metrics = {
            "grid_id": "Test-Cell-05"
            # Missing: business_count, instagram_volume, reddit_mentions
        }
        max_values = {
            "max_business_count": 4.0,
            "max_instagram_volume": 38.0,
            "max_reddit_mentions": 50.0
        }
        
        result = normalize_metrics(metrics, max_values)
        
        assert result["supply_norm"] == 0.0
        assert result["demand_instagram_norm"] == 0.0
        assert result["demand_reddit_norm"] == 0.0
    
    def test_max_values_all_ones(self):
        """Test normalization when max_values are default 1.0 (edge case)."""
        metrics = {
            "grid_id": "Test-Cell-06",
            "business_count": 0,
            "instagram_volume": 0,
            "reddit_mentions": 0
        }
        max_values = {
            "max_business_count": 1.0,
            "max_instagram_volume": 1.0,
            "max_reddit_mentions": 1.0
        }
        
        result = normalize_metrics(metrics, max_values)
        
        # All should be 0/1 = 0.0
        assert result["supply_norm"] == 0.0
        assert result["demand_instagram_norm"] == 0.0
        assert result["demand_reddit_norm"] == 0.0


class TestIntegration:
    """Integration tests for normalization workflow."""
    
    def test_workflow(self):
        """Test complete workflow: compute max values → normalize each grid."""
        metrics_list = [
            {
                "grid_id": "Cell-01",
                "business_count": 0,
                "instagram_volume": 28,
                "reddit_mentions": 47
            },
            {
                "grid_id": "Cell-02",
                "business_count": 4,
                "instagram_volume": 38,
                "reddit_mentions": 50
            },
            {
                "grid_id": "Cell-03",
                "business_count": 2,
                "instagram_volume": 19,
                "reddit_mentions": 25
            }
        ]
        
        # Step 1: Compute max values
        max_values = compute_max_values(metrics_list)
        assert max_values["max_business_count"] == 4.0
        assert max_values["max_instagram_volume"] == 38.0
        assert max_values["max_reddit_mentions"] == 50.0
        
        # Step 2: Normalize each grid
        normalized_list = [
            normalize_metrics(metrics, max_values)
            for metrics in metrics_list
        ]
        
        # Cell-01: High opportunity (0 businesses, high demand)
        assert normalized_list[0]["supply_norm"] == 0.0
        assert normalized_list[0]["demand_instagram_norm"] == pytest.approx(0.7368, rel=1e-3)
        assert normalized_list[0]["demand_reddit_norm"] == pytest.approx(0.94, rel=1e-3)
        
        # Cell-02: Saturated (max businesses, max demand)
        assert normalized_list[1]["supply_norm"] == 1.0
        assert normalized_list[1]["demand_instagram_norm"] == 1.0
        assert normalized_list[1]["demand_reddit_norm"] == 1.0
        
        # Cell-03: Medium (half businesses, half demand)
        assert normalized_list[2]["supply_norm"] == 0.5
        assert normalized_list[2]["demand_instagram_norm"] == 0.5
        assert normalized_list[2]["demand_reddit_norm"] == 0.5
    
    def test_gos_calculation_preview(self):
        """Preview GOS calculation with normalized values."""
        # Cell-01: High opportunity
        metrics = {
            "grid_id": "Cell-01",
            "business_count": 0,
            "instagram_volume": 28,
            "reddit_mentions": 47
        }
        max_values = {
            "max_business_count": 4.0,
            "max_instagram_volume": 38.0,
            "max_reddit_mentions": 50.0
        }
        
        normalized = normalize_metrics(metrics, max_values)
        
        # GOS formula preview (will be in scoring.py):
        # GOS = (1 - supply_norm) * 0.4 + demand_instagram_norm * 0.25 + demand_reddit_norm * 0.35
        gos = (
            (1 - normalized["supply_norm"]) * 0.4 +
            normalized["demand_instagram_norm"] * 0.25 +
            normalized["demand_reddit_norm"] * 0.35
        )
        
        # Expected: (1-0)*0.4 + 0.7368*0.25 + 0.94*0.35 ≈ 0.91
        assert gos == pytest.approx(0.9132, rel=1e-3)
        assert gos > 0.9  # High opportunity confirmed!
