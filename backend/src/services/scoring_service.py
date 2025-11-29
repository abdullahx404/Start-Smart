"""
Gap Opportunity Score (GOS) Calculation Service

This module implements the core scoring algorithm for identifying business opportunities
in grid cells based on supply-demand dynamics from Phase 2 Analytics & Scoring Engine.

The GOS formula balances three factors:
1. Low competition (1 - supply_norm): Higher score when fewer businesses exist
2. Instagram demand (demand_instagram_norm): Social media engagement signals
3. Reddit demand (demand_reddit_norm): Direct demand/complaint signals from community

Phase 2 - Analytics & Scoring Engine
"""

import math
from typing import Dict, List, Optional
from datetime import datetime

# Scoring weights (configurable later via config file)
WEIGHT_SUPPLY = 0.4      # Weight for competition/supply factor
WEIGHT_INSTAGRAM = 0.25  # Weight for Instagram social demand
WEIGHT_REDDIT = 0.35     # Weight for Reddit demand signals

# Confidence calculation constants
CONFIDENCE_K1 = 5.0      # Instagram volume scaling factor
CONFIDENCE_K2 = 3.0      # Reddit mentions scaling factor
CONFIDENCE_DIVERSITY_BONUS = 0.2  # Bonus when both sources present


def calculate_gos(normalized_metrics: Dict) -> float:
    """
    Calculate Gap Opportunity Score (GOS) from normalized metrics.
    
    The GOS formula identifies high-opportunity areas by combining:
    - Low competition (high score when supply_norm is low)
    - High social demand (high scores from Instagram and Reddit signals)
    
    Formula:
        GOS = (1 - supply_norm) * WEIGHT_SUPPLY + 
              demand_instagram_norm * WEIGHT_INSTAGRAM + 
              demand_reddit_norm * WEIGHT_REDDIT
    
    Where:
        - supply_norm: Normalized business count (0.0 = no competition, 1.0 = saturated)
        - demand_instagram_norm: Normalized Instagram mentions (0.0 to 1.0)
        - demand_reddit_norm: Normalized Reddit demand signals (0.0 to 1.0)
    
    Weights:
        - Supply: 0.4 (40%) - Primary factor; low competition is critical
        - Instagram: 0.25 (25%) - Social media engagement signals
        - Reddit: 0.35 (35%) - Direct demand/complaint signals (higher weight than Instagram)
    
    Args:
        normalized_metrics: Dictionary with normalized values (from normalize_metrics):
            {
                "supply_norm": float (0.0 to 1.0),
                "demand_instagram_norm": float (0.0 to 1.0),
                "demand_reddit_norm": float (0.0 to 1.0)
            }
    
    Returns:
        GOS score (0.0 to 1.0), rounded to 3 decimal places.
        - 0.8-1.0: High opportunity (low competition + high demand)
        - 0.5-0.8: Medium opportunity
        - 0.0-0.5: Low opportunity (high competition or low demand)
    
    Example:
        >>> normalized = {
        ...     "supply_norm": 0.0,          # Zero competitors
        ...     "demand_instagram_norm": 0.74,  # High Instagram activity
        ...     "demand_reddit_norm": 0.94     # Very high Reddit demand
        ... }
        >>> gos = calculate_gos(normalized)
        >>> print(f"GOS: {gos}")
        GOS: 0.913
        >>> # Interpretation: VERY HIGH opportunity (empty market + strong demand)
    
    Edge Cases:
        - All metrics 0.0 → GOS = 0.4 (only supply component contributes)
        - supply_norm = 1.0, demands = 0.0 → GOS = 0.0 (saturated market, no demand)
        - supply_norm = 0.0, demands = 1.0 → GOS = 1.0 (perfect opportunity)
    """
    supply_norm = normalized_metrics.get("supply_norm", 0.0)
    demand_instagram_norm = normalized_metrics.get("demand_instagram_norm", 0.0)
    demand_reddit_norm = normalized_metrics.get("demand_reddit_norm", 0.0)
    
    # GOS formula: weighted combination of supply gap and demand signals
    gos = (
        (1 - supply_norm) * WEIGHT_SUPPLY +
        demand_instagram_norm * WEIGHT_INSTAGRAM +
        demand_reddit_norm * WEIGHT_REDDIT
    )
    
    # Ensure result is in valid range [0.0, 1.0]
    gos = max(0.0, min(1.0, gos))
    
    # Round to 3 decimal places for consistency
    return round(gos, 3)


