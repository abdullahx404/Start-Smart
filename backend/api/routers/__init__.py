# API Routers Package
"""
Contains all route handlers for the StartSmart API.
"""

from .neighborhoods import router as neighborhoods_router
from .grids import router as grids_router
from .recommendations import router as recommendations_router
from .grid_detail import router as grid_detail_router
from .feedback import router as feedback_router

__all__ = [
    "neighborhoods_router",
    "grids_router",
    "recommendations_router",
    "grid_detail_router",
    "feedback_router",
]
