"""
Real Data Scorer

Phase 1 scoring service that uses only real Google Places data.
No synthetic Instagram/Reddit signals.

Features:
- Opportunity score based on business density (inverse)
- Competition strength from ratings and reviews
- Category-specific adjustments
- Simple, transparent scoring formula
- Easy to validate with real data

Usage:
    from src.services.real_data_scorer import RealDataScorer
    
    scorer = RealDataScorer()
    score = scorer.calculate_opportunity_score(
        business_count=5,
        avg_rating=4.2,
        total_reviews=150,
        max_business_count=20,
        category="Gym"
    )
"""

import math
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

from src.utils.logger import get_logger


# ============================================================================
# Constants
# ============================================================================

# Scoring weights for Phase 1
WEIGHTS = {
    "density_inverse": 0.6,      # Higher weight = fewer competitors better
    "competition_weakness": 0.4,  # Lower competition strength = better opportunity
}

# Category-specific adjustments
CATEGORY_CONFIG = {
    "Gym": {
        "ideal_rating_threshold": 4.0,    # Below this rating = weaker competitor
        "ideal_review_threshold": 100,     # Below this = less established
        "saturation_threshold": 10,        # Above this count = saturated market
        "weight_boost": 1.0                # No boost for Gym
    },
    "Cafe": {
        "ideal_rating_threshold": 4.2,
        "ideal_review_threshold": 50,
        "saturation_threshold": 15,
        "weight_boost": 1.0
    }
}

# Score boundaries
MIN_SCORE = 0.0
MAX_SCORE = 1.0


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class GridScoreResult:
    """
    Result of scoring a grid cell.
    
    Attributes:
        grid_id: Grid cell identifier
        category: Business category scored
        opportunity_score: Final GOS (0-1)
        density_score: Score component from business density
        competition_score: Score component from competition strength
        business_count: Number of competitors in grid
        avg_rating: Average competitor rating
        total_reviews: Total competitor reviews
        scoring_mode: "real_data" for Phase 1
        calculated_at: Timestamp
    """
    grid_id: str
    category: str
    opportunity_score: float
    density_score: float
    competition_score: float
    business_count: int
    avg_rating: Optional[float]
    total_reviews: int
    scoring_mode: str = "real_data"
    calculated_at: str = ""
    
    def __post_init__(self):
        if not self.calculated_at:
            self.calculated_at = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict:
        return asdict(self)


# ============================================================================
# Real Data Scorer
# ============================================================================

