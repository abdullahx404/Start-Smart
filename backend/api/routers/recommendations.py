"""
Recommendations Router

GET /api/v1/recommendations - Get top-N recommendations for neighborhood + category
"""

import logging
from typing import List, Optional
from enum import Enum

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from src.database.connection import get_session
from src.database.models import GridCellModel, GridMetricsModel

logger = logging.getLogger("startsmart.api.recommendations")

router = APIRouter()


# ========== Enums ==========

class CategoryEnum(str, Enum):
    GYM = "Gym"
    CAFE = "Cafe"


# ========== Response Models ==========

class RecommendationItem(BaseModel):
    """Single recommendation item."""
    grid_id: str
    rank: int
    gos: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    rationale: str
    lat_center: float
    lon_center: float
    business_count: int = 0
    instagram_volume: int = 0
    reddit_mentions: int = 0


class RecommendationsResponse(BaseModel):
    """Response model for recommendations endpoint."""
    neighborhood: str
    category: str
    recommendations: List[RecommendationItem]

    class Config:
        json_schema_extra = {
            "example": {
                "neighborhood": "DHA-Phase2",
                "category": "Gym",
                "recommendations": [
                    {
                        "grid_id": "DHA-Phase2-Cell-07",
                        "rank": 1,
                        "gos": 0.820,
                        "confidence": 0.750,
                        "rationale": "High demand (48 Instagram posts, 7 Reddit mentions), low competition (2 gyms)",
                        "lat_center": 24.8290,
                        "lon_center": 67.0610,
                        "business_count": 2,
                        "instagram_volume": 48,
                        "reddit_mentions": 7
                    }
                ]
            }
        }


# ========== Helper Functions ==========

def generate_rationale(metrics: GridMetricsModel) -> str:
    """
    Generate human-readable rationale for a recommendation.
    
    Args:
        metrics: GridMetricsModel with scoring data
        
    Returns:
        String explaining why this location is recommended
    """
    business_count = metrics.business_count or 0
    instagram_volume = metrics.instagram_volume or 0
    reddit_mentions = metrics.reddit_mentions or 0
    gos = float(metrics.gos) if metrics.gos else 0.5
    
    parts = []
    
    # Demand analysis
    total_demand = instagram_volume + reddit_mentions
    if total_demand >= 100:
        parts.append(f"Very high demand ({instagram_volume} Instagram posts, {reddit_mentions} Reddit mentions)")
    elif total_demand >= 50:
        parts.append(f"High demand ({instagram_volume} Instagram posts, {reddit_mentions} Reddit mentions)")
    elif total_demand >= 20:
        parts.append(f"Moderate demand ({total_demand} social mentions)")
    else:
        parts.append(f"Growing demand ({total_demand} social mentions)")
    
    # Competition analysis
    if business_count == 0:
        parts.append("no existing competitors")
    elif business_count == 1:
        parts.append("minimal competition (1 business)")
    elif business_count <= 3:
        parts.append(f"low competition ({business_count} businesses)")
    else:
        parts.append(f"{business_count} existing competitors")
    
    # GOS summary
    if gos >= 0.8:
        opportunity = "Excellent opportunity"
    elif gos >= 0.6:
        opportunity = "Good opportunity"
    else:
        opportunity = "Potential opportunity"
    
    return f"{opportunity}: {', '.join(parts)}"


# ========== Endpoints ==========

@router.get(
    "/recommendations",
    response_model=RecommendationsResponse,
    summary="Get top-N recommendations",
    description="""
Returns the top-ranked location recommendations for a given
neighborhood and category, sorted by Gap Opportunity Score (GOS).

Each recommendation includes:
- GOS score (0.0 - 1.0)
- Confidence score (0.0 - 1.0)
- Human-readable rationale explaining the score
    """,
    responses={
        200: {"description": "Successfully retrieved recommendations"},
        400: {"description": "Invalid parameters"},
        404: {"description": "No recommendations found"}
    }
)
async def get_recommendations(
    neighborhood: str = Query(
        ...,
        description="Neighborhood ID",
        example="DHA-Phase2"
    ),
    category: CategoryEnum = Query(
        ...,
        description="Business category",
        example="Gym"
    ),
    limit: int = Query(
        default=3,
        ge=1,
        le=10,
        description="Maximum number of recommendations"
    )
) -> RecommendationsResponse:
    """
    Get top recommendations for a neighborhood and category.
    
    Args:
        neighborhood: Neighborhood ID to filter by
        category: Business category (Gym or Cafe)
        limit: Maximum recommendations to return (default 3, max 10)
        
    Returns:
        Top recommendations sorted by GOS descending
    """
    try:
        with get_session() as session:
            # Check if neighborhood exists
            neighborhood_exists = (
                session.query(GridCellModel)
                .filter(GridCellModel.neighborhood == neighborhood)
                .first()
            )
            
            if not neighborhood_exists:
                raise HTTPException(
                    status_code=404,
                    detail=f"Neighborhood '{neighborhood}' not found"
                )
            
            # Query top grids by GOS
            results = (
                session.query(GridCellModel, GridMetricsModel)
                .join(
                    GridMetricsModel,
                    (GridCellModel.grid_id == GridMetricsModel.grid_id) &
                    (GridMetricsModel.category == category.value)
                )
                .filter(GridCellModel.neighborhood == neighborhood)
                .order_by(GridMetricsModel.gos.desc())
                .limit(limit)
                .all()
            )
            
            if not results:
                # Return empty recommendations if no scored grids
                logger.warning(
                    f"No scored grids found for {neighborhood}/{category.value}"
                )
                return RecommendationsResponse(
                    neighborhood=neighborhood,
                    category=category.value,
                    recommendations=[]
                )
            
            recommendations = []
            for rank, (grid_cell, metrics) in enumerate(results, 1):
                recommendations.append(
                    RecommendationItem(
                        grid_id=grid_cell.grid_id,
                        rank=rank,
                        gos=round(float(metrics.gos), 3),
                        confidence=round(float(metrics.confidence), 3),
                        rationale=generate_rationale(metrics),
                        lat_center=float(grid_cell.lat_center),
                        lon_center=float(grid_cell.lon_center),
                        business_count=metrics.business_count or 0,
                        instagram_volume=metrics.instagram_volume or 0,
                        reddit_mentions=metrics.reddit_mentions or 0
                    )
                )
            
            logger.info(
                f"Returning {len(recommendations)} recommendations for "
                f"{neighborhood}/{category.value}, top GOS: {recommendations[0].gos}"
            )
            
            return RecommendationsResponse(
                neighborhood=neighborhood,
                category=category.value,
                recommendations=recommendations
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching recommendations: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve recommendations"
        )
