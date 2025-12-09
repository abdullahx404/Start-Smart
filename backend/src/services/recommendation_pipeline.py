"""
Recommendation Pipeline Module

Orchestrates the full recommendation flow:
BEV → Rule Engine → LLM Evaluator → Score Combiner → Final Recommendation

This is the main entry point for generating location recommendations.

Usage:
    from src.services.recommendation_pipeline import RecommendationPipeline
    
    pipeline = RecommendationPipeline()
    result = pipeline.recommend(
        lat=24.8160,
        lon=67.0280,
        grid_id="Clifton-Block2-007-008"
    )
    print(result.to_api_response())
"""

import os
import json
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from src.services.bev_generator import BEVGenerator, BusinessEnvironmentVector
from src.services.rule_engine import RuleEngine, RuleEvaluationResult
from src.services.llm_evaluator import LLMEvaluator, LLMEvaluationResult
from src.services.score_combiner import ScoreCombiner, CombinedRecommendation
from src.utils.logger import get_logger


# ============================================================================
# Constants
# ============================================================================

# Default search radius for BEV generation
DEFAULT_RADIUS_METERS = 500

# Pipeline modes
class PipelineMode:
    FULL = "full"           # BEV + Rule + LLM
    FAST = "fast"           # BEV + Rule only (no LLM)
    LLM_ONLY = "llm_only"   # BEV + LLM only (no rules)


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class PipelineResult:
    """Complete result from the recommendation pipeline."""
    grid_id: str
    lat: float
    lon: float
    radius_meters: int
    
    # Full results
    bev: BusinessEnvironmentVector
    rule_result: RuleEvaluationResult
    llm_result: Optional[LLMEvaluationResult]
    combined: CombinedRecommendation
    
    # Timing
    total_time_ms: float
    bev_time_ms: float
    rule_time_ms: float
    llm_time_ms: float
    combine_time_ms: float
    
    # Meta
    mode: str
    generated_at: str = ""
    
    def __post_init__(self):
        if not self.generated_at:
            self.generated_at = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Full dictionary representation."""
        return {
            "grid_id": self.grid_id,
            "location": {
                "lat": self.lat,
                "lon": self.lon,
                "radius_meters": self.radius_meters
            },
            "bev": self.bev.to_dict(),
            "rule_engine": self.rule_result.to_dict(),
            "llm_evaluation": self.llm_result.to_dict() if self.llm_result else None,
            "combined": self.combined.to_dict(),
            "timing": {
                "total_ms": round(self.total_time_ms, 2),
                "bev_ms": round(self.bev_time_ms, 2),
                "rule_ms": round(self.rule_time_ms, 2),
                "llm_ms": round(self.llm_time_ms, 2),
                "combine_ms": round(self.combine_time_ms, 2)
            },
            "mode": self.mode,
            "generated_at": self.generated_at
        }
    
    def to_api_response(self) -> Dict[str, Any]:
        """Simplified API response."""
        return self.combined.to_api_response()


# ============================================================================
# Recommendation Pipeline Class
# ============================================================================

class RecommendationPipeline:
    """
    Full recommendation pipeline orchestrating all components.
    
    Flow:
    1. Generate BEV from location
    2. Apply rule engine
    3. Evaluate with LLM (optional)
    4. Combine scores
    5. Return recommendation
    """
    
    def __init__(
        self,
        google_api_key: str = None,
        groq_api_key: str = None,
        rule_weight: float = 0.65,
        llm_weight: float = 0.35,
        default_radius: int = DEFAULT_RADIUS_METERS
    ):
        """
        Initialize the recommendation pipeline.
        
        Args:
            google_api_key: Google Maps API key
            groq_api_key: Groq API key for LLM
            rule_weight: Weight for rule engine (0-1)
            llm_weight: Weight for LLM (0-1)
            default_radius: Default search radius in meters
        """
        self.google_api_key = google_api_key or os.getenv("GOOGLE_PLACES_API_KEY")
        self.groq_api_key = groq_api_key or os.getenv("GROQ_API_KEY")
        self.default_radius = default_radius
        
        self.logger = get_logger(__name__)
        
        # Initialize components
        self.bev_generator = BEVGenerator(self.google_api_key)
        self.rule_engine = RuleEngine()
        self.llm_evaluator = None  # Lazy initialization
        self.score_combiner = ScoreCombiner(rule_weight, llm_weight)
        
        self.logger.info("RecommendationPipeline initialized")
    
    def recommend(
        self,
        lat: float,
        lon: float,
        grid_id: str = None,
        radius_meters: int = None,
        mode: str = PipelineMode.FULL,
        use_cached_bev: BusinessEnvironmentVector = None
    ) -> PipelineResult:
        """
        Generate recommendation for a location.
        
        Args:
            lat: Latitude
            lon: Longitude
            grid_id: Grid cell identifier (optional)
            radius_meters: Search radius (optional)
            mode: Pipeline mode (full, fast, llm_only)
            use_cached_bev: Pre-computed BEV (optional)
            
        Returns:
            PipelineResult with full recommendation
        """
        start_time = time.time()
        radius = radius_meters or self.default_radius
        grid_id = grid_id or f"custom-{lat:.4f}-{lon:.4f}"
        
        self.logger.info(
            f"Starting recommendation pipeline",
            extra={"extra_fields": {
                "lat": lat, "lon": lon, "grid_id": grid_id, "mode": mode
            }}
        )
        
        # ===== Step 1: Generate BEV =====
        bev_start = time.time()
        if use_cached_bev:
            bev = use_cached_bev
            self.logger.debug("Using cached BEV")
        else:
            bev = self.bev_generator.generate_bev(
                center_lat=lat,
                center_lon=lon,
                radius_meters=radius,
                grid_id=grid_id
            )
        bev_time = (time.time() - bev_start) * 1000
        
        # ===== Step 2: Apply Rule Engine =====
        rule_start = time.time()
        if mode != PipelineMode.LLM_ONLY:
            rule_result = self.rule_engine.evaluate(bev)
        else:
            # Skip rule engine
            rule_result = RuleEvaluationResult(
                gym_score=0.5,
                cafe_score=0.5,
                gym_rules_applied={},
                cafe_rules_applied={},
                evaluated_at=datetime.utcnow().isoformat()
            )
        rule_time = (time.time() - rule_start) * 1000
        
        # ===== Step 3: LLM Evaluation =====
        llm_start = time.time()
        llm_result = None
        if mode != PipelineMode.FAST:
            try:
                if self.llm_evaluator is None:
                    self.llm_evaluator = LLMEvaluator(self.groq_api_key)
                llm_result = self.llm_evaluator.evaluate(bev)
            except Exception as e:
                self.logger.warning(f"LLM evaluation failed: {e}")
                # Create fallback result
                llm_result = LLMEvaluationResult(
                    gym_probability=0.5,
                    cafe_probability=0.5,
                    gym_reasoning="LLM unavailable",
                    cafe_reasoning="LLM unavailable",
                    key_factors=["fallback"],
                    risks=["LLM error"],
                    recommendation="Using rule-based scoring only",
                    model_used="fallback",
                    tokens_used=0
                )
        else:
            # Fast mode - no LLM, use rule scores as LLM probabilities
            llm_result = LLMEvaluationResult(
                gym_probability=rule_result.gym_score,
                cafe_probability=rule_result.cafe_score,
                gym_reasoning="Fast mode - using rule scores",
                cafe_reasoning="Fast mode - using rule scores",
                key_factors=["fast_mode"],
                risks=[],
                recommendation="Based on rule engine only",
                model_used="none",
                tokens_used=0
            )
        llm_time = (time.time() - llm_start) * 1000
        
        # ===== Step 4: Combine Scores =====
        combine_start = time.time()
        combined = self.score_combiner.combine(
            grid_id=grid_id,
            rule_result=rule_result,
            llm_result=llm_result,
            bev=bev
        )
        combine_time = (time.time() - combine_start) * 1000
        
        total_time = (time.time() - start_time) * 1000
        
        # Build result
        result = PipelineResult(
            grid_id=grid_id,
            lat=lat,
            lon=lon,
            radius_meters=radius,
            bev=bev,
            rule_result=rule_result,
            llm_result=llm_result,
            combined=combined,
            total_time_ms=total_time,
            bev_time_ms=bev_time,
            rule_time_ms=rule_time,
            llm_time_ms=llm_time,
            combine_time_ms=combine_time,
            mode=mode
        )
        
        self.logger.info(
            "Pipeline complete",
            extra={"extra_fields": {
                "grid_id": grid_id,
                "best_category": combined.best_category,
                "best_score": combined.best_score,
                "total_ms": total_time
            }}
        )
        
        return result
    
    def recommend_batch(
        self,
        locations: List[Dict[str, Any]],
        mode: str = PipelineMode.FAST  # Default to fast for batch
    ) -> List[PipelineResult]:
        """
        Generate recommendations for multiple locations.
        
        Args:
            locations: List of dicts with lat, lon, grid_id
            mode: Pipeline mode
            
        Returns:
            List of PipelineResult
        """
        results = []
        total = len(locations)
        
        self.logger.info(f"Starting batch recommendation for {total} locations")
        
        for i, loc in enumerate(locations):
            try:
                result = self.recommend(
                    lat=loc["lat"],
                    lon=loc["lon"],
                    grid_id=loc.get("grid_id"),
                    radius_meters=loc.get("radius_meters"),
                    mode=mode
                )
                results.append(result)
                
                if (i + 1) % 10 == 0:
                    self.logger.info(f"Processed {i + 1}/{total} locations")
                    
            except Exception as e:
                self.logger.error(f"Error processing location {i}: {e}")
        
        return results
    
    def recommend_from_grid_file(
        self,
        grid_file: str,
        limit: int = None,
        mode: str = PipelineMode.FAST
    ) -> List[PipelineResult]:
        """
        Generate recommendations from a micro-grid JSON file.
        
        Args:
            grid_file: Path to micro-grid JSON file
            limit: Max number of grids to process
            mode: Pipeline mode
            
        Returns:
            List of PipelineResult
        """
        with open(grid_file, 'r') as f:
            grids = json.load(f)
        
        if limit:
            grids = grids[:limit]
        
        locations = [
            {
                "lat": g["center_lat"],
                "lon": g["center_lon"],
                "grid_id": g["grid_id"]
            }
            for g in grids
        ]
        
        return self.recommend_batch(locations, mode)


# ============================================================================
# Convenience Functions
# ============================================================================

def get_recommendation(
    lat: float,
    lon: float,
    grid_id: str = None,
    mode: str = PipelineMode.FULL
) -> Dict[str, Any]:
    """
    Convenience function to get a recommendation.
    
    Returns API-ready response dict.
    """
    pipeline = RecommendationPipeline()
    result = pipeline.recommend(lat, lon, grid_id, mode=mode)
    return result.to_api_response()


# ============================================================================
# Testing
# ============================================================================

if __name__ == "__main__":
    import sys
    from pathlib import Path
    from dotenv import load_dotenv
    
    # Load environment
    backend_path = Path(__file__).parent.parent.parent
    load_dotenv(backend_path / ".env")
    
    # Test coordinates (Clifton Block 2)
    TEST_LAT = 24.8160
    TEST_LON = 67.0280
    TEST_GRID = "Clifton-Block2-007-008"
    
    print("\n" + "="*70)
    print("RECOMMENDATION PIPELINE TEST")
    print("="*70)
    
    # Check API keys
    if not os.getenv("GOOGLE_PLACES_API_KEY"):
        print("Warning: GOOGLE_PLACES_API_KEY not set")
    if not os.getenv("GROQ_API_KEY"):
        print("Warning: GROQ_API_KEY not set - will use FAST mode")
    
    # Initialize pipeline
    pipeline = RecommendationPipeline()
    
    # Determine mode
    mode = PipelineMode.FULL if os.getenv("GROQ_API_KEY") else PipelineMode.FAST
    print(f"\nMode: {mode}")
    print(f"Location: {TEST_LAT}, {TEST_LON}")
    print(f"Grid ID: {TEST_GRID}")
    
    # Run pipeline
    print("\nRunning pipeline...")
    result = pipeline.recommend(
        lat=TEST_LAT,
        lon=TEST_LON,
        grid_id=TEST_GRID,
        mode=mode
    )
    
    # Print results
    print("\n" + "-"*70)
    print("TIMING")
    print("-"*70)
    print(f"  BEV Generation: {result.bev_time_ms:.0f}ms")
    print(f"  Rule Engine:    {result.rule_time_ms:.0f}ms")
    print(f"  LLM Evaluation: {result.llm_time_ms:.0f}ms")
    print(f"  Score Combine:  {result.combine_time_ms:.0f}ms")
    print(f"  TOTAL:          {result.total_time_ms:.0f}ms")
    
    print("\n" + "-"*70)
    print("BEV SUMMARY")
    print("-"*70)
    print(f"  Restaurants: {result.bev.restaurant_count}")
    print(f"  Cafes:       {result.bev.cafe_count}")
    print(f"  Gyms:        {result.bev.gym_count}")
    print(f"  Offices:     {result.bev.office_count}")
    print(f"  Avg Rating:  {result.bev.avg_rating:.2f}")
    print(f"  Income Proxy: {result.bev.income_proxy:.2f}")
    
    print("\n" + "-"*70)
    print("SCORES")
    print("-"*70)
    print(f"  GYM:")
    print(f"    Rule Score: {result.rule_result.gym_score:.3f}")
    if result.llm_result:
        print(f"    LLM Prob:   {result.llm_result.gym_probability:.3f}")
    print(f"    Final:      {result.combined.gym.final_score:.3f} ({result.combined.gym.suitability})")
    print(f"  CAFE:")
    print(f"    Rule Score: {result.rule_result.cafe_score:.3f}")
    if result.llm_result:
        print(f"    LLM Prob:   {result.llm_result.cafe_probability:.3f}")
    print(f"    Final:      {result.combined.cafe.final_score:.3f} ({result.combined.cafe.suitability})")
    
    print("\n" + "-"*70)
    print("RECOMMENDATION")
    print("-"*70)
    print(f"  Best Category: {result.combined.best_category.upper()}")
    print(f"  Best Score:    {result.combined.best_score:.3f}")
    print(f"  Suitability:   {result.combined.best_suitability.upper()}")
    
    if result.llm_result:
        print(f"\n  LLM Analysis:")
        print(f"    {result.llm_result.recommendation}")
        print(f"  Key Factors: {result.llm_result.key_factors}")
        print(f"  Risks: {result.llm_result.risks}")
    
    print("\n" + "-"*70)
    print("API RESPONSE")
    print("-"*70)
    print(json.dumps(result.to_api_response(), indent=2))
    print("="*70)
