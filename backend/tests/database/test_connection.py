"""
Database Connection Tests

Run these tests to verify the database connection module works correctly.

Usage:
    pytest tests/database/test_connection.py -v
"""

import pytest
import os
from unittest.mock import patch, MagicMock

# Note: These imports will fail until sqlalchemy is installed
# Run: pip install sqlalchemy python-dotenv psycopg2-binary


def test_database_url_required():
    """Test that DATABASE_URL environment variable is required"""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError, match="DATABASE_URL environment variable not set"):
            # This will fail on import if DATABASE_URL is not set
            import importlib
            import sys
            
            # Remove module if already imported
            if 'src.database.connection' in sys.modules:
                del sys.modules['src.database.connection']
            
            # Try to import (should fail)
            from src.database import connection


def test_engine_creation_postgres():
    """Test engine creation with PostgreSQL URL"""
    with patch.dict(os.environ, {
        'DATABASE_URL': 'postgresql://user:pass@localhost:5432/testdb',
        'SKIP_DB_CHECK': 'true'  # Skip connection check during import
    }):
        import importlib
        import sys
        
        # Reload module with test environment
        if 'src.database.connection' in sys.modules:
            del sys.modules['src.database.connection']
        
        from src.database import connection
        
        assert connection.is_postgres is True
        assert connection.is_sqlite is False
        assert connection.engine is not None


def test_engine_creation_sqlite():
    """Test engine creation with SQLite URL"""
    with patch.dict(os.environ, {
        'DATABASE_URL': 'sqlite:///test.db',
        'SKIP_DB_CHECK': 'true'
    }):
        import importlib
        import sys
        
        if 'src.database.connection' in sys.modules:
            del sys.modules['src.database.connection']
        
        from src.database import connection
        
        assert connection.is_sqlite is True
        assert connection.is_postgres is False


@pytest.mark.skipif(
    os.getenv('DATABASE_URL', '').startswith('sqlite'),
    reason="Requires PostgreSQL for integration test"
)
def test_session_context_manager():
    """Test session creation with context manager (integration test)"""
    from src.database import get_session
    
    # Test session creation and cleanup
    with get_session() as session:
        assert session is not None
        # Execute simple query
        result = session.execute("SELECT 1")
        assert result is not None


@pytest.mark.skipif(
    os.getenv('DATABASE_URL', '').startswith('sqlite'),
    reason="Requires PostgreSQL for integration test"
)
def test_connection_health_check():
    """Test database connection health check"""
    from src.database import check_connection
    
    result = check_connection()
    assert result is True


def test_base_declarative_exists():
    """Test that declarative base is created"""
    from src.database.connection import Base
    
    assert Base is not None
    assert hasattr(Base, 'metadata')


# ========== Usage Examples (not actual tests) ==========

def example_usage_context_manager():
    """
    Example: Using get_session() with context manager (RECOMMENDED)
    """
    from src.database import get_session
    # Assuming BusinessModel exists
    # from src.database.models import BusinessModel
    
    with get_session() as session:
        # Query example
        # businesses = session.query(BusinessModel).filter_by(category="Gym").all()
        # for business in businesses:
        #     print(business.name)
        
        # Insert example
        # new_business = BusinessModel(
        #     business_id="test-001",
        #     name="Test Gym",
        #     lat=24.8300,
        #     lon=67.0600,
        #     category="Gym"
        # )
        # session.add(new_business)
        # Session auto-commits on exit (if no exceptions)
        pass


def example_usage_direct_session():
    """
    Example: Using get_session_direct() (manual cleanup required)
    """
    from src.database import get_session_direct
    
    session = get_session_direct()
    try:
        # Your database operations here
        # result = session.query(BusinessModel).all()
        session.commit()
    except Exception as e:
        session.rollback()
        raise
    finally:
        session.close()  # MUST close manually!


def example_create_tables():
    """
    Example: Create all tables from ORM models (testing only)
    """
    from src.database import create_all_tables
    # from src.database.models import BusinessModel, SocialPostModel
    
    # This will create all tables defined in models.py
    create_all_tables()


if __name__ == "__main__":
    # Quick connection test
    print("Testing database connection...")
    
    from src.database import check_connection
    
    if check_connection():
        print("✅ Database connection successful!")
    else:
        print("❌ Database connection failed!")
