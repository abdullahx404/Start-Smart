"""
Grids Router

GET /api/v1/grids - Get all grids for neighborhood + category
"""

import logging
from typing import List, Optional
from enum import Enum

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src.database.connection import get_session
from src.database.models import GridCellModel, GridMetricsModel

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
    
    Args:
        neighborhood: Neighborhood ID to filter by
        category: Business category (Gym or Cafe)
        
    Returns:
        List of grid cells with GOS and metrics
    """
    try:
        with get_session() as session:
            # First check if neighborhood exists
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
            
            # Join grid_cells with grid_metrics
            results = (
                session.query(GridCellModel, GridMetricsModel)
                .outerjoin(
                    GridMetricsModel,
                    (GridCellModel.grid_id == GridMetricsModel.grid_id) &
                    (GridMetricsModel.category == category.value)
                )
                .filter(GridCellModel.neighborhood == neighborhood)
                .order_by(GridCellModel.grid_id)
                .all()
            )
            
            grids = []
            for grid_cell, metrics in results:
                grids.append(
                    GridSummaryResponse(
                        grid_id=grid_cell.grid_id,
                        neighborhood=grid_cell.neighborhood,
                        lat_center=float(grid_cell.lat_center),
                        lon_center=float(grid_cell.lon_center),
                        lat_north=float(grid_cell.lat_north),
                        lat_south=float(grid_cell.lat_south),
                        lon_east=float(grid_cell.lon_east),
                        lon_west=float(grid_cell.lon_west),
                        gos=float(metrics.gos) if metrics else 0.5,
                        confidence=float(metrics.confidence) if metrics else 0.5,
                        business_count=metrics.business_count if metrics else 0,
                        instagram_volume=metrics.instagram_volume if metrics else 0,
                        reddit_mentions=metrics.reddit_mentions if metrics else 0
                    )
                )
            
            logger.info(
                f"Returning {len(grids)} grids for {neighborhood}/{category.value}"
            )
            
            # Add cache headers
            response = JSONResponse(
                content=[g.model_dump() for g in grids],
                headers={"Cache-Control": "max-age=3600"}  # 1 hour cache
            )
            return grids
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching grids: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve grids"
        )
