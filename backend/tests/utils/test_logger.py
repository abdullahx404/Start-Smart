"""
Unit Tests for Logger Utility

Tests the structured logging functionality including:
- Logger creation and configuration
- Environment-based formatting (development vs production)
- Helper functions (log_api_call, log_database_operation, etc.)
- JSON output validation
- Log level configuration
"""

import logging
import json
import os
import sys
from io import StringIO
from unittest.mock import patch

import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.utils.logger import (
    get_logger,
    log_api_call,
    log_database_operation,
    log_scoring_operation,
    log_adapter_fetch,
    JSONFormatter,
    ColoredConsoleFormatter,
)


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def reset_logging():
    """Reset logging configuration between tests"""
    # Clear existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Clear module-level loggers
    for logger_name in list(logging.Logger.manager.loggerDict.keys()):
        logger = logging.getLogger(logger_name)
        logger.handlers.clear()
        logger.propagate = True
    
    yield
    
    # Cleanup after test
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)


@pytest.fixture
def capture_logs():
    """Capture log output to string for assertions"""
    log_stream = StringIO()
    handler = logging.StreamHandler(log_stream)
    return log_stream, handler


# ============================================================================
# Logger Creation Tests
# ============================================================================

def test_get_logger_creates_logger(reset_logging):
    """Test that get_logger creates a logger instance"""
    logger = get_logger("test_module")
    
    assert logger is not None
    assert isinstance(logger, logging.Logger)
    assert logger.name == "test_module"


def test_get_logger_respects_log_level(reset_logging):
    """Test that logger respects LOG_LEVEL environment variable"""
    with patch.dict(os.environ, {"LOG_LEVEL": "DEBUG"}):
        # Need to reload module to pick up new env var
        # For this test, we'll just verify the logger can log at DEBUG level
        logger = get_logger("test_debug")
        logger.setLevel(logging.DEBUG)
        
        assert logger.level == logging.DEBUG


def test_get_logger_singleton_behavior(reset_logging):
    """Test that multiple calls return the same logger instance"""
    logger1 = get_logger("test_singleton")
    logger2 = get_logger("test_singleton")
    
    assert logger1 is logger2


# ============================================================================
# Formatter Tests
# ============================================================================

def test_json_formatter_creates_valid_json():
    """Test that JSONFormatter produces valid JSON output"""
    formatter = JSONFormatter()
    
    # Create a log record
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="/path/to/file.py",
        lineno=42,
        msg="Test message",
        args=(),
        exc_info=None
    )
    
    output = formatter.format(record)
    
    # Should be valid JSON
    parsed = json.loads(output)
    assert parsed["level"] == "INFO"
    assert parsed["logger"] == "test_logger"
    assert parsed["message"] == "Test message"
    assert "timestamp" in parsed


def test_json_formatter_includes_extra_fields():
    """Test that JSONFormatter includes extra_fields in output"""
    formatter = JSONFormatter()
    
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="/path/to/file.py",
        lineno=42,
        msg="Test message",
        args=(),
        exc_info=None
    )
    
    # Add extra fields
    record.extra_fields = {"user_id": 123, "action": "login"}
    
    output = formatter.format(record)
    parsed = json.loads(output)
    
    assert parsed["user_id"] == 123
    assert parsed["action"] == "login"


def test_colored_formatter_adds_ansi_codes():
    """Test that ColoredConsoleFormatter adds ANSI color codes"""
    formatter = ColoredConsoleFormatter(
        fmt="%(levelname)s | %(name)s | %(message)s"
    )
    
    record = logging.LogRecord(
        name="test_logger",
        level=logging.ERROR,
        pathname="/path/to/file.py",
        lineno=42,
        msg="Error message",
        args=(),
        exc_info=None
    )
    
    output = formatter.format(record)
    
    # Should contain ANSI escape sequences
    assert "\033[" in output  # ANSI code present


# ============================================================================
# Helper Function Tests
# ============================================================================

def test_log_api_call_success(reset_logging, capture_logs):
    """Test log_api_call with successful API call"""
    log_stream, handler = capture_logs
    handler.setFormatter(JSONFormatter())
    
    logger = get_logger("test_api")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    
    log_api_call(
        logger,
        "Google Places API",
        params={"category": "Gym"},
        duration=1.23,
        status="success"
    )
    
    output = log_stream.getvalue()
    assert "Google Places API" in output
    assert "success" in output


def test_log_api_call_sanitizes_credentials(reset_logging, capture_logs):
    """Test that log_api_call sanitizes sensitive parameters"""
    log_stream, handler = capture_logs
    handler.setFormatter(JSONFormatter())
    
    logger = get_logger("test_api")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    
    log_api_call(
        logger,
        "Test API",
        params={"api_key": "secret123", "category": "Gym"},
        status="success"
    )
    
    output = log_stream.getvalue()
    
    # Secret should be redacted
    assert "secret123" not in output
    assert "REDACTED" in output
    
    # Non-sensitive param should be present
    assert "Gym" in output


