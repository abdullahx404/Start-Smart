"""
Neighborhoods Router

GET /api/v1/neighborhoods - List all available neighborhoods
"""

import logging
from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.database.connection import get_session
from src.database.models import GridCellModel

logger = logging.getLogger("startsmart.api.neighborhoods")

router = APIRouter()


# ========== Response Models ==========

class NeighborhoodResponse(BaseModel):
    """Response model for a neighborhood."""
    id: str
    name: str
    grid_count: int

    class Config:
        json_schema_extra = {
            "example": {
                "id": "DHA-Phase2",
                "name": "DHA Phase 2",
                "grid_count": 9
            }
        }


# ========== Helper Functions ==========

def format_neighborhood_name(neighborhood_id: str) -> str:
    """
    Convert neighborhood ID to display name.
    
    Examples:
        "DHA-Phase2" -> "DHA Phase 2"
        "Clifton-Block2" -> "Clifton Block 2"
    """
    # Common replacements
    name = neighborhood_id.replace("-", " ")
    
    # Handle special cases
    name = name.replace("Phase ", "Phase ")
    name = name.replace("Block ", "Block ")
    
    return name


# ========== Endpoints ==========

@router.get(
    "/neighborhoods",
    response_model=List[NeighborhoodResponse],
    summary="List all available neighborhoods",
    description="""
Returns all neighborhoods currently supported by the platform.
Each neighborhood is subdivided into ~0.5 km² grid cells.
    """,
    responses={
        200: {
            "description": "Successfully retrieved neighborhood list",
            "content": {
                "application/json": {
                    "example": [
                        {"id": "DHA-Phase2", "name": "DHA Phase 2", "grid_count": 9},
                        {"id": "Clifton-Block2", "name": "Clifton Block 2", "grid_count": 9},
                    ]
                }
            }
        },
        500: {"description": "Internal server error"}
    }
)
async def list_neighborhoods() -> List[NeighborhoodResponse]:
    """
    Get all neighborhoods with grid counts.
    
    Returns:
        List of neighborhoods with their IDs, display names, and grid counts.
    """
    try:
        with get_session() as session:
            # Query distinct neighborhoods with grid counts
            from sqlalchemy import func
            
            results = (
                session.query(
                    GridCellModel.neighborhood,
                    func.count(GridCellModel.grid_id).label("grid_count")
                )
                .group_by(GridCellModel.neighborhood)
                .order_by(GridCellModel.neighborhood)
                .all()
            )
            
            neighborhoods = []
            for neighborhood_id, grid_count in results:
                neighborhoods.append(
                    NeighborhoodResponse(
                        id=neighborhood_id,
                        name=format_neighborhood_name(neighborhood_id),
                        grid_count=grid_count
                    )
                )
            
            logger.info(f"Returning {len(neighborhoods)} neighborhoods")
            return neighborhoods
            
    except Exception as e:
        logger.error(f"Error fetching neighborhoods: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve neighborhoods"
        )
