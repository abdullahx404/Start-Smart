"""
LLM Evaluator Module

Uses Groq's LLM API to evaluate location suitability based on the
Business Environment Vector (BEV). Provides probabilistic assessments
and natural language reasoning.

Features:
- Structured prompt generation from BEV
- JSON response parsing
- Fallback handling for API errors
- Configurable model selection

Usage:
    from src.services.llm_evaluator import LLMEvaluator
    
    evaluator = LLMEvaluator()
    result = evaluator.evaluate(bev)
    print(f"Gym Probability: {result['gym_probability']}")
"""

import os
import json
import re
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

from groq import Groq

from src.services.bev_generator import BusinessEnvironmentVector
from src.utils.logger import get_logger


# ============================================================================
# Constants
# ============================================================================

# Groq model options (reasoning models)
DEFAULT_MODEL = "llama-3.3-70b-versatile"  # Best reasoning
FALLBACK_MODEL = "llama-3.1-8b-instant"    # Faster fallback

# Prompt templates
SYSTEM_PROMPT = """You are an expert location analyst for business site selection in Karachi, Pakistan.
Your task is to evaluate the suitability of a location for opening a GYM or CAFE based on the provided Business Environment Vector (BEV).

Consider these factors:
1. Customer Base: Who would be the potential customers? (office workers, students, residents)
2. Foot Traffic: What drives people to this area?
3. Competition: How saturated is the market?
4. Income Level: Can the local population afford the services?
5. Accessibility: How easy is it to reach this location?
6. Synergies: What nearby businesses could benefit or complement a gym/cafe?

You must respond ONLY with valid JSON in this exact format:
{
  "gym_probability": <float between 0.0 and 1.0>,
  "cafe_probability": <float between 0.0 and 1.0>,
  "gym_reasoning": "<2-3 sentence explanation for gym score>",
  "cafe_reasoning": "<2-3 sentence explanation for cafe score>",
  "key_factors": ["factor1", "factor2", "factor3"],
  "risks": ["risk1", "risk2"],
  "recommendation": "<overall recommendation in 1-2 sentences>"
}

Be analytical and base your probabilities on the actual data provided. 
A probability of 0.7+ indicates strong suitability.
A probability of 0.4-0.7 indicates moderate suitability.
A probability below 0.4 indicates poor suitability.
"""

USER_PROMPT_TEMPLATE = """{bev_data}

[Task]
Analyze this location for opening:
1. A GYM (fitness center)
2. A CAFE (coffee shop / casual dining)

Consider the business environment data above and provide your assessment as JSON.
Remember: Karachi's Clifton area is generally affluent with good commercial activity.
"""


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class LLMEvaluationResult:
    """Result of LLM evaluation."""
    gym_probability: float
    cafe_probability: float
    gym_reasoning: str
    cafe_reasoning: str
    key_factors: list
    risks: list
    recommendation: str
    model_used: str
    tokens_used: int = 0
    evaluated_at: str = ""
    raw_response: str = ""
    
    def __post_init__(self):
        if not self.evaluated_at:
            self.evaluated_at = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "gym_llm_probability": self.gym_probability,
            "cafe_llm_probability": self.cafe_probability,
            "gym_reasoning": self.gym_reasoning,
            "cafe_reasoning": self.cafe_reasoning,
            "key_factors": self.key_factors,
            "risks": self.risks,
            "recommendation": self.recommendation,
            "model_used": self.model_used,
            "tokens_used": self.tokens_used,
            "evaluated_at": self.evaluated_at
        }


# ============================================================================
# LLM Evaluator Class
# ============================================================================

