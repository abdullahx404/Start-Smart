"""
Rule-Based Scoring Engine

Deterministic rule engine that computes base scores (0-1) for Gym and Café
categories based on the Business Environment Vector (BEV).

Rules are designed to capture business location suitability based on:
- Nearby amenities and foot traffic generators
- Competition levels
- Economic indicators
- Transportation accessibility

Usage:
    from src.services.rule_engine import RuleEngine
    
    engine = RuleEngine()
    scores = engine.evaluate(bev)
    print(f"Gym Score: {scores['gym_score']}")
    print(f"Cafe Score: {scores['cafe_score']}")
"""

from typing import Dict, List, Tuple, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime

from src.services.bev_generator import BusinessEnvironmentVector
from src.utils.logger import get_logger


# ============================================================================
# Rule Definitions
# ============================================================================

@dataclass
class Rule:
    """
    Represents a scoring rule.
    
    Attributes:
        name: Human-readable rule name
        category: 'gym', 'cafe', or 'both'
        condition: Lambda function that takes BEV and returns bool
        score_delta: Score adjustment when condition is True
        explanation: Why this rule matters
    """
    name: str
    category: str  # 'gym', 'cafe', or 'both'
    condition: Callable[[BusinessEnvironmentVector], bool]
    score_delta: float
    explanation: str
    priority: int = 1  # Higher = more important


# ============================================================================
# Gym Rules
# ============================================================================

GYM_RULES = [
    # Positive factors
    Rule(
        name="office_heavy_area",
        category="gym",
        condition=lambda bev: bev.density.offices > 30,
        score_delta=0.25,
        explanation="High office density indicates working professionals who need gym access",
        priority=3
    ),
    Rule(
        name="moderate_offices",
        category="gym",
        condition=lambda bev: 15 <= bev.density.offices <= 30,
        score_delta=0.15,
        explanation="Moderate office presence provides good customer base",
        priority=2
    ),
    Rule(
        name="residential_area",
        category="gym",
        condition=lambda bev: bev.density.residential > 5,
        score_delta=0.15,
        explanation="Residential areas provide local membership base",
        priority=2
    ),
    Rule(
        name="near_university",
        category="gym",
        condition=lambda bev: bev.density.universities > 0 or 
                              (bev.distance.distance_to_university >= 0 and 
                               bev.distance.distance_to_university < 500),
        score_delta=0.20,
        explanation="University students are key gym demographic",
        priority=3
    ),
    Rule(
        name="good_transit_access",
        category="gym",
        condition=lambda bev: bev.distance.distance_to_transit >= 0 and 
                              bev.distance.distance_to_transit < 300,
        score_delta=0.15,
        explanation="Easy transit access increases catchment area",
        priority=2
    ),
    Rule(
        name="high_income_area",
        category="gym",
        condition=lambda bev: bev.economic.income_proxy == "high",
        score_delta=0.20,
        explanation="High income areas have more gym membership capacity",
        priority=3
    ),
    Rule(
        name="mid_income_area",
        category="gym",
        condition=lambda bev: bev.economic.income_proxy == "mid",
        score_delta=0.10,
        explanation="Middle income areas have moderate gym potential",
        priority=1
    ),
    Rule(
        name="high_rated_area",
        category="gym",
        condition=lambda bev: bev.economic.avg_business_rating >= 4.2,
        score_delta=0.10,
        explanation="High-rated business area indicates quality-conscious customers",
        priority=2
    ),
    Rule(
        name="near_healthcare",
        category="gym",
        condition=lambda bev: bev.density.healthcare > 2,
        score_delta=0.10,
        explanation="Healthcare proximity suggests health-conscious population",
        priority=1
    ),
    Rule(
        name="near_park",
        category="gym",
        condition=lambda bev: bev.distance.distance_to_park >= 0 and 
                              bev.distance.distance_to_park < 400,
        score_delta=0.10,
        explanation="Park proximity attracts fitness-oriented customers",
        priority=1
    ),
    
    # Negative factors
    Rule(
        name="high_gym_competition",
        category="gym",
        condition=lambda bev: bev.density.gyms >= 4,
        score_delta=-0.30,
        explanation="Too many existing gyms - saturated market",
        priority=3
    ),
    Rule(
        name="moderate_gym_competition",
        category="gym",
        condition=lambda bev: 2 <= bev.density.gyms < 4,
        score_delta=-0.15,
        explanation="Moderate competition from existing gyms",
        priority=2
    ),
    Rule(
        name="low_income_area",
        category="gym",
        condition=lambda bev: bev.economic.income_proxy == "low",
        score_delta=-0.20,
        explanation="Low income areas have limited gym subscription capacity",
        priority=2
    ),
    Rule(
        name="poor_transit",
        category="gym",
        condition=lambda bev: bev.distance.distance_to_transit < 0 or 
                              bev.distance.distance_to_transit > 800,
        score_delta=-0.10,
        explanation="Poor transit access limits customer reach",
        priority=1
    ),
    Rule(
        name="very_low_foot_traffic",
        category="gym",
        condition=lambda bev: bev.economic.total_businesses < 10,
        score_delta=-0.15,
        explanation="Very low commercial activity indicates limited foot traffic",
        priority=2
    ),
]


