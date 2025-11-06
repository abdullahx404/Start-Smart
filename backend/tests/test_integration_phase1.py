"""
Integration Tests for Phase 1 Data Pipeline

Tests the complete data flow:
    GooglePlacesAdapter (API fetch with mocked responses)
    → GeospatialService (grid assignment)
    → Database (ORM persistence)

This verifies:
- Adapter correctly fetches and converts business data
- GeospatialService assigns correct grid_ids
- ORM models serialize/deserialize properly
- Database constraints are satisfied
- Full pipeline executes without errors

Usage:
    pytest tests/test_integration_phase1.py -v
    pytest tests/test_integration_phase1.py -v --cov=src --cov-report=term
"""

import pytest
from decimal import Decimal
from datetime import datetime
from typing import List
from unittest.mock import MagicMock, patch
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.adapters.google_places_adapter import GooglePlacesAdapter
from src.services.geospatial_service import GeospatialService
from src.database.models import Base, GridCellModel, BusinessModel


# ============================================================================
# Test Database Setup
# ============================================================================

@contextmanager
def create_test_database():
    """
    Create an in-memory SQLite database for integration testing.
    
    Creates only the tables we need (grid_cells, businesses).
    Avoids tables with PostgreSQL-specific types (JSONB).
    """
    # Create in-memory SQLite engine
    engine = create_engine("sqlite:///:memory:", echo=False)
    
    # Create only the tables we need (avoid JSONB incompatibility)
    GridCellModel.__table__.create(engine, checkfirst=True)
    BusinessModel.__table__.create(engine, checkfirst=True)
    
    # Create session factory
    SessionLocal = sessionmaker(bind=engine)
    
    try:
        yield SessionLocal
    finally:
        # Cleanup
        BusinessModel.__table__.drop(engine, checkfirst=True)
        GridCellModel.__table__.drop(engine, checkfirst=True)
        engine.dispose()


def seed_test_grids(session) -> List[GridCellModel]:
    """
    Seed test database with realistic Karachi grid cells.
    
    Returns 3 grids:
    - DHA-Phase2-Cell-01: Center (24.8278, 67.0595)
    - DHA-Phase2-Cell-02: Adjacent to Cell-01
    - Clifton-Cell-01: Separate neighborhood
    """
    grids = [
        GridCellModel(
            grid_id="DHA-Phase2-Cell-01",
            neighborhood="DHA Phase 2",
            lat_center=Decimal("24.8278"),
            lon_center=Decimal("67.0595"),
            lat_north=Decimal("24.8308"),
            lat_south=Decimal("24.8248"),
            lon_east=Decimal("67.0625"),
            lon_west=Decimal("67.0565"),
            area_km2=Decimal("0.5"),
        ),
        GridCellModel(
            grid_id="DHA-Phase2-Cell-02",
            neighborhood="DHA Phase 2",
            lat_center=Decimal("24.8338"),
            lon_center=Decimal("67.0595"),
            lat_north=Decimal("24.8368"),
            lat_south=Decimal("24.8308"),
            lon_east=Decimal("67.0625"),
            lon_west=Decimal("67.0565"),
            area_km2=Decimal("0.5"),
        ),
        GridCellModel(
            grid_id="Clifton-Cell-01",
            neighborhood="Clifton",
            lat_center=Decimal("24.8100"),
            lon_center=Decimal("67.0300"),
            lat_north=Decimal("24.8130"),
            lat_south=Decimal("24.8070"),
            lon_east=Decimal("67.0330"),
            lon_west=Decimal("67.0270"),
            area_km2=Decimal("0.5"),
        ),
    ]
    
    for grid in grids:
        session.add(grid)
    session.commit()
    
    return grids


# ============================================================================
# Mock Google Places API Responses
# ============================================================================

