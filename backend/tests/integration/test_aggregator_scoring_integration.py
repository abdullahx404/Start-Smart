"""
Integration test: Aggregator + Scoring Service

Tests the complete workflow from database → aggregation → normalization → scoring.
"""

import sys
from pathlib import Path

# Add backend to path for integration testing
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from src.services.aggregator import aggregate_all_grids, normalize_metrics
from src.services.scoring_service import calculate_gos, calculate_confidence, score_grid


def test_full_pipeline():
    """Test complete pipeline: aggregate → normalize → score."""
    
    print(f"\n{'='*70}")
    print("INTEGRATION TEST: Aggregator + Scoring Service")
    print(f"{'='*70}\n")
    
    # Step 1: Aggregate all grids
    print("Step 1: Aggregating data from database...")
    metrics_list, max_values = aggregate_all_grids("Gym")
    print(f"✓ Aggregated {len(metrics_list)} grids")
    print(f"✓ Max values: {max_values}")
    
    # Step 2: Score each grid
    print(f"\nStep 2: Scoring each grid...")
    scored_grids = []
    
    for raw_metrics in metrics_list:
        # Normalize metrics
        normalized = normalize_metrics(raw_metrics, max_values)
        
        # Calculate scores
        result = score_grid(
            raw_metrics["grid_id"],
            raw_metrics,
            normalized
        )
        
        # Add raw and normalized metrics to result
        result.update({
            "business_count": raw_metrics["business_count"],
            "instagram_volume": raw_metrics["instagram_volume"],
            "reddit_mentions": raw_metrics["reddit_mentions"],
            "supply_norm": normalized["supply_norm"],
            "demand_instagram_norm": normalized["demand_instagram_norm"],
            "demand_reddit_norm": normalized["demand_reddit_norm"]
        })
        
        scored_grids.append(result)
    
    print(f"✓ Scored {len(scored_grids)} grids")
    
    # Step 3: Sort by GOS (descending)
    scored_grids.sort(key=lambda x: x["gos"], reverse=True)
    
    # Step 4: Display results
    print(f"\n{'='*70}")
    print("TOP 5 OPPORTUNITY GRIDS (by GOS)")
    print(f"{'='*70}\n")
    
    for i, grid in enumerate(scored_grids[:5], 1):
        print(f"{i}. {grid['grid_id']}")
        print(f"   GOS: {grid['gos']:.3f} ({grid['opportunity_level'].upper()})")
        print(f"   Confidence: {grid['confidence']:.3f}")
        print(f"   Raw: {grid['business_count']} businesses, "
              f"{grid['instagram_volume']} Instagram, {grid['reddit_mentions']} Reddit")
        print(f"   Normalized: supply={grid['supply_norm']:.2f}, "
              f"instagram={grid['demand_instagram_norm']:.2f}, reddit={grid['demand_reddit_norm']:.2f}")
        print()
    
    # Step 5: Verify top grids are high opportunity
    print(f"{'='*70}")
    print("VALIDATION CHECKS")
    print(f"{'='*70}\n")
    
    top_grid = scored_grids[0]
    print(f"✓ Top grid: {top_grid['grid_id']}")
    print(f"  Expected: Cell-01 or Cell-02 (zero businesses + high demand)")
    assert top_grid['grid_id'] in ['DHA-Phase2-Cell-01', 'DHA-Phase2-Cell-02']
    print(f"  ✓ PASS")
    
    print(f"\n✓ Top grid GOS: {top_grid['gos']:.3f}")
    print(f"  Expected: >= 0.8 (high opportunity)")
    assert top_grid['gos'] >= 0.8
    print(f"  ✓ PASS")
    
    print(f"\n✓ Top grid business count: {top_grid['business_count']}")
    print(f"  Expected: 0 (no competition)")
    assert top_grid['business_count'] == 0
    print(f"  ✓ PASS")
    
    # Find saturated grid (most businesses)
    saturated_grid = max(scored_grids, key=lambda x: x['business_count'])
    print(f"\n✓ Most saturated grid: {saturated_grid['grid_id']}")
    print(f"  Businesses: {saturated_grid['business_count']}")
    print(f"  GOS: {saturated_grid['gos']:.3f}")
    print(f"  Expected: Lower GOS than top grid")
    assert saturated_grid['gos'] < top_grid['gos']
    print(f"  ✓ PASS")
    
    # Count opportunity levels
    high_count = sum(1 for g in scored_grids if g['opportunity_level'] == 'high')
    medium_count = sum(1 for g in scored_grids if g['opportunity_level'] == 'medium')
    low_count = sum(1 for g in scored_grids if g['opportunity_level'] == 'low')
    
    print(f"\n✓ Opportunity distribution:")
    print(f"  High: {high_count} grids")
    print(f"  Medium: {medium_count} grids")
    print(f"  Low: {low_count} grids")
    
    print(f"\n{'='*70}")
    print("✅ ALL INTEGRATION TESTS PASSED!")
    print(f"{'='*70}\n")
    
    return scored_grids


if __name__ == "__main__":
    scored_grids = test_full_pipeline()
    
    # Export results for Phase 2 handoff
    print(f"{'='*70}")
    print("RESULTS SUMMARY FOR PHASE 2")
    print(f"{'='*70}\n")
    
    print("Ready for next steps:")
    print("  1. ✅ Aggregator service (complete)")
    print("  2. ✅ Normalization functions (complete)")
    print("  3. ✅ Scoring service (complete)")
    print("  4. ⏳ Explainability module (next)")
    print("  5. ⏳ Database population (grid_metrics table)")
    print("  6. ⏳ High-level API (scoring_service.py extensions)")
    
    print(f"\n{'='*70}\n")
