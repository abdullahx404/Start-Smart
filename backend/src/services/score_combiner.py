"""
Score Combiner Module

Combines rule-based scores with LLM probabilities to produce
final recommendation scores using a weighted ensemble approach.

Formula:
    final_score = (RULE_WEIGHT * rule_score) + (LLM_WEIGHT * llm_probability)
    
Default Weights:
    - Rule Engine: 0.65 (deterministic, data-driven)
    - LLM: 0.35 (contextual reasoning, pattern recognition)

Usage:
    from src.services.score_combiner import ScoreCombiner
    
    combiner = ScoreCombiner()
    final = combiner.combine(rule_result, llm_result)
    print(f"Final Gym Score: {final.gym_final_score}")
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

from src.services.rule_engine import RuleEvaluationResult
from src.services.llm_evaluator import LLMEvaluationResult
from src.services.bev_generator import BusinessEnvironmentVector
from src.utils.logger import get_logger


# ============================================================================
# Constants
# ============================================================================

# Default weights
DEFAULT_RULE_WEIGHT = 0.65
DEFAULT_LLM_WEIGHT = 0.35

# Score thresholds for recommendations
class SuitabilityLevel(Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    MODERATE = "moderate"
    POOR = "poor"
    NOT_RECOMMENDED = "not_recommended"

THRESHOLD_EXCELLENT = 0.80
THRESHOLD_GOOD = 0.65
THRESHOLD_MODERATE = 0.45
THRESHOLD_POOR = 0.25


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class CategoryScore:
    """Score breakdown for a single category (gym or cafe)."""
    category: str
    rule_score: float
    llm_probability: float
    final_score: float
    suitability: str
    rank: int = 0
    rule_details: List[Dict] = field(default_factory=list)
    llm_reasoning: str = ""
    factors_positive: List[str] = field(default_factory=list)
    factors_negative: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "rule_score": round(self.rule_score, 4),
            "llm_probability": round(self.llm_probability, 4),
            "final_score": round(self.final_score, 4),
            "suitability": self.suitability,
            "rank": self.rank,
            "rule_details": self.rule_details,
            "llm_reasoning": self.llm_reasoning,
            "factors_positive": self.factors_positive,
            "factors_negative": self.factors_negative
        }


@dataclass
class CombinedRecommendation:
    """Final combined recommendation for a grid cell."""
    grid_id: str
    
    # Scores by category
    gym: CategoryScore
    cafe: CategoryScore
    
    # Best recommendation
    best_category: str
    best_score: float
    best_suitability: str
    
    # Weights used
    rule_weight: float
    llm_weight: float
    
    # Meta
    bev_summary: Dict = field(default_factory=dict)
    llm_meta: Dict = field(default_factory=dict)
    combined_at: str = ""
    processing_time_ms: float = 0.0
    
    def __post_init__(self):
        if not self.combined_at:
            self.combined_at = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "grid_id": self.grid_id,
            "best_category": self.best_category,
            "best_score": round(self.best_score, 4),
            "best_suitability": self.best_suitability,
            "categories": {
                "gym": self.gym.to_dict(),
                "cafe": self.cafe.to_dict()
            },
            "weights": {
                "rule_engine": self.rule_weight,
                "llm": self.llm_weight
            },
            "bev_summary": self.bev_summary,
            "llm_meta": self.llm_meta,
            "combined_at": self.combined_at,
            "processing_time_ms": round(self.processing_time_ms, 2)
        }
    
    def to_api_response(self) -> Dict[str, Any]:
        """Format for API response."""
        return {
            "grid_id": self.grid_id,
            "recommendation": {
                "best_category": self.best_category,
                "score": round(self.best_score, 2),
                "suitability": self.best_suitability,
                "message": self._generate_message()
            },
            "gym": {
                "score": round(self.gym.final_score, 2),
                "suitability": self.gym.suitability,
                "reasoning": self.gym.llm_reasoning,
                "positive_factors": self.gym.factors_positive[:3],
                "concerns": self.gym.factors_negative[:2]
            },
            "cafe": {
                "score": round(self.cafe.final_score, 2),
                "suitability": self.cafe.suitability,
                "reasoning": self.cafe.llm_reasoning,
                "positive_factors": self.cafe.factors_positive[:3],
                "concerns": self.cafe.factors_negative[:2]
            },
            "analysis": {
                "model_used": self.llm_meta.get("model_used", "unknown"),
                "total_businesses_nearby": self.bev_summary.get("total_businesses", 0),
                "key_factors": self.llm_meta.get("key_factors", [])
            }
        }
    
    def _generate_message(self) -> str:
        """Generate human-readable recommendation message."""
        category = self.best_category.upper()
        
        if self.best_suitability == SuitabilityLevel.EXCELLENT.value:
            return f"This location is EXCELLENT for a {category}. Strong recommendation to proceed."
        elif self.best_suitability == SuitabilityLevel.GOOD.value:
            return f"This location is GOOD for a {category}. Recommended with minor considerations."
        elif self.best_suitability == SuitabilityLevel.MODERATE.value:
            return f"This location has MODERATE potential for a {category}. Further analysis recommended."
        elif self.best_suitability == SuitabilityLevel.POOR.value:
            return f"This location shows POOR potential for a {category}. Consider alternatives."
        else:
            return f"This location is NOT RECOMMENDED for a {category}. High risk."


# ============================================================================
# Score Combiner Class
# ============================================================================

class ScoreCombiner:
    """
    Combines rule engine and LLM scores into final recommendations.
    """
    
    def __init__(
        self,
        rule_weight: float = DEFAULT_RULE_WEIGHT,
        llm_weight: float = DEFAULT_LLM_WEIGHT
    ):
        """
        Initialize score combiner.
        
        Args:
            rule_weight: Weight for rule engine scores (0-1)
            llm_weight: Weight for LLM probabilities (0-1)
        """
        # Normalize weights if they don't sum to 1
        total = rule_weight + llm_weight
        self.rule_weight = rule_weight / total
        self.llm_weight = llm_weight / total
        
        self.logger = get_logger(__name__)
        
        self.logger.info(
            "ScoreCombiner initialized",
            extra={"extra_fields": {
                "rule_weight": self.rule_weight,
                "llm_weight": self.llm_weight
            }}
        )
    
    def combine(
        self,
        grid_id: str,
        rule_result: RuleEvaluationResult,
        llm_result: LLMEvaluationResult,
        bev: Optional[BusinessEnvironmentVector] = None
    ) -> CombinedRecommendation:
        """
        Combine rule and LLM scores.
        
        Args:
            grid_id: Grid cell identifier
            rule_result: Output from rule engine
            llm_result: Output from LLM evaluator
            bev: Original BEV (optional, for summary)
            
        Returns:
            CombinedRecommendation with final scores
        """
        start_time = datetime.utcnow()
        
        # Calculate combined scores
        gym_final = self._weighted_combine(
            rule_result.gym_score,
            llm_result.gym_probability
        )
        
        cafe_final = self._weighted_combine(
            rule_result.cafe_score,
            llm_result.cafe_probability
        )
        
        # Extract positive/negative factors
        gym_positive, gym_negative = self._extract_factors(
            rule_result.gym_rules_applied
        )
        cafe_positive, cafe_negative = self._extract_factors(
            rule_result.cafe_rules_applied
        )
        
        # Build category scores
        gym_score = CategoryScore(
            category="gym",
            rule_score=rule_result.gym_score,
            llm_probability=llm_result.gym_probability,
            final_score=gym_final,
            suitability=self._get_suitability(gym_final),
            rule_details=rule_result.gym_rules_applied,
            llm_reasoning=llm_result.gym_reasoning,
            factors_positive=gym_positive,
            factors_negative=gym_negative
        )
        
        cafe_score = CategoryScore(
            category="cafe",
            rule_score=rule_result.cafe_score,
            llm_probability=llm_result.cafe_probability,
            final_score=cafe_final,
            suitability=self._get_suitability(cafe_final),
            rule_details=rule_result.cafe_rules_applied,
            llm_reasoning=llm_result.cafe_reasoning,
            factors_positive=cafe_positive,
            factors_negative=cafe_negative
        )
        
        # Determine best category
        if gym_final >= cafe_final:
            best_category = "gym"
            best_score = gym_final
            best_suitability = gym_score.suitability
            gym_score.rank = 1
            cafe_score.rank = 2
        else:
            best_category = "cafe"
            best_score = cafe_final
            best_suitability = cafe_score.suitability
            cafe_score.rank = 1
            gym_score.rank = 2
        
        # Build BEV summary
        bev_summary = {}
        if bev:
            bev_summary = {
                "total_businesses": bev.economic.total_businesses,
                "competition_gym": bev.density.gyms,
                "competition_cafe": bev.density.cafes,
                "avg_rating": bev.economic.avg_business_rating,
                "income_proxy": bev.economic.income_proxy
            }
        
        # Build LLM meta
        llm_meta = {
            "model_used": llm_result.model_used,
            "tokens_used": llm_result.tokens_used,
            "key_factors": llm_result.key_factors,
            "risks": llm_result.risks,
            "recommendation": llm_result.recommendation
        }
        
        end_time = datetime.utcnow()
        processing_time = (end_time - start_time).total_seconds() * 1000
        
        result = CombinedRecommendation(
            grid_id=grid_id,
            gym=gym_score,
            cafe=cafe_score,
            best_category=best_category,
            best_score=best_score,
            best_suitability=best_suitability,
            rule_weight=self.rule_weight,
            llm_weight=self.llm_weight,
            bev_summary=bev_summary,
            llm_meta=llm_meta,
            processing_time_ms=processing_time
        )
        
        self.logger.info(
            "Score combination complete",
            extra={"extra_fields": {
                "grid_id": grid_id,
                "gym_final": gym_final,
                "cafe_final": cafe_final,
                "best": best_category
            }}
        )
        
        return result
    
    def _weighted_combine(
        self,
        rule_score: float,
        llm_probability: float
    ) -> float:
        """Calculate weighted combination of scores."""
        combined = (
            self.rule_weight * rule_score +
            self.llm_weight * llm_probability
        )
        return round(max(0.0, min(1.0, combined)), 4)
    
    def _get_suitability(self, score: float) -> str:
        """Convert score to suitability level."""
        if score >= THRESHOLD_EXCELLENT:
            return SuitabilityLevel.EXCELLENT.value
        elif score >= THRESHOLD_GOOD:
            return SuitabilityLevel.GOOD.value
        elif score >= THRESHOLD_MODERATE:
            return SuitabilityLevel.MODERATE.value
        elif score >= THRESHOLD_POOR:
            return SuitabilityLevel.POOR.value
        else:
            return SuitabilityLevel.NOT_RECOMMENDED.value
    
    def _extract_factors(
        self,
        rules_applied: List[Dict]
    ) -> tuple:
        """Extract positive and negative factors from applied rules."""
        positive = []
        negative = []
        
        for rule in rules_applied:
            delta = rule.get("delta", rule.get("score_delta", 0))
            explanation = rule.get("explanation", rule.get("description", rule.get("name", "Unknown")))
            
            if delta > 0:
                positive.append(explanation)
            elif delta < 0:
                negative.append(explanation)
        
        return positive, negative
    
    def adjust_weights(self, rule_weight: float, llm_weight: float):
        """Dynamically adjust weights."""
        total = rule_weight + llm_weight
        self.rule_weight = rule_weight / total
        self.llm_weight = llm_weight / total
        
        self.logger.info(
            "Weights adjusted",
            extra={"extra_fields": {
                "new_rule_weight": self.rule_weight,
                "new_llm_weight": self.llm_weight
            }}
        )


# ============================================================================
# Convenience Functions
# ============================================================================

def combine_scores(
    grid_id: str,
    rule_result: RuleEvaluationResult,
    llm_result: LLMEvaluationResult,
    bev: Optional[BusinessEnvironmentVector] = None
) -> CombinedRecommendation:
    """Convenience function to combine scores."""
    combiner = ScoreCombiner()
    return combiner.combine(grid_id, rule_result, llm_result, bev)


# ============================================================================
# Testing
# ============================================================================

if __name__ == "__main__":
    # Test with mock data
    from src.services.rule_engine import RuleEvaluationResult
    from src.services.llm_evaluator import LLMEvaluationResult
    
    # Mock rule result
    rule_result = RuleEvaluationResult(
        gym_score=0.72,
        cafe_score=0.58,
        gym_rules_applied={
            "office_boost": {"applied": True, "score_delta": 0.12, "description": "Nearby offices boost"},
            "competition_penalty": {"applied": True, "score_delta": -0.08, "description": "Some competition"}
        },
        cafe_rules_applied={
            "restaurant_density": {"applied": True, "score_delta": 0.10, "description": "Good restaurant area"},
            "saturation": {"applied": True, "score_delta": -0.15, "description": "Cafe saturation"}
        },
        evaluated_at=datetime.utcnow().isoformat()
    )
    
    # Mock LLM result
    llm_result = LLMEvaluationResult(
        gym_probability=0.78,
        cafe_probability=0.62,
        gym_reasoning="Strong office presence and limited gym competition make this ideal.",
        cafe_reasoning="Moderate potential due to existing cafe density.",
        key_factors=["office workers", "limited competition", "good foot traffic"],
        risks=["cafe saturation"],
        recommendation="Gym is strongly recommended; cafe is a secondary option.",
        model_used="llama-3.3-70b-versatile",
        tokens_used=350
    )
    
    # Combine
    combiner = ScoreCombiner()
    result = combiner.combine(
        grid_id="Clifton-Block2-007-008",
        rule_result=rule_result,
        llm_result=llm_result
    )
    
    print("\n" + "="*60)
    print("SCORE COMBINER TEST")
    print("="*60)
    print(f"\nGrid: {result.grid_id}")
    print(f"\n--- GYM ---")
    print(f"  Rule Score: {result.gym.rule_score:.3f}")
    print(f"  LLM Prob:   {result.gym.llm_probability:.3f}")
    print(f"  FINAL:      {result.gym.final_score:.3f} ({result.gym.suitability})")
    print(f"\n--- CAFE ---")
    print(f"  Rule Score: {result.cafe.rule_score:.3f}")
    print(f"  LLM Prob:   {result.cafe.llm_probability:.3f}")
    print(f"  FINAL:      {result.cafe.final_score:.3f} ({result.cafe.suitability})")
    print(f"\n--- BEST ---")
    print(f"  Category:   {result.best_category}")
    print(f"  Score:      {result.best_score:.3f}")
    print(f"  Suitability: {result.best_suitability}")
    print("\n--- API RESPONSE ---")
    import json
    print(json.dumps(result.to_api_response(), indent=2))
    print("="*60)