class RealDataScorer:
    """
    Phase 1 scoring service using only real Google Places data.
    
    Calculates opportunity scores based on:
    1. Business density (inverse - fewer competitors = higher score)
    2. Competition strength (weaker competition = higher score)
    
    The formula is transparent and can be validated against real data.
    
    Attributes:
        weights: Scoring weights dictionary
        category_config: Category-specific configuration
        logger: Logger instance
    """
    
    def __init__(
        self,
        weights: Dict[str, float] = None,
        category_config: Dict = None
    ):
        """
        Initialize the real data scorer.
        
        Args:
            weights: Custom scoring weights (optional)
            category_config: Custom category configuration (optional)
        """
        self.weights = weights or WEIGHTS.copy()
        self.category_config = category_config or CATEGORY_CONFIG.copy()
        self.logger = get_logger(__name__)
        
        self.logger.info(
            "RealDataScorer initialized",
            extra={"extra_fields": {
                "mode": "Phase 1 - Real Data Only",
                "weights": self.weights
            }}
        )
    
    def calculate_opportunity_score(
        self,
        business_count: int,
        avg_rating: Optional[float],
        total_reviews: int,
        max_business_count: int,
        category: str = "Gym"
    ) -> float:
        """
        Calculate opportunity score for a grid cell.
        
        Phase 1 formula (real data only):
        
        GOS = (density_inverse * 0.6) + (competition_weakness * 0.4)
        
        Where:
        - density_inverse = 1 - (business_count / max_business_count)
        - competition_weakness = 1 - competition_strength_normalized
        - competition_strength = f(avg_rating, total_reviews)
        
        Args:
            business_count: Number of competitors in grid
            avg_rating: Average rating of competitors (1-5)
            total_reviews: Total review count of all competitors
            max_business_count: Maximum count across all grids (for normalization)
            category: Business category
            
        Returns:
            Opportunity score between 0 and 1
        """
        # Get category config
        config = self.category_config.get(category, CATEGORY_CONFIG["Gym"])
        
        # Handle edge case: no competitors = high opportunity
        if business_count == 0:
            return MAX_SCORE
        
        # Handle edge case: max is 0 (shouldn't happen)
        if max_business_count == 0:
            max_business_count = 1
        
        # 1. Calculate density inverse score
        # Higher when fewer competitors
        density_ratio = business_count / max_business_count
        density_inverse = 1.0 - density_ratio
        
        # 2. Calculate competition strength
        # Strong competition = high ratings + many reviews
        competition_strength = self._calculate_competition_strength(
            avg_rating=avg_rating,
            total_reviews=total_reviews,
            config=config
        )
        
        # 3. Invert competition strength (weaker competition = better opportunity)
        competition_weakness = 1.0 - competition_strength
        
        # 4. Combine with weights
        score = (
            density_inverse * self.weights["density_inverse"] +
            competition_weakness * self.weights["competition_weakness"]
        )
        
        # 5. Apply category boost if any
        score *= config.get("weight_boost", 1.0)
        
        # 6. Clamp to valid range
        score = max(MIN_SCORE, min(MAX_SCORE, score))
        
        return round(score, 4)
    
    def _calculate_competition_strength(
        self,
        avg_rating: Optional[float],
        total_reviews: int,
        config: Dict
    ) -> float:
        """
        Calculate competition strength from ratings and reviews.
        
        Strong competition indicators:
        - High average rating (close to 5.0)
        - Many reviews (established businesses)
        
        Weak competition indicators:
        - Low average rating (below threshold)
        - Few reviews (new or unpopular businesses)
        
        Args:
            avg_rating: Average competitor rating
            total_reviews: Total reviews across competitors
            config: Category configuration
            
        Returns:
            Competition strength between 0 and 1
        """
        # Handle missing rating
        if avg_rating is None:
            avg_rating = 3.0  # Assume average if unknown
        
        # Normalize rating (0-1 scale)
        # 5.0 rating = 1.0 strength, 1.0 rating = 0.0 strength
        rating_strength = (avg_rating - 1.0) / 4.0
        rating_strength = max(0.0, min(1.0, rating_strength))
        
        # Normalize reviews using logarithmic scale
        # This prevents very high review counts from dominating
        # 0 reviews = 0.0, 100 reviews = ~0.5, 1000 reviews = ~0.75
        review_threshold = config.get("ideal_review_threshold", 100)
        if total_reviews > 0:
            # Log scale with threshold
            review_strength = math.log10(1 + total_reviews) / math.log10(1 + review_threshold * 10)
            review_strength = min(1.0, review_strength)
        else:
            review_strength = 0.0
        
        # Combine rating and review strength
        # Weight rating slightly more than reviews
        strength = (rating_strength * 0.6) + (review_strength * 0.4)
        
        return round(strength, 4)
    
    def score_grid(
        self,
        grid_id: str,
        businesses: List[Dict],
        category: str,
        max_business_count: int
    ) -> GridScoreResult:
        """
        Score a grid cell based on its businesses.
        
        Args:
            grid_id: Grid cell identifier
            businesses: List of business dictionaries with rating and total_ratings
            category: Business category
            max_business_count: Maximum count for normalization
            
        Returns:
            GridScoreResult with detailed scoring breakdown
        """
        # Calculate aggregate metrics
        business_count = len(businesses)
        
        if business_count > 0:
            ratings = [b.get("rating") for b in businesses if b.get("rating") is not None]
            avg_rating = sum(ratings) / len(ratings) if ratings else None
            total_reviews = sum(b.get("total_ratings", 0) for b in businesses)
        else:
            avg_rating = None
            total_reviews = 0
        
        # Calculate score
        opportunity_score = self.calculate_opportunity_score(
            business_count=business_count,
            avg_rating=avg_rating,
            total_reviews=total_reviews,
            max_business_count=max_business_count,
            category=category
        )
        
        # Calculate component scores for transparency
        config = self.category_config.get(category, CATEGORY_CONFIG["Gym"])
        
        density_score = 1.0 - (business_count / max_business_count) if max_business_count > 0 else 1.0
        competition_strength = self._calculate_competition_strength(avg_rating, total_reviews, config)
        competition_score = 1.0 - competition_strength
        
        return GridScoreResult(
            grid_id=grid_id,
            category=category,
            opportunity_score=opportunity_score,
            density_score=round(density_score, 4),
            competition_score=round(competition_score, 4),
            business_count=business_count,
            avg_rating=round(avg_rating, 2) if avg_rating else None,
            total_reviews=total_reviews,
            scoring_mode="real_data"
        )
    
    def score_all_grids(
        self,
        grid_businesses: Dict[str, List[Dict]],
        category: str
    ) -> List[GridScoreResult]:
        """
        Score all grids and return sorted results.
        
        Args:
            grid_businesses: Dictionary mapping grid_id to list of businesses
            category: Business category
            
        Returns:
            List of GridScoreResult sorted by opportunity_score (descending)
        """
        if not grid_businesses:
            return []
        
        # Find max business count for normalization
        max_count = max(len(businesses) for businesses in grid_businesses.values())
        
        if max_count == 0:
            max_count = 1  # Avoid division by zero
        
        results = []
        for grid_id, businesses in grid_businesses.items():
            result = self.score_grid(
                grid_id=grid_id,
                businesses=businesses,
                category=category,
                max_business_count=max_count
            )
            results.append(result)
        
        # Sort by opportunity score (highest first)
        results.sort(key=lambda r: r.opportunity_score, reverse=True)
        
        self.logger.info(
            f"Scored {len(results)} grids for {category}",
            extra={"extra_fields": {
                "max_business_count": max_count,
                "best_grid": results[0].grid_id if results else None,
                "best_score": results[0].opportunity_score if results else None
            }}
        )
        
        return results
    
    def explain_score(self, result: GridScoreResult) -> str:
        """
        Generate human-readable explanation of a score.
        
        Args:
            result: GridScoreResult to explain
            
        Returns:
            Explanation string
        """
        explanation = []
        
        # Overall score interpretation
        if result.opportunity_score >= 0.8:
            explanation.append(f"🟢 EXCELLENT opportunity (score: {result.opportunity_score:.2f})")
        elif result.opportunity_score >= 0.6:
            explanation.append(f"🟡 GOOD opportunity (score: {result.opportunity_score:.2f})")
        elif result.opportunity_score >= 0.4:
            explanation.append(f"🟠 MODERATE opportunity (score: {result.opportunity_score:.2f})")
        else:
            explanation.append(f"🔴 LOW opportunity (score: {result.opportunity_score:.2f})")
        
        # Density analysis
        if result.business_count == 0:
            explanation.append("• No competitors found - untapped market!")
        elif result.density_score >= 0.7:
            explanation.append(f"• Low competitor density ({result.business_count} businesses)")
        elif result.density_score >= 0.4:
            explanation.append(f"• Moderate competitor density ({result.business_count} businesses)")
        else:
            explanation.append(f"• High competitor density ({result.business_count} businesses)")
        
        # Competition strength
        if result.avg_rating:
            if result.competition_score >= 0.6:
                explanation.append(f"• Weak competition (avg rating: {result.avg_rating:.1f}★)")
            elif result.competition_score >= 0.4:
                explanation.append(f"• Moderate competition (avg rating: {result.avg_rating:.1f}★)")
            else:
                explanation.append(f"• Strong competition (avg rating: {result.avg_rating:.1f}★)")
        
        # Review volume
        if result.total_reviews < 50:
            explanation.append(f"• Low review volume ({result.total_reviews} total)")
        elif result.total_reviews < 200:
            explanation.append(f"• Moderate review volume ({result.total_reviews} total)")
        else:
            explanation.append(f"• High review volume ({result.total_reviews} total)")
        
        return "\n".join(explanation)


