"""
Feedback Router

POST /api/v1/feedback - Submit user feedback on recommendations
"""

import logging
from typing import Optional
from enum import Enum
from datetime import datetime

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, EmailStr, field_validator

from src.database.connection import get_session
from src.database.models import GridCellModel, UserFeedbackModel

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

Feedback is used to refine the scoring algorithm in future phases.
    """,
    responses={
        201: {"description": "Feedback successfully saved"},
        400: {"description": "Invalid feedback data"},
        404: {"description": "Grid not found"},
        422: {"description": "Validation error"}
    }
)
async def submit_feedback(feedback: FeedbackRequest) -> FeedbackResponse:
    """
    Submit feedback for a grid recommendation.
    
    Args:
        feedback: Feedback data including grid_id, rating, and optional comment
        
    Returns:
        Confirmation with feedback ID
    """
    try:
        with get_session() as session:
            # Verify grid exists
            grid_exists = (
                session.query(GridCellModel)
                .filter(GridCellModel.grid_id == feedback.grid_id)
                .first()
            )
            
            if not grid_exists:
                raise HTTPException(
                    status_code=404,
                    detail=f"Grid '{feedback.grid_id}' not found"
                )
            
            # Create feedback record
            feedback_record = UserFeedbackModel(
                grid_id=feedback.grid_id,
                category=feedback.category,
                rating=feedback.rating,
                comment=feedback.comment,
                user_email=feedback.user_email,
                created_at=datetime.utcnow()
            )
            
            session.add(feedback_record)
            session.commit()
            session.refresh(feedback_record)
            
            logger.info(
                f"Feedback submitted: grid={feedback.grid_id}, "
                f"rating={feedback.rating}, id={feedback_record.id}"
            )
            
            # Track rating distribution for analytics
            positive_count = (
                session.query(UserFeedbackModel)
                .filter(UserFeedbackModel.rating == 1)
                .count()
            )
            negative_count = (
                session.query(UserFeedbackModel)
                .filter(UserFeedbackModel.rating == -1)
                .count()
            )
            total = positive_count + negative_count
            if total > 0:
                logger.info(
                    f"Feedback distribution: "
                    f"positive={positive_count} ({positive_count/total*100:.1f}%), "
                    f"negative={negative_count} ({negative_count/total*100:.1f}%)"
                )
            
            return FeedbackResponse(
                message="Feedback received. Thank you!",
                feedback_id=feedback_record.id
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to submit feedback"
        )