def create_mock_google_places_response():
    """
    Create realistic mock response from Google Places API.
    
    Returns 3 gyms in DHA Phase 2 area with realistic coordinates.
    """
    return [
        {
            "name": "Gold's Gym DHA",
            "place_id": "ChIJ_test_golds_gym_dha",
            "geometry": {
                "location": {
                    "lat": 24.8278,  # Center of DHA-Phase2-Cell-01
                    "lng": 67.0595,
                }
            },
            "rating": 4.5,
            "user_ratings_total": 127,
            "vicinity": "Phase 2 Extension, DHA",
            "types": ["gym", "health", "point_of_interest"],
            "business_status": "OPERATIONAL",
        },
        {
            "name": "Fitness First DHA",
            "place_id": "ChIJ_test_fitness_first_dha",
            "geometry": {
                "location": {
                    "lat": 24.8285,  # Inside DHA-Phase2-Cell-01
                    "lng": 67.0600,
                }
            },
            "rating": 4.3,
            "user_ratings_total": 89,
            "vicinity": "Khayaban-e-Seher, DHA Phase 2",
            "types": ["gym", "health"],
            "business_status": "OPERATIONAL",
        },
        {
            "name": "The Gym Clifton",
            "place_id": "ChIJ_test_gym_clifton",
            "geometry": {
                "location": {
                    "lat": 24.8100,  # Center of Clifton-Cell-01
                    "lng": 67.0300,
                }
            },
            "rating": 4.2,
            "user_ratings_total": 56,
            "vicinity": "Clifton Block 2",
            "types": ["gym", "health"],
            "business_status": "OPERATIONAL",
        },
    ]


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def test_db():
    """Provide test database session factory."""
    with create_test_database() as SessionLocal:
        yield SessionLocal


@pytest.fixture
def seeded_db(test_db):
    """Provide database pre-seeded with grid cells."""
    session = test_db()
    try:
        grids = seed_test_grids(session)
        yield test_db, grids
    finally:
        session.close()


@pytest.fixture
def mock_googlemaps_client():
    """
    Provide mock googlemaps.Client with realistic API responses.
    """
    mock_client = MagicMock()
    mock_places = create_mock_google_places_response()
    
    # Mock places_nearby() to return our test data
    mock_client.places_nearby.return_value = {
        "results": mock_places,
        "status": "OK",
    }
    
    return mock_client


def mock_get_session(SessionLocal):
    """Create a mock get_session that returns test database session."""
    @contextmanager
    def _get_session():
        session = SessionLocal()
        try:
            yield session
        finally:
            session.close()
    
    return _get_session


# ============================================================================
# Integration Tests
# ============================================================================