# ============================================================================
# Cafe Rules
# ============================================================================

CAFE_RULES = [
    # Positive factors
    Rule(
        name="restaurant_cluster",
        category="cafe",
        condition=lambda bev: bev.density.restaurants > 10,
        score_delta=0.20,
        explanation="Restaurant clusters attract food-seeking customers",
        priority=3
    ),
    Rule(
        name="office_area",
        category="cafe",
        condition=lambda bev: bev.density.offices > 30,
        score_delta=0.30,
        explanation="Office workers are prime cafe customers for coffee/lunch",
        priority=3
    ),
    Rule(
        name="moderate_offices",
        category="cafe",
        condition=lambda bev: 15 <= bev.density.offices <= 30,
        score_delta=0.20,
        explanation="Moderate office presence provides steady customer flow",
        priority=2
    ),
    Rule(
        name="near_university",
        category="cafe",
        condition=lambda bev: bev.density.universities > 0 or 
                              (bev.distance.distance_to_university >= 0 and 
                               bev.distance.distance_to_university < 400),
        score_delta=0.25,
        explanation="University students are frequent cafe visitors",
        priority=3
    ),
    Rule(
        name="school_area",
        category="cafe",
        condition=lambda bev: bev.density.schools > 3,
        score_delta=0.10,
        explanation="Schools bring parents who may visit cafes",
        priority=1
    ),
    Rule(
        name="mall_proximity",
        category="cafe",
        condition=lambda bev: bev.distance.distance_to_mall >= 0 and 
                              bev.distance.distance_to_mall < 300,
        score_delta=0.20,
        explanation="Mall proximity brings shopping traffic to cafes",
        priority=2
    ),
    Rule(
        name="good_transit_access",
        category="cafe",
        condition=lambda bev: bev.distance.distance_to_transit >= 0 and 
                              bev.distance.distance_to_transit < 200,
        score_delta=0.20,
        explanation="Transit stations create high foot traffic for cafes",
        priority=3
    ),
    Rule(
        name="high_income_area",
        category="cafe",
        condition=lambda bev: bev.economic.income_proxy == "high",
        score_delta=0.15,
        explanation="High income areas spend more on dining out",
        priority=2
    ),
    Rule(
        name="high_rated_area",
        category="cafe",
        condition=lambda bev: bev.economic.avg_business_rating >= 4.0,
        score_delta=0.10,
        explanation="Quality-conscious area supports premium cafes",
        priority=1
    ),
    Rule(
        name="entertainment_zone",
        category="cafe",
        condition=lambda bev: bev.density.cinemas > 0 or bev.density.bars > 2,
        score_delta=0.15,
        explanation="Entertainment venues create cafe-friendly foot traffic",
        priority=2
    ),
    Rule(
        name="bank_presence",
        category="cafe",
        condition=lambda bev: bev.density.banks > 2,
        score_delta=0.10,
        explanation="Banks indicate commercial activity and professional traffic",
        priority=1
    ),
    Rule(
        name="park_adjacent",
        category="cafe",
        condition=lambda bev: bev.distance.distance_to_park >= 0 and 
                              bev.distance.distance_to_park < 200,
        score_delta=0.10,
        explanation="Park proximity attracts leisure visitors",
        priority=1
    ),
    
    # Negative factors
    Rule(
        name="high_cafe_competition",
        category="cafe",
        condition=lambda bev: bev.density.cafes >= 6,
        score_delta=-0.25,
        explanation="Too many existing cafes - saturated market",
        priority=3
    ),
    Rule(
        name="moderate_cafe_competition",
        category="cafe",
        condition=lambda bev: 3 <= bev.density.cafes < 6,
        score_delta=-0.10,
        explanation="Moderate competition from existing cafes",
        priority=2
    ),
    Rule(
        name="low_income_area",
        category="cafe",
        condition=lambda bev: bev.economic.income_proxy == "low",
        score_delta=-0.15,
        explanation="Low income areas have limited cafe spending",
        priority=2
    ),
    Rule(
        name="poor_transit",
        category="cafe",
        condition=lambda bev: bev.distance.distance_to_transit < 0 or 
                              bev.distance.distance_to_transit > 600,
        score_delta=-0.10,
        explanation="Poor transit access limits customer flow",
        priority=1
    ),
    Rule(
        name="isolated_area",
        category="cafe",
        condition=lambda bev: bev.economic.total_businesses < 15,
        score_delta=-0.20,
        explanation="Low commercial activity means limited foot traffic",
        priority=2
    ),
]


