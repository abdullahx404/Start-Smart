"""
Database Connection Module

Provides SQLAlchemy engine, session factory, and ORM base for all database operations.
Uses connection pooling and proper session lifecycle management.

Usage:
    from src.database.connection import get_session, engine
    
    # Query with context manager (recommended)
    with get_session() as session:
        businesses = session.query(BusinessModel).all()
    
    # Create tables (testing only)
    from src.database.connection import create_all_tables
    create_all_tables()
"""

import os
import logging
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event, Engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.pool import NullPool, QueuePool
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ========== Configuration ==========

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL environment variable not set. "
        "Please set it in your .env file. "
        "Example: postgresql://user:password@localhost:5432/startsmart_dev"
    )

# Detect database type
is_sqlite = DATABASE_URL.startswith("sqlite")
is_postgres = DATABASE_URL.startswith("postgresql")

logger.info(f"Database type detected: {'SQLite' if is_sqlite else 'PostgreSQL'}")
logger.info(f"Database URL (masked): {DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else 'sqlite'}")

# ========== Engine Configuration ==========

# Connection pool settings
if is_sqlite:
    # SQLite: No connection pooling (single file, not thread-safe for writes)
    engine_kwargs = {
        "poolclass": NullPool,
        "connect_args": {"check_same_thread": False},  # Allow multi-threading for reads
        "echo": False,  # Set to True for SQL query logging
    }
    logger.info("Using NullPool for SQLite (no connection pooling)")
else:
    # PostgreSQL: Use connection pooling
    engine_kwargs = {
        "poolclass": QueuePool,
        "pool_size": 5,  # Number of connections to keep open
        "max_overflow": 10,  # Max connections beyond pool_size
        "pool_timeout": 30,  # Seconds to wait for available connection
        "pool_recycle": 3600,  # Recycle connections after 1 hour
        "pool_pre_ping": True,  # Verify connections before use
        "echo": False,  # Set to True for SQL query logging
    }
    logger.info("Using QueuePool for PostgreSQL (pool_size=5, max_overflow=10)")

# Create SQLAlchemy engine
try:
    engine: Engine = create_engine(DATABASE_URL, **engine_kwargs)
    logger.info("Database engine created successfully")
except Exception as e:
    logger.error(f"Failed to create database engine: {e}")
    raise


# ========== Event Listeners (PostgreSQL optimizations) ==========

if is_postgres:
    @event.listens_for(engine, "connect")
    def set_postgres_pragmas(dbapi_conn, connection_record):
        """
        Set PostgreSQL connection parameters for optimal performance.
        Called once per connection when created.
        """
        cursor = dbapi_conn.cursor()
        # Set statement timeout (30 seconds) to prevent hung queries
        cursor.execute("SET statement_timeout = '30s'")
        # Set timezone to UTC for consistency
        cursor.execute("SET timezone = 'UTC'")
        cursor.close()
        logger.debug("PostgreSQL connection pragmas set")


# ========== Declarative Base ==========

# Base class for all ORM models
Base = declarative_base()

logger.info("Declarative base created for ORM models")


# ========== Session Factory ==========

# Session factory with proper configuration
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,  # Explicit transaction control
    autoflush=False,  # Manual flush for better control
    expire_on_commit=True,  # Expire objects after commit (avoid stale data)
)

logger.info("Session factory created")


# ========== Session Management Functions ==========

@contextmanager
def get_session() -> Generator[Session, None, None]:
    """
    Context manager for database sessions.
    
    Provides automatic session cleanup and error handling.
    Use this for all database operations.
    
    Yields:
        Session: SQLAlchemy session for database operations
        
    Example:
        with get_session() as session:
            businesses = session.query(BusinessModel).all()
            
        # Session automatically closed, even if exception occurs
    
    Raises:
        Exception: Any database errors are re-raised after rollback
    """
    session = SessionLocal()
    try:
        logger.debug("Database session opened")
        yield session
        session.commit()
        logger.debug("Session committed successfully")
    except Exception as e:
        session.rollback()
        logger.error(f"Session rollback due to error: {e}")
        raise
    finally:
        session.close()
        logger.debug("Database session closed")


def get_session_direct() -> Session:
    """
    Get a database session without context manager.
    
    WARNING: You MUST manually close this session when done!
    Prefer using get_session() context manager instead.
    
    Returns:
        Session: SQLAlchemy session (must be closed manually)
        
    Example:
        session = get_session_direct()
        try:
            businesses = session.query(BusinessModel).all()
            session.commit()
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()
    """
    logger.debug("Direct session created (manual cleanup required)")
    return SessionLocal()


# ========== Table Creation (Testing/Development) ==========

def create_all_tables() -> None:
    """
    Create all tables defined by ORM models.
    
    WARNING: This should only be used for testing or initial setup.
    For production, use Alembic migrations instead.
    
    Requires:
        - All ORM models must be imported before calling this function
        - Models must inherit from Base (declarative_base)
    
    Example:
        from src.database.connection import create_all_tables
        from src.database.models import BusinessModel, SocialPostModel
        
        create_all_tables()
    
    Raises:
        Exception: If table creation fails
    """
    try:
        logger.info("Creating all tables from ORM models...")
        Base.metadata.create_all(bind=engine)
        logger.info("All tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create tables: {e}")
        raise


def drop_all_tables() -> None:
    """
    Drop all tables defined by ORM models.
    
    DANGER: This will DELETE ALL DATA! Only use for testing.
    
    Example:
        from src.database.connection import drop_all_tables
        drop_all_tables()  # Destroys all data!
    """
    try:
        logger.warning("Dropping all tables (THIS WILL DELETE ALL DATA)...")
        Base.metadata.drop_all(bind=engine)
        logger.warning("All tables dropped")
    except Exception as e:
        logger.error(f"Failed to drop tables: {e}")
        raise


# ========== Connection Health Check ==========

def check_connection() -> bool:
    """
    Test database connection.
    
    Returns:
        bool: True if connection successful, False otherwise
        
    Example:
        from src.database.connection import check_connection
        
        if check_connection():
            print("Database is accessible")
        else:
            print("Database connection failed")
    """
    try:
        with get_session() as session:
            # Execute simple query to verify connection
            session.execute("SELECT 1")
        logger.info("Database connection test: SUCCESS")
        return True
    except Exception as e:
        logger.error(f"Database connection test: FAILED - {e}")
        return False


# ========== Cleanup on Module Unload ==========

def dispose_engine() -> None:
    """
    Dispose of the database engine and close all connections.
    
    Call this during application shutdown to ensure clean exit.
    
    Example:
        import atexit
        from src.database.connection import dispose_engine
        
        atexit.register(dispose_engine)
    """
    logger.info("Disposing database engine and closing connections...")
    engine.dispose()
    logger.info("Database engine disposed")


# ========== Module Initialization ==========

# Verify connection on module import (optional, can be disabled for faster imports)
if os.getenv("SKIP_DB_CHECK") != "true":
    try:
        check_connection()
    except Exception as e:
        logger.warning(
            f"Database connection check failed during module import: {e}. "
            "Set SKIP_DB_CHECK=true to disable this check."
        )