class TestPhase1Integration:
    """Integration tests for complete Phase 1 data pipeline."""
    
    def test_full_pipeline_google_places_to_database(self, seeded_db, mock_googlemaps_client):
        """
        Test complete pipeline: API fetch → Grid assignment → Database storage.
        
        This is the PRIMARY integration test verifying:
        1. GooglePlacesAdapter fetches and converts API data
        2. GeospatialService assigns correct grid_ids
        3. Businesses are persisted to database
        4. All ORM fields are populated correctly
        5. Database constraints are satisfied
        """
        SessionLocal, grids = seeded_db
        
        # Patch googlemaps.Client and get_session for geospatial service
        with patch('src.adapters.google_places_adapter.googlemaps.Client', return_value=mock_googlemaps_client):
            with patch('src.services.geospatial_service.get_session', mock_get_session(SessionLocal)):
                # Note: GooglePlacesAdapter doesn't persist to DB directly
                # It returns Pydantic Business objects
                # We need to manually convert and persist them for this integration test
                
                # Step 1: Initialize GeospatialService (loads grids)
                geo_service = GeospatialService(auto_load=True)
                
                # Verify grids loaded
                assert geo_service.is_initialized()
                assert len(geo_service.grids) == 3
                
                # Step 2: Fetch businesses using GooglePlacesAdapter
                adapter = GooglePlacesAdapter(api_key="test_api_key_12345")
                
                # Define search bounds (covers DHA Phase 2 area)
                bounds = {
                    "lat_north": 24.84,
                    "lat_south": 24.82,
                    "lon_east": 67.07,
                    "lon_west": 67.05,
                }
                
                businesses = adapter.fetch_businesses(
                    category="Gym",
                    bounds=bounds,
                    force_refresh=True  # Bypass cache
                )
                
                # Step 3: Verify businesses fetched (Pydantic objects)
                assert len(businesses) == 3, "Should fetch 3 businesses"
                
                # Verify business data structure
                for business in businesses:
                    assert business.name is not None
                    assert business.business_id is not None
                    assert business.category == "Gym"
                    assert business.lat is not None
                    assert business.lon is not None
                    assert business.grid_id is not None, "grid_id should be assigned"
                
                # Step 4: Manually persist Pydantic businesses to database
                # (In real pipeline, this would be done by a separate persistence layer)
                session = SessionLocal()
                try:
                    for biz in businesses:
                        # Convert Pydantic to ORM model
                        db_business = BusinessModel.from_pydantic(biz)
                        session.add(db_business)
                    session.commit()
                    
                    # Step 5: Verify grid assignments
                    grid_assignments = {b.name: b.grid_id for b in businesses}
                    
                    # Gold's Gym at (24.8278, 67.0595) → DHA-Phase2-Cell-01
                    assert grid_assignments["Gold's Gym DHA"] == "DHA-Phase2-Cell-01"
                    
                    # Fitness First at (24.8285, 67.0600) → DHA-Phase2-Cell-01
                    assert grid_assignments["Fitness First DHA"] == "DHA-Phase2-Cell-01"
                    
                    # The Gym Clifton at (24.8100, 67.0300) → Clifton-Cell-01
                    assert grid_assignments["The Gym Clifton"] == "Clifton-Cell-01"
                    
                    # Step 6: Query database to verify persistence
                    db_businesses = session.query(BusinessModel).all()
                    
                    # Verify count
                    assert len(db_businesses) == 3, "All 3 businesses should be in database"
                    
                    # Verify all fields populated
                    for db_biz in db_businesses:
                        assert db_biz.name is not None
                        assert db_biz.business_id is not None
                        assert db_biz.category == "Gym"
                        assert db_biz.lat is not None
                        assert db_biz.lon is not None
                        assert db_biz.grid_id is not None
                        assert db_biz.rating is not None
                        assert db_biz.review_count is not None
                        assert db_biz.source == "google_places"
                        assert db_biz.fetched_at is not None
                        
                    # Verify grid distribution
                    dha_businesses = session.query(BusinessModel).filter_by(
                        grid_id="DHA-Phase2-Cell-01"
                    ).all()
                    assert len(dha_businesses) == 2, "2 businesses in DHA-Phase2-Cell-01"
                    
                    clifton_businesses = session.query(BusinessModel).filter_by(
                        grid_id="Clifton-Cell-01"
                    ).all()
                    assert len(clifton_businesses) == 1, "1 business in Clifton-Cell-01"
                    
                finally:
                    session.close()
    
    def test_pipeline_with_no_results(self, seeded_db, mock_googlemaps_client):
        """Test pipeline handles empty API results gracefully."""
        SessionLocal, grids = seeded_db
        
        # Mock empty response
        mock_googlemaps_client.places_nearby.return_value = {
            "results": [],
            "status": "ZERO_RESULTS",
        }
        
        with patch('src.adapters.google_places_adapter.googlemaps.Client', return_value=mock_googlemaps_client):
            with patch('src.services.geospatial_service.get_session', mock_get_session(SessionLocal)):
                
                # Initialize services
                geo_service = GeospatialService(auto_load=True)
                adapter = GooglePlacesAdapter(api_key="test_api_key_12345")
                
                bounds = {
                    "lat_south": 24.82,
                    "lat_north": 24.84,
                    "lon_west": 67.05,
                    "lon_east": 67.07,
                }
                
                businesses = adapter.fetch_businesses(
                    category="Gym",
                    bounds=bounds,
                    force_refresh=True
                )
                
                # Should return empty list, not crash
                assert businesses == []
                
                # Database should be empty
                session = SessionLocal()
                try:
                    db_count = session.query(BusinessModel).count()
                    assert db_count == 0
                finally:
                    session.close()
    
    def test_pipeline_with_missing_coordinates(self, seeded_db, mock_googlemaps_client):
        """Test pipeline handles businesses with missing coordinates."""
        SessionLocal, grids = seeded_db
        
        # Mock response with missing coordinates
        mock_googlemaps_client.places_nearby.return_value = {
            "results": [
                {
                    "name": "Incomplete Gym",
                    "place_id": "ChIJ_test_incomplete",
                    "geometry": {},  # Missing location
                    "types": ["gym"],
                }
            ],
            "status": "OK",
        }
        
        with patch('src.adapters.google_places_adapter.googlemaps.Client', return_value=mock_googlemaps_client):
            with patch('src.services.geospatial_service.get_session', mock_get_session(SessionLocal)):
                
                geo_service = GeospatialService(auto_load=True)
                adapter = GooglePlacesAdapter(api_key="test_api_key_12345")
                
                bounds = {
                    "lat_south": 24.82,
                    "lat_north": 24.84,
                    "lon_west": 67.05,
                    "lon_east": 67.07,
                }
                
                businesses = adapter.fetch_businesses(
                    category="Gym",
                    bounds=bounds,
                    force_refresh=True
                )
                
                # Should skip businesses without coordinates
                assert businesses == []
    
    def test_pipeline_with_coordinates_outside_grids(self, seeded_db, mock_googlemaps_client):
        """Test pipeline handles businesses outside all grid cells."""
        SessionLocal, grids = seeded_db
        
        # Mock response with coordinates outside all grids
        mock_googlemaps_client.places_nearby.return_value = {
            "results": [
                {
                    "name": "Far Away Gym",
                    "place_id": "ChIJ_test_far_gym",
                    "geometry": {
                        "location": {
                            "lat": 25.0000,  # Outside all test grids
                            "lng": 68.0000,
                        }
                    },
                    "rating": 4.0,
                    "user_ratings_total": 10,
                    "vicinity": "Far Location",
                    "types": ["gym"],
                    "business_status": "OPERATIONAL",
                }
            ],
            "status": "OK",
        }
        
        with patch('src.adapters.google_places_adapter.googlemaps.Client', return_value=mock_googlemaps_client):
            with patch('src.services.geospatial_service.get_session', mock_get_session(SessionLocal)):
                
                geo_service = GeospatialService(auto_load=True)
                adapter = GooglePlacesAdapter(api_key="test_api_key_12345")
                
                bounds = {
                    "lat_south": 24.82,
                    "lat_north": 25.50,
                    "lon_west": 67.05,
                    "lon_east": 68.50,
                }
                
                businesses = adapter.fetch_businesses(
                    category="Gym",
                    bounds=bounds,
                    force_refresh=True
                )
                
                # Adapter returns business even if grid_id is None
                # (Allows storing businesses that are outside grids)
                assert len(businesses) == 1
                assert businesses[0].grid_id is None  # No grid assignment
                assert businesses[0].name == "Far Away Gym"
    
    def test_orm_serialization_deserialization(self, seeded_db):
        """Test ORM models serialize/deserialize correctly."""
        SessionLocal, grids = seeded_db
        
        session = SessionLocal()
        try:
            # Create a business manually using correct column names
            business = BusinessModel(
                business_id="ChIJ_test_serialization",
                name="Test Gym",
                category="Gym",
                lat=Decimal("24.8278"),
                lon=Decimal("67.0595"),
                grid_id="DHA-Phase2-Cell-01",
                rating=Decimal("4.5"),
                review_count=100,
                source="google_places",
            )
            
            session.add(business)
            session.commit()
            
            # Query it back
            db_business = session.query(BusinessModel).filter_by(
                business_id="ChIJ_test_serialization"
            ).first()
            
            assert db_business is not None
            assert db_business.name == "Test Gym"
            assert db_business.category == "Gym"
            assert float(db_business.lat) == 24.8278
            assert float(db_business.lon) == 67.0595
            assert db_business.grid_id == "DHA-Phase2-Cell-01"
            assert float(db_business.rating) == 4.5
            assert db_business.review_count == 100
            
            # Test to_dict() method
            business_dict = db_business.to_dict()
            assert business_dict["name"] == "Test Gym"
            assert business_dict["category"] == "Gym"
            assert business_dict["grid_id"] == "DHA-Phase2-Cell-01"
            
        finally:
            session.close()
    
    def test_database_constraints(self, seeded_db):
        """Test database constraints are enforced."""
        SessionLocal, grids = seeded_db
        
        session = SessionLocal()
        try:
            # Test unique constraint on business_id
            biz1 = BusinessModel(
                business_id="ChIJ_test_duplicate",
                name="Gym 1",
                category="Gym",
                lat=Decimal("24.8278"),
                lon=Decimal("67.0595"),
                grid_id="DHA-Phase2-Cell-01",
                source="google_places",
            )
            session.add(biz1)
            session.commit()
            
            # Try to add duplicate - should raise IntegrityError
            biz2 = BusinessModel(
                business_id="ChIJ_test_duplicate",  # Duplicate
                name="Gym 2",
                category="Gym",
                lat=Decimal("24.8285"),
                lon=Decimal("67.0600"),
                grid_id="DHA-Phase2-Cell-01",
                source="google_places",
            )
            session.add(biz2)
            
            # Expect IntegrityError
            with pytest.raises(Exception) as exc_info:
                session.commit()
            
            # Verify it's an integrity error
            assert "UNIQUE constraint" in str(exc_info.value) or "IntegrityError" in str(type(exc_info.value))
            
        finally:
            session.rollback()
            session.close()