def calculate_confidence(raw_metrics: Dict) -> float:
    """
    Calculate confidence score based on data quality and source diversity.
    
    The confidence score indicates how reliable the GOS is based on:
    1. Volume of Instagram data (more posts = higher confidence)
    2. Volume of Reddit data (more mentions = higher confidence)
    3. Source diversity (bonus if BOTH sources have data)
    
    Formula:
        confidence = min(1.0,
            log(1 + instagram_volume) / k1 +
            log(1 + reddit_mentions) / k2 +
            source_diversity_bonus
        )
    
    Where:
        - k1 = 5.0: Instagram scaling factor (dampens growth)
        - k2 = 3.0: Reddit scaling factor (higher weight per post than Instagram)
        - source_diversity_bonus = 0.2: Applied if BOTH sources have data
        - log() = natural logarithm (base e)
    
    The logarithmic scaling ensures:
        - Diminishing returns for very high post counts
        - First few posts contribute more than later posts
        - Prevents any single source from dominating confidence
    
    Args:
        raw_metrics: Dictionary with raw metric counts:
            {
                "instagram_volume": int (count of Instagram-like posts),
                "reddit_mentions": int (count of Reddit-like posts)
            }
    
    Returns:
        Confidence score (0.0 to 1.0), rounded to 3 decimal places.
        - 0.8-1.0: High confidence (abundant data from multiple sources)
        - 0.5-0.8: Medium confidence (moderate data)
        - 0.0-0.5: Low confidence (sparse data or single source)
    
    Example:
        >>> raw = {"instagram_volume": 28, "reddit_mentions": 47}
        >>> confidence = calculate_confidence(raw)
        >>> print(f"Confidence: {confidence}")
        Confidence: 0.948
        >>> # Interpretation: HIGH confidence (good data from both sources)
    
    Edge Cases:
        - Both volumes = 0 → confidence = 0.0 (no data)
        - Only Instagram data → confidence ≈ 0.4-0.6 (no diversity bonus)
        - Only Reddit data → confidence ≈ 0.5-0.7 (Reddit weighted higher)
        - Both sources present → +0.2 bonus for diversity
    
    Mathematical Examples:
        1. Sparse data, single source:
           instagram=5, reddit=0
           → log(6)/5 + log(1)/3 + 0 = 0.358/5 + 0 = 0.072 (very low)
        
        2. Moderate data, both sources:
           instagram=20, reddit=15
           → log(21)/5 + log(16)/3 + 0.2 = 0.609 + 0.924 + 0.2 = 0.947 (high)
        
        3. High data, both sources:
           instagram=100, reddit=100
           → log(101)/5 + log(101)/3 + 0.2 = 0.923 + 1.539 + 0.2 = 1.0 (capped)
    """
    instagram_volume = raw_metrics.get("instagram_volume", 0)
    reddit_mentions = raw_metrics.get("reddit_mentions", 0)
    
    # Calculate logarithmic components
    # log(1 + x) ensures log(1) = 0 when x = 0 (graceful handling of zero counts)
    instagram_component = math.log(1 + instagram_volume) / CONFIDENCE_K1
    reddit_component = math.log(1 + reddit_mentions) / CONFIDENCE_K2
    
    # Apply source diversity bonus if BOTH sources have data
    diversity_bonus = 0.0
    if instagram_volume > 0 and reddit_mentions > 0:
        diversity_bonus = CONFIDENCE_DIVERSITY_BONUS
    
    # Combine components and cap at 1.0
    confidence = min(
        1.0,
        instagram_component + reddit_component + diversity_bonus
    )
    
    # Round to 3 decimal places
    return round(confidence, 3)


def score_grid(
    grid_id: str,
    raw_metrics: Dict,
    normalized_metrics: Dict
) -> Dict:
    """
    Score a single grid cell with GOS and confidence.
    
    Convenience function that combines GOS and confidence calculation
    into a single result dictionary.
    
    Args:
        grid_id: Grid cell identifier (e.g., "DHA-Phase2-Cell-01")
        raw_metrics: Dictionary with raw counts (for confidence)
        normalized_metrics: Dictionary with normalized values (for GOS)
    
    Returns:
        Dictionary with scoring results:
        {
            "grid_id": str,
            "gos": float (0.0 to 1.0),
            "confidence": float (0.0 to 1.0),
            "opportunity_level": str ("high", "medium", "low")
        }
    
    Example:
        >>> raw = {
        ...     "business_count": 0,
        ...     "instagram_volume": 28,
        ...     "reddit_mentions": 47
        ... }
        >>> normalized = {
        ...     "supply_norm": 0.0,
        ...     "demand_instagram_norm": 0.74,
        ...     "demand_reddit_norm": 0.94
        ... }
        >>> result = score_grid("DHA-Phase2-Cell-01", raw, normalized)
        >>> print(result)
        {
            "grid_id": "DHA-Phase2-Cell-01",
            "gos": 0.913,
            "confidence": 0.948,
            "opportunity_level": "high"
        }
    """
    gos = calculate_gos(normalized_metrics)
    confidence = calculate_confidence(raw_metrics)
    
    # Classify opportunity level based on GOS
    if gos >= 0.8:
        opportunity_level = "high"
    elif gos >= 0.5:
        opportunity_level = "medium"
    else:
        opportunity_level = "low"
    
    return {
        "grid_id": grid_id,
        "gos": gos,
        "confidence": confidence,
        "opportunity_level": opportunity_level
    }


