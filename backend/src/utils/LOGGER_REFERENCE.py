"""
Logger Quick Reference Guide

This file provides quick examples of using the structured logging utility.
Copy these patterns into your code as needed.
"""

# ============================================================================
# Basic Usage
# ============================================================================

from src.utils import get_logger

# Create a logger for your module
logger = get_logger(__name__)

# Log at different levels
logger.debug("Detailed diagnostic information")
logger.info("Normal operation message")
logger.warning("Something unexpected happened")
logger.error("Operation failed")
logger.critical("System-level failure")


# ============================================================================
# API Call Logging
# ============================================================================

from src.utils import get_logger, log_api_call
import time

logger = get_logger(__name__)

# Example 1: Successful API call
start = time.time()
# ... make API call ...
duration = time.time() - start

log_api_call(
    logger,
    endpoint="Google Places API",
    params={"category": "Gym", "location": "24.83,67.06"},
    duration=duration,
    status="success"
)

# Example 2: Failed API call
log_api_call(
    logger,
    endpoint="Instagram API",
    params={"hashtag": "gym"},
    status="error",
    error="Rate limit exceeded"
)

# Example 3: Slow API call (auto-warns if > 5s)
log_api_call(
    logger,
    endpoint="Reddit API",
    params={"subreddit": "pakistan"},
    duration=8.5,  # Will log as WARNING
    status="success"
)


# ============================================================================
# Database Operation Logging
# ============================================================================

from src.utils import get_logger, log_database_operation

logger = get_logger(__name__)

# Example 1: INSERT operation
log_database_operation(
    logger,
    operation="INSERT",
    table="businesses",
    row_count=73,
    duration=0.45
)

# Example 2: SELECT operation
log_database_operation(
    logger,
    operation="SELECT",
    table="social_posts",
    row_count=500,
    duration=1.2
)

# Example 3: UPDATE operation
log_database_operation(
    logger,
    operation="UPDATE",
    table="grid_metrics",
    row_count=12,
    duration=0.3
)

# Example 4: Failed operation
log_database_operation(
    logger,
    operation="DELETE",
    table="user_feedback",
    error="Foreign key constraint violation"
)

# Example 5: Slow query (auto-warns if > 2s)
log_database_operation(
    logger,
    operation="SELECT",
    table="businesses",
    row_count=1000,
    duration=3.5  # Will log as WARNING
)


# ============================================================================
# Scoring Operation Logging
# ============================================================================

from src.utils import get_logger, log_scoring_operation

logger = get_logger(__name__)

# Log GOS calculation
log_scoring_operation(
    logger,
    grid_id="DHA-Phase2-Cell-07",
    category="Gym",
    gos=0.825,
    confidence=0.780,
    metrics={
        "business_count": 3,
        "instagram_volume": 45,
        "reddit_mentions": 12
    },
    duration=0.05
)


# ============================================================================
# Adapter Fetch Logging
# ============================================================================

from src.utils import get_logger, log_adapter_fetch

logger = get_logger(__name__)

# Example 1: Successful fetch
log_adapter_fetch(
    logger,
    adapter_name="GooglePlacesAdapter",
    category="Gym",
    bounds={
        "lat_north": 24.83,
        "lat_south": 24.82,
        "lon_east": 67.07,
        "lon_west": 67.06
    },
    result_count=15,
    duration=2.1
)

# Example 2: Failed fetch
log_adapter_fetch(
    logger,
    adapter_name="GooglePlacesAdapter",
    category="Cafe",
    error="API quota exceeded"
)

# Example 3: Simulated data (no bounds)
log_adapter_fetch(
    logger,
    adapter_name="SimulatedSocialAdapter",
    category="Gym",
    result_count=250,
    duration=0.3
)


# ============================================================================
# Environment Configuration
# ============================================================================

"""
Control logging behavior with environment variables:

# Development mode (colorized console output)
export ENVIRONMENT=development
export LOG_LEVEL=DEBUG

# Production mode (JSON output for log aggregation)
export ENVIRONMENT=production
export LOG_LEVEL=INFO

# Available log levels:
# - DEBUG: Detailed diagnostic information
# - INFO: Normal operation messages
# - WARNING: Unexpected but handled situations
# - ERROR: Operation failures
# - CRITICAL: System-level failures
"""


# ============================================================================
# Integration with Existing Code
# ============================================================================

"""
Example: Adding logging to GooglePlacesAdapter
"""

from src.utils import get_logger, log_api_call, log_adapter_fetch
import time

class GooglePlacesAdapter:
    def __init__(self):
        self.logger = get_logger(__name__)
    
    def fetch_businesses(self, category, bounds):
        self.logger.info(f"Starting fetch for category: {category}")
        
        start_time = time.time()
        
        try:
            # Make API call
            response = self._call_api(category, bounds)
            duration = time.time() - start_time
            
            # Log API call
            log_api_call(
                self.logger,
                "Google Places API",
                params={"category": category},
                duration=duration,
                status="success"
            )
            
            # Parse results
            businesses = self._parse_response(response)
            
            # Log adapter fetch
            log_adapter_fetch(
                self.logger,
                "GooglePlacesAdapter",
                category,
                bounds=bounds,
                result_count=len(businesses),
                duration=duration
            )
            
            return businesses
            
        except Exception as e:
            duration = time.time() - start_time
            
            # Log error
            log_api_call(
                self.logger,
                "Google Places API",
                params={"category": category},
                duration=duration,
                status="error",
                error=str(e)
            )
            
            log_adapter_fetch(
                self.logger,
                "GooglePlacesAdapter",
                category,
                error=str(e)
            )
            
            raise


"""
Example: Adding logging to database operations
"""

from src.utils import get_logger, log_database_operation
from src.database import get_session
from src.database.models import BusinessModel
import time

logger = get_logger(__name__)

def insert_businesses(businesses):
    start_time = time.time()
    
    try:
        with get_session() as session:
            # Insert businesses
            for business in businesses:
                session.add(BusinessModel.from_pydantic(business))
            
            session.commit()
            duration = time.time() - start_time
            
            # Log successful operation
            log_database_operation(
                logger,
                operation="INSERT",
                table="businesses",
                row_count=len(businesses),
                duration=duration
            )
            
    except Exception as e:
        duration = time.time() - start_time
        
        # Log failed operation
        log_database_operation(
            logger,
            operation="INSERT",
            table="businesses",
            error=str(e)
        )
        
        raise


"""
Example: Adding logging to scoring service
"""

from src.utils import get_logger, log_scoring_operation
import time

logger = get_logger(__name__)

def calculate_gos(grid_id, category, metrics):
    logger.info(f"Calculating GOS for {grid_id} ({category})")
    
    start_time = time.time()
    
    # Perform calculations
    gos = _compute_gos(metrics)
    confidence = _compute_confidence(metrics)
    
    duration = time.time() - start_time
    
    # Log scoring operation
    log_scoring_operation(
        logger,
        grid_id=grid_id,
        category=category,
        gos=gos,
        confidence=confidence,
        metrics=metrics,
        duration=duration
    )
    
    return gos, confidence


# ============================================================================
# Testing the Logger
# ============================================================================

"""
To test the logger output, run:

    python backend/src/utils/logger.py

This will show sample output for all log levels and helper functions.

To run unit tests:

    pytest backend/tests/utils/test_logger.py -v
"""
