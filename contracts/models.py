"""
StartSmart MVP - Data Models Contract
Phase 0: Interface Contracts

This module defines all Pydantic models used across the backend.
These models are LOCKED for MVP - no modifications in later phases.

Models serve three purposes:
1. Database ORM mapping (via SQLAlchemy)
2. API request/response validation
3. Type safety across all Python code

All models use Pydantic v2 syntax with strict type hints.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ============================================================================
# Enums - Standardized Categories and Types
# ============================================================================

class Category(str, Enum):
    """Business categories supported by the MVP."""
    GYM = "Gym"
    CAFE = "Cafe"
    
    def __str__(self) -> str:
        return self.value


class Source(str, Enum):
    """Data source identifiers for businesses and social posts."""
    GOOGLE_PLACES = "google_places"
    INSTAGRAM = "instagram"
    REDDIT = "reddit"
    SIMULATED = "simulated"
    
    def __str__(self) -> str:
        return self.value


class PostType(str, Enum):
    """Types of social media posts for demand signal classification."""
    DEMAND = "demand"        # Explicit request for a service
    COMPLAINT = "complaint"  # Complaint about lack of service
    MENTION = "mention"      # General mention or discussion
    
    def __str__(self) -> str:
        return self.value


# ============================================================================
# Database Models - Match database_schema.sql exactly
# ============================================================================

class GridCell(BaseModel):
    """
    Represents a geographic grid cell (~0.5 km²).
    
    Grid cells are static for MVP, computed once during Phase 0.
    Each cell covers a portion of a pilot neighborhood.
    """
    grid_id: str = Field(..., description="Unique grid identifier (e.g., 'DHA-Phase2-Cell-01')")
    neighborhood: str = Field(..., description="Parent neighborhood name")
    lat_center: float = Field(..., ge=-90, le=90, description="Latitude of grid center")
    lon_center: float = Field(..., ge=-180, le=180, description="Longitude of grid center")
    lat_north: float = Field(..., ge=-90, le=90, description="Northern boundary latitude")
    lat_south: float = Field(..., ge=-90, le=90, description="Southern boundary latitude")
    lon_east: float = Field(..., ge=-180, le=180, description="Eastern boundary longitude")
    lon_west: float = Field(..., ge=-180, le=180, description="Western boundary longitude")
    area_km2: float = Field(default=0.5, gt=0, description="Grid area in square kilometers")
    created_at: Optional[datetime] = Field(default=None, description="Timestamp of grid creation")
    
    class Config:
        from_attributes = True  # Enable ORM mode for SQLAlchemy
        json_schema_extra = {
            "example": {
                "grid_id": "DHA-Phase2-Cell-07",
                "neighborhood": "DHA Phase 2",
                "lat_center": 24.8290,
                "lon_center": 67.0610,
                "lat_north": 24.8320,
                "lat_south": 24.8260,
                "lon_east": 67.0640,
                "lon_west": 67.0580,
                "area_km2": 0.5
            }
        }


class Business(BaseModel):
    """
    Represents a business location (from Google Places API).
    
    Primary data source for supply-side metrics.
    Each business is assigned to a grid cell via point-in-polygon logic.
    """
    business_id: str = Field(..., description="Unique business identifier")
    name: str = Field(..., min_length=1, max_length=255, description="Business name")
    lat: float = Field(..., ge=-90, le=90, description="Business latitude")
    lon: float = Field(..., ge=-180, le=180, description="Business longitude")
    category: Category = Field(..., description="Business category")
    rating: Optional[float] = Field(default=None, ge=0.0, le=5.0, description="Google Places rating (0.0-5.0)")
    review_count: int = Field(default=0, ge=0, description="Number of reviews")
    source: Source = Field(default=Source.GOOGLE_PLACES, description="Data source identifier")
    grid_id: Optional[str] = Field(default=None, description="Assigned grid cell ID")
    fetched_at: datetime = Field(default_factory=datetime.utcnow, description="Data fetch timestamp")
    
    @field_validator('rating')
    @classmethod
    def validate_rating(cls, v: Optional[float]) -> Optional[float]:
        """Ensure rating is within valid range or None."""
        if v is not None and not (0.0 <= v <= 5.0):
            raise ValueError('Rating must be between 0.0 and 5.0')
        return v
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "business_id": "ChIJN1t_tDeuEmsRUsoyG83frY4",
                "name": "FitZone Personal Training",
                "lat": 24.8285,
                "lon": 67.0605,
                "category": "Gym",
                "rating": 3.8,
                "review_count": 42,
                "source": "google_places",
                "grid_id": "DHA-Phase2-Cell-07",
                "fetched_at": "2025-11-05T10:30:00Z"
            }
        }


class SocialPost(BaseModel):
    """
    Represents a social media post or mention.
    
    For MVP: primarily synthetic data (is_simulated=True).
    Post-MVP: real Instagram/Reddit data via scraping/API.
    Used for demand-side signal detection.
    """
    post_id: str = Field(..., description="Unique post identifier")
    source: Source = Field(..., description="Data source (instagram, reddit, simulated)")
    text: Optional[str] = Field(default=None, description="Post content or excerpt")
    timestamp: datetime = Field(..., description="Post creation timestamp")
    lat: Optional[float] = Field(default=None, ge=-90, le=90, description="Post latitude (if geotagged)")
    lon: Optional[float] = Field(default=None, ge=-180, le=180, description="Post longitude (if geotagged)")
    grid_id: Optional[str] = Field(default=None, description="Assigned grid cell ID")
    post_type: Optional[PostType] = Field(default=None, description="Post classification (demand/complaint/mention)")
    engagement_score: int = Field(default=0, ge=0, description="Engagement metric (likes, upvotes, etc.)")
    is_simulated: bool = Field(default=False, description="True if synthetic data, False if real")
    created_at: Optional[datetime] = Field(default=None, description="Database insertion timestamp")
    
    @field_validator('lat', 'lon')
    @classmethod
    def validate_coordinates(cls, v: Optional[float], info) -> Optional[float]:
        """Ensure lat/lon are both present or both None."""
        # This validator ensures coordinate pairs are consistent
        return v
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "post_id": "sim_post_001",
                "source": "simulated",
                "text": "We need a proper gym in Phase 2, all we have is tiny PT places",
                "timestamp": "2025-10-15T14:30:00Z",
                "lat": 24.8290,
                "lon": 67.0610,
                "grid_id": "DHA-Phase2-Cell-07",
                "post_type": "demand",
                "engagement_score": 15,
                "is_simulated": True
            }
        }


class GridMetrics(BaseModel):
    """
    Computed metrics and Gap Opportunity Score (GOS) for a grid cell.
    
    Generated by scoring engine (Phase 2).
    One record per (grid_id, category) combination.
    Contains all data needed to explain a recommendation.
    """
    grid_id: str = Field(..., description="Grid cell identifier")
    category: Category = Field(..., description="Business category")
    business_count: int = Field(default=0, ge=0, description="Number of competing businesses")
    instagram_volume: int = Field(default=0, ge=0, description="Instagram posts in last 90 days")
    reddit_mentions: int = Field(default=0, ge=0, description="Reddit mentions (demand + complaints)")
    gos: float = Field(..., ge=0.0, le=1.0, description="Gap Opportunity Score (0.0-1.0)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0.0-1.0)")
    top_posts_json: Optional[Dict[str, Any]] = Field(default=None, description="Top 3 posts as JSON")
    competitors_json: Optional[Dict[str, Any]] = Field(default=None, description="Competitor list as JSON")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Last computation timestamp")
    
    @field_validator('gos', 'confidence')
    @classmethod
    def validate_scores(cls, v: float) -> float:
        """Ensure scores are within valid range [0.0, 1.0]."""
        if not (0.0 <= v <= 1.0):
            raise ValueError('Score must be between 0.0 and 1.0')
        return v
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "grid_id": "DHA-Phase2-Cell-07",
                "category": "Gym",
                "business_count": 2,
                "instagram_volume": 48,
                "reddit_mentions": 7,
                "gos": 0.820,
                "confidence": 0.750,
                "top_posts_json": {
                    "posts": [
                        {
                            "source": "reddit",
                            "text": "We need a proper gym in Phase 2",
                            "timestamp": "2025-10-15T14:30:00Z"
                        }
                    ]
                },
                "competitors_json": {
                    "businesses": [
                        {
                            "name": "FitZone Personal Training",
                            "distance_km": 0.3
                        }
                    ]
                },
                "last_updated": "2025-11-05T12:00:00Z"
            }
        }


# ============================================================================
# API Response Models - Used by FastAPI endpoints
# ============================================================================

class NeighborhoodResponse(BaseModel):
    """Response model for /neighborhoods endpoint."""
    id: str = Field(..., description="Neighborhood identifier")
    name: str = Field(..., description="Human-readable neighborhood name")
    grid_count: int = Field(..., ge=0, description="Number of grid cells in neighborhood")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "DHA-Phase2",
                "name": "DHA Phase 2",
                "grid_count": 12
            }
        }


class GridSummaryResponse(BaseModel):
    """Response model for /grids endpoint (heatmap data)."""
    grid_id: str = Field(..., description="Grid cell identifier")
    lat_center: float = Field(..., ge=-90, le=90, description="Grid center latitude")
    lon_center: float = Field(..., ge=-180, le=180, description="Grid center longitude")
    gos: float = Field(..., ge=0.0, le=1.0, description="Gap Opportunity Score")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    
    class Config:
        json_schema_extra = {
            "example": {
                "grid_id": "DHA-Phase2-Cell-07",
                "lat_center": 24.8290,
                "lon_center": 67.0610,
                "gos": 0.820,
                "confidence": 0.750
            }
        }


class RecommendationResponse(BaseModel):
    """Response model for individual recommendation in /recommendations endpoint."""
    grid_id: str = Field(..., description="Grid cell identifier")
    gos: float = Field(..., ge=0.0, le=1.0, description="Gap Opportunity Score")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    rationale: str = Field(..., description="Human-readable explanation of score")
    lat_center: float = Field(..., ge=-90, le=90, description="Grid center latitude")
    lon_center: float = Field(..., ge=-180, le=180, description="Grid center longitude")
    
    class Config:
        json_schema_extra = {
            "example": {
                "grid_id": "DHA-Phase2-Cell-07",
                "gos": 0.820,
                "confidence": 0.750,
                "rationale": "High demand (48 posts), low competition (2 gyms)",
                "lat_center": 24.8290,
                "lon_center": 67.0610
            }
        }


class TopPostDetail(BaseModel):
    """Detail model for social posts in grid detail response."""
    source: str = Field(..., description="Data source identifier")
    text: str = Field(..., description="Post content or excerpt")
    timestamp: str = Field(..., description="ISO 8601 timestamp")
    link: Optional[str] = Field(default=None, description="URL to original post (if available)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "source": "reddit",
                "text": "We need a proper gym in Phase 2, all we have is tiny PT places",
                "timestamp": "2025-10-15T14:30:00Z",
                "link": "https://reddit.com/r/Karachi/comments/abc123"
            }
        }


class CompetitorDetail(BaseModel):
    """Detail model for competing businesses in grid detail response."""
    name: str = Field(..., description="Business name")
    distance_km: float = Field(..., ge=0, description="Distance from grid center in km")
    rating: Optional[float] = Field(default=None, ge=0.0, le=5.0, description="Google Places rating")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "FitZone Personal Training",
                "distance_km": 0.3,
                "rating": 3.8
            }
        }


class GridDetailResponse(BaseModel):
    """Response model for /grid/{grid_id} endpoint (detailed view)."""
    grid_id: str = Field(..., description="Grid cell identifier")
    gos: float = Field(..., ge=0.0, le=1.0, description="Gap Opportunity Score")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    metrics: Dict[str, int] = Field(..., description="Raw metrics (business_count, instagram_volume, reddit_mentions)")
    top_posts: List[TopPostDetail] = Field(..., description="Top 3 social posts that influenced score")
    competitors: List[CompetitorDetail] = Field(..., description="List of competing businesses")
    
    class Config:
        json_schema_extra = {
            "example": {
                "grid_id": "DHA-Phase2-Cell-07",
                "gos": 0.820,
                "confidence": 0.750,
                "metrics": {
                    "business_count": 2,
                    "instagram_volume": 48,
                    "reddit_mentions": 7
                },
                "top_posts": [
                    {
                        "source": "reddit",
                        "text": "We need a proper gym in Phase 2",
                        "timestamp": "2025-10-15T14:30:00Z",
                        "link": "https://reddit.com/r/Karachi/comments/abc123"
                    }
                ],
                "competitors": [
                    {
                        "name": "FitZone Personal Training",
                        "distance_km": 0.3,
                        "rating": 3.8
                    }
                ]
            }
        }


class RecommendationsListResponse(BaseModel):
    """Response model for /recommendations endpoint (top-N list)."""
    neighborhood: str = Field(..., description="Neighborhood identifier")
    category: str = Field(..., description="Business category")
    recommendations: List[RecommendationResponse] = Field(..., description="Ordered list (highest GOS first)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "neighborhood": "DHA-Phase2",
                "category": "Gym",
                "recommendations": [
                    {
                        "grid_id": "DHA-Phase2-Cell-07",
                        "gos": 0.820,
                        "confidence": 0.750,
                        "rationale": "High demand (48 posts), low competition (2 gyms)",
                        "lat_center": 24.8290,
                        "lon_center": 67.0610
                    }
                ]
            }
        }


class FeedbackRequest(BaseModel):
    """Request model for POST /feedback endpoint."""
    grid_id: str = Field(..., description="Grid cell being rated")
    category: Category = Field(..., description="Business category context")
    rating: int = Field(..., description="User rating (-1 or 1)")
    comment: Optional[str] = Field(default=None, max_length=1000, description="Optional text feedback")
    user_email: Optional[str] = Field(default=None, description="Optional email for follow-up")
    
    @field_validator('rating')
    @classmethod
    def validate_rating_value(cls, v: int) -> int:
        """Ensure rating is either -1 (thumbs down) or 1 (thumbs up)."""
        if v not in (-1, 1):
            raise ValueError('Rating must be -1 (thumbs down) or 1 (thumbs up)')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "grid_id": "DHA-Phase2-Cell-07",
                "category": "Gym",
                "rating": 1,
                "comment": "This area is indeed underserved. I'm planning to open a gym here!",
                "user_email": "entrepreneur@example.com"
            }
        }


class ErrorResponse(BaseModel):
    """Standardized error response model."""
    error: str = Field(..., description="Error type identifier")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional error context")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "NOT_FOUND",
                "message": "Neighborhood 'InvalidID' not found",
                "details": {
                    "available_neighborhoods": ["DHA-Phase2", "Clifton-Block5"]
                }
            }
        }
