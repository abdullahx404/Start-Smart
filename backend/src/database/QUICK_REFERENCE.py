"""
Database Connection - Quick Reference

Common usage patterns for src/database/connection.py
"""

# ========== IMPORTS ==========

from src.database import get_session
from src.database.models import BusinessModel, SocialPostModel, GridMetricsModel


# ========== QUERY PATTERNS ==========

# Simple query
with get_session() as session:
    businesses = session.query(BusinessModel).all()


# Filter by field
with get_session() as session:
    gyms = session.query(BusinessModel).filter_by(category="Gym").all()


# Filter with conditions
with get_session() as session:
    top_rated = session.query(BusinessModel).filter(
        BusinessModel.rating >= 4.5
    ).all()


# Get single record
with get_session() as session:
    business = session.query(BusinessModel).filter_by(
        business_id="gym-001"
    ).first()  # Returns None if not found


# Count records
with get_session() as session:
    count = session.query(BusinessModel).filter_by(category="Gym").count()


# Order results
with get_session() as session:
    top_businesses = session.query(BusinessModel).order_by(
        BusinessModel.rating.desc()
    ).limit(10).all()


# Join queries
with get_session() as session:
    results = session.query(BusinessModel, GridMetricsModel).join(
        GridMetricsModel,
        BusinessModel.grid_id == GridMetricsModel.grid_id
    ).all()


# ========== INSERT PATTERNS ==========

# Insert single record
with get_session() as session:
    new_business = BusinessModel(
        business_id="gym-001",
        name="PowerHouse Gym",
        lat=24.8300,
        lon=67.0600,
        category="Gym",
        rating=4.5,
        review_count=120
    )
    session.add(new_business)
    # Auto-commits on exit


# Insert multiple records
with get_session() as session:
    businesses = [
        BusinessModel(business_id=f"gym-{i}", name=f"Gym {i}")
        for i in range(10)
    ]
    session.add_all(businesses)


# Bulk insert (faster for large datasets)
with get_session() as session:
    businesses = [...]  # List of BusinessModel objects
    session.bulk_save_objects(businesses)


# ========== UPDATE PATTERNS ==========

# Update single record
with get_session() as session:
    business = session.query(BusinessModel).filter_by(
        business_id="gym-001"
    ).first()
    
    if business:
        business.rating = 4.8
        business.review_count = 150
        # Auto-commits on exit


# Update multiple records
with get_session() as session:
    session.query(BusinessModel).filter_by(category="Gym").update({
        "source": "google_places"
    })


# ========== DELETE PATTERNS ==========

# Delete single record
with get_session() as session:
    business = session.query(BusinessModel).filter_by(
        business_id="gym-001"
    ).first()
    
    if business:
        session.delete(business)


# Delete multiple records
with get_session() as session:
    session.query(BusinessModel).filter_by(category="Gym").delete()


# ========== TRANSACTION PATTERNS ==========

# Manual transaction control
with get_session() as session:
    try:
        # Multiple operations
        session.add(business1)
        session.add(business2)
        session.flush()  # Send to DB but don't commit
        
        # More operations
        session.add(business3)
        
        # Auto-commits on successful exit
    except Exception as e:
        # Auto-rolls back on error
        raise


# ========== AGGREGATION PATTERNS ==========

from sqlalchemy import func

# Count by category
with get_session() as session:
    results = session.query(
        BusinessModel.category,
        func.count(BusinessModel.business_id)
    ).group_by(BusinessModel.category).all()


# Average rating per grid
with get_session() as session:
    results = session.query(
        BusinessModel.grid_id,
        func.avg(BusinessModel.rating)
    ).group_by(BusinessModel.grid_id).all()


# ========== ERROR HANDLING ==========

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

try:
    with get_session() as session:
        # Your operations
        pass
except IntegrityError as e:
    print(f"Constraint violation: {e}")
except SQLAlchemyError as e:
    print(f"Database error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")


# ========== UTILITIES ==========

from src.database import check_connection, create_all_tables, drop_all_tables

# Health check
if check_connection():
    print("Database accessible")

# Create tables (testing only)
create_all_tables()

# Drop all tables (DANGER - testing only)
drop_all_tables()
