"""
Structured Logging Utility for StartSmart Backend

Provides centralized logging configuration with:
- JSON formatting for production (log aggregation friendly)
- Colorized console output for development
- Environment-based configuration
- Module-specific loggers
- Helper functions for common logging patterns

Usage:
    from src.utils.logger import get_logger, log_api_call, log_database_operation
    
    logger = get_logger(__name__)
    logger.info("Application started")
    
    # API call logging
    log_api_call(logger, "Google Places API", {"category": "Gym"}, 1.23)
    
    # Database operation logging
    log_database_operation(logger, "INSERT", "businesses", 73)
"""

import logging
import json
import os
import sys
from datetime import datetime
from typing import Any, Dict, Optional


# ============================================================================
# Environment Configuration
# ============================================================================

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()  # development or production


# ============================================================================
# ANSI Color Codes for Console Output
# ============================================================================

class Colors:
    """ANSI color codes for terminal output"""
    RESET = "\033[0m"
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"
    BOLD = "\033[1m"


# ============================================================================
# Custom Formatters
# ============================================================================

class ColoredConsoleFormatter(logging.Formatter):
    """
    Formatter that adds colors to console output for development.
    
    Log levels are color-coded:
    - DEBUG: Cyan
    - INFO: Green
    - WARNING: Yellow
    - ERROR: Red
    - CRITICAL: Bright Red + Bold
    """
    
    LEVEL_COLORS = {
        logging.DEBUG: Colors.CYAN,
        logging.INFO: Colors.GREEN,
        logging.WARNING: Colors.YELLOW,
        logging.ERROR: Colors.RED,
        logging.CRITICAL: Colors.BRIGHT_RED + Colors.BOLD,
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors"""
        # Add color to level name
        level_color = self.LEVEL_COLORS.get(record.levelno, Colors.WHITE)
        record.levelname = f"{level_color}{record.levelname:8s}{Colors.RESET}"
        
        # Add color to logger name
        record.name = f"{Colors.BRIGHT_BLACK}{record.name}{Colors.RESET}"
        
        # Format timestamp
        record.asctime = f"{Colors.BRIGHT_BLACK}{self.formatTime(record, '%Y-%m-%d %H:%M:%S')}{Colors.RESET}"
        
        # Format message
        if record.levelno >= logging.ERROR:
            record.msg = f"{Colors.RED}{record.msg}{Colors.RESET}"
        elif record.levelno == logging.WARNING:
            record.msg = f"{Colors.YELLOW}{record.msg}{Colors.RESET}"
        
        return super().format(record)


class JSONFormatter(logging.Formatter):
    """
    Formatter that outputs logs as JSON lines for production.
    
    Each log entry is a single-line JSON object with:
    - timestamp (ISO 8601)
    - level
    - logger (module name)
    - message
    - extra fields (if provided)
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add extra fields if present
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add file/line info for errors
        if record.levelno >= logging.ERROR:
            log_data["file"] = record.pathname
            log_data["line"] = record.lineno
            log_data["function"] = record.funcName
        
        return json.dumps(log_data)


# ============================================================================
# Logger Configuration
# ============================================================================

def _get_log_level(level_str: str) -> int:
    """Convert string log level to logging constant"""
    levels = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    return levels.get(level_str, logging.INFO)


def _configure_handler(environment: str) -> logging.Handler:
    """
    Create and configure log handler based on environment.
    
    Args:
        environment: 'development' or 'production'
        
    Returns:
        Configured logging handler
    """
    handler = logging.StreamHandler(sys.stdout)
    
    if environment == "production":
        # Production: JSON formatter
        formatter = JSONFormatter()
    else:
        # Development: Colorized console formatter
        formatter = ColoredConsoleFormatter(
            fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    
    handler.setFormatter(formatter)
    return handler


# Global handler (created once)
_log_handler = _configure_handler(ENVIRONMENT)


def get_logger(name: str) -> logging.Logger:
    """
    Get a configured logger for a module.
    
    Creates a logger with the specified name and attaches the
    appropriate handler based on environment.
    
    Args:
        name: Logger name (typically __name__ of the calling module)
        
    Returns:
        Configured logging.Logger instance
        
    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Starting data fetch")
        >>> logger.error("API call failed", extra={"extra_fields": {"api": "Google Places"}})
    """
    logger = logging.getLogger(name)
    
    # Only configure if not already configured
    if not logger.handlers:
        logger.setLevel(_get_log_level(LOG_LEVEL))
        logger.addHandler(_log_handler)
        logger.propagate = False
    
    return logger


# ============================================================================
# Helper Functions
# ============================================================================

def log_api_call(
    logger: logging.Logger,
    endpoint: str,
    params: Optional[Dict[str, Any]] = None,
    duration: Optional[float] = None,
    status: str = "success",
    error: Optional[str] = None,
) -> None:
    """
    Log an API call with structured metadata.
    
    Args:
        logger: Logger instance
        endpoint: API endpoint or service name (e.g., "Google Places API")
        params: Request parameters (will be sanitized)
        duration: Request duration in seconds
        status: "success" or "error"
        error: Error message if status is "error"
        
    Example:
        >>> logger = get_logger(__name__)
        >>> log_api_call(
        ...     logger,
        ...     "Google Places API",
        ...     {"category": "Gym", "location": "24.83,67.06"},
        ...     duration=1.23,
        ...     status="success"
        ... )
    """
    extra_fields = {
        "event_type": "api_call",
        "endpoint": endpoint,
        "status": status,
    }
    
    if params:
        # Sanitize params (remove sensitive keys)
        sanitized_params = {
            k: v if k not in ["api_key", "token", "password"] else "***REDACTED***"
            for k, v in params.items()
        }
        extra_fields["params"] = sanitized_params
    
    if duration is not None:
        extra_fields["duration_seconds"] = round(duration, 3)
    
    if error:
        extra_fields["error"] = error
    
    # Choose log level based on status
    if status == "error":
        logger.error(
            f"API call failed: {endpoint}",
            extra={"extra_fields": extra_fields}
        )
    elif duration and duration > 5.0:
        logger.warning(
            f"Slow API call: {endpoint} ({duration:.2f}s)",
            extra={"extra_fields": extra_fields}
        )
    else:
        logger.info(
            f"API call: {endpoint}",
            extra={"extra_fields": extra_fields}
        )


def log_database_operation(
    logger: logging.Logger,
    operation: str,
    table: str,
    row_count: Optional[int] = None,
    duration: Optional[float] = None,
    error: Optional[str] = None,
) -> None:
    """
    Log a database operation with structured metadata.
    
    Args:
        logger: Logger instance
        operation: SQL operation type (SELECT, INSERT, UPDATE, DELETE)
        table: Table name
        row_count: Number of rows affected/returned
        duration: Query duration in seconds
        error: Error message if operation failed
        
    Example:
        >>> logger = get_logger(__name__)
        >>> log_database_operation(
        ...     logger,
        ...     "INSERT",
        ...     "businesses",
        ...     row_count=73,
        ...     duration=0.45
        ... )
    """
    extra_fields = {
        "event_type": "database_operation",
        "operation": operation.upper(),
        "table": table,
    }
    
    if row_count is not None:
        extra_fields["row_count"] = row_count
    
    if duration is not None:
        extra_fields["duration_seconds"] = round(duration, 3)
    
    if error:
        extra_fields["error"] = error
        logger.error(
            f"Database {operation} failed on {table}: {error}",
            extra={"extra_fields": extra_fields}
        )
    elif duration and duration > 2.0:
        logger.warning(
            f"Slow database {operation} on {table} ({duration:.2f}s)",
            extra={"extra_fields": extra_fields}
        )
    else:
        msg = f"Database {operation} on {table}"
        if row_count is not None:
            msg += f" ({row_count} rows)"
        
        logger.info(msg, extra={"extra_fields": extra_fields})


def log_scoring_operation(
    logger: logging.Logger,
    grid_id: str,
    category: str,
    gos: Optional[float] = None,
    confidence: Optional[float] = None,
    metrics: Optional[Dict[str, Any]] = None,
    duration: Optional[float] = None,
) -> None:
    """
    Log a scoring/GOS calculation operation.
    
    Args:
        logger: Logger instance
        grid_id: Grid cell identifier
        category: Business category
        gos: Computed GOS score (0.0 to 1.0)
        confidence: Confidence score (0.0 to 1.0)
        metrics: Additional metrics (business_count, instagram_volume, etc.)
        duration: Computation duration in seconds
        
    Example:
        >>> logger = get_logger(__name__)
        >>> log_scoring_operation(
        ...     logger,
        ...     "DHA-Phase2-Cell-07",
        ...     "Gym",
        ...     gos=0.825,
        ...     confidence=0.780,
        ...     metrics={"business_count": 3, "instagram_volume": 45}
        ... )
    """
    extra_fields = {
        "event_type": "scoring",
        "grid_id": grid_id,
        "category": category,
    }
    
    if gos is not None:
        extra_fields["gos"] = round(gos, 3)
    
    if confidence is not None:
        extra_fields["confidence"] = round(confidence, 3)
    
    if metrics:
        extra_fields["metrics"] = metrics
    
    if duration is not None:
        extra_fields["duration_seconds"] = round(duration, 3)
    
    msg = f"Scored grid {grid_id} ({category})"
    if gos is not None:
        msg += f" - GOS: {gos:.3f}"
    
    logger.info(msg, extra={"extra_fields": extra_fields})


def log_adapter_fetch(
    logger: logging.Logger,
    adapter_name: str,
    category: str,
    bounds: Optional[Dict[str, float]] = None,
    result_count: Optional[int] = None,
    duration: Optional[float] = None,
    error: Optional[str] = None,
) -> None:
    """
    Log a data adapter fetch operation.
    
    Args:
        logger: Logger instance
        adapter_name: Name of adapter (e.g., "GooglePlacesAdapter")
        category: Category being fetched
        bounds: Geographic bounds (lat_north, lat_south, lon_east, lon_west)
        result_count: Number of items fetched
        duration: Fetch duration in seconds
        error: Error message if fetch failed
        
    Example:
        >>> logger = get_logger(__name__)
        >>> log_adapter_fetch(
        ...     logger,
        ...     "GooglePlacesAdapter",
        ...     "Gym",
        ...     bounds={"lat_north": 24.83, "lat_south": 24.82, ...},
        ...     result_count=15,
        ...     duration=2.1
        ... )
    """
    extra_fields = {
        "event_type": "adapter_fetch",
        "adapter": adapter_name,
        "category": category,
    }
    
    if bounds:
        extra_fields["bounds"] = bounds
    
    if result_count is not None:
        extra_fields["result_count"] = result_count
    
    if duration is not None:
        extra_fields["duration_seconds"] = round(duration, 3)
    
    if error:
        extra_fields["error"] = error
        logger.error(
            f"{adapter_name} fetch failed for {category}: {error}",
            extra={"extra_fields": extra_fields}
        )
    else:
        msg = f"{adapter_name} fetched {category}"
        if result_count is not None:
            msg += f" ({result_count} items)"
        
        logger.info(msg, extra={"extra_fields": extra_fields})


# ============================================================================
# Module Initialization
# ============================================================================

# Create a default logger for this module
_module_logger = get_logger(__name__)

# Log logger configuration on import
_module_logger.debug(
    f"Logger configured: environment={ENVIRONMENT}, level={LOG_LEVEL}"
)


# ============================================================================
# Example Usage (for testing)
# ============================================================================

if __name__ == "__main__":
    """
    Test the logger configuration.
    
    Run this file directly to see sample output:
        python backend/src/utils/logger.py
    """
    print("=" * 70)
    print("LOGGER TEST - All Log Levels")
    print("=" * 70)
    print()
    
    # Create test logger
    test_logger = get_logger("test_module")
    
    # Test all log levels
    test_logger.debug("This is a DEBUG message (detailed diagnostic info)")
    test_logger.info("This is an INFO message (normal operation)")
    test_logger.warning("This is a WARNING message (something unexpected)")
    test_logger.error("This is an ERROR message (operation failed)")
    test_logger.critical("This is a CRITICAL message (system failure)")
    
    print()
    print("=" * 70)
    print("HELPER FUNCTIONS TEST")
    print("=" * 70)
    print()
    
    # Test API call logging
    log_api_call(
        test_logger,
        "Google Places API",
        params={"category": "Gym", "location": "24.83,67.06"},
        duration=1.234,
        status="success"
    )
    
    log_api_call(
        test_logger,
        "Google Places API",
        params={"category": "Cafe", "api_key": "secret123"},
        duration=0.5,
        status="success"
    )
    
    log_api_call(
        test_logger,
        "Google Places API",
        params={"category": "Gym"},
        duration=8.5,  # Slow call
        status="success"
    )
    
    log_api_call(
        test_logger,
        "Instagram API",
        params={"hashtag": "gym"},
        status="error",
        error="Rate limit exceeded"
    )
    
    # Test database operation logging
    log_database_operation(
        test_logger,
        "INSERT",
        "businesses",
        row_count=73,
        duration=0.45
    )
    
    log_database_operation(
        test_logger,
        "SELECT",
        "social_posts",
        row_count=1500,
        duration=2.3  # Slow query
    )
    
    log_database_operation(
        test_logger,
        "UPDATE",
        "grid_metrics",
        row_count=12,
        duration=0.1
    )
    
    log_database_operation(
        test_logger,
        "DELETE",
        "user_feedback",
        error="Foreign key constraint violation"
    )
    
    # Test scoring operation logging
    log_scoring_operation(
        test_logger,
        "DHA-Phase2-Cell-07",
        "Gym",
        gos=0.825,
        confidence=0.780,
        metrics={"business_count": 3, "instagram_volume": 45, "reddit_mentions": 12},
        duration=0.05
    )
    
    # Test adapter fetch logging
    log_adapter_fetch(
        test_logger,
        "GooglePlacesAdapter",
        "Gym",
        bounds={"lat_north": 24.83, "lat_south": 24.82, "lon_east": 67.07, "lon_west": 67.06},
        result_count=15,
        duration=2.1
    )
    
    log_adapter_fetch(
        test_logger,
        "SimulatedSocialAdapter",
        "Gym",
        result_count=250,
        duration=0.3
    )
    
    log_adapter_fetch(
        test_logger,
        "GooglePlacesAdapter",
        "Cafe",
        error="API quota exceeded"
    )
    
    print()
    print("=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)
    print()
    print(f"Environment: {ENVIRONMENT}")
    print(f"Log Level: {LOG_LEVEL}")
    print()
    print("To change environment:")
    print("  export ENVIRONMENT=production")
    print("  export LOG_LEVEL=DEBUG")
    print()
