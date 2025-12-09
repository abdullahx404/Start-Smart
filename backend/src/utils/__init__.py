"""
Utilities Module

This module contains shared utility functions and helpers used across
the application.

Components:
    - logger: Structured logging configuration
"""

# Import utilities
from src.utils.logger import (
    get_logger,
    log_api_call,
    log_database_operation,
    log_scoring_operation,
    log_adapter_fetch,
)

__all__ = [
    "get_logger",
    "log_api_call",
    "log_database_operation",
    "log_scoring_operation",
    "log_adapter_fetch",
]