# ============================================================================
# Module-level convenience functions
# ============================================================================

def calculate_gos(
    business_count: int,
    avg_rating: Optional[float],
    total_reviews: int,
    max_count: int,
    category: str = "Gym"
) -> float:
    """
    Quick function to calculate Grid Opportunity Score.
    
    Args:
        business_count: Competitors in grid
        avg_rating: Average competitor rating
        total_reviews: Total competitor reviews
        max_count: Max competitors across all grids
        category: Business category
        
    Returns:
        Opportunity score (0-1)
    """
    scorer = RealDataScorer()
    return scorer.calculate_opportunity_score(
        business_count, avg_rating, total_reviews, max_count, category
    )


# ============================================================================
# Testing
# ============================================================================

if __name__ == "__main__":
    scorer = RealDataScorer()
    
    print("=== Real Data Scorer Test ===\n")
    
    # Test scenarios
    test_cases = [
        {"business_count": 0, "avg_rating": None, "total_reviews": 0, "description": "Empty grid"},
        {"business_count": 2, "avg_rating": 3.5, "total_reviews": 50, "description": "Few weak competitors"},
        {"business_count": 5, "avg_rating": 4.0, "total_reviews": 200, "description": "Moderate competition"},
        {"business_count": 10, "avg_rating": 4.5, "total_reviews": 1000, "description": "Strong competition"},
        {"business_count": 15, "avg_rating": 4.8, "total_reviews": 2000, "description": "Saturated market"},
    ]
    
    max_count = 15
    
    for case in test_cases:
        score = scorer.calculate_opportunity_score(
            business_count=case["business_count"],
            avg_rating=case["avg_rating"],
            total_reviews=case["total_reviews"],
            max_business_count=max_count,
            category="Gym"
        )
        print(f"{case['description']}: GOS = {score:.3f}")
    
    print("\n=== Grid Scoring Test ===\n")
    
    # Test grid scoring with explanation
    test_businesses = [
        {"rating": 4.2, "total_ratings": 50},
        {"rating": 3.8, "total_ratings": 30},
        {"rating": 4.0, "total_ratings": 20},
    ]
    
    result = scorer.score_grid(
        grid_id="Clifton-Block2-005-008",
        businesses=test_businesses,
        category="Gym",
        max_business_count=max_count
    )
    
    print(f"Grid: {result.grid_id}")
    print(f"Score: {result.opportunity_score:.3f}")
    print(f"\n{scorer.explain_score(result)}")
