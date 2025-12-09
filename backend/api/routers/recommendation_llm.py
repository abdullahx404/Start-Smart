"""
LLM Recommendations Router

Advanced recommendation endpoint using the full pipeline:
BEV → Rule Engine → LLM Evaluator → Score Combiner

Endpoints:
    GET /api/v1/recommendation_llm - Full LLM-powered recommendation
    GET /api/v1/recommendation_fast - Fast rule-based only
"""

import logging
import os
from typing import Dict, Any, Optional, List
from enum import Enum

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field

from src.services.recommendation_pipeline import (
    RecommendationPipeline,
    PipelineMode,
    PipelineResult
)
from src.services.bev_generator import BusinessEnvironmentVector

logger = logging.getLogger("startsmart.api.recommendation_llm")

router = APIRouter()


# ============================================================================
# Response Models
# ============================================================================

class LocationInput(BaseModel):
    """Input location for recommendation."""
    lat: float = Field(..., ge=-90, le=90, description="Latitude")
    lon: float = Field(..., ge=-180, le=180, description="Longitude")
    grid_id: Optional[str] = Field(None, description="Grid cell identifier")
    radius_meters: Optional[int] = Field(500, ge=100, le=2000, description="Search radius")


class CategoryRecommendation(BaseModel):
    """Recommendation for a single category."""
    score: float = Field(..., ge=0, le=1, description="Final score (0-1)")
    suitability: str = Field(..., description="Suitability level")
    reasoning: str = Field(..., description="LLM reasoning")
    positive_factors: List[str] = Field(default_factory=list)
    concerns: List[str] = Field(default_factory=list)


class RecommendationOutput(BaseModel):
    """Best recommendation output."""
    best_category: str = Field(..., description="Recommended category")
    score: float = Field(..., ge=0, le=1)
    suitability: str
    message: str = Field(..., description="Human-readable recommendation")


class AnalysisMeta(BaseModel):
    """Analysis metadata."""
    model_used: str = Field(..., description="LLM model used")
    total_businesses_nearby: int = Field(0, description="Total businesses analyzed")
    key_factors: List[str] = Field(default_factory=list)
    processing_time_ms: float = Field(0, description="Total processing time")


class LLMRecommendationResponse(BaseModel):
    """Full response from LLM recommendation endpoint."""
    grid_id: str
    recommendation: RecommendationOutput
    gym: CategoryRecommendation
    cafe: CategoryRecommendation
    analysis: AnalysisMeta

    class Config:
        json_schema_extra = {
            "example": {
                "grid_id": "Clifton-Block2-007-008",
                "recommendation": {
                    "best_category": "gym",
                    "score": 0.78,
                    "suitability": "good",
                    "message": "This location is GOOD for a GYM. Recommended with minor considerations."
                },
                "gym": {
                    "score": 0.78,
                    "suitability": "good",
                    "reasoning": "Strong office presence and limited gym competition make this ideal.",
                    "positive_factors": ["Nearby offices boost", "Good foot traffic"],
                    "concerns": ["Some competition in area"]
                },
                "cafe": {
                    "score": 0.62,
                    "suitability": "moderate",
                    "reasoning": "Moderate potential due to existing cafe density.",
                    "positive_factors": ["Restaurant area synergy"],
                    "concerns": ["Cafe saturation"]
                },
                "analysis": {
                    "model_used": "llama-3.3-70b-versatile",
                    "total_businesses_nearby": 45,
                    "key_factors": ["office workers", "limited competition"],
                    "processing_time_ms": 2340.5
                }
            }
        }


class BEVResponse(BaseModel):
    """BEV summary for debugging/transparency."""
    restaurant_count: int
    cafe_count: int
    gym_count: int
    office_count: int
    school_count: int
    avg_rating: float
    avg_reviews: float
    income_proxy: str
    mall_within_1km: bool
    university_within_2km: bool


