"""
Grid Detail Router

GET /api/v1/grid/{grid_id} - Get detailed view of a single grid
"""

import logging
import json
from typing import List, Optional
from enum import Enum

from fastapi import APIRouter, HTTPException, Query, Path
from pydantic import BaseModel, Field

from src.database.connection import get_session
from src.database.models import GridCellModel, GridMetricsModel, BusinessModel

logger = logging.getLogger("startsmart.api.grid_detail")

router = APIRouter()


# ========== Enums ==========

class CategoryEnum(str, Enum):
    GYM = "Gym"
    CAFE = "Cafe"


# ========== Response Models ==========

class TopPost(BaseModel):
    """Social media post that influenced the score."""
    source: str
    text: str
    timestamp: Optional[str] = None
    link: Optional[str] = None


class Competitor(BaseModel):
    """Competing business in the area."""
    name: str
    distance_km: float
    rating: Optional[float] = None


class GridMetrics(BaseModel):
    """Detailed metrics for a grid."""
    business_count: int = 0
    instagram_volume: int = 0
    reddit_mentions: int = 0
    total_demand: int = 0
    demand_level: str = "Low"
    competition_level: str = "None"


class GridDetailResponse(BaseModel):
    """Detailed response for a single grid."""
    grid_id: str
    neighborhood: str
    lat_center: float
    lon_center: float
    lat_north: float
    lat_south: float
    lon_east: float
    lon_west: float
    gos: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    opportunity_level: str
    confidence_level: str
    rationale: Optional[str] = None
    metrics: GridMetrics
    top_posts: List[TopPost] = []
    competitors: List[Competitor] = []

    class Config:
        json_schema_extra = {
            "example": {
                "grid_id": "DHA-Phase2-Cell-07",
                "neighborhood": "DHA-Phase2",
                "lat_center": 24.8290,
                "lon_center": 67.0610,
                "lat_north": 24.8312,
                "lat_south": 24.8268,
                "lon_east": 67.0645,
                "lon_west": 67.0575,
                "gos": 0.820,
                "confidence": 0.750,
                "opportunity_level": "High",
                "confidence_level": "Good",
                "rationale": "High demand with low competition makes this an excellent location.",
                "metrics": {
                    "business_count": 2,
                    "instagram_volume": 48,
                    "reddit_mentions": 7,
                    "total_demand": 55,
                    "demand_level": "High",
                    "competition_level": "Low"
                },
                "top_posts": [
                    {
                        "source": "reddit",
                        "text": "We need a proper gym in Phase 2...",
                        "timestamp": "2025-10-15T14:30:00Z",
                        "link": "https://reddit.com/r/Karachi/comments/abc123"
                    }
                ],
                "competitors": [
                    {"name": "FitZone Personal Training", "distance_km": 0.3, "rating": 3.8}
                ]
            }
        }


# ========== Helper Functions ==========

def get_opportunity_level(gos: float) -> str:
    """Get opportunity level label from GOS."""
    if gos >= 0.75:
        return "High"
    elif gos >= 0.5:
        return "Medium"
    else:
        return "Low"


def get_confidence_level(confidence: float) -> str:
    """Get confidence level label."""
    if confidence >= 0.7:
        return "High"
    elif confidence >= 0.4:
        return "Good"
    else:
        return "Low"


def get_demand_level(total_demand: int) -> str:
    """Get demand level label."""
    if total_demand >= 100:
        return "Very High"
    elif total_demand >= 50:
        return "High"
    elif total_demand >= 20:
        return "Medium"
    else:
        return "Low"


def get_competition_level(business_count: int) -> str:
    """Get competition level label."""
    if business_count == 0:
        return "None"
    elif business_count <= 2:
        return "Low"
    elif business_count <= 5:
        return "Medium"
    else:
        return "High"


def parse_top_posts(top_posts_json) -> List[TopPost]:
    """Parse top_posts_json field to list of TopPost objects.
    
    Handles both JSON string and already-parsed list (SQLAlchemy auto-deserialize).
    """
    if not top_posts_json:
        return []
    
    try:
        # If already a list (SQLAlchemy auto-deserialized), use directly
        if isinstance(top_posts_json, list):
            posts_data = top_posts_json
        else:
            # Parse JSON string
            posts_data = json.loads(top_posts_json)
        
        if isinstance(posts_data, list):
            return [
                TopPost(
                    source=post.get("source", "unknown"),
                    text=post.get("text", ""),
                    timestamp=post.get("timestamp"),
                    link=post.get("link")
                )
                for post in posts_data[:5]  # Limit to 5 posts
            ]
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning(f"Failed to parse top_posts_json: {e}")
    
    return []


def parse_competitors(competitors_json) -> List[Competitor]:
    """Parse competitors_json field to list of Competitor objects.
    
    Handles both JSON string and already-parsed list (SQLAlchemy auto-deserialize).
    """
    if not competitors_json:
        return []
    
    try:
        # If already a list (SQLAlchemy auto-deserialized), use directly
        if isinstance(competitors_json, list):
            competitors_data = competitors_json
        else:
            # Parse JSON string
            competitors_data = json.loads(competitors_json)
        
        if isinstance(competitors_data, list):
            return [
                Competitor(
                    name=comp.get("name", "Unknown"),
                    distance_km=comp.get("distance_km", 0.0),
                    rating=comp.get("rating")
                )
                for comp in competitors_data[:10]  # Limit to 10 competitors
            ]
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning(f"Failed to parse competitors_json: {e}")
    
    return []