class LLMEvaluator:
    """
    LLM-based location evaluator using Groq API.
    
    Provides probabilistic assessments of location suitability
    based on BEV data and domain knowledge.
    """
    
    def __init__(
        self,
        api_key: str = None,
        model: str = DEFAULT_MODEL
    ):
        """
        Initialize LLM evaluator.
        
        Args:
            api_key: Groq API key. If None, reads from environment.
            model: Groq model to use.
        """
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY is required")
        
        self.client = Groq(api_key=self.api_key)
        self.model = model
        self.logger = get_logger(__name__)
        
        self.logger.info(
            "LLMEvaluator initialized",
            extra={"extra_fields": {"model": model}}
        )
    
    def evaluate(
        self,
        bev: BusinessEnvironmentVector,
        temperature: float = 0.3
    ) -> LLMEvaluationResult:
        """
        Evaluate location suitability using LLM.
        
        Args:
            bev: Business Environment Vector
            temperature: LLM temperature (lower = more deterministic)
            
        Returns:
            LLMEvaluationResult with probabilities and reasoning
        """
        # Generate prompt
        user_prompt = USER_PROMPT_TEMPLATE.format(
            bev_data=bev.to_prompt_format()
        )
        
        self.logger.debug(f"Sending prompt to {self.model}")
        
        try:
            # Call Groq API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                max_tokens=1000,
                response_format={"type": "json_object"}
            )
            
            # Extract response
            raw_response = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if response.usage else 0
            
            # Parse JSON response
            result = self._parse_response(raw_response, tokens_used)
            
            self.logger.info(
                "LLM evaluation complete",
                extra={"extra_fields": {
                    "gym_prob": result.gym_probability,
                    "cafe_prob": result.cafe_probability,
                    "tokens": tokens_used
                }}
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"LLM evaluation error: {e}")
            return self._get_fallback_result(str(e))
    
    def _parse_response(
        self,
        raw_response: str,
        tokens_used: int
    ) -> LLMEvaluationResult:
        """Parse LLM JSON response."""
        try:
            # Try to parse JSON
            data = json.loads(raw_response)
            
            return LLMEvaluationResult(
                gym_probability=self._clamp_probability(data.get("gym_probability", 0.5)),
                cafe_probability=self._clamp_probability(data.get("cafe_probability", 0.5)),
                gym_reasoning=data.get("gym_reasoning", "No reasoning provided"),
                cafe_reasoning=data.get("cafe_reasoning", "No reasoning provided"),
                key_factors=data.get("key_factors", []),
                risks=data.get("risks", []),
                recommendation=data.get("recommendation", "No recommendation"),
                model_used=self.model,
                tokens_used=tokens_used,
                raw_response=raw_response
            )
            
        except json.JSONDecodeError as e:
            self.logger.warning(f"JSON parse error: {e}")
            
            # Try to extract probabilities from text
            return self._extract_from_text(raw_response, tokens_used)
    
    def _extract_from_text(
        self,
        text: str,
        tokens_used: int
    ) -> LLMEvaluationResult:
        """Extract probabilities from non-JSON text response."""
        gym_prob = 0.5
        cafe_prob = 0.5
        
        # Try to find probability patterns
        gym_match = re.search(r'gym[_\s]?probability["\s:]+([0-9.]+)', text.lower())
        cafe_match = re.search(r'cafe[_\s]?probability["\s:]+([0-9.]+)', text.lower())
        
        if gym_match:
            gym_prob = float(gym_match.group(1))
        if cafe_match:
            cafe_prob = float(cafe_match.group(1))
        
        return LLMEvaluationResult(
            gym_probability=self._clamp_probability(gym_prob),
            cafe_probability=self._clamp_probability(cafe_prob),
            gym_reasoning="Extracted from non-standard response",
            cafe_reasoning="Extracted from non-standard response",
            key_factors=[],
            risks=["Response parsing was imperfect"],
            recommendation="Please verify the analysis",
            model_used=self.model,
            tokens_used=tokens_used,
            raw_response=text
        )
    
    def _get_fallback_result(self, error_msg: str) -> LLMEvaluationResult:
        """Return fallback result when LLM fails."""
        return LLMEvaluationResult(
            gym_probability=0.5,
            cafe_probability=0.5,
            gym_reasoning=f"LLM evaluation unavailable: {error_msg}",
            cafe_reasoning=f"LLM evaluation unavailable: {error_msg}",
            key_factors=["fallback_mode"],
            risks=["LLM evaluation failed - using neutral scores"],
            recommendation="Please retry or check API configuration",
            model_used=self.model,
            tokens_used=0,
            raw_response=""
        )
    
    def _clamp_probability(self, value: float) -> float:
        """Ensure probability is in [0, 1] range."""
        try:
            return round(max(0.0, min(1.0, float(value))), 3)
        except (ValueError, TypeError):
            return 0.5
    
    async def evaluate_async(
        self,
        bev: BusinessEnvironmentVector,
        temperature: float = 0.3
    ) -> LLMEvaluationResult:
        """Async version of evaluate (for future use)."""
        # For now, just call sync version
        # Can be upgraded to async Groq client later
        return self.evaluate(bev, temperature)


# ============================================================================
# Convenience Functions
# ============================================================================

def evaluate_with_llm(bev: BusinessEnvironmentVector) -> LLMEvaluationResult:
    """Convenience function to evaluate a location with LLM."""
    evaluator = LLMEvaluator()
    return evaluator.evaluate(bev)


# ============================================================================
# Testing
# ============================================================================

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    # Check for API key
    if not os.getenv("GROQ_API_KEY"):
        print("Error: GROQ_API_KEY not set in environment")
        print("Get your API key from: https://console.groq.com/")
        exit(1)
    
    from src.services.bev_generator import BEVGenerator
    
    # Generate test BEV
    bev_generator = BEVGenerator()
    bev = bev_generator.generate_bev(
        center_lat=24.8160,
        center_lon=67.0280,
        radius_meters=500,
        grid_id="Clifton-Block2-007-008"
    )
    
    # Evaluate with LLM
    evaluator = LLMEvaluator()
    result = evaluator.evaluate(bev)
    
    print("\n" + "="*60)
    print("LLM EVALUATOR TEST")
    print("="*60)
    print(f"Model: {result.model_used}")
    print(f"Tokens: {result.tokens_used}")
    print(f"\nGym Probability: {result.gym_probability:.3f}")
    print(f"Gym Reasoning: {result.gym_reasoning}")
    print(f"\nCafe Probability: {result.cafe_probability:.3f}")
    print(f"Cafe Reasoning: {result.cafe_reasoning}")
    print(f"\nKey Factors: {result.key_factors}")
    print(f"Risks: {result.risks}")
    print(f"Recommendation: {result.recommendation}")
    print("="*60)
