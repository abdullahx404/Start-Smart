"""
Database Connection Module (DATABASE DISABLED)

This module provides mock/dummy implementations for database operations.
The actual PostgreSQL database has been disabled for serverless deployment.

All data is now fetched live from Google Places API.
"""

import os
import logging
from contextlib import contextmanager
from typing import Generator, Any

from sqlalchemy.orm import declarative_base

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

logger.info("🚫 Database DISABLED - Running in serverless mode (no PostgreSQL)")

# ========== Real Base for Model Definitions ==========
# We still need a real Base so the model classes can be defined
# They just won't be used to actually query a database

Base = declarative_base()

# ========== Mock Objects ==========

class MockSession:
    """Mock session that does nothing - database operations are disabled."""
    
    def execute(self, *args, **kwargs):
        return None
    
    def query(self, *args, **kwargs):
        return MockQuery()
    
    def add(self, *args, **kwargs):
        pass
    
    def commit(self):
        pass
    
    def rollback(self):
        pass
    
    def close(self):
        pass
    
    def flush(self):
        pass


class MockQuery:
    """Mock query that returns empty results."""
    
    def filter(self, *args, **kwargs):
        return self
    
    def filter_by(self, *args, **kwargs):
        return self
    
    def all(self):
        return []
    
    def first(self):
        return None
    
    def count(self):
        return 0
    
    def order_by(self, *args, **kwargs):
        return self
    
    def limit(self, *args, **kwargs):
        return self
    
    def offset(self, *args, **kwargs):
        return self
    
    def group_by(self, *args, **kwargs):
        return self
    
    def outerjoin(self, *args, **kwargs):
        return self


class MockEngine:
    """Mock engine that does nothing."""
    
    def dispose(self):
        pass
    
    def execute(self, *args, **kwargs):
        return None


# ========== Exports (Mock Implementations) ==========

engine = MockEngine()


@contextmanager
def get_session() -> Generator[MockSession, None, None]:
    """
    Provides a mock database session.
    Database is disabled - this is a no-op.
    """
    session = MockSession()
    try:
        yield session
    finally:
        pass


def get_session_direct() -> MockSession:
    """Returns a mock session."""
    return MockSession()


def create_all_tables() -> None:
    """No-op - database disabled."""
    logger.info("create_all_tables called but database is disabled")


def drop_all_tables() -> None:
    """No-op - database disabled."""
    logger.info("drop_all_tables called but database is disabled")


def check_connection() -> bool:
    """Always returns True - database check disabled."""
    logger.info("Database check skipped - running in serverless mode")
    return True


def dispose_engine() -> None:
    """No-op - database disabled."""
    logger.info("dispose_engine called but database is disabled")