# ============================================================================
# Rule Engine Class
# ============================================================================

@dataclass
class RuleEvaluationResult:
    """Result of rule engine evaluation."""
    gym_score: float
    cafe_score: float
    gym_rules_applied: List[Dict[str, Any]]
    cafe_rules_applied: List[Dict[str, Any]]
    gym_base_score: float = 0.5  # Starting score
    cafe_base_score: float = 0.5
    evaluated_at: str = ""
    
    def __post_init__(self):
        if not self.evaluated_at:
            self.evaluated_at = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "gym_rule_score": self.gym_score,
            "cafe_rule_score": self.cafe_score,
            "gym_rules_applied": self.gym_rules_applied,
            "cafe_rules_applied": self.cafe_rules_applied,
            "evaluated_at": self.evaluated_at
        }
    
    def get_explanation(self) -> str:
        """Generate human-readable explanation."""
        lines = ["=== Rule Engine Evaluation ===", ""]
        
        lines.append(f"Gym Score: {self.gym_score:.3f}")
        if self.gym_rules_applied:
            for rule in self.gym_rules_applied:
                sign = "+" if rule["delta"] > 0 else ""
                lines.append(f"  {sign}{rule['delta']:.2f}: {rule['name']} - {rule['explanation']}")
        
        lines.append("")
        lines.append(f"Cafe Score: {self.cafe_score:.3f}")
        if self.cafe_rules_applied:
            for rule in self.cafe_rules_applied:
                sign = "+" if rule["delta"] > 0 else ""
                lines.append(f"  {sign}{rule['delta']:.2f}: {rule['name']} - {rule['explanation']}")
        
        return "\n".join(lines)


