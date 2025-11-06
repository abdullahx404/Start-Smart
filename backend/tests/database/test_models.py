"""
ORM Models Tests

Tests for SQLAlchemy ORM models in src/database/models.py

Usage:
    pytest tests/database/test_models.py -v
"""

import pytest
from datetime import datetime
from decimal import Decimal


# Note: These tests require sqlalchemy to be installed
# Run: pip install sqlalchemy python-dotenv psycopg2-binary


def test_grid_cell_model_creation():
    """Test GridCellModel instantiation and to_dict()"""
    from src.database.models import GridCellModel
    
    grid = GridCellModel(
        grid_id="DHA-Phase2-Cell-07",
        neighborhood="DHA Phase 2",
        lat_center=Decimal("24.8290"),
        lon_center=Decimal("67.0610"),
        lat_north=Decimal("24.8320"),
        lat_south=Decimal("24.8260"),
        lon_east=Decimal("67.0640"),
        lon_west=Decimal("67.0580"),
        area_km2=Decimal("0.5"),
    )
    
    assert grid.grid_id == "DHA-Phase2-Cell-07"
    assert grid.neighborhood == "DHA Phase 2"
    assert float(grid.lat_center) == 24.8290
    
    # Test to_dict()
    grid_dict = grid.to_dict()
    assert grid_dict["grid_id"] == "DHA-Phase2-Cell-07"
    assert grid_dict["lat_center"] == 24.8290
    assert isinstance(grid_dict["lat_center"], float)


def test_business_model_creation():
    """Test BusinessModel instantiation"""
    from src.database.models import BusinessModel
    
    business = BusinessModel(
        business_id="gym-001",
        name="PowerHouse Gym",
        lat=Decimal("24.8300"),
        lon=Decimal("67.0600"),
        category="Gym",
        rating=Decimal("4.5"),
        review_count=120,
        source="google_places",
        grid_id="DHA-Phase2-Cell-07",
    )
    
    assert business.business_id == "gym-001"
    assert business.name == "PowerHouse Gym"
    assert business.category == "Gym"
    assert float(business.rating) == 4.5
    
    # Test to_dict()
    business_dict = business.to_dict()
    assert business_dict["rating"] == 4.5
    assert business_dict["category"] == "Gym"


def test_social_post_model_creation():
    """Test SocialPostModel instantiation"""
    from src.database.models import SocialPostModel
    
    post = SocialPostModel(
        post_id="post-001",
        source="simulated",
        text="Looking for a good gym in DHA Phase 2",
        timestamp=datetime.utcnow(),
        lat=Decimal("24.8300"),
        lon=Decimal("67.0600"),
        grid_id="DHA-Phase2-Cell-07",
        post_type="demand",
        engagement_score=25,
        is_simulated=True,
    )
    
    assert post.post_id == "post-001"
    assert post.source == "simulated"
    assert post.post_type == "demand"
    assert post.is_simulated is True
    
    # Test to_dict()
    post_dict = post.to_dict()
    assert post_dict["is_simulated"] is True
    assert post_dict["post_type"] == "demand"


def test_grid_metrics_model_creation():
    """Test GridMetricsModel instantiation"""
    from src.database.models import GridMetricsModel
    
    metrics = GridMetricsModel(
        grid_id="DHA-Phase2-Cell-07",
        category="Gym",
        business_count=5,
        instagram_volume=120,
        reddit_mentions=45,
        gos=Decimal("0.825"),
        confidence=Decimal("0.780"),
        top_posts_json={"posts": []},
        competitors_json={"businesses": []},
    )
    
    assert metrics.grid_id == "DHA-Phase2-Cell-07"
    assert metrics.category == "Gym"
    assert float(metrics.gos) == 0.825
    assert float(metrics.confidence) == 0.780
    
    # Test to_dict()
    metrics_dict = metrics.to_dict()
    assert metrics_dict["gos"] == 0.825
    assert isinstance(metrics_dict["top_posts_json"], dict)


def test_user_feedback_model_creation():
    """Test UserFeedbackModel instantiation"""
    from src.database.models import UserFeedbackModel
    
    feedback = UserFeedbackModel(
        grid_id="DHA-Phase2-Cell-07",
        category="Gym",
        rating=1,  # thumbs up
        comment="Great recommendation!",
        user_email="test@example.com",
    )
    
    assert feedback.grid_id == "DHA-Phase2-Cell-07"
    assert feedback.rating == 1
    assert feedback.comment == "Great recommendation!"
    
    # Test to_dict()
    feedback_dict = feedback.to_dict()
    assert feedback_dict["rating"] == 1