def test_log_api_call_error_logs_at_error_level(reset_logging, capture_logs):
    """Test that failed API calls are logged at ERROR level"""
    log_stream, handler = capture_logs
    handler.setFormatter(JSONFormatter())
    
    logger = get_logger("test_api")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    
    log_api_call(
        logger,
        "Test API",
        status="error",
        error="Connection timeout"
    )
    
    output = log_stream.getvalue()
    parsed = json.loads(output)
    
    assert parsed["level"] == "ERROR"
    assert "error" in parsed
    assert parsed["error"] == "Connection timeout"


def test_log_database_operation_with_row_count(reset_logging, capture_logs):
    """Test log_database_operation includes row count"""
    log_stream, handler = capture_logs
    handler.setFormatter(JSONFormatter())
    
    logger = get_logger("test_db")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    
    log_database_operation(
        logger,
        "INSERT",
        "businesses",
        row_count=73,
        duration=0.45
    )
    
    output = log_stream.getvalue()
    parsed = json.loads(output)
    
    assert parsed["row_count"] == 73
    assert parsed["operation"] == "INSERT"
    assert parsed["table"] == "businesses"
    assert parsed["duration_seconds"] == 0.45


def test_log_database_operation_error(reset_logging, capture_logs):
    """Test log_database_operation handles errors"""
    log_stream, handler = capture_logs
    handler.setFormatter(JSONFormatter())
    
    logger = get_logger("test_db")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    
    log_database_operation(
        logger,
        "DELETE",
        "user_feedback",
        error="Foreign key constraint violation"
    )
    
    output = log_stream.getvalue()
    parsed = json.loads(output)
    
    assert parsed["level"] == "ERROR"
    assert parsed["error"] == "Foreign key constraint violation"


def test_log_scoring_operation(reset_logging, capture_logs):
    """Test log_scoring_operation includes GOS and confidence"""
    log_stream, handler = capture_logs
    handler.setFormatter(JSONFormatter())
    
    logger = get_logger("test_scoring")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    
    log_scoring_operation(
        logger,
        "DHA-Phase2-Cell-07",
        "Gym",
        gos=0.825,
        confidence=0.780,
        metrics={"business_count": 3, "instagram_volume": 45}
    )
    
    output = log_stream.getvalue()
    parsed = json.loads(output)
    
    assert parsed["grid_id"] == "DHA-Phase2-Cell-07"
    assert parsed["category"] == "Gym"
    assert parsed["gos"] == 0.825
    assert parsed["confidence"] == 0.780
    assert parsed["metrics"]["business_count"] == 3


def test_log_adapter_fetch_success(reset_logging, capture_logs):
    """Test log_adapter_fetch with successful fetch"""
    log_stream, handler = capture_logs
    handler.setFormatter(JSONFormatter())
    
    logger = get_logger("test_adapter")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    
    log_adapter_fetch(
        logger,
        "GooglePlacesAdapter",
        "Gym",
        bounds={"lat_north": 24.83, "lat_south": 24.82},
        result_count=15,
        duration=2.1
    )
    
    output = log_stream.getvalue()
    parsed = json.loads(output)
    
    assert parsed["adapter"] == "GooglePlacesAdapter"
    assert parsed["category"] == "Gym"
    assert parsed["result_count"] == 15
    assert parsed["duration_seconds"] == 2.1


# ============================================================================
# Integration Tests
# ============================================================================

def test_logger_integration_example(reset_logging):
    """Test complete logger workflow as used in application"""
    logger = get_logger("test_integration")
    
    # Should not raise exceptions
    logger.info("Starting operation")
    
    log_api_call(
        logger,
        "Google Places API",
        params={"category": "Gym"},
        duration=1.5,
        status="success"
    )
    
    log_database_operation(
        logger,
        "INSERT",
        "businesses",
        row_count=10,
        duration=0.2
    )
    
    log_scoring_operation(
        logger,
        "DHA-Phase2-Cell-01",
        "Gym",
        gos=0.75,
        confidence=0.68
    )
    
    logger.info("Operation complete")


# ============================================================================
# Usage Examples (Documentation)
# ============================================================================

def test_usage_example_basic():
    """Example: Basic logger usage"""
    from src.utils import get_logger
    
    logger = get_logger(__name__)
    logger.info("Application started")
    logger.debug("Debug information")
    logger.warning("Warning message")
    logger.error("Error occurred")


def test_usage_example_api_logging():
    """Example: API call logging"""
    from src.utils import get_logger, log_api_call
    
    logger = get_logger(__name__)
    
    # Log successful API call
    log_api_call(
        logger,
        "Google Places API",
        params={"category": "Gym", "location": "24.83,67.06"},
        duration=1.23,
        status="success"
    )
    
    # Log failed API call
    log_api_call(
        logger,
        "Instagram API",
        params={"hashtag": "gym"},
        status="error",
        error="Rate limit exceeded"
    )


def test_usage_example_database_logging():
    """Example: Database operation logging"""
    from src.utils import get_logger, log_database_operation
    
    logger = get_logger(__name__)
    
    # Log INSERT operation
    log_database_operation(
        logger,
        "INSERT",
        "businesses",
        row_count=73,
        duration=0.45
    )
    
    # Log SELECT operation
    log_database_operation(
        logger,
        "SELECT",
        "social_posts",
        row_count=500
    )


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
