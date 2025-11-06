"""
SQLAlchemy ORM Models

This module defines ORM models for all database tables.
Models EXACTLY match the schema in contracts/database_schema.sql.

CRITICAL RULES:
- Column names and types MUST match SQL schema exactly
- Grid IDs are strings (e.g., "DHA-Phase2-Cell-07"), not integers
- Use DECIMAL for precise numeric values (ratings, scores)
- All models have to_dict() for JSON serialization
- All models have from_pydantic() for Pydantic conversion

Usage:
    from src.database.models import BusinessModel, GridCellModel
    from src.database import get_session
    
    with get_session() as session:
        gyms = session.query(BusinessModel).filter_by(category="Gym").all()
"""

from datetime import datetime
from typing import Optional, Dict, Any
from decimal import Decimal

from sqlalchemy import (
    Column, String, Integer, Float, DateTime, Boolean, Text,
    ForeignKey, Index, CheckConstraint, DECIMAL, func
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from src.database.connection import Base


# ============================================================================
# Grid Cells Model
# ============================================================================

class GridCellModel(Base):
    """
    ORM model for grid_cells table.
    
    Represents geographic grid cells (~0.5 km²) covering pilot neighborhoods.
    Static for MVP, computed once during Phase 0.
    
    Table: grid_cells
    Primary Key: grid_id (VARCHAR(50))
    """
    
    __tablename__ = "grid_cells"
    
    # Columns (match database_schema.sql exactly)
    grid_id = Column(String(50), primary_key=True)
    neighborhood = Column(String(100), nullable=False)
    lat_center = Column(DECIMAL(10, 7), nullable=False)
    lon_center = Column(DECIMAL(10, 7), nullable=False)
    lat_north = Column(DECIMAL(10, 7), nullable=False)
    lat_south = Column(DECIMAL(10, 7), nullable=False)
    lon_east = Column(DECIMAL(10, 7), nullable=False)
    lon_west = Column(DECIMAL(10, 7), nullable=False)
    area_km2 = Column(DECIMAL(5, 2), default=0.5)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    businesses = relationship("BusinessModel", back_populates="grid", cascade="all, delete-orphan")
    social_posts = relationship("SocialPostModel", back_populates="grid", cascade="all, delete-orphan")
    grid_metrics = relationship("GridMetricsModel", back_populates="grid", cascade="all, delete-orphan")
    user_feedback = relationship("UserFeedbackModel", back_populates="grid", cascade="all, delete-orphan")
    
    # Indexes (defined in __table_args__)
    __table_args__ = (
        Index('idx_grid_neighborhood', 'neighborhood'),
        Index('idx_grid_center', 'lat_center', 'lon_center'),
    )
    
    def __repr__(self) -> str:
        return (
            f"<GridCell(grid_id='{self.grid_id}', "
            f"neighborhood='{self.neighborhood}', "
            f"center=({float(self.lat_center)}, {float(self.lon_center)}))>"
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "grid_id": self.grid_id,
            "neighborhood": self.neighborhood,
            "lat_center": float(self.lat_center),
            "lon_center": float(self.lon_center),
            "lat_north": float(self.lat_north),
            "lat_south": float(self.lat_south),
            "lon_east": float(self.lon_east),
            "lon_west": float(self.lon_west),
            "area_km2": float(self.area_km2),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
    
    @classmethod
    def from_pydantic(cls, pydantic_model):
        """
        Create ORM instance from Pydantic GridCell model.
        
        Args:
            pydantic_model: contracts.models.GridCell instance
            
        Returns:
            GridCellModel instance
        """
        return cls(
            grid_id=pydantic_model.grid_id,
            neighborhood=pydantic_model.neighborhood,
            lat_center=Decimal(str(pydantic_model.lat_center)),
            lon_center=Decimal(str(pydantic_model.lon_center)),
            lat_north=Decimal(str(pydantic_model.lat_north)),
            lat_south=Decimal(str(pydantic_model.lat_south)),
            lon_east=Decimal(str(pydantic_model.lon_east)),
            lon_west=Decimal(str(pydantic_model.lon_west)),
            area_km2=Decimal(str(pydantic_model.area_km2)),
            created_at=pydantic_model.created_at,
        )


# ============================================================================
# Businesses Model
# ============================================================================

class BusinessModel(Base):
    """
    ORM model for businesses table.
    
    Populated from Google Places API (real data for MVP).
    One row per business location.
    
    Table: businesses
    Primary Key: business_id (VARCHAR(100))
    Foreign Key: grid_id → grid_cells.grid_id
    """
    
    __tablename__ = "businesses"
    
    # Columns (match database_schema.sql exactly)
    business_id = Column(String(100), primary_key=True)
    name = Column(String(255), nullable=False)
    lat = Column(DECIMAL(10, 7), nullable=False)
    lon = Column(DECIMAL(10, 7), nullable=False)
    category = Column(String(50), nullable=False)  # 'Gym', 'Cafe', etc.
    rating = Column(DECIMAL(2, 1), nullable=True)  # 0.0 to 5.0
    review_count = Column(Integer, default=0)
    source = Column(String(50), default='google_places')
    grid_id = Column(String(50), ForeignKey('grid_cells.grid_id', ondelete='SET NULL'), nullable=True)
    fetched_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    grid = relationship("GridCellModel", back_populates="businesses")
    
    # Indexes
    __table_args__ = (
        Index('idx_business_category', 'category'),
        Index('idx_business_grid_category', 'grid_id', 'category'),
        Index('idx_business_location', 'lat', 'lon'),
        Index('idx_business_source', 'source'),
    )
    
    def __repr__(self) -> str:
        return (
            f"<Business(id='{self.business_id}', "
            f"name='{self.name}', "
            f"category='{self.category}', "
            f"rating={float(self.rating) if self.rating else None}, "
            f"grid_id='{self.grid_id}')>"
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "business_id": self.business_id,
            "name": self.name,
            "lat": float(self.lat),
            "lon": float(self.lon),
            "category": self.category,
            "rating": float(self.rating) if self.rating is not None else None,
            "review_count": self.review_count,
            "source": self.source,
            "grid_id": self.grid_id,
            "fetched_at": self.fetched_at.isoformat() if self.fetched_at else None,
        }
    
    @classmethod
    def from_pydantic(cls, pydantic_model):
        """
        Create ORM instance from Pydantic Business model.
        
        Args:
            pydantic_model: contracts.models.Business instance
            
        Returns:
            BusinessModel instance
        """
        return cls(
            business_id=pydantic_model.business_id,
            name=pydantic_model.name,
            lat=Decimal(str(pydantic_model.lat)),
            lon=Decimal(str(pydantic_model.lon)),
            category=pydantic_model.category.value if hasattr(pydantic_model.category, 'value') else pydantic_model.category,
            rating=Decimal(str(pydantic_model.rating)) if pydantic_model.rating is not None else None,
            review_count=pydantic_model.review_count,
            source=pydantic_model.source.value if hasattr(pydantic_model.source, 'value') else pydantic_model.source,
            grid_id=pydantic_model.grid_id,
            fetched_at=pydantic_model.fetched_at,
        )


# ============================================================================
# Social Posts Model
# ============================================================================

class SocialPostModel(Base):
    """
    ORM model for social_posts table.
    
    Synthetic data for MVP (is_simulated = TRUE).
    Future phases will add real Instagram/Reddit data.
    
    Table: social_posts
    Primary Key: post_id (VARCHAR(100))
    Foreign Key: grid_id → grid_cells.grid_id
    """
    
    __tablename__ = "social_posts"
    
    # Columns (match database_schema.sql exactly)
    post_id = Column(String(100), primary_key=True)
    source = Column(String(50), nullable=False)  # 'instagram', 'reddit', 'simulated'
    text = Column(Text, nullable=True)
    timestamp = Column(DateTime, nullable=True)
    lat = Column(DECIMAL(10, 7), nullable=True)
    lon = Column(DECIMAL(10, 7), nullable=True)
    grid_id = Column(String(50), ForeignKey('grid_cells.grid_id', ondelete='SET NULL'), nullable=True)
    post_type = Column(String(50), nullable=True)  # 'demand', 'complaint', 'mention'
    engagement_score = Column(Integer, default=0)
    is_simulated = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    grid = relationship("GridCellModel", back_populates="social_posts")
    
    # Indexes
    __table_args__ = (
        Index('idx_post_grid_type', 'grid_id', 'post_type'),
        Index('idx_post_source', 'source'),
        Index('idx_post_timestamp', 'timestamp'),
        Index('idx_post_simulated', 'is_simulated'),
        # Partial index for non-null locations (PostgreSQL specific)
        Index('idx_post_location', 'lat', 'lon', postgresql_where=(Column('lat').isnot(None))),
    )
    
    def __repr__(self) -> str:
        return (
            f"<SocialPost(id='{self.post_id}', "
            f"source='{self.source}', "
            f"type='{self.post_type}', "
            f"simulated={self.is_simulated}, "
            f"grid_id='{self.grid_id}')>"
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "post_id": self.post_id,
            "source": self.source,
            "text": self.text,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "lat": float(self.lat) if self.lat is not None else None,
            "lon": float(self.lon) if self.lon is not None else None,
            "grid_id": self.grid_id,
            "post_type": self.post_type,
            "engagement_score": self.engagement_score,
            "is_simulated": self.is_simulated,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
    
    @classmethod
    def from_pydantic(cls, pydantic_model):
        """
        Create ORM instance from Pydantic SocialPost model.
        
        Args:
            pydantic_model: contracts.models.SocialPost instance
            
        Returns:
            SocialPostModel instance
        """
        return cls(
            post_id=pydantic_model.post_id,
            source=pydantic_model.source.value if hasattr(pydantic_model.source, 'value') else pydantic_model.source,
            text=pydantic_model.text,
            timestamp=pydantic_model.timestamp,
            lat=Decimal(str(pydantic_model.lat)) if pydantic_model.lat is not None else None,
            lon=Decimal(str(pydantic_model.lon)) if pydantic_model.lon is not None else None,
            grid_id=pydantic_model.grid_id,
            post_type=pydantic_model.post_type.value if pydantic_model.post_type and hasattr(pydantic_model.post_type, 'value') else pydantic_model.post_type,
            engagement_score=pydantic_model.engagement_score,
            is_simulated=pydantic_model.is_simulated,
        )


# ============================================================================
# Grid Metrics Model
# ============================================================================

class GridMetricsModel(Base):
    """
    ORM model for grid_metrics table.
    
    Computed by scoring engine (Phase 2).
    One row per (grid_id, category) combination.
    Contains Gap Opportunity Score (GOS) and supporting metrics.
    
    Table: grid_metrics
    Primary Key: id (SERIAL)
    Foreign Key: grid_id → grid_cells.grid_id
    Unique Constraint: (grid_id, category)
    """
    
    __tablename__ = "grid_metrics"
    
    # Columns (match database_schema.sql exactly)
    id = Column(Integer, primary_key=True, autoincrement=True)
    grid_id = Column(String(50), ForeignKey('grid_cells.grid_id', ondelete='CASCADE'), nullable=False)
    category = Column(String(50), nullable=False)
    business_count = Column(Integer, default=0)
    instagram_volume = Column(Integer, default=0)
    reddit_mentions = Column(Integer, default=0)
    gos = Column(DECIMAL(4, 3), nullable=True)  # 0.000 to 1.000
    confidence = Column(DECIMAL(4, 3), nullable=True)  # 0.000 to 1.000
    top_posts_json = Column(JSONB, nullable=True)  # Top 3 posts with text + links
    competitors_json = Column(JSONB, nullable=True)  # List of nearby businesses
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    grid = relationship("GridCellModel", back_populates="grid_metrics")
    
    # Indexes and constraints
    __table_args__ = (
        Index('idx_metrics_gos', 'gos', postgresql_using='btree', postgresql_ops={'gos': 'DESC'}),
        Index('idx_metrics_category_gos', 'category', 'gos', postgresql_ops={'gos': 'DESC'}),
        Index('idx_metrics_grid', 'grid_id'),
        Index('idx_metrics_last_updated', 'last_updated'),
        # GIN indexes for JSONB columns (PostgreSQL specific)
        Index('idx_metrics_top_posts', 'top_posts_json', postgresql_using='gin'),
        Index('idx_metrics_competitors', 'competitors_json', postgresql_using='gin'),
        # Unique constraint
        {'extend_existing': True},  # Allow re-definition during testing
    )
    
    def __repr__(self) -> str:
        return (
            f"<GridMetrics(id={self.id}, "
            f"grid_id='{self.grid_id}', "
            f"category='{self.category}', "
            f"gos={float(self.gos) if self.gos else None}, "
            f"confidence={float(self.confidence) if self.confidence else None})>"
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "grid_id": self.grid_id,
            "category": self.category,
            "business_count": self.business_count,
            "instagram_volume": self.instagram_volume,
            "reddit_mentions": self.reddit_mentions,
            "gos": float(self.gos) if self.gos is not None else None,
            "confidence": float(self.confidence) if self.confidence is not None else None,
            "top_posts_json": self.top_posts_json,
            "competitors_json": self.competitors_json,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
        }
    
    @classmethod
    def from_pydantic(cls, pydantic_model):
        """
        Create ORM instance from Pydantic GridMetrics model.
        
        Args:
            pydantic_model: contracts.models.GridMetrics instance
            
        Returns:
            GridMetricsModel instance
        """
        return cls(
            grid_id=pydantic_model.grid_id,
            category=pydantic_model.category.value if hasattr(pydantic_model.category, 'value') else pydantic_model.category,
            business_count=pydantic_model.business_count,
            instagram_volume=pydantic_model.instagram_volume,
            reddit_mentions=pydantic_model.reddit_mentions,
            gos=Decimal(str(pydantic_model.gos)),
            confidence=Decimal(str(pydantic_model.confidence)),
            top_posts_json=pydantic_model.top_posts_json,
            competitors_json=pydantic_model.competitors_json,
            last_updated=pydantic_model.last_updated,
        )


# ============================================================================
# User Feedback Model
# ============================================================================

class UserFeedbackModel(Base):
    """
    ORM model for user_feedback table.
    
    Optional for MVP, prepared for Phase 4.
    Captures user validation of recommendations.
    
    Table: user_feedback
    Primary Key: id (SERIAL)
    Foreign Key: grid_id → grid_cells.grid_id
    Check Constraint: rating IN (-1, 1)
    """
    
    __tablename__ = "user_feedback"
    
    # Columns (match database_schema.sql exactly)
    id = Column(Integer, primary_key=True, autoincrement=True)
    grid_id = Column(String(50), ForeignKey('grid_cells.grid_id', ondelete='CASCADE'), nullable=True)
    category = Column(String(50), nullable=True)
    rating = Column(Integer, nullable=True)  # -1 (thumbs down) or 1 (thumbs up)
    comment = Column(Text, nullable=True)
    user_email = Column(String(255), nullable=True)  # nullable for guest users
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    grid = relationship("GridCellModel", back_populates="user_feedback")
    
    # Indexes and constraints
    __table_args__ = (
        Index('idx_feedback_grid', 'grid_id'),
        Index('idx_feedback_category', 'category'),
        Index('idx_feedback_rating', 'rating'),
        Index('idx_feedback_created', 'created_at'),
        # Check constraint for rating values
        CheckConstraint('rating IN (-1, 1)', name='check_rating_values'),
    )
    
    def __repr__(self) -> str:
        return (
            f"<UserFeedback(id={self.id}, "
            f"grid_id='{self.grid_id}', "
            f"category='{self.category}', "
            f"rating={self.rating})>"
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "grid_id": self.grid_id,
            "category": self.category,
            "rating": self.rating,
            "comment": self.comment,
            "user_email": self.user_email,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
    
    @classmethod
    def from_pydantic(cls, pydantic_model):
        """
        Create ORM instance from Pydantic model.
        
        Note: There's no UserFeedback Pydantic model in contracts/models.py yet.
        This method is provided for future compatibility.
        
        Args:
            pydantic_model: Future UserFeedback Pydantic model
            
        Returns:
            UserFeedbackModel instance
        """
        return cls(
            grid_id=getattr(pydantic_model, 'grid_id', None),
            category=getattr(pydantic_model, 'category', None),
            rating=getattr(pydantic_model, 'rating', None),
            comment=getattr(pydantic_model, 'comment', None),
            user_email=getattr(pydantic_model, 'user_email', None),
        )


# ============================================================================
# Helper Functions
# ============================================================================

def get_all_models():
    """
    Get list of all ORM model classes.
    
    Useful for:
    - Creating all tables at once
    - Testing and validation
    - Database migrations
    
    Returns:
        List of ORM model classes
    """
    return [
        GridCellModel,
        BusinessModel,
        SocialPostModel,
        GridMetricsModel,
        UserFeedbackModel,
    ]


def get_model_by_table_name(table_name: str):
    """
    Get ORM model class by table name.
    
    Args:
        table_name: Name of the database table
        
    Returns:
        ORM model class or None if not found
    """
    model_map = {
        'grid_cells': GridCellModel,
        'businesses': BusinessModel,
        'social_posts': SocialPostModel,
        'grid_metrics': GridMetricsModel,
        'user_feedback': UserFeedbackModel,
    }
    return model_map.get(table_name)


# ============================================================================
# Export all models
# ============================================================================

__all__ = [
    'GridCellModel',
    'BusinessModel',
    'SocialPostModel',
    'GridMetricsModel',
    'UserFeedbackModel',
    'get_all_models',
    'get_model_by_table_name',
]
