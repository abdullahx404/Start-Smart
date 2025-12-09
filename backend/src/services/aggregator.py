"""
Data Aggregation Service for Grid Metrics

This module computes raw metrics per grid × category by aggregating data from:
- businesses table: competitor counts, ratings, reviews
- social_posts table: Instagram-like mentions, Reddit-like demand signals

Phase 2 - Analytics & Scoring Engine
"""

from typing import Dict, List, Optional
import time

# Import database components
try:
    from sqlalchemy import func
    from src.database.connection import get_session
    from src.database.models import BusinessModel, SocialPostModel, GridCellModel
    from src.utils.logger import get_logger
    
    logger = get_logger(__name__)
except ModuleNotFoundError:
    # For CLI testing, add parent directory to path
    import sys
    from pathlib import Path
    backend_dir = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(backend_dir))
    
    from sqlalchemy import func
    from src.database.connection import get_session
    from src.database.models import BusinessModel, SocialPostModel, GridCellModel
    from src.utils.logger import get_logger
    
    logger = get_logger(__name__)


def aggregate_grid_metrics(grid_id: str, category: str) -> Dict:
    """
    Compute raw metrics for a single grid × category combination.
    
    Args:
        grid_id: Grid cell identifier (e.g., "DHA-Phase2-Cell-01")
        category: Business category (e.g., "Gym", "Cafe")
    
    Returns:
        Dictionary with aggregated metrics:
        {
            "grid_id": str,
            "category": str,
            "business_count": int,
            "instagram_volume": int,  # mention posts
            "reddit_mentions": int,   # demand + complaint posts
            "avg_rating": float or None,
            "total_reviews": int
        }
    
    Example:
        >>> metrics = aggregate_grid_metrics("DHA-Phase2-Cell-01", "Gym")
        >>> print(f"Business count: {metrics['business_count']}")
        Business count: 0
    """
    logger.info(f"Aggregating metrics for grid_id={grid_id}, category={category}")
    
    with get_session() as session:
        # 1. Business count
        business_count = (
            session.query(func.count(BusinessModel.business_id))
            .filter(
                BusinessModel.grid_id == grid_id,
                BusinessModel.category == category
            )
            .scalar()
        )
        
        # 2. Instagram volume (mention posts)
        # For MVP: simulated posts with post_type='mention' treated as Instagram-like
        instagram_volume = (
            session.query(func.count(SocialPostModel.post_id))
            .filter(
                SocialPostModel.grid_id == grid_id,
                SocialPostModel.source == 'simulated',
                SocialPostModel.post_type == 'mention'
            )
            .scalar()
        )
        
        # 3. Reddit mentions (demand + complaint posts)
        # These represent explicit demand signals
        reddit_mentions = (
            session.query(func.count(SocialPostModel.post_id))
            .filter(
                SocialPostModel.grid_id == grid_id,
                SocialPostModel.source == 'simulated',
                SocialPostModel.post_type.in_(['demand', 'complaint'])
            )
            .scalar()
        )
        
        # 4. Average rating and total reviews
        # Only include businesses with non-null ratings
        rating_stats = (
            session.query(
                func.avg(BusinessModel.rating).label('avg_rating'),
                func.sum(BusinessModel.review_count).label('total_reviews')
            )
            .filter(
                BusinessModel.grid_id == grid_id,
                BusinessModel.category == category,
                BusinessModel.rating.isnot(None)
            )
            .first()
        )
        
        avg_rating = float(rating_stats.avg_rating) if rating_stats.avg_rating else None
        total_reviews = int(rating_stats.total_reviews) if rating_stats.total_reviews else 0
    
    # Log warnings for edge cases
    if business_count == 0:
        logger.warning(f"Grid {grid_id} has ZERO businesses for category {category}")
    
    if instagram_volume == 0 and reddit_mentions == 0:
        logger.warning(f"Grid {grid_id} has ZERO social posts")
    
    metrics = {
        "grid_id": grid_id,
        "category": category,
        "business_count": business_count or 0,
        "instagram_volume": instagram_volume or 0,
        "reddit_mentions": reddit_mentions or 0,
        "avg_rating": avg_rating,
        "total_reviews": total_reviews
    }
    
    logger.debug(
        f"Metrics for {grid_id}: "
        f"businesses={business_count}, "
        f"instagram={instagram_volume}, "
        f"reddit={reddit_mentions}, "
        f"rating={avg_rating if avg_rating is not None else 'N/A'}"
    )
    
    return metrics


