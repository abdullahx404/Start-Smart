"""
Grids Router (DATABASE DISABLED)

GET /api/v1/grids - Returns empty grid list (database disabled for serverless)
"""

import logging
from typing import List, Optional
from enum import Enum

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Database disabled for serverless deployment
# from src.database.connection import get_session
# from src.database.models import GridCellModel, GridMetricsModel

logger = logging.getLogger("startsmart.api.grids")

router = APIRouter()


# ========== Enums ==========

class CategoryEnum(str, Enum):
    GYM = "Gym"
    CAFE = "Cafe"


# ========== Response Models ==========

class GridSummaryResponse(BaseModel):
    """Response model for a grid cell summary."""
    grid_id: str
    neighborhood: str
    lat_center: float
    lon_center: float
    lat_north: float
    lat_south: float
    lon_east: float
    lon_west: float
    gos: float = Field(..., ge=0.0, le=1.0, description="Gap Opportunity Score")
    confidence: float = Field(..., ge=0.0, le=1.0)
    business_count: int = 0
    instagram_volume: int = 0
    reddit_mentions: int = 0

    class Config:
        json_schema_extra = {
            "example": {
                "grid_id": "DHA-Phase2-Cell-01",
                "neighborhood": "DHA-Phase2",
                "lat_center": 24.8278,
                "lon_center": 67.0595,
                "lat_north": 24.8300,
                "lat_south": 24.8256,
                "lon_east": 67.0620,
                "lon_west": 67.0570,
                "gos": 0.820,
                "confidence": 0.750,
                "business_count": 2,
                "instagram_volume": 48,
                "reddit_mentions": 7
            }
        }


# ========== Endpoints ==========

@router.get(
    "/grids",
    response_model=List[GridSummaryResponse],
    summary="Get all grids for neighborhood + category",
    description="""
Returns all grid cells within a neighborhood along with their
Gap Opportunity Scores (GOS) for the specified category.

Use this endpoint to power heatmap visualizations.
    """,
    responses={
        200: {"description": "Successfully retrieved grid data"},
        400: {"description": "Invalid parameters"},
        404: {"description": "Neighborhood not found"}
    }
)
async def get_grids(
    neighborhood: str = Query(
        ...,
        description="Neighborhood ID (e.g., 'DHA-Phase2')",
        example="DHA-Phase2"
    ),
    category: CategoryEnum = Query(
        ...,
        description="Business category",
        example="Gym"
    )
) -> List[GridSummaryResponse]:
    """
    Get all grids for a neighborhood and category.
    
    NOTE: Database disabled for serverless deployment.
    Returns empty list - use /recommendation_llm endpoint for live data.
    """
    logger.info(f"Grids endpoint called for {neighborhood}/{category.value}")
    logger.info("🚫 Database disabled - returning empty grid list")
    logger.info("💡 Use /recommendation_llm endpoint for live location analysis")
    
    # Return empty list - database is disabled
    # The frontend should use /recommendation_llm for live analysis
    return []
