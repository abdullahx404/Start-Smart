"""
StartSmart Location Intelligence API

Main FastAPI application entry point.
Phase 4 - API & Deployment

This module:
- Initializes the FastAPI application
- Configures CORS middleware
- Adds request logging middleware
- Includes all route handlers
- Provides health check endpoint

Run locally:
    uvicorn api.main:app --reload --port 8000

Access docs:
    http://localhost:8000/docs (Swagger UI)
    http://localhost:8000/redoc (ReDoc)
"""

import time
import logging
from datetime import datetime
from contextlib import asynccontextmanager
from typing import Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

# Import routers
from api.routers import (
    neighborhoods_router,
    grids_router,
    recommendations_router,
    grid_detail_router,
    feedback_router,
)

# Import database connection for startup check
from src.database.connection import get_session, engine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("startsmart.api")


# ========== Lifespan Events ==========

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handle startup and shutdown events.
    """
    # Startup
    logger.info("🚀 StartSmart API starting...")
    
    # Verify database connection
    try:
        with get_session() as session:
            session.execute(text("SELECT 1"))
        logger.info("✅ Database connection verified")
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        # Continue anyway - API can still serve cached/mock data
    
    logger.info("✅ StartSmart API ready!")
    
    yield
    
    # Shutdown
    logger.info("👋 StartSmart API shutting down...")
    engine.dispose()
    logger.info("✅ Database connections closed")


# ========== FastAPI Application ==========

app = FastAPI(
    title="StartSmart Location Intelligence API",
    version="1.0.0",
    description="""
## StartSmart MVP API

**Location Intelligence Platform for Karachi Entrepreneurs**

This API provides data-driven location recommendations for new businesses 
by analyzing:
- Real business data (Google Places API)
- Social media signals (Instagram, Reddit)
- Gap Opportunity Score (GOS) algorithm

### Coverage
- **Neighborhoods**: 5 pilot areas in Karachi
- **Categories**: Gym, Cafe

### Key Endpoints
- `/api/v1/neighborhoods` - List available neighborhoods
- `/api/v1/grids` - Get grid cells with opportunity scores
- `/api/v1/recommendations` - Get top location recommendations
- `/api/v1/grid/{grid_id}` - Detailed grid analysis
- `/api/v1/feedback` - Submit user feedback

### Status
MVP Version - Phase 4 Deployment
    """,
    contact={
        "name": "StartSmart Development Team",
        "url": "https://github.com/startsmart",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    lifespan=lifespan,
)


# ========== CORS Middleware ==========

# Allowed origins for cross-origin requests
ALLOWED_ORIGINS = [
    "http://localhost:*",
    "http://localhost:3000",
    "http://localhost:8080",
    "http://127.0.0.1:*",
    "https://startsmart-mvp.web.app",
    "https://startsmart-mvp.firebaseapp.com",
    "https://*.onrender.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for MVP (more permissive)
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


# ========== Request Logging Middleware ==========

@app.middleware("http")
async def log_requests(request: Request, call_next: Callable) -> Response:
    """
    Log all incoming requests with method, path, duration, and status code.
    """
    start_time = time.time()
    
    # Process request
    response = await call_next(request)
    
    # Calculate duration
    duration_ms = (time.time() - start_time) * 1000
    
    # Log request details
    logger.info(
        f"{request.method} {request.url.path} "
        f"- Status: {response.status_code} "
        f"- Duration: {duration_ms:.2f}ms"
    )
    
    return response


# ========== Global Exception Handler ==========

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Handle all unhandled exceptions with structured error response.
    """
    logger.error(
        f"Unhandled exception on {request.method} {request.url.path}: {exc}",
        exc_info=True,
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred. Please try again later.",
            "path": str(request.url.path),
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


# ========== Health Check Endpoint ==========

@app.get("/health", tags=["system"])
async def health_check():
    """
    Health check endpoint for monitoring and load balancers.
    
    Returns:
        200 OK with status information
    """
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "service": "startsmart-api",
    }


@app.get("/", tags=["system"])
async def root():
    """
    Root endpoint - redirects to docs or provides basic info.
    """
    return {
        "message": "Welcome to StartSmart Location Intelligence API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


# ========== Include Routers ==========

app.include_router(
    neighborhoods_router,
    prefix="/api/v1",
    tags=["neighborhoods"],
)

app.include_router(
    grids_router,
    prefix="/api/v1",
    tags=["grids"],
)

app.include_router(
    recommendations_router,
    prefix="/api/v1",
    tags=["recommendations"],
)

app.include_router(
    grid_detail_router,
    prefix="/api/v1",
    tags=["grid"],
)

app.include_router(
    feedback_router,
    prefix="/api/v1",
    tags=["feedback"],
)


# ========== Run with Uvicorn (for development) ==========

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