def aggregate_all_grids(category: str) -> tuple[List[Dict], Dict]:
    """
    Compute metrics for all grid cells in a given category.
    
    Args:
        category: Business category (e.g., "Gym", "Cafe")
    
    Returns:
        Tuple of (metrics_list, max_values):
        - metrics_list: List of metric dictionaries, one per grid cell
        - max_values: Dict with max_business_count, max_instagram_volume, max_reddit_mentions
    
    Example:
        >>> all_metrics, max_vals = aggregate_all_grids("Gym")
        >>> print(f"Total grids: {len(all_metrics)}")
        Total grids: 9
        >>> high_opportunity = [m for m in all_metrics if m['business_count'] == 0]
        >>> print(f"Grids with zero businesses: {len(high_opportunity)}")
        Grids with zero businesses: 5
    """
    logger.info(f"Starting aggregation for all grids, category={category}")
    start_time = time.time()
    
    # Get all grid IDs from grid_cells table
    with get_session() as session:
        grid_ids = (
            session.query(GridCellModel.grid_id)
            .order_by(GridCellModel.grid_id)
            .all()
        )
    
    grid_id_list = [row.grid_id for row in grid_ids]
    logger.info(f"Found {len(grid_id_list)} grid cells to process")
    
    # Aggregate metrics for each grid
    all_metrics = []
    grids_with_zero_businesses = []
    grids_with_zero_posts = []
    
    for grid_id in grid_id_list:
        metrics = aggregate_grid_metrics(grid_id, category)
        all_metrics.append(metrics)
        
        # Track edge cases
        if metrics['business_count'] == 0:
            grids_with_zero_businesses.append(grid_id)
        
        if metrics['instagram_volume'] == 0 and metrics['reddit_mentions'] == 0:
            grids_with_zero_posts.append(grid_id)
    
    # Summary statistics
    total_businesses = sum(m['business_count'] for m in all_metrics)
    total_instagram = sum(m['instagram_volume'] for m in all_metrics)
    total_reddit = sum(m['reddit_mentions'] for m in all_metrics)
    
    elapsed_time = time.time() - start_time
    
    logger.info(
        f"Aggregation complete in {elapsed_time:.2f}s: "
        f"{len(all_metrics)} grids processed"
    )
    logger.info(
        f"Summary: {total_businesses} businesses, "
        f"{total_instagram} Instagram posts, "
        f"{total_reddit} Reddit mentions"
    )
    
    if grids_with_zero_businesses:
        logger.warning(
            f"{len(grids_with_zero_businesses)} grids with zero businesses: "
            f"{', '.join(grids_with_zero_businesses)}"
        )
    
    if grids_with_zero_posts:
        logger.warning(
            f"{len(grids_with_zero_posts)} grids with zero social posts: "
            f"{', '.join(grids_with_zero_posts)}"
        )
    
    # Compute max values for normalization
    max_values = compute_max_values(all_metrics)
    
    return all_metrics, max_values


def compute_max_values(metrics_list: List[Dict]) -> Dict:
    """
    Calculate maximum values across all grids for normalization.
    
    Args:
        metrics_list: List of metric dictionaries from aggregate_all_grids()
    
    Returns:
        Dictionary with max values:
        {
            "max_business_count": float,
            "max_instagram_volume": float,
            "max_reddit_mentions": float
        }
    
    Example:
        >>> metrics_list, max_vals = aggregate_all_grids("Gym")
        >>> print(f"Max businesses in any grid: {max_vals['max_business_count']}")
        Max businesses in any grid: 4.0
    """
    if not metrics_list:
        logger.warning("Empty metrics list provided to compute_max_values()")
        return {
            "max_business_count": 1.0,  # Avoid division by zero
            "max_instagram_volume": 1.0,
            "max_reddit_mentions": 1.0
        }
    
    max_business = max(m['business_count'] for m in metrics_list)
    max_instagram = max(m['instagram_volume'] for m in metrics_list)
    max_reddit = max(m['reddit_mentions'] for m in metrics_list)
    
    # Handle edge case: if max is 0, use 1 to avoid division by zero
    max_values = {
        "max_business_count": float(max_business) if max_business > 0 else 1.0,
        "max_instagram_volume": float(max_instagram) if max_instagram > 0 else 1.0,
        "max_reddit_mentions": float(max_reddit) if max_reddit > 0 else 1.0
    }
    
    logger.info(
        f"Max values for normalization: "
        f"businesses={max_values['max_business_count']}, "
        f"instagram={max_values['max_instagram_volume']}, "
        f"reddit={max_values['max_reddit_mentions']}"
    )
    
    return max_values


