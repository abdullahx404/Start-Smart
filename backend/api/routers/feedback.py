"""
Feedback Router (DATABASE DISABLED)

POST /api/v1/feedback - Submit user feedback (logged only, not stored)
"""

import logging
from typing import Optional
from enum import Enum
from datetime import datetime
import random

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, EmailStr, field_validator

# Database disabled for serverless deployment
# from src.database.connection import get_session
# from src.database.models import GridCellModel, UserFeedbackModel

logger = logging.getLogger("startsmart.api.feedback")

router = APIRouter()


# ========== Request/Response Models ==========

class FeedbackRequest(BaseModel):
    """Request model for feedback submission."""
    grid_id: str = Field(..., description="Grid cell identifier")
    category: str = Field(..., description="Business category")
    rating: int = Field(..., description="Rating: 1 (thumbs up) or -1 (thumbs down)")
    comment: Optional[str] = Field(
        None, 
        max_length=500, 
        description="Optional comment (max 500 chars)"
    )
    user_email: Optional[str] = Field(None, description="Optional user email")

    @field_validator('rating')
    @classmethod
    def validate_rating(cls, v):
        if v not in [-1, 1]:
            raise ValueError('Rating must be 1 (thumbs up) or -1 (thumbs down)')
        return v

    @field_validator('category')
    @classmethod
    def validate_category(cls, v):
        if v not in ['Gym', 'Cafe']:
            raise ValueError('Category must be Gym or Cafe')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "grid_id": "DHA-Phase2-Cell-07",
                "category": "Gym",
                "rating": 1,
                "comment": "Great recommendation! This area is indeed underserved.",
                "user_email": "entrepreneur@example.com"
            }
        }


class FeedbackResponse(BaseModel):
    """Response model for successful feedback submission."""
    message: str
    feedback_id: int

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Feedback received. Thank you!",
                "feedback_id": 42
            }
        }


# ========== Endpoints ==========

@router.post(
    "/feedback",
    response_model=FeedbackResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit user feedback",
    description="""
Allows users to provide feedback on recommendation quality.

**Rating values**:
- `1`: Thumbs up (good recommendation)
- `-1`: Thumbs down (poor recommendation)

NOTE: Database disabled - feedback is logged but not stored.
    """,
    responses={
        201: {"description": "Feedback successfully received"},
        400: {"description": "Invalid feedback data"},
        422: {"description": "Validation error"}
    }
)
async def submit_feedback(feedback: FeedbackRequest) -> FeedbackResponse:
    """
    Submit feedback for a grid recommendation.
    
    NOTE: Database disabled - feedback is logged but not stored.
    """
    # Log the feedback (since database is disabled)
    logger.info(
        f"📝 Feedback received (not stored - DB disabled): "
        f"grid={feedback.grid_id}, "
        f"category={feedback.category}, "
        f"rating={feedback.rating}, "
        f"comment={feedback.comment or 'None'}"
    )
    
    # Generate a mock feedback ID
    mock_feedback_id = random.randint(1000, 9999)
    
    return FeedbackResponse(
        message="Feedback received. Thank you! (Note: Database disabled for serverless deployment)",
        feedback_id=mock_feedback_id
    )