# ============================================================================
# Performance Tests
# ============================================================================

class TestPhase1Performance:
    """Performance tests for Phase 1 pipeline."""
    
    def test_pipeline_performance_10_businesses(self, seeded_db, mock_googlemaps_client):
        """Test pipeline can handle 10 businesses efficiently."""
        import time
        
        SessionLocal, grids = seeded_db
        
        # Mock 10 businesses
        mock_businesses = []
        for i in range(10):
            mock_businesses.append({
                "name": f"Gym {i+1}",
                "place_id": f"ChIJ_test_gym_{i+1}",
                "geometry": {
                    "location": {
                        "lat": 24.8278 + (i * 0.001),
                        "lng": 67.0595 + (i * 0.001),
                    }
                },
                "rating": 4.0 + (i * 0.1),
                "user_ratings_total": 50 + i,
                "vicinity": f"Location {i+1}",
                "types": ["gym"],
                "business_status": "OPERATIONAL",
            })
        
        mock_googlemaps_client.places_nearby.return_value = {
            "results": mock_businesses,
            "status": "OK",
        }
        
        with patch('src.adapters.google_places_adapter.googlemaps.Client', return_value=mock_googlemaps_client):
            with patch('src.services.geospatial_service.get_session', mock_get_session(SessionLocal)):
                
                geo_service = GeospatialService(auto_load=True)
                adapter = GooglePlacesAdapter(api_key="test_api_key_12345")
                
                bounds = {
                    "lat_south": 24.82,
                    "lat_north": 24.84,
                    "lon_west": 67.05,
                    "lon_east": 67.07,
                }
                
                start_time = time.time()
                businesses = adapter.fetch_businesses(
                    category="Gym",
                    bounds=bounds,
                    force_refresh=True
                )
                duration = time.time() - start_time
                
                # Should complete in reasonable time (< 1 second for 10 businesses)
                assert duration < 1.0, f"Pipeline took {duration:.3f}s (should be < 1s)"
                
                # Verify all businesses processed
                assert len(businesses) == 10


# ============================================================================
# Summary
# ============================================================================

if __name__ == "__main__":
    """
    Run integration tests with:
        pytest tests/test_integration_phase1.py -v
        pytest tests/test_integration_phase1.py -v --cov=src --cov-report=term-missing
    """
    pytest.main([__file__, "-v", "--tb=short"])