def test_from_pydantic_grid_cell():
    """Test GridCellModel.from_pydantic()"""
    from contracts.models import GridCell
    from src.database.models import GridCellModel
    
    # Create Pydantic model
    pydantic_grid = GridCell(
        grid_id="DHA-Phase2-Cell-07",
        neighborhood="DHA Phase 2",
        lat_center=24.8290,
        lon_center=67.0610,
        lat_north=24.8320,
        lat_south=24.8260,
        lon_east=67.0640,
        lon_west=67.0580,
        area_km2=0.5,
    )
    
    # Convert to ORM model
    orm_grid = GridCellModel.from_pydantic(pydantic_grid)
    
    assert orm_grid.grid_id == "DHA-Phase2-Cell-07"
    assert float(orm_grid.lat_center) == 24.8290
    assert isinstance(orm_grid.lat_center, Decimal)


def test_from_pydantic_business():
    """Test BusinessModel.from_pydantic()"""
    from contracts.models import Business, Category, Source
    from src.database.models import BusinessModel
    
    # Create Pydantic model
    pydantic_business = Business(
        business_id="gym-001",
        name="PowerHouse Gym",
        lat=24.8300,
        lon=67.0600,
        category=Category.GYM,
        rating=4.5,
        review_count=120,
        source=Source.GOOGLE_PLACES,
        grid_id="DHA-Phase2-Cell-07",
        fetched_at=datetime.utcnow(),
    )
    
    # Convert to ORM model
    orm_business = BusinessModel.from_pydantic(pydantic_business)
    
    assert orm_business.business_id == "gym-001"
    assert orm_business.category == "Gym"
    assert float(orm_business.rating) == 4.5


def test_get_all_models():
    """Test get_all_models() helper function"""
    from src.database.models import get_all_models
    
    models = get_all_models()
    assert len(models) == 5
    
    # Check model names
    model_names = [m.__name__ for m in models]
    assert 'GridCellModel' in model_names
    assert 'BusinessModel' in model_names
    assert 'SocialPostModel' in model_names
    assert 'GridMetricsModel' in model_names
    assert 'UserFeedbackModel' in model_names


def test_get_model_by_table_name():
    """Test get_model_by_table_name() helper function"""
    from src.database.models import get_model_by_table_name, BusinessModel
    
    model = get_model_by_table_name('businesses')
    assert model is BusinessModel
    
    # Test invalid table name
    model = get_model_by_table_name('invalid_table')
    assert model is None


@pytest.mark.skipif(
    True,  # Skip by default (requires database)
    reason="Requires database connection for integration test"
)
def test_model_database_integration():
    """
    Integration test: Create models and save to database.
    
    This test is skipped by default. To run:
    1. Ensure DATABASE_URL is set in .env
    2. Run: pytest tests/database/test_models.py::test_model_database_integration -v
    """
    from src.database import get_session, create_all_tables
    from src.database.models import GridCellModel, BusinessModel
    
    # Create tables
    create_all_tables()
    
    # Create and save a grid
    with get_session() as session:
        grid = GridCellModel(
            grid_id="TEST-Grid-01",
            neighborhood="Test Area",
            lat_center=Decimal("24.8290"),
            lon_center=Decimal("67.0610"),
            lat_north=Decimal("24.8320"),
            lat_south=Decimal("24.8260"),
            lon_east=Decimal("67.0640"),
            lon_west=Decimal("67.0580"),
        )
        session.add(grid)
    
    # Verify it was saved
    with get_session() as session:
        saved_grid = session.query(GridCellModel).filter_by(
            grid_id="TEST-Grid-01"
        ).first()
        assert saved_grid is not None
        assert saved_grid.neighborhood == "Test Area"
    
    # Clean up
    with get_session() as session:
        session.query(GridCellModel).filter_by(grid_id="TEST-Grid-01").delete()


# ========== Usage Examples (not actual tests) ==========

def example_query_businesses():
    """Example: Query businesses by category"""
    from src.database import get_session
    from src.database.models import BusinessModel
    
    with get_session() as session:
        # Get all gyms
        gyms = session.query(BusinessModel).filter_by(category="Gym").all()
        
        # Get gyms in specific grid
        grid_gyms = session.query(BusinessModel).filter_by(
            category="Gym",
            grid_id="DHA-Phase2-Cell-07"
        ).all()
        
        # Get high-rated businesses
        top_rated = session.query(BusinessModel).filter(
            BusinessModel.rating >= 4.5
        ).all()


def example_create_grid_metrics():
    """Example: Create grid metrics entry"""
    from src.database import get_session
    from src.database.models import GridMetricsModel
    from decimal import Decimal
    
    with get_session() as session:
        metrics = GridMetricsModel(
            grid_id="DHA-Phase2-Cell-07",
            category="Gym",
            business_count=5,
            instagram_volume=120,
            reddit_mentions=45,
            gos=Decimal("0.825"),
            confidence=Decimal("0.780"),
            top_posts_json={"posts": [{"text": "Need a gym", "source": "simulated"}]},
            competitors_json={"businesses": [{"name": "Gym A", "distance": 0.3}]},
        )
        session.add(metrics)
        # Auto-commits on exit


if __name__ == "__main__":
    print("Running ORM models tests...")
    print("\nTo run all tests:")
    print("  pytest tests/database/test_models.py -v")
    print("\nTo run with coverage:")
    print("  pytest tests/database/test_models.py -v --cov=src/database/models")