class RuleEngine:
    """
    Deterministic rule-based scoring engine.
    
    Evaluates a BEV against predefined rules to compute base scores
    for Gym and Cafe suitability.
    """
    
    def __init__(
        self,
        gym_rules: List[Rule] = None,
        cafe_rules: List[Rule] = None,
        base_score: float = 0.5
    ):
        """
        Initialize rule engine.
        
        Args:
            gym_rules: Custom gym rules (uses defaults if None)
            cafe_rules: Custom cafe rules (uses defaults if None)
            base_score: Starting score before rules are applied
        """
        self.gym_rules = gym_rules or GYM_RULES
        self.cafe_rules = cafe_rules or CAFE_RULES
        self.base_score = base_score
        self.logger = get_logger(__name__)
        
        self.logger.info(
            "RuleEngine initialized",
            extra={"extra_fields": {
                "gym_rules": len(self.gym_rules),
                "cafe_rules": len(self.cafe_rules),
                "base_score": base_score
            }}
        )
    
    def evaluate(self, bev: BusinessEnvironmentVector) -> RuleEvaluationResult:
        """
        Evaluate BEV against all rules.
        
        Args:
            bev: Business Environment Vector to evaluate
            
        Returns:
            RuleEvaluationResult with scores and applied rules
        """
        gym_score = self.base_score
        cafe_score = self.base_score
        gym_rules_applied = []
        cafe_rules_applied = []
        
        # Evaluate gym rules
        for rule in sorted(self.gym_rules, key=lambda r: -r.priority):
            try:
                if rule.condition(bev):
                    gym_score += rule.score_delta
                    gym_rules_applied.append({
                        "name": rule.name,
                        "delta": rule.score_delta,
                        "explanation": rule.explanation,
                        "priority": rule.priority
                    })
            except Exception as e:
                self.logger.warning(f"Error evaluating gym rule {rule.name}: {e}")
        
        # Evaluate cafe rules
        for rule in sorted(self.cafe_rules, key=lambda r: -r.priority):
            try:
                if rule.condition(bev):
                    cafe_score += rule.score_delta
                    cafe_rules_applied.append({
                        "name": rule.name,
                        "delta": rule.score_delta,
                        "explanation": rule.explanation,
                        "priority": rule.priority
                    })
            except Exception as e:
                self.logger.warning(f"Error evaluating cafe rule {rule.name}: {e}")
        
        # Normalize scores to [0, 1]
        gym_score = self._normalize_score(gym_score)
        cafe_score = self._normalize_score(cafe_score)
        
        result = RuleEvaluationResult(
            gym_score=gym_score,
            cafe_score=cafe_score,
            gym_rules_applied=gym_rules_applied,
            cafe_rules_applied=cafe_rules_applied,
            gym_base_score=self.base_score,
            cafe_base_score=self.base_score
        )
        
        self.logger.info(
            f"Rule evaluation complete",
            extra={"extra_fields": {
                "gym_score": gym_score,
                "cafe_score": cafe_score,
                "gym_rules": len(gym_rules_applied),
                "cafe_rules": len(cafe_rules_applied)
            }}
        )
        
        return result
    
    def _normalize_score(self, score: float) -> float:
        """Normalize score to [0, 1] range."""
        return round(max(0.0, min(1.0, score)), 3)
    
    def get_rule_summary(self) -> Dict[str, Any]:
        """Get summary of all rules."""
        return {
            "gym_rules": [
                {"name": r.name, "delta": r.score_delta, "priority": r.priority}
                for r in self.gym_rules
            ],
            "cafe_rules": [
                {"name": r.name, "delta": r.score_delta, "priority": r.priority}
                for r in self.cafe_rules
            ],
            "base_score": self.base_score,
            "total_rules": len(self.gym_rules) + len(self.cafe_rules)
        }


# ============================================================================
# Convenience Functions
# ============================================================================

def evaluate_location(bev: BusinessEnvironmentVector) -> RuleEvaluationResult:
    """Convenience function to evaluate a location."""
    engine = RuleEngine()
    return engine.evaluate(bev)


# ============================================================================
# Testing
# ============================================================================

if __name__ == "__main__":
    from src.services.bev_generator import BEVGenerator
    from dotenv import load_dotenv
    load_dotenv()
    
    # Generate test BEV
    bev_generator = BEVGenerator()
    bev = bev_generator.generate_bev(
        center_lat=24.8160,
        center_lon=67.0280,
        radius_meters=500,
        grid_id="Clifton-Block2-007-008"
    )
    
    # Evaluate
    engine = RuleEngine()
    result = engine.evaluate(bev)
    
    print("\n" + "="*60)
    print("RULE ENGINE TEST")
    print("="*60)
    print(result.get_explanation())
    print("="*60)
