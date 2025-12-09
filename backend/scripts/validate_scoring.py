"""
Scoring Validation Script

Validates that computed GOS scores make intuitive sense and flags anomalies.

Outputs:
1. Detailed per-grid analysis (console)
2. Anomaly detection (console)
3. Summary statistics (console)
4. CSV export for manual review

Usage:
    python scripts/validate_scoring.py --category Gym
    python scripts/validate_scoring.py --category Gym --neighborhood "DHA Phase 2"
    python scripts/validate_scoring.py --category Gym --export results/validation.csv
"""

import sys
from pathlib import Path
import argparse
from datetime import datetime
from typing import List, Dict, Any

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from src.database.connection import get_session
from src.database.models import GridMetricsModel, GridCellModel

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    print("Warning: pandas not installed. CSV export disabled.")
    print("Install with: pip install pandas")


# ============================================================================
# VALIDATION LOGIC
# ============================================================================

def validate_scoring(category: str, neighborhood: str = None) -> Dict[str, Any]:
    """
    Validate scoring results for given category.
    
    Returns:
        dict: Validation results with grids, anomalies, and summary
    """
    with get_session() as session:
        # Query scored grids
        query = session.query(GridMetricsModel).filter_by(category=category)
        
        if neighborhood:
            # Join with grid_cells to filter by neighborhood
            query = query.join(
                GridCellModel,
                GridMetricsModel.grid_id == GridCellModel.grid_id
            ).filter(GridCellModel.neighborhood == neighborhood)
        
        scored_grids = query.all()
        scored_grids = query.all()
        
        if len(scored_grids) == 0:
            print(f"\nNo scored grids found for category '{category}'")
            if neighborhood:
                print(f"  in neighborhood '{neighborhood}'")
            print("\nRun scoring first:")
            print(f"  python scripts/run_scoring.py --category {category}")
            return {"grids": [], "anomalies": [], "summary": {}}
        
        # Process each grid
        grids_data = []
        anomalies = []
        
        for grid_metric in scored_grids:
            # Get neighborhood from grid_cells table
            grid_cell = session.query(GridCellModel).filter_by(grid_id=grid_metric.grid_id).first()
            neighborhood_name = grid_cell.neighborhood if grid_cell else "Unknown"
            
            grid_data = {
                "grid_id": grid_metric.grid_id,
                "neighborhood": neighborhood_name,
                "gos": float(grid_metric.gos) if grid_metric.gos is not None else 0.0,
                "confidence": float(grid_metric.confidence) if grid_metric.confidence is not None else 0.0,
                "business_count": grid_metric.business_count,
                "instagram_volume": grid_metric.instagram_volume,
                "reddit_mentions": grid_metric.reddit_mentions,
                "demand_total": grid_metric.instagram_volume + grid_metric.reddit_mentions,
                "top_posts": grid_metric.top_posts_json or [],
                "competitors": grid_metric.competitors_json or [],
            }
            
            grids_data.append(grid_data)
            
            # Anomaly detection
            anomaly_reasons = []
            
            # Anomaly 1: High GOS but high business count (shouldn't happen)
            if grid_data["gos"] >= 0.7 and grid_data["business_count"] >= 8:
                anomaly_reasons.append(
                    f"High GOS ({grid_data['gos']:.3f}) despite high competition ({grid_data['business_count']} businesses)"
                )
            
            # Anomaly 2: Low GOS but low businesses + high demand (shouldn't happen)
            if (grid_data["gos"] < 0.4 and 
                grid_data["business_count"] <= 2 and 
                grid_data["demand_total"] >= 20):
                anomaly_reasons.append(
                    f"Low GOS ({grid_data['gos']:.3f}) despite low competition ({grid_data['business_count']}) and high demand ({grid_data['demand_total']} posts)"
                )
            
            # Anomaly 3: Low confidence (flag for review)
            if grid_data["confidence"] < 0.5:
                anomaly_reasons.append(
                    f"Low confidence ({grid_data['confidence']:.3f}) - insufficient data"
                )
            
            # Anomaly 4: GOS outside valid range
            if not (0.0 <= grid_data["gos"] <= 1.0):
                anomaly_reasons.append(
                    f"GOS out of range: {grid_data['gos']:.3f}"
                )
            
            # Anomaly 5: Confidence outside valid range
            if not (0.0 <= grid_data["confidence"] <= 1.0):
                anomaly_reasons.append(
                    f"Confidence out of range: {grid_data['confidence']:.3f}"
                )
            
            if anomaly_reasons:
                anomalies.append({
                    "grid_id": grid_data["grid_id"],
                    "reasons": anomaly_reasons
                })
        
        # Generate summary statistics
        gos_scores = [g["gos"] for g in grids_data]
        confidence_scores = [g["confidence"] for g in grids_data]
        
        # GOS distribution histogram
        gos_low = sum(1 for s in gos_scores if 0.0 <= s < 0.3)
        gos_medium = sum(1 for s in gos_scores if 0.3 <= s < 0.6)
        gos_high = sum(1 for s in gos_scores if 0.6 <= s <= 1.0)
        
        summary = {
            "total_grids": len(grids_data),
            "avg_gos": sum(gos_scores) / len(gos_scores) if gos_scores else 0,
            "avg_confidence": sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0,
            "gos_distribution": {
                "low (0.0-0.3)": gos_low,
                "medium (0.3-0.6)": gos_medium,
                "high (0.6-1.0)": gos_high
            },
            "anomaly_count": len(anomalies)
        }
    
    return {
        "grids": grids_data,
        "anomalies": anomalies,
        "summary": summary
    }