class FullPipelineResponse(BaseModel):
    """Detailed response including BEV and all scores."""
    grid_id: str
    location: Dict[str, float]
    bev: BEVResponse
    rule_scores: Dict[str, float]
    llm_scores: Dict[str, float]
    final_scores: Dict[str, float]
    recommendation: RecommendationOutput
    timing: Dict[str, float]
    mode: str


# ============================================================================
# Dependencies
# ============================================================================

_pipeline_instance: Optional[RecommendationPipeline] = None

def get_pipeline() -> RecommendationPipeline:
    """Get or create the recommendation pipeline instance."""
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = RecommendationPipeline()
    return _pipeline_instance


# ============================================================================
# Endpoints
# ============================================================================

@router.get(
    "/recommendation_llm",
    response_model=LLMRecommendationResponse,
    summary="Get LLM-powered recommendation",
    description="""
    Get a full recommendation using the BEV → Rule Engine → LLM pipeline.
    
    This endpoint:
    1. Generates a Business Environment Vector (BEV) from Google Places
    2. Applies deterministic rule-based scoring
    3. Evaluates with Groq LLM for contextual reasoning
    4. Combines scores with weighted ensemble
    
    **Parameters:**
    - `lat`: Latitude of the location
    - `lon`: Longitude of the location
    - `grid_id`: Optional grid cell identifier
    - `radius`: Search radius in meters (default: 500)
    
    **Returns:**
    - Best category recommendation (gym or cafe)
    - Scores and reasoning for both categories
    - Key factors and concerns
    """
)
async def get_llm_recommendation(
    lat: float = Query(..., ge=-90, le=90, description="Latitude"),
    lon: float = Query(..., ge=-180, le=180, description="Longitude"),
    grid_id: Optional[str] = Query(None, description="Grid cell identifier"),
    radius: int = Query(500, ge=100, le=2000, description="Search radius in meters"),
    pipeline: RecommendationPipeline = Depends(get_pipeline)
) -> LLMRecommendationResponse:
    """Get LLM-powered recommendation for a location."""
    try:
        logger.info(f"LLM recommendation request: lat={lat}, lon={lon}")
        
        result = pipeline.recommend(
            lat=lat,
            lon=lon,
            grid_id=grid_id,
            radius_meters=radius,
            mode=PipelineMode.FULL
        )
        
        api_response = result.to_api_response()
        
        # Build response
        return LLMRecommendationResponse(
            grid_id=api_response["grid_id"],
            recommendation=RecommendationOutput(**api_response["recommendation"]),
            gym=CategoryRecommendation(**api_response["gym"]),
            cafe=CategoryRecommendation(**api_response["cafe"]),
            analysis=AnalysisMeta(
                **api_response["analysis"],
                processing_time_ms=result.total_time_ms
            )
        )
        
    except Exception as e:
        logger.error(f"LLM recommendation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/recommendation_fast",
    response_model=LLMRecommendationResponse,
    summary="Get fast rule-based recommendation",
    description="""
    Get a fast recommendation using only BEV and Rule Engine (no LLM).
    
    Much faster than /recommendation_llm but without LLM reasoning.
    Good for bulk processing or when LLM quota is limited.
    """
)
async def get_fast_recommendation(
    lat: float = Query(..., ge=-90, le=90, description="Latitude"),
    lon: float = Query(..., ge=-180, le=180, description="Longitude"),
    grid_id: Optional[str] = Query(None, description="Grid cell identifier"),
    radius: int = Query(500, ge=100, le=2000, description="Search radius in meters"),
    pipeline: RecommendationPipeline = Depends(get_pipeline)
) -> LLMRecommendationResponse:
    """Get fast rule-based recommendation for a location."""
    try:
        logger.info(f"Fast recommendation request: lat={lat}, lon={lon}")
        
        result = pipeline.recommend(
            lat=lat,
            lon=lon,
            grid_id=grid_id,
            radius_meters=radius,
            mode=PipelineMode.FAST
        )
        
        api_response = result.to_api_response()
        
        return LLMRecommendationResponse(
            grid_id=api_response["grid_id"],
            recommendation=RecommendationOutput(**api_response["recommendation"]),
            gym=CategoryRecommendation(**api_response["gym"]),
            cafe=CategoryRecommendation(**api_response["cafe"]),
            analysis=AnalysisMeta(
                **api_response["analysis"],
                processing_time_ms=result.total_time_ms
            )
        )
        
    except Exception as e:
        logger.error(f"Fast recommendation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/recommendation_debug",
    response_model=FullPipelineResponse,
    summary="Get detailed pipeline output",
    description="Full debugging output including BEV, all scores, and timing."
)
async def get_debug_recommendation(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    grid_id: Optional[str] = Query(None),
    radius: int = Query(500, ge=100, le=2000),
    mode: str = Query("full", regex="^(full|fast)$"),
    pipeline: RecommendationPipeline = Depends(get_pipeline)
) -> FullPipelineResponse:
    """Get detailed pipeline output for debugging."""
    try:
        pipeline_mode = PipelineMode.FULL if mode == "full" else PipelineMode.FAST
        
        result = pipeline.recommend(
            lat=lat,
            lon=lon,
            grid_id=grid_id,
            radius_meters=radius,
            mode=pipeline_mode
        )
        
        bev = result.bev
        
        return FullPipelineResponse(
            grid_id=result.grid_id,
            location={"lat": result.lat, "lon": result.lon, "radius": result.radius_meters},
            bev=BEVResponse(
                restaurant_count=bev.density.restaurants,
                cafe_count=bev.density.cafes,
                gym_count=bev.density.gyms,
                office_count=bev.density.offices,
                school_count=bev.density.schools,
                avg_rating=round(bev.economic.avg_business_rating, 2),
                avg_reviews=round(bev.economic.avg_review_count, 1),
                income_proxy=bev.economic.income_proxy,
                mall_within_1km=bev.distance.distance_to_mall > 0 and bev.distance.distance_to_mall <= 1000,
                university_within_2km=bev.distance.distance_to_university > 0 and bev.distance.distance_to_university <= 2000
            ),
            rule_scores={
                "gym": round(result.rule_result.gym_score, 4),
                "cafe": round(result.rule_result.cafe_score, 4)
            },
            llm_scores={
                "gym": round(result.llm_result.gym_probability, 4) if result.llm_result else 0,
                "cafe": round(result.llm_result.cafe_probability, 4) if result.llm_result else 0
            },
            final_scores={
                "gym": round(result.combined.gym.final_score, 4),
                "cafe": round(result.combined.cafe.final_score, 4)
            },
            recommendation=RecommendationOutput(
                best_category=result.combined.best_category,
                score=round(result.combined.best_score, 2),
                suitability=result.combined.best_suitability,
                message=result.combined._generate_message()
            ),
            timing={
                "bev_ms": round(result.bev_time_ms, 1),
                "rule_ms": round(result.rule_time_ms, 1),
                "llm_ms": round(result.llm_time_ms, 1),
                "combine_ms": round(result.combine_time_ms, 1),
                "total_ms": round(result.total_time_ms, 1)
            },
            mode=result.mode
        )
        
    except Exception as e:
        logger.error(f"Debug recommendation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/recommendation_batch",
    summary="Batch recommendations",
    description="Get recommendations for multiple locations at once."
)
async def get_batch_recommendations(
    locations: List[LocationInput],
    mode: str = Query("fast", regex="^(full|fast)$"),
    pipeline: RecommendationPipeline = Depends(get_pipeline)
) -> List[Dict[str, Any]]:
    """Get recommendations for multiple locations."""
    try:
        logger.info(f"Batch recommendation request: {len(locations)} locations")
        
        pipeline_mode = PipelineMode.FULL if mode == "full" else PipelineMode.FAST
        
        results = []
        for loc in locations:
            result = pipeline.recommend(
                lat=loc.lat,
                lon=loc.lon,
                grid_id=loc.grid_id,
                radius_meters=loc.radius_meters or 500,
                mode=pipeline_mode
            )
            results.append(result.to_api_response())
        
        return results
        
    except Exception as e:
        logger.error(f"Batch recommendation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