def generate_rationale(metrics: GridMetricsModel) -> str:
    """Generate detailed rationale for the grid."""
    business_count = metrics.business_count or 0
    instagram_volume = metrics.instagram_volume or 0
    reddit_mentions = metrics.reddit_mentions or 0
    gos = float(metrics.gos) if metrics.gos else 0.5
    
    total_demand = instagram_volume + reddit_mentions
    
    parts = []
    
    # Opportunity summary
    if gos >= 0.75:
        parts.append("This location shows excellent potential for a new business.")
    elif gos >= 0.5:
        parts.append("This location has good potential for a new business.")
    else:
        parts.append("This location has limited potential currently.")
    
    # Demand analysis
    if total_demand >= 50:
        parts.append(f"Strong demand signals detected with {total_demand} social media mentions.")
    elif total_demand >= 20:
        parts.append(f"Moderate demand with {total_demand} social media mentions.")
    else:
        parts.append(f"Limited social media activity ({total_demand} mentions).")
    
    # Competition analysis
    if business_count == 0:
        parts.append("No existing competitors in this area presents a first-mover advantage.")
    elif business_count <= 2:
        parts.append(f"Low competition with only {business_count} existing business(es).")
    else:
        parts.append(f"Consider the {business_count} existing competitors in this area.")
    
    return " ".join(parts)


# ========== Endpoints ==========

@router.get(
    "/grid/{grid_id}",
    response_model=GridDetailResponse,
    summary="Get detailed view of single grid",
    description="""
Returns comprehensive details for a specific grid cell, including:
- Computed metrics (business count, social volume, GOS, confidence)
- Top social media posts that influenced the score
- List of competing businesses in the area
    """,
    responses={
        200: {"description": "Successfully retrieved grid details"},
        404: {"description": "Grid not found"}
    }
)
async def get_grid_detail(
    grid_id: str = Path(
        ...,
        description="Grid cell identifier",
        example="DHA-Phase2-Cell-07"
    ),
    category: CategoryEnum = Query(
        ...,
        description="Business category for context",
        example="Gym"
    )
) -> GridDetailResponse:
    """
    Get detailed information for a specific grid.
    
    Args:
        grid_id: Grid cell identifier
        category: Business category for metrics context
        
    Returns:
        Detailed grid information with metrics, posts, and competitors
    """
    try:
        with get_session() as session:
            # Query grid cell
            grid_cell = (
                session.query(GridCellModel)
                .filter(GridCellModel.grid_id == grid_id)
                .first()
            )
            
            if not grid_cell:
                raise HTTPException(
                    status_code=404,
                    detail=f"Grid '{grid_id}' not found"
                )
            
            # Query metrics for this grid and category
            metrics = (
                session.query(GridMetricsModel)
                .filter(
                    GridMetricsModel.grid_id == grid_id,
                    GridMetricsModel.category == category.value
                )
                .first()
            )
            
            # Build response
            gos_value = float(metrics.gos) if metrics else 0.5
            confidence_value = float(metrics.confidence) if metrics else 0.5
            business_count = metrics.business_count if metrics else 0
            instagram_volume = metrics.instagram_volume if metrics else 0
            reddit_mentions = metrics.reddit_mentions if metrics else 0
            total_demand = instagram_volume + reddit_mentions
            
            # Parse JSON fields
            top_posts = parse_top_posts(metrics.top_posts_json if metrics else None)
            competitors = parse_competitors(metrics.competitors_json if metrics else None)
            
            # If no competitors from JSON, try to get from businesses table
            if not competitors and metrics:
                businesses = (
                    session.query(BusinessModel)
                    .filter(
                        BusinessModel.grid_id == grid_id,
                        BusinessModel.category == category.value
                    )
                    .limit(10)
                    .all()
                )
                competitors = [
                    Competitor(
                        name=b.name,
                        distance_km=0.1,  # Approximate since in same grid
                        rating=float(b.rating) if b.rating else None
                    )
                    for b in businesses
                ]
            
            response = GridDetailResponse(
                grid_id=grid_cell.grid_id,
                neighborhood=grid_cell.neighborhood,
                lat_center=float(grid_cell.lat_center),
                lon_center=float(grid_cell.lon_center),
                lat_north=float(grid_cell.lat_north),
                lat_south=float(grid_cell.lat_south),
                lon_east=float(grid_cell.lon_east),
                lon_west=float(grid_cell.lon_west),
                gos=round(gos_value, 3),
                confidence=round(confidence_value, 3),
                opportunity_level=get_opportunity_level(gos_value),
                confidence_level=get_confidence_level(confidence_value),
                rationale=generate_rationale(metrics) if metrics else None,
                metrics=GridMetrics(
                    business_count=business_count,
                    instagram_volume=instagram_volume,
                    reddit_mentions=reddit_mentions,
                    total_demand=total_demand,
                    demand_level=get_demand_level(total_demand),
                    competition_level=get_competition_level(business_count)
                ),
                top_posts=top_posts,
                competitors=competitors
            )
            
            logger.info(f"Returning details for grid {grid_id}/{category.value}")
            return response
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching grid detail: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve grid details"
        )
