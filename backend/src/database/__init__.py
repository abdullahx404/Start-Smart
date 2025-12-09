"""
Database Module

This module manages database connections and ORM models. All database
operations should go through the session factory provided here.

Components:
    - connection: SQLAlchemy engine and session management
    - models: ORM models matching contracts/database_schema.sql

Usage:
    from src.database import get_session
    from src.database.models import BusinessModel, SocialPostModel
    
    with get_session() as session:
        businesses = session.query(BusinessModel).all()
"""

# Import database connection components
from .connection import (
    get_session,
    get_session_direct,
    engine,
    Base,
    create_all_tables,
    drop_all_tables,
    check_connection,
    dispose_engine,
)

# Import ORM models
from .models import (
    GridCellModel,
    BusinessModel,
    SocialPostModel,
    GridMetricsModel,
    UserFeedbackModel,
    get_all_models,
    get_model_by_table_name,
)

__all__ = [
    # Connection management
    "get_session",
    "get_session_direct",
    "engine",
    "Base",
    # Table operations
    "create_all_tables",
    "drop_all_tables",
    "check_connection",
    "dispose_engine",
    # ORM models
    "GridCellModel",
    "BusinessModel",
    "SocialPostModel",
    "GridMetricsModel",
    "UserFeedbackModel",
    # Helper functions
    "get_all_models",
    "get_model_by_table_name",
]