def normalize_metrics(metrics: Dict, max_values: Dict) -> Dict:
    """
    Normalize a single grid's metrics using max values from all grids.
    
    Converts raw counts to 0.0-1.0 range for scoring engine.
    
    Args:
        metrics: Single grid's raw metrics (from aggregate_grid_metrics)
        max_values: Max values across all grids (from compute_max_values)
    
    Returns:
        Dictionary with normalized values:
        {
            "supply_norm": float,  # business_count / max_business_count
            "demand_instagram_norm": float,  # instagram_volume / max_instagram_volume
            "demand_reddit_norm": float  # reddit_mentions / max_reddit_mentions
        }
        
        All values are 0.0 to 1.0.
    
    Example:
        >>> metrics = aggregate_grid_metrics("DHA-Phase2-Cell-01", "Gym")
        >>> all_metrics, max_vals = aggregate_all_grids("Gym")
        >>> normalized = normalize_metrics(metrics, max_vals)
        >>> print(f"Supply normalized: {normalized['supply_norm']:.2f}")
        Supply normalized: 0.00
    """
    # Extract raw values
    business_count = metrics.get('business_count', 0)
    instagram_volume = metrics.get('instagram_volume', 0)
    reddit_mentions = metrics.get('reddit_mentions', 0)
    
    # Extract max values
    max_business = max_values.get('max_business_count', 1.0)
    max_instagram = max_values.get('max_instagram_volume', 1.0)
    max_reddit = max_values.get('max_reddit_mentions', 1.0)
    
    # Normalize to 0.0-1.0 range
    normalized = {
        "supply_norm": business_count / max_business,
        "demand_instagram_norm": instagram_volume / max_instagram,
        "demand_reddit_norm": reddit_mentions / max_reddit
    }
    
    logger.debug(
        f"Normalized {metrics.get('grid_id', 'unknown')}: "
        f"supply={normalized['supply_norm']:.2f}, "
        f"instagram={normalized['demand_instagram_norm']:.2f}, "
        f"reddit={normalized['demand_reddit_norm']:.2f}"
    )
    
    return normalized


# CLI for testing
if __name__ == "__main__":
    import sys
    
    # Simple CLI for manual testing
    if len(sys.argv) > 1:
        category = sys.argv[1]
    else:
        category = "Gym"  # Default
    
    print(f"\n{'='*70}")
    print(f"DATA AGGREGATION TEST - Category: {category}")
    print(f"{'='*70}\n")
    
    # Test single grid
    print("Testing single grid aggregation:")
    test_grid = "DHA-Phase2-Cell-01"
    single_metrics = aggregate_grid_metrics(test_grid, category)
    print(f"\nMetrics for {test_grid}:")
    for key, value in single_metrics.items():
        print(f"  {key}: {value}")
    
    # Test all grids
    print(f"\n{'='*70}")
    print("Testing all grids aggregation:")
    all_metrics, max_vals = aggregate_all_grids(category)
    
    print(f"\nTotal grids processed: {len(all_metrics)}")
    print("\nTop 5 grids by business count:")
    sorted_by_business = sorted(
        all_metrics,
        key=lambda x: x['business_count'],
        reverse=True
    )
    for i, m in enumerate(sorted_by_business[:5], 1):
        print(
            f"  {i}. {m['grid_id']}: {m['business_count']} businesses, "
            f"{m['instagram_volume']} Instagram, {m['reddit_mentions']} Reddit"
        )
    
    print("\nTop 5 grids by social activity:")
    sorted_by_social = sorted(
        all_metrics,
        key=lambda x: x['instagram_volume'] + x['reddit_mentions'],
        reverse=True
    )
    for i, m in enumerate(sorted_by_social[:5], 1):
        total_social = m['instagram_volume'] + m['reddit_mentions']
        print(
            f"  {i}. {m['grid_id']}: {total_social} total posts "
            f"({m['instagram_volume']} Instagram, {m['reddit_mentions']} Reddit)"
        )
    
    # Test normalization
    print(f"\n{'='*70}")
    print("Max values for normalization:")
    for key, value in max_vals.items():
        print(f"  {key}: {value}")
    
    # Test normalize_metrics with first grid
    if all_metrics:
        print(f"\n{'='*70}")
        print("Testing normalization (first grid):")
        first_grid = all_metrics[0]
        normalized = normalize_metrics(first_grid, max_vals)
        print(f"\nGrid: {first_grid['grid_id']}")
        print(f"Raw metrics:")
        print(f"  business_count: {first_grid['business_count']}")
        print(f"  instagram_volume: {first_grid['instagram_volume']}")
        print(f"  reddit_mentions: {first_grid['reddit_mentions']}")
        print(f"\nNormalized metrics:")
        for key, value in normalized.items():
            print(f"  {key}: {value:.4f}")
    
    print(f"\n{'='*70}")
    print("✅ Aggregation and normalization test complete!")
    print(f"{'='*70}\n")