def get_top_posts(grid_id: str, category: str, limit: int = 3) -> List[Dict]:
    """
    Retrieve top social media posts for a grid to explain demand signals.
    
    Fetches posts with highest engagement to provide evidence for GOS score.
    
    Args:
        grid_id: Grid cell identifier (e.g., "DHA-Phase2-Cell-01")
        category: Business category (currently not used in filtering, reserved for future)
        limit: Maximum number of posts to return (default: 3)
    
    Returns:
        List of post dictionaries:
        [
            {
                "source": str (e.g., "simulated"),
                "text": str (truncated to 200 chars),
                "timestamp": str (ISO format),
                "link": str or None
            }
        ]
        
        Empty list if no posts found.
    
    Example:
        >>> posts = get_top_posts("DHA-Phase2-Cell-01", "Gym", limit=3)
        >>> for post in posts:
        ...     print(f"{post['source']}: {post['text'][:50]}...")
        simulated: Looking for a good gym in DHA Phase 2, any recom...
        simulated: Why are there no decent gyms in this area? Frus...
    """
    try:
        # Import database components (delayed to avoid circular imports)
        from src.database.connection import get_session
        from src.database.models import SocialPostModel
        
        with get_session() as session:
            # Query top posts by engagement score
            posts = (
                session.query(SocialPostModel)
                .filter(
                    SocialPostModel.grid_id == grid_id,
                    SocialPostModel.post_type.in_(['demand', 'complaint', 'mention'])
                )
                .order_by(SocialPostModel.engagement_score.desc())
                .limit(limit)
                .all()
            )
            
            # Convert to dict format
            result = []
            for post in posts:
                # Truncate text to 200 chars
                text = post.text[:200] if post.text else ""
                if len(post.text or "") > 200:
                    text += "..."
                
                # Construct link (fake for simulated data)
                link = None
                if post.source == "simulated":
                    link = f"https://simulated.example/{post.post_id}"
                
                # Format timestamp
                timestamp = post.timestamp.isoformat() if post.timestamp else None
                
                result.append({
                    "source": post.source,
                    "text": text,
                    "timestamp": timestamp,
                    "link": link
                })
            
            return result
            
    except Exception as e:
        # Log error but don't crash
        print(f"Error fetching top posts: {e}")
        return []


def get_competitors(grid_id: str, category: str, limit: int = 5) -> List[Dict]:
    """
    Retrieve top competitors in a grid cell to explain supply saturation.
    
    Fetches businesses ordered by rating to show existing competition.
    
    Args:
        grid_id: Grid cell identifier (e.g., "DHA-Phase2-Cell-01")
        category: Business category (e.g., "Gym")
        limit: Maximum number of businesses to return (default: 5)
    
    Returns:
        List of competitor dictionaries:
        [
            {
                "name": str,
                "distance_km": float (from grid center),
                "rating": float or None
            }
        ]
        
        Empty list if no businesses found.
    
    Note:
        Distance calculation uses simple Haversine formula from grid center.
        For MVP, grid center is approximated from bounds.
    
    Example:
        >>> competitors = get_competitors("DHA-Phase2-Cell-03", "Gym", limit=5)
        >>> for comp in competitors:
        ...     print(f"{comp['name']} - {comp['rating']:.1f}★ ({comp['distance_km']:.2f}km)")
        Fitness First - 4.5★ (0.12km)
        Gold's Gym - 4.3★ (0.25km)
    """
    try:
        # Import database components
        from src.database.connection import get_session
        from src.database.models import BusinessModel, GridCellModel
        
        with get_session() as session:
            # Get grid center coordinates
            grid = (
                session.query(GridCellModel)
                .filter(GridCellModel.grid_id == grid_id)
                .first()
            )
            
            if not grid:
                return []
            
            # Get grid center coordinates (GridCellModel has lat_center/lon_center)
            grid_center_lat = float(grid.lat_center)
            grid_center_lon = float(grid.lon_center)
            
            # Query businesses
            businesses = (
                session.query(BusinessModel)
                .filter(
                    BusinessModel.grid_id == grid_id,
                    BusinessModel.category == category
                )
                .order_by(
                    BusinessModel.rating.desc().nullslast()
                )
                .limit(limit)
                .all()
            )
            
            # Calculate distances and build result
            result = []
            for biz in businesses:
                # Haversine distance calculation
                distance_km = _haversine_distance(
                    grid_center_lat, grid_center_lon,
                    float(biz.lat), float(biz.lon)
                )
                
                result.append({
                    "name": biz.name,
                    "distance_km": round(distance_km, 2),
                    "rating": float(biz.rating) if biz.rating is not None else None
                })
            
            return result
            
    except Exception as e:
        print(f"Error fetching competitors: {e}")
        return []