# ============================================================================
# OUTPUT FUNCTIONS
# ============================================================================

def print_grid_details(grid: Dict[str, Any]) -> None:
    """Print detailed analysis for a single grid."""
    print(f"\n{'='*80}")
    print(f"Grid: {grid['grid_id']} ({grid['neighborhood']})")
    print(f"{'='*80}")
    
    print(f"\n📊 SCORES:")
    print(f"  GOS:        {grid['gos']:.3f}")
    print(f"  Confidence: {grid['confidence']:.3f}")
    
    print(f"\n📈 METRICS:")
    print(f"  Businesses:       {grid['business_count']}")
    print(f"  Instagram Volume: {grid['instagram_volume']}")
    print(f"  Reddit Mentions:  {grid['reddit_mentions']}")
    print(f"  Total Demand:     {grid['demand_total']}")
    
    print(f"\n📝 TOP POSTS:")
    if grid['top_posts']:
        for i, post in enumerate(grid['top_posts'][:3], 1):
            text = post.get('text', 'N/A')
            if len(text) > 100:
                text = text[:97] + "..."
            print(f"  {i}. [{post.get('source', 'N/A')}] {text}")
    else:
        print("  (No posts available)")
    
    print(f"\n🏢 TOP COMPETITORS:")
    if grid['competitors']:
        for i, comp in enumerate(grid['competitors'][:3], 1):
            print(f"  {i}. {comp.get('name', 'N/A')} ({comp.get('distance_km', 0):.2f} km)")
    else:
        print("  (No competitors found)")


def print_anomalies(anomalies: List[Dict[str, Any]]) -> None:
    """Print detected anomalies."""
    if not anomalies:
        print(f"\n{'='*80}")
        print("✅ NO ANOMALIES DETECTED")
        print(f"{'='*80}")
        return
    
    print(f"\n{'='*80}")
    print(f"⚠️  ANOMALIES DETECTED ({len(anomalies)})")
    print(f"{'='*80}")
    
    for anomaly in anomalies:
        print(f"\nGrid: {anomaly['grid_id']}")
        for reason in anomaly['reasons']:
            print(f"  - {reason}")


def print_summary(summary: Dict[str, Any]) -> None:
    """Print summary statistics."""
    print(f"\n{'='*80}")
    print("📊 SUMMARY STATISTICS")
    print(f"{'='*80}")
    
    print(f"\nTotal Grids: {summary['total_grids']}")
    print(f"Average GOS: {summary['avg_gos']:.3f}")
    print(f"Average Confidence: {summary['avg_confidence']:.3f}")
    
    print(f"\nGOS Distribution:")
    for range_name, count in summary['gos_distribution'].items():
        percentage = (count / summary['total_grids'] * 100) if summary['total_grids'] > 0 else 0
        bar = "█" * int(percentage / 5)  # Scale bar to fit
        print(f"  {range_name:20s}: {count:3d} ({percentage:5.1f}%) {bar}")
    
    print(f"\nAnomalies Flagged: {summary['anomaly_count']}")


def export_to_csv(grids: List[Dict[str, Any]], filename: str) -> None:
    """Export validation results to CSV."""
    if not HAS_PANDAS:
        print("\n❌ CSV export failed: pandas not installed")
        return
    
    # Prepare data for CSV
    csv_data = []
    for grid in grids:
        csv_data.append({
            "grid_id": grid["grid_id"],
            "neighborhood": grid["neighborhood"],
            "gos": f"{grid['gos']:.3f}",
            "confidence": f"{grid['confidence']:.3f}",
            "business_count": grid["business_count"],
            "instagram_volume": grid["instagram_volume"],
            "reddit_mentions": grid["reddit_mentions"],
            "demand_total": grid["demand_total"]
        })
    
    df = pd.DataFrame(csv_data)
    
    # Sort by GOS descending
    df = df.sort_values("gos", ascending=False)
    
    # Export
    df.to_csv(filename, index=False)
    print(f"\n✅ CSV exported to: {filename}")
    print(f"   Rows: {len(df)}")


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Validate scoring results and flag anomalies"
    )
    parser.add_argument(
        "--category",
        required=True,
        help="Category to validate (e.g., Gym, Cafe)"
    )
    parser.add_argument(
        "--neighborhood",
        help="Optional: Filter by neighborhood"
    )
    parser.add_argument(
        "--export",
        help="Optional: Export to CSV file (e.g., results/validation.csv)"
    )
    parser.add_argument(
        "--details",
        action="store_true",
        help="Show detailed analysis for each grid"
    )
    
    args = parser.parse_args()
    
    print(f"\n{'='*80}")
    print(f"SCORING VALIDATION - {args.category}")
    if args.neighborhood:
        print(f"Neighborhood: {args.neighborhood}")
    print(f"{'='*80}")
    
    # Run validation
    results = validate_scoring(args.category, args.neighborhood)
    
    if not results["grids"]:
        return
    
    # Print grid details if requested
    if args.details:
        for grid in sorted(results["grids"], key=lambda g: g["gos"], reverse=True):
            print_grid_details(grid)
    
    # Print anomalies
    print_anomalies(results["anomalies"])
    
    # Print summary
    print_summary(results["summary"])
    
    # Export to CSV if requested
    if args.export:
        export_to_csv(results["grids"], args.export)
    
    print("\n")


if __name__ == "__main__":
    main()
