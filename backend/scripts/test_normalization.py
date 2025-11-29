"""Quick validation of normalization and GOS calculation."""

import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from src.services.aggregator import aggregate_all_grids, normalize_metrics

# Get all metrics and max values
metrics_list, max_vals = aggregate_all_grids('Gym')

# Test with first grid (Cell-01)
first_grid = metrics_list[0]
normalized = normalize_metrics(first_grid, max_vals)

# Calculate GOS (preview for scoring.py)
gos = (
    (1 - normalized['supply_norm']) * 0.4 +
    normalized['demand_instagram_norm'] * 0.25 +
    normalized['demand_reddit_norm'] * 0.35
)

print(f"\n{'='*60}")
print(f"GOS CALCULATION VALIDATION")
print(f"{'='*60}")
print(f"\nGrid: {first_grid['grid_id']}")
print(f"\nRaw Metrics:")
print(f"  Businesses: {first_grid['business_count']}")
print(f"  Instagram: {first_grid['instagram_volume']}")
print(f"  Reddit: {first_grid['reddit_mentions']}")
print(f"\nMax Values:")
print(f"  Max Businesses: {max_vals['max_business_count']}")
print(f"  Max Instagram: {max_vals['max_instagram_volume']}")
print(f"  Max Reddit: {max_vals['max_reddit_mentions']}")
print(f"\nNormalized Metrics:")
print(f"  Supply: {normalized['supply_norm']:.4f}")
print(f"  Instagram Demand: {normalized['demand_instagram_norm']:.4f}")
print(f"  Reddit Demand: {normalized['demand_reddit_norm']:.4f}")
print(f"\nGOS Calculation:")
print(f"  (1 - {normalized['supply_norm']:.4f}) * 0.4 = {(1 - normalized['supply_norm']) * 0.4:.4f}")
print(f"  {normalized['demand_instagram_norm']:.4f} * 0.25 = {normalized['demand_instagram_norm'] * 0.25:.4f}")
print(f"  {normalized['demand_reddit_norm']:.4f} * 0.35 = {normalized['demand_reddit_norm'] * 0.35:.4f}")
print(f"\n  GOS = {gos:.4f}")

if gos > 0.8:
    print(f"\n✅ HIGH OPPORTUNITY (GOS > 0.8)")
elif gos > 0.5:
    print(f"\n⚠️ MEDIUM OPPORTUNITY (0.5 < GOS ≤ 0.8)")
else:
    print(f"\n❌ LOW OPPORTUNITY (GOS ≤ 0.5)")

print(f"{'='*60}\n")