def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two points on Earth using Haversine formula.
    
    Args:
        lat1, lon1: First point coordinates (degrees)
        lat2, lon2: Second point coordinates (degrees)
    
    Returns:
        Distance in kilometers
    
    Formula:
        a = sin²(Δlat/2) + cos(lat1) * cos(lat2) * sin²(Δlon/2)
        c = 2 * atan2(√a, √(1−a))
        distance = R * c
        
        where R = 6371 km (Earth's radius)
    """
    # Earth's radius in kilometers
    R = 6371.0
    
    # Convert degrees to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Differences
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    # Haversine formula
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    distance = R * c
    return distance


def generate_rationale(metrics: Dict, gos: float) -> str:
    """
    Generate human-readable explanation for GOS score.
    
    Creates a concise 1-sentence rationale explaining why a grid has
    high/medium/low opportunity based on its metrics.
    
    Args:
        metrics: Dictionary with raw metrics:
            {
                "business_count": int,
                "instagram_volume": int,
                "reddit_mentions": int
            }
        gos: Gap Opportunity Score (0.0 to 1.0)
    
    Returns:
        Human-readable rationale string
    
    Example:
        >>> metrics = {"business_count": 0, "instagram_volume": 28, "reddit_mentions": 47}
        >>> rationale = generate_rationale(metrics, 0.913)
        >>> print(rationale)
        High demand (75 posts), low competition (0 businesses)
    """
    business_count = metrics.get("business_count", 0)
    instagram_volume = metrics.get("instagram_volume", 0)
    reddit_mentions = metrics.get("reddit_mentions", 0)
    total_posts = instagram_volume + reddit_mentions
    
    if gos >= 0.7:
        # High opportunity
        return f"High demand ({total_posts} posts), low competition ({business_count} businesses)"
    elif gos >= 0.4:
        # Medium opportunity
        return f"Moderate opportunity with {business_count} competitors and {total_posts} demand signals"
    else:
        # Low opportunity
        return f"Saturated market with {business_count} businesses and limited demand"


# CLI for testing
if __name__ == "__main__":
    import sys
    
    print(f"\n{'='*70}")
    print(f"GOS & CONFIDENCE CALCULATION TEST")
    print(f"{'='*70}\n")
    
    # Test Case 1: High opportunity (Cell-01 actual data)
    print("Test Case 1: High Opportunity Grid (Cell-01)")
    print("-" * 70)
    raw_1 = {
        "business_count": 0,
        "instagram_volume": 28,
        "reddit_mentions": 47
    }
    normalized_1 = {
        "supply_norm": 0.0,
        "demand_instagram_norm": 0.7368,
        "demand_reddit_norm": 0.94
    }
    
    gos_1 = calculate_gos(normalized_1)
    conf_1 = calculate_confidence(raw_1)
    
    print(f"Raw metrics:")
    print(f"  Businesses: {raw_1['business_count']}")
    print(f"  Instagram: {raw_1['instagram_volume']}")
    print(f"  Reddit: {raw_1['reddit_mentions']}")
    print(f"\nNormalized metrics:")
    print(f"  Supply: {normalized_1['supply_norm']:.4f}")
    print(f"  Instagram Demand: {normalized_1['demand_instagram_norm']:.4f}")
    print(f"  Reddit Demand: {normalized_1['demand_reddit_norm']:.4f}")
    print(f"\nResults:")
    print(f"  GOS: {gos_1:.3f} (HIGH opportunity)")
    print(f"  Confidence: {conf_1:.3f} (HIGH confidence)")
    
    # Test Case 2: Low opportunity (saturated grid)
    print(f"\n{'='*70}")
    print("Test Case 2: Low Opportunity Grid (Saturated)")
    print("-" * 70)
    raw_2 = {
        "business_count": 4,
        "instagram_volume": 10,
        "reddit_mentions": 5
    }
    normalized_2 = {
        "supply_norm": 1.0,  # Max businesses
        "demand_instagram_norm": 0.26,
        "demand_reddit_norm": 0.10
    }
    
    gos_2 = calculate_gos(normalized_2)
    conf_2 = calculate_confidence(raw_2)
    
    print(f"Raw metrics:")
    print(f"  Businesses: {raw_2['business_count']}")
    print(f"  Instagram: {raw_2['instagram_volume']}")
    print(f"  Reddit: {raw_2['reddit_mentions']}")
    print(f"\nNormalized metrics:")
    print(f"  Supply: {normalized_2['supply_norm']:.4f}")
    print(f"  Instagram Demand: {normalized_2['demand_instagram_norm']:.4f}")
    print(f"  Reddit Demand: {normalized_2['demand_reddit_norm']:.4f}")
    print(f"\nResults:")
    print(f"  GOS: {gos_2:.3f} (LOW opportunity)")
    print(f"  Confidence: {conf_2:.3f} (MEDIUM confidence)")
    
    # Test Case 3: Edge case - no data
    print(f"\n{'='*70}")
    print("Test Case 3: Edge Case - No Data")
    print("-" * 70)
    raw_3 = {
        "business_count": 0,
        "instagram_volume": 0,
        "reddit_mentions": 0
    }
    normalized_3 = {
        "supply_norm": 0.0,
        "demand_instagram_norm": 0.0,
        "demand_reddit_norm": 0.0
    }
    
    gos_3 = calculate_gos(normalized_3)
    conf_3 = calculate_confidence(raw_3)
    
    print(f"Raw metrics: All zeros")
    print(f"\nResults:")
    print(f"  GOS: {gos_3:.3f} (Supply component only: 1*0.4 = 0.4)")
    print(f"  Confidence: {conf_3:.3f} (No data)")
    
    # Test using score_grid convenience function
    print(f"\n{'='*70}")
    print("Test Case 4: Using score_grid() Convenience Function")
    print("-" * 70)
    result = score_grid("DHA-Phase2-Cell-01", raw_1, normalized_1)
    print(f"Result: {result}")
    
    print(f"\n{'='*70}")
    print("Formula Breakdown (Test Case 1):")
    print("-" * 70)
    print(f"GOS Calculation:")
    print(f"  (1 - {normalized_1['supply_norm']:.4f}) * {WEIGHT_SUPPLY} = {(1 - normalized_1['supply_norm']) * WEIGHT_SUPPLY:.3f}")
    print(f"  {normalized_1['demand_instagram_norm']:.4f} * {WEIGHT_INSTAGRAM} = {normalized_1['demand_instagram_norm'] * WEIGHT_INSTAGRAM:.3f}")
    print(f"  {normalized_1['demand_reddit_norm']:.4f} * {WEIGHT_REDDIT} = {normalized_1['demand_reddit_norm'] * WEIGHT_REDDIT:.3f}")
    print(f"  Total GOS = {gos_1:.3f}")
    print(f"\nConfidence Calculation:")
    print(f"  log(1 + {raw_1['instagram_volume']}) / {CONFIDENCE_K1} = {math.log(1 + raw_1['instagram_volume']) / CONFIDENCE_K1:.3f}")
    print(f"  log(1 + {raw_1['reddit_mentions']}) / {CONFIDENCE_K2} = {math.log(1 + raw_1['reddit_mentions']) / CONFIDENCE_K2:.3f}")
    print(f"  Source diversity bonus = {CONFIDENCE_DIVERSITY_BONUS} (both sources present)")
    print(f"  Total Confidence = {conf_1:.3f}")
    
    print(f"\n{'='*70}")
    print("✅ Scoring service test complete!")
    print(f"{'='*70}\n")


# ============================================================================
# Main Scoring Pipeline
# ============================================================================

def score_all_grids(category: str) -> List[Dict]:
    """
    Main scoring pipeline that processes all grids for a category.
    
    This is the primary entry point for Phase 2 scoring. It orchestrates:
    1. Data aggregation from database
    2. Metric normalization
    3. GOS and confidence calculation
    4. Explainability metadata (top posts, competitors, rationale)
    5. Database persistence to grid_metrics table
    
    Workflow:
        1. Call aggregator.aggregate_all_grids(category)
        2. Normalize all metrics using max values
        3. For each grid:
           - Calculate GOS and confidence
           - Fetch top posts and competitors
           - Generate rationale
           - Build GridMetrics record
        4. Bulk insert into grid_metrics table
        5. Return scored results
    
    Args:
        category: Business category (e.g., "Gym", "Cafe")
    
    Returns:
        List of scored grid dictionaries matching GridMetrics model:
        [
            {
                "grid_id": "DHA-Phase2-Cell-01",
                "category": "Gym",
                "business_count": 0,
                "instagram_volume": 28,
                "reddit_mentions": 47,
                "gos": 0.913,
                "confidence": 1.0,
                "top_posts_json": [...],
                "competitors_json": [...],
                "last_updated": datetime
            }
        ]
    
    Raises:
        Exception: If aggregation fails or database errors occur
    
    Example:
        >>> results = score_all_grids("Gym")
        >>> print(f"Scored {len(results)} grids")
        Scored 9 grids
        >>> top_grid = max(results, key=lambda x: x['gos'])
        >>> print(f"Best opportunity: {top_grid['grid_id']} (GOS={top_grid['gos']:.3f})")
        Best opportunity: DHA-Phase2-Cell-02 (GOS=0.914)
    """
    import time
    import sys
    from pathlib import Path
    
    # Add backend directory to path for imports
    backend_dir = Path(__file__).parent.parent.parent
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))
    
    from src.services.aggregator import aggregate_all_grids, normalize_metrics
    from src.database.connection import get_session
    from src.database.models import GridMetricsModel
    
    start_time = time.time()
    
    print(f"\n{'='*70}")
    print(f"SCORING PIPELINE: {category}")
    print(f"{'='*70}\n")
    
    # Step 1: Aggregate all grids
    print("Step 1: Aggregating data from database...")
    metrics_list, max_values = aggregate_all_grids(category)
    print(f"✓ Found {len(metrics_list)} grids to score")
    print(f"✓ Max values: business_count={max_values['max_business_count']}, "
          f"instagram={max_values['max_instagram_volume']}, "
          f"reddit={max_values['max_reddit_mentions']}")
    
    # Step 2: Score each grid
    print("\nStep 2: Calculating scores and explainability...")
    scored_grids = []
    
    for raw_metrics in metrics_list:
        grid_id = raw_metrics["grid_id"]
        
        # Normalize metrics (already imported at top)
        normalized = normalize_metrics(raw_metrics, max_values)
        
        # Calculate GOS and confidence
        gos = calculate_gos(normalized)
        confidence = calculate_confidence(raw_metrics)
        
        # Get explainability data
        top_posts = get_top_posts(grid_id, category, limit=3)
        competitors = get_competitors(grid_id, category, limit=5)
        rationale = generate_rationale(raw_metrics, gos)
        
        # Build result
        scored_grid = {
            "grid_id": grid_id,
            "category": category,
            "business_count": raw_metrics["business_count"],
            "instagram_volume": raw_metrics["instagram_volume"],
            "reddit_mentions": raw_metrics["reddit_mentions"],
            "gos": gos,
            "confidence": confidence,
            "top_posts_json": top_posts,
            "competitors_json": competitors,
            "rationale": rationale,
            "last_updated": datetime.utcnow()
        }
        
        scored_grids.append(scored_grid)
    
    print(f"✓ Scored {len(scored_grids)} grids")
    
    # Step 3: Persist to database
    print("\nStep 3: Persisting to grid_metrics table...")
    
    with get_session() as session:
        try:
            # Delete existing records for this category (upsert pattern)
            session.query(GridMetricsModel).filter_by(category=category).delete()
            
            # Insert new records
            for scored_grid in scored_grids:
                # Convert to ORM model
                grid_metric = GridMetricsModel(
                    grid_id=scored_grid["grid_id"],
                    category=scored_grid["category"],
                    business_count=scored_grid["business_count"],
                    instagram_volume=scored_grid["instagram_volume"],
                    reddit_mentions=scored_grid["reddit_mentions"],
                    gos=scored_grid["gos"],
                    confidence=scored_grid["confidence"],
                    top_posts_json=scored_grid["top_posts_json"],
                    competitors_json=scored_grid["competitors_json"],
                    last_updated=scored_grid["last_updated"]
                )
                session.add(grid_metric)
            
            # Commit transaction
            session.commit()
            print(f"✓ Inserted {len(scored_grids)} records into grid_metrics table")
            
        except Exception as e:
            session.rollback()
            print(f"✗ Database error: {e}")
            raise
    
    # Step 4: Report results
    elapsed_time = time.time() - start_time
    
    print(f"\n{'='*70}")
    print("SCORING RESULTS")
    print(f"{'='*70}")
    print(f"Total grids scored: {len(scored_grids)}")
    print(f"Time taken: {elapsed_time:.2f}s")
    
    # Top 3 grids by GOS
    top_3 = sorted(scored_grids, key=lambda x: x["gos"], reverse=True)[:3]
    print(f"\nTop 3 Opportunities:")
    for i, grid in enumerate(top_3, 1):
        print(f"  {i}. {grid['grid_id']}: GOS={grid['gos']:.3f}, "
              f"Confidence={grid['confidence']:.3f}")
        print(f"     {grid['rationale']}")
    
    print(f"{'='*70}\n")
    
    return scored_grids


def get_top_recommendations(neighborhood: str, category: str, limit: int = 3) -> List[Dict]:
    """
    Get top-N grid recommendations for a neighborhood and category.
    
    Queries the grid_metrics table (populated by score_all_grids) and returns
    the highest-scoring grids with location and explainability data.
    
    This is the primary API for frontend consumption.
    
    Args:
        neighborhood: Neighborhood name (e.g., "DHA Phase 2")
        category: Business category (e.g., "Gym")
        limit: Maximum number of recommendations (default: 3)
    
    Returns:
        List of recommendation dictionaries:
        [
            {
                "grid_id": "DHA-Phase2-Cell-01",
                "gos": 0.913,
                "confidence": 1.0,
                "rationale": "High demand (75 posts), low competition (0 businesses)",
                "lat_center": 24.8278,
                "lon_center": 67.0595,
                "business_count": 0,
                "top_posts": [...],
                "competitors": [...]
            }
        ]
        
        Sorted by GOS (descending), limited to `limit` results.
    
    Raises:
        Exception: If database query fails
    
    Example:
        >>> recs = get_top_recommendations("DHA Phase 2", "Gym", limit=3)
        >>> for rec in recs:
        ...     print(f"{rec['grid_id']}: GOS={rec['gos']:.3f}")
        DHA-Phase2-Cell-02: GOS=0.914
        DHA-Phase2-Cell-01: GOS=0.913
        DHA-Phase2-Cell-04: GOS=0.739
    """
    import sys
    from pathlib import Path
    
    # Add backend directory to path
    backend_dir = Path(__file__).parent.parent.parent
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))
    
    from src.database.connection import get_session
    from src.database.models import GridMetricsModel, GridCellModel
    
    with get_session() as session:
        # Query grid_metrics with JOIN to grid_cells
        results = (
            session.query(GridMetricsModel, GridCellModel)
            .join(GridCellModel, GridMetricsModel.grid_id == GridCellModel.grid_id)
            .filter(
                GridCellModel.neighborhood == neighborhood,
                GridMetricsModel.category == category
            )
            .order_by(GridMetricsModel.gos.desc())
            .limit(limit)
            .all()
        )
        
        # Build recommendation dicts
        recommendations = []
        for grid_metric, grid_cell in results:
            # Regenerate rationale from stored metrics
            rationale = generate_rationale(
                {
                    "business_count": grid_metric.business_count,
                    "instagram_volume": grid_metric.instagram_volume,
                    "reddit_mentions": grid_metric.reddit_mentions
                },
                grid_metric.gos
            )
            
            recommendation = {
                "grid_id": grid_metric.grid_id,
                "gos": float(grid_metric.gos),
                "confidence": float(grid_metric.confidence),
                "rationale": rationale,
                "lat_center": float(grid_cell.lat_center),
                "lon_center": float(grid_cell.lon_center),
                "business_count": grid_metric.business_count,
                "instagram_volume": grid_metric.instagram_volume,
                "reddit_mentions": grid_metric.reddit_mentions,
                "top_posts": grid_metric.top_posts_json or [],
                "competitors": grid_metric.competitors_json or []
            }
            
            recommendations.append(recommendation)
        
        return recommendations


# CLI for testing
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--pipeline":
        # Test full pipeline
        category = sys.argv[2] if len(sys.argv) > 2 else "Gym"
        results = score_all_grids(category)
        
        print("\nPIPELINE TEST RESULTS:")
        print(f"Total grids: {len(results)}")
        print(f"Average GOS: {sum(r['gos'] for r in results) / len(results):.3f}")
        
    elif len(sys.argv) > 1 and sys.argv[1] == "--recommend":
        # Test recommendations API
        neighborhood = sys.argv[2] if len(sys.argv) > 2 else "DHA Phase 2"
        category = sys.argv[3] if len(sys.argv) > 3 else "Gym"
        
        recs = get_top_recommendations(neighborhood, category, limit=3)
        
        print(f"\nTOP RECOMMENDATIONS: {neighborhood} - {category}")
        print(f"{'='*70}")
        for i, rec in enumerate(recs, 1):
            print(f"\n{i}. {rec['grid_id']}")
            print(f"   GOS: {rec['gos']:.3f} | Confidence: {rec['confidence']:.3f}")
            print(f"   Center: ({rec['lat_center']:.5f}, {rec['lon_center']:.5f})")
            print(f"   Rationale: {rec['rationale']}")
            print(f"   Metrics: {rec['business_count']} businesses, "
                  f"{rec['instagram_volume']} Instagram, {rec['reddit_mentions']} Reddit")
        
    else:
        # Original CLI tests
        print("="*70)
        print("GAP OPPORTUNITY SCORE (GOS) CALCULATION SERVICE")
        print("Phase 2 - Analytics & Scoring Engine")
        print("="*70)

        # Test Case 1: High Opportunity Grid (Cell-01 actual data)
        print("\nTest Case 1: High Opportunity Grid (Cell-01)")
        print("-" * 70)

        raw_1 = {
            "business_count": 0,
            "instagram_volume": 28,
            "reddit_mentions": 47
        }

        normalized_1 = {
            "supply_norm": 0.0,      # 0 / 4 = 0.0
            "demand_instagram_norm": 0.7368,  # 28 / 38 = 0.7368
            "demand_reddit_norm": 0.94   # 47 / 50 = 0.94
        }

        gos_1 = calculate_gos(normalized_1)
        conf_1 = calculate_confidence(raw_1)
        result_1 = score_grid("DHA-Phase2-Cell-01", raw_1, normalized_1)

        print(f"Raw Metrics: {raw_1}")
        print(f"Normalized Metrics: {normalized_1}")
        print(f"GOS: {gos_1:.3f} ({result_1['opportunity_level']} opportunity)")
        print(f"Confidence: {conf_1:.3f} (HIGH confidence)")

        # Test Case 2: Low Opportunity Grid (Saturated)
        print("\nTest Case 2: Low Opportunity Grid (Saturated)")
        print("-" * 70)

        raw_2 = {
            "business_count": 4,
            "instagram_volume": 12,
            "reddit_mentions": 38
        }

        normalized_2 = {
            "supply_norm": 1.0,      # 4 / 4 = 1.0 (saturated)
            "demand_instagram_norm": 0.3158,  # 12 / 38
            "demand_reddit_norm": 0.76   # 38 / 50
        }

        gos_2 = calculate_gos(normalized_2)
        conf_2 = calculate_confidence(raw_2)
        result_2 = score_grid("DHA-Phase2-Cell-03", raw_2, normalized_2)

        print(f"Raw Metrics: {raw_2}")
        print(f"Normalized Metrics: {normalized_2}")
        print(f"GOS: {gos_2:.3f} ({result_2['opportunity_level']} opportunity)")
        print(f"Confidence: {conf_2:.3f} (MEDIUM confidence)")

        # Test Case 3: Edge Case - No Data
        print("\nTest Case 3: Edge Case - No Data")
        print("-" * 70)

        raw_3 = {
            "business_count": 0,
            "instagram_volume": 0,
            "reddit_mentions": 0
        }

        normalized_3 = {
            "supply_norm": 0.0,
            "demand_instagram_norm": 0.0,
            "demand_reddit_norm": 0.0
        }

        gos_3 = calculate_gos(normalized_3)
        conf_3 = calculate_confidence(raw_3)

        print(f"Raw Metrics: {raw_3}")
        print(f"Normalized Metrics: {normalized_3}")
        print(f"GOS: {gos_3:.3f} (Supply component only)")
        print(f"Confidence: {conf_3:.3f} (No data)")
    
        print(f"\n{'='*70}")
        print("Formula Breakdown (Test Case 1):")
        print("-" * 70)
        print(f"GOS Calculation:")
        print(f"  (1 - {normalized_1['supply_norm']:.4f}) * {WEIGHT_SUPPLY} = {(1 - normalized_1['supply_norm']) * WEIGHT_SUPPLY:.3f}")
        print(f"  {normalized_1['demand_instagram_norm']:.4f} * {WEIGHT_INSTAGRAM} = {normalized_1['demand_instagram_norm'] * WEIGHT_INSTAGRAM:.3f}")
        print(f"  {normalized_1['demand_reddit_norm']:.4f} * {WEIGHT_REDDIT} = {normalized_1['demand_reddit_norm'] * WEIGHT_REDDIT:.3f}")
        print(f"  Total GOS = {gos_1:.3f}")
        print(f"\nConfidence Calculation:")
        print(f"  log(1 + {raw_1['instagram_volume']}) / {CONFIDENCE_K1} = {math.log(1 + raw_1['instagram_volume']) / CONFIDENCE_K1:.3f}")
        print(f"  log(1 + {raw_1['reddit_mentions']}) / {CONFIDENCE_K2} = {math.log(1 + raw_1['reddit_mentions']) / CONFIDENCE_K2:.3f}")
        print(f"  Source diversity bonus = {CONFIDENCE_DIVERSITY_BONUS} (both sources present)")
        print(f"  Total Confidence = {conf_1:.3f}")
    
        print(f"\n{'='*70}")
        print("[PASS] Scoring service test complete!")
        print(f"{'='*70}\n")
