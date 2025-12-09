"""
Unit Tests for Geospatial Service

Tests the grid assignment functionality using in-memory SQLite database.

Test Coverage:
- Service initialization and grid loading
- Point-in-polygon assignment (center, edge, outside)
- Bounds retrieval
- Error handling and edge cases
- Empty database handling
- Overlapping grids edge case

Coverage target: ≥95%

Uses:
- pytest framework
- In-memory SQLite database with real GridCellModel instances
- Realistic Karachi coordinates

Usage:
    pytest tests/services/test_geospatial_service.py -v
    pytest tests/services/test_geospatial_service.py --cov=src.services.geospatial_service --cov-report=term
"""

import pytest
from decimal import Decimal
from typing import List
from unittest.mock import patch
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from src.services.geospatial_service import (
    GeospatialService,
    KARACHI_BOUNDS,
)
from src.database.models import Base, GridCellModel


# ============================================================================
# Test Database Setup
# ============================================================================

@contextmanager
def create_test_database():
    """Create an in-memory SQLite database for testing."""
    # Create in-memory SQLite engine
    engine = create_engine("sqlite:///:memory:", echo=False)
    
    # Create only the grid_cells table (avoid tables with JSONB which SQLite doesn't support)
    # JSONB is PostgreSQL-specific; grid_metrics table has JSONB columns
    GridCellModel.__table__.create(engine, checkfirst=True)
    
    # Create session factory
    SessionLocal = sessionmaker(bind=engine)
    
    try:
        yield SessionLocal
    finally:
        # Cleanup
        GridCellModel.__table__.drop(engine, checkfirst=True)
        engine.dispose()


def create_sample_grids() -> List[GridCellModel]:
    """
    Create sample grid cells with realistic Karachi coordinates.
    
    Returns 4 grids:
    - DHA-Phase2-Cell-01: Center (24.8278, 67.0595)
    - DHA-Phase2-Cell-02: Adjacent north
    - Clifton-Cell-01: Separate neighborhood
    - Overlapping-Cell: Partially overlaps with Cell-01 (edge case)
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
        GridCellModel(
            grid_id="Overlapping-Cell",
            neighborhood="Test Overlap",
            lat_center=Decimal("24.8283"),
            lon_center=Decimal("67.0600"),
            # Slightly overlaps with Cell-01
            lat_north=Decimal("24.8313"),
            lat_south=Decimal("24.8253"),
            lon_east=Decimal("67.0630"),
            lon_west=Decimal("67.0570"),
            area_km2=Decimal("0.5"),
        ),
    ]
    
    return grids


@pytest.fixture
def test_db():
    """Fixture providing test database session factory."""
    with create_test_database() as SessionLocal:
        yield SessionLocal


@pytest.fixture
def populated_db(test_db):
    """Fixture providing database populated with sample grids."""
    session = test_db()
    try:
        # Add sample grids
        grids = create_sample_grids()
        for grid in grids:
            session.add(grid)
        session.commit()
        yield test_db
    finally:
        session.close()


@pytest.fixture
def empty_db(test_db):
    """Fixture providing empty database (no grids)."""
    # Database is already empty, just return it
    yield test_db


# ============================================================================
# Helper Functions
# ============================================================================

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
# Initialization Tests
# ============================================================================

def test_service_initialization_with_auto_load(populated_db):
    """Test that service initializes and loads grids automatically."""
    with patch('src.services.geospatial_service.get_session', mock_get_session(populated_db)):
        service = GeospatialService(auto_load=True)
        
        assert service.is_initialized()
        assert len(service.grids) == 4
        assert "DHA-Phase2-Cell-01" in service.grids
        assert "DHA-Phase2-Cell-02" in service.grids
        assert "Clifton-Cell-01" in service.grids
        assert "Overlapping-Cell" in service.grids


def test_service_initialization_without_auto_load():
    """Test that service can be initialized without auto-loading."""
    service = GeospatialService(auto_load=False)
    
    assert not service.is_initialized()
    assert len(service.grids) == 0


def test_load_grids_manually(populated_db):
    """Test manual grid loading."""
    with patch('src.services.geospatial_service.get_session', mock_get_session(populated_db)):
        service = GeospatialService(auto_load=False)
        assert not service.is_initialized()
        
        count = service.load_grids()
        
        assert count == 4
        assert service.is_initialized()
        assert len(service.grids) == 4


def test_empty_database(empty_db):
    """Test error handling when database has no grids (test_empty_database)."""
    with patch('src.services.geospatial_service.get_session', mock_get_session(empty_db)):
        with pytest.raises(RuntimeError, match="No grid cells in database"):
            GeospatialService(auto_load=True)


def test_empty_database_graceful_none_return(empty_db):
    """Test that empty database returns None for assign_grid_id gracefully."""
    # Create service without auto_load to avoid RuntimeError
    service = GeospatialService(auto_load=False)
    
    # Manually try to assign (should fail gracefully or raise RuntimeError)
    with pytest.raises(RuntimeError, match="Grid cache is empty"):
        service.assign_grid_id(24.8278, 67.0595)


# ============================================================================
# Grid Assignment Tests - Core Functionality
# ============================================================================

def test_assign_grid_id_center(populated_db):
    """Test assignment of point in center of grid (test_assign_grid_id_center)."""
    with patch('src.services.geospatial_service.get_session', mock_get_session(populated_db)):
        service = GeospatialService()
        
        # Point at exact center of DHA-Phase2-Cell-01
        grid_id = service.assign_grid_id(24.8278, 67.0595)
        
        assert grid_id == "DHA-Phase2-Cell-01"


def test_assign_grid_id_edge(populated_db):
    """Test assignment of point on grid boundary (test_assign_grid_id_edge)."""
    with patch('src.services.geospatial_service.get_session', mock_get_session(populated_db)):
        service = GeospatialService()
        
        # Point on north boundary of DHA-Phase2-Cell-01 (shared with Cell-02)
        # At the boundary (24.8308), could be assigned to Cell-01, Cell-02, or Overlapping-Cell
        grid_id = service.assign_grid_id(24.8308, 67.0595)
        
        # Should return a valid grid_id (any of the grids that share this boundary)
        assert grid_id in ["DHA-Phase2-Cell-01", "DHA-Phase2-Cell-02", "Overlapping-Cell"]


def test_assign_grid_id_outside(populated_db):
    """Test assignment of point outside all grids (test_assign_grid_id_outside)."""
    with patch('src.services.geospatial_service.get_session', mock_get_session(populated_db)):
        service = GeospatialService()
        
        # Point far from any grid (realistic Karachi coordinates but outside grids)
        grid_id = service.assign_grid_id(25.0000, 68.0000)
        
        assert grid_id is None


def test_assign_grid_id_multiple_grids(populated_db):
    """Test overlapping grids edge case - returns first match (test_assign_grid_id_multiple_grids)."""
    with patch('src.services.geospatial_service.get_session', mock_get_session(populated_db)):
        service = GeospatialService()
        
        # Point in overlapping region between Cell-01 and Overlapping-Cell
        # Center of overlap: approximately (24.8280, 67.0600)
        grid_id = service.assign_grid_id(24.8280, 67.0600)
        
        # Should return one of the overlapping grids (first match found)
        assert grid_id in ["DHA-Phase2-Cell-01", "Overlapping-Cell"]


def test_assign_multiple_points(populated_db):
    """Test assigning multiple points to verify consistency."""
    with patch('src.services.geospatial_service.get_session', mock_get_session(populated_db)):
        service = GeospatialService()
        
        test_points = [
            (24.8278, 67.0595, "DHA-Phase2-Cell-01"),  # Center of Cell-01
            (24.8338, 67.0595, "DHA-Phase2-Cell-02"),  # Center of Cell-02
            (24.8100, 67.0300, "Clifton-Cell-01"),     # Center of Clifton
            (25.0000, 68.0000, None),                   # Outside all grids
        ]
        
        for lat, lon, expected_grid in test_points:
            result = service.assign_grid_id(lat, lon)
            assert result == expected_grid, f"Point ({lat}, {lon}) should be in {expected_grid}, got {result}"


# ============================================================================
# Bounds Retrieval Tests
# ============================================================================

def test_get_grid_bounds(populated_db):
    """Test retrieving bounds for a valid grid (test_get_grid_bounds)."""
    with patch('src.services.geospatial_service.get_session', mock_get_session(populated_db)):
        service = GeospatialService()
        
        bounds = service.get_grid_bounds("DHA-Phase2-Cell-01")
        
        assert bounds is not None
        assert bounds["lat_north"] == 24.8308
        assert bounds["lat_south"] == 24.8248
        assert bounds["lon_east"] == 67.0625
        assert bounds["lon_west"] == 67.0565
        assert bounds["lat_center"] == 24.8278
        assert bounds["lon_center"] == 67.0595


def test_get_grid_bounds_invalid_grid(populated_db):
    """Test retrieving bounds for non-existent grid."""
    with patch('src.services.geospatial_service.get_session', mock_get_session(populated_db)):
        service = GeospatialService()
        
        bounds = service.get_grid_bounds("NonExistent-Grid")
        
        assert bounds is None


def test_get_grid_bounds_returns_dict(populated_db):
    """Test that bounds dict has all required keys."""
    with patch('src.services.geospatial_service.get_session', mock_get_session(populated_db)):
        service = GeospatialService()
        
        bounds = service.get_grid_bounds("DHA-Phase2-Cell-01")
        
        required_keys = ["lat_north", "lat_south", "lon_east", "lon_west", "lat_center", "lon_center"]
        for key in required_keys:
            assert key in bounds, f"Missing key {key} in bounds dict"


# ============================================================================
# Validation Tests
# ============================================================================

def test_invalid_latitude_too_high(populated_db):
    """Test error handling for latitude > 90."""
    with patch('src.services.geospatial_service.get_session', mock_get_session(populated_db)):
        service = GeospatialService()
        
        with pytest.raises(ValueError, match="Latitude must be between"):
            service.assign_grid_id(100, 67.0595)


def test_invalid_latitude_too_low(populated_db):
    """Test error handling for latitude < -90."""
    with patch('src.services.geospatial_service.get_session', mock_get_session(populated_db)):
        service = GeospatialService()
        
        with pytest.raises(ValueError, match="Latitude must be between"):
            service.assign_grid_id(-100, 67.0595)


def test_invalid_longitude_too_high(populated_db):
    """Test error handling for longitude > 180."""
    with patch('src.services.geospatial_service.get_session', mock_get_session(populated_db)):
        service = GeospatialService()
        
        with pytest.raises(ValueError, match="Longitude must be between"):
            service.assign_grid_id(24.8278, 200)


def test_invalid_longitude_too_low(populated_db):
    """Test error handling for longitude < -180."""
    with patch('src.services.geospatial_service.get_session', mock_get_session(populated_db)):
        service = GeospatialService()
        
        with pytest.raises(ValueError, match="Longitude must be between"):
            service.assign_grid_id(24.8278, -200)


def test_non_numeric_coordinates(populated_db):
    """Test error handling for non-numeric coordinates."""
    with patch('src.services.geospatial_service.get_session', mock_get_session(populated_db)):
        service = GeospatialService()
        
        with pytest.raises(ValueError, match="Coordinates must be numeric"):
            service.assign_grid_id("invalid", "coords")


def test_coordinates_outside_karachi_bounds(populated_db):
    """Test warning for coordinates outside Karachi (but valid globally)."""
    with patch('src.services.geospatial_service.get_session', mock_get_session(populated_db)):
        service = GeospatialService()
        
        # Valid coordinates but outside Karachi (London)
        # Should log warning, not raise error
        grid_id = service.assign_grid_id(51.5074, -0.1278)
        
        # Should return None (not in any grid) but shouldn't raise error
        assert grid_id is None


def test_coordinates_at_karachi_bounds(populated_db):
    """Test coordinates exactly at Karachi boundary limits."""
    with patch('src.services.geospatial_service.get_session', mock_get_session(populated_db)):
        service = GeospatialService()
        
        # Coordinates at Karachi boundary (should not raise error)
        grid_id = service.assign_grid_id(KARACHI_BOUNDS["lat_min"], KARACHI_BOUNDS["lon_min"])
        
        # Should return None (not in any grid) but no error
        assert grid_id is None


# ============================================================================
# Metadata Tests
# ============================================================================

def test_get_grid_metadata(populated_db):
    """Test retrieving full metadata for a grid."""
    with patch('src.services.geospatial_service.get_session', mock_get_session(populated_db)):
        service = GeospatialService()
        
        metadata = service.get_grid_metadata("DHA-Phase2-Cell-01")
        
        assert metadata is not None
        assert metadata["grid_id"] == "DHA-Phase2-Cell-01"
        assert metadata["neighborhood"] == "DHA Phase 2"
        assert metadata["area_km2"] == 0.5
        assert metadata["lat_center"] == 24.8278
        assert metadata["lon_center"] == 67.0595


def test_get_grid_metadata_invalid(populated_db):
    """Test metadata retrieval for non-existent grid."""
    with patch('src.services.geospatial_service.get_session', mock_get_session(populated_db)):
        service = GeospatialService()
        
        metadata = service.get_grid_metadata("NonExistent")
        
        assert metadata is None


def test_list_grids_all(populated_db):
    """Test listing all grids."""
    with patch('src.services.geospatial_service.get_session', mock_get_session(populated_db)):
        service = GeospatialService()
        
        grids = service.list_grids()
        
        assert len(grids) == 4
        assert "DHA-Phase2-Cell-01" in grids
        assert "DHA-Phase2-Cell-02" in grids
        assert "Clifton-Cell-01" in grids
        assert "Overlapping-Cell" in grids


def test_list_grids_by_neighborhood(populated_db):
    """Test listing grids filtered by neighborhood."""
    with patch('src.services.geospatial_service.get_session', mock_get_session(populated_db)):
        service = GeospatialService()
        
        dha_grids = service.list_grids("DHA Phase 2")
        
        assert len(dha_grids) == 2
        assert "DHA-Phase2-Cell-01" in dha_grids
        assert "DHA-Phase2-Cell-02" in dha_grids
        assert "Clifton-Cell-01" not in dha_grids


def test_list_grids_case_insensitive(populated_db):
    """Test that neighborhood filter is case-insensitive."""
    with patch('src.services.geospatial_service.get_session', mock_get_session(populated_db)):
        service = GeospatialService()
        
        grids_lower = service.list_grids("dha phase 2")
        grids_upper = service.list_grids("DHA PHASE 2")
        grids_mixed = service.list_grids("DHA Phase 2")
        
        assert grids_lower == grids_upper == grids_mixed


def test_get_neighborhoods(populated_db):
    """Test retrieving unique neighborhoods."""
    with patch('src.services.geospatial_service.get_session', mock_get_session(populated_db)):
        service = GeospatialService()
        
        neighborhoods = service.get_neighborhoods()
        
        assert len(neighborhoods) == 3
        assert "DHA Phase 2" in neighborhoods
        assert "Clifton" in neighborhoods
        assert "Test Overlap" in neighborhoods


# ============================================================================
# Service Management Tests
# ============================================================================

def test_reload_grids(populated_db):
    """Test reloading grids from database."""
    with patch('src.services.geospatial_service.get_session', mock_get_session(populated_db)):
        service = GeospatialService()
        
        initial_count = len(service.grids)
        
        # Reload
        count = service.reload_grids()
        
        assert count == initial_count
        assert len(service.grids) == initial_count


def test_is_initialized(populated_db):
    """Test is_initialized check."""
    with patch('src.services.geospatial_service.get_session', mock_get_session(populated_db)):
        service_loaded = GeospatialService(auto_load=True)
        service_not_loaded = GeospatialService(auto_load=False)
        
        assert service_loaded.is_initialized()
        assert not service_not_loaded.is_initialized()


def test_get_stats(populated_db):
    """Test retrieving service statistics."""
    with patch('src.services.geospatial_service.get_session', mock_get_session(populated_db)):
        service = GeospatialService()
        
        stats = service.get_stats()
        
        assert stats["total_grids"] == 4
        assert stats["neighborhoods"] == 3
        assert stats["initialized"] is True
        assert stats["cache_size_bytes"] > 0


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================

def test_assign_grid_id_before_initialization():
    """Test that assigning grid before loading raises error."""
    service = GeospatialService(auto_load=False)
    
    with pytest.raises(RuntimeError, match="Grid cache is empty"):
        service.assign_grid_id(24.8278, 67.0595)


def test_polygon_at_exact_corner(populated_db):
    """Test point at exact corner of grid."""
    with patch('src.services.geospatial_service.get_session', mock_get_session(populated_db)):
        service = GeospatialService()
        
        # NW corner of Cell-01
        grid_id = service.assign_grid_id(24.8308, 67.0565)
        
        # Should be assigned to a grid (corner behavior varies)
        assert grid_id in ["DHA-Phase2-Cell-01", "DHA-Phase2-Cell-02", "Overlapping-Cell", None]


def test_precision_at_grid_boundary(populated_db):
    """Test high-precision coordinates at boundary."""
    with patch('src.services.geospatial_service.get_session', mock_get_session(populated_db)):
        service = GeospatialService()
        
        # Point very close to boundary (7 decimal places)
        grid_id = service.assign_grid_id(24.8307999, 67.0595)
        
        # Should be assigned to one of the adjacent grids
        assert grid_id is not None


# ============================================================================
# Integration Tests
# ============================================================================

def test_full_workflow_assign_and_get_bounds(populated_db):
    """Test complete workflow: assign grid then get bounds."""
    with patch('src.services.geospatial_service.get_session', mock_get_session(populated_db)):
        service = GeospatialService()
        
        # Assign grid
        grid_id = service.assign_grid_id(24.8278, 67.0595)
        assert grid_id is not None
        
        # Get bounds
        bounds = service.get_grid_bounds(grid_id)
        assert bounds is not None
        
        # Verify point is within bounds
        assert bounds["lat_south"] <= 24.8278 <= bounds["lat_north"]
        assert bounds["lon_west"] <= 67.0595 <= bounds["lon_east"]


def test_full_workflow_list_and_get_metadata(populated_db):
    """Test workflow: list grids then get metadata for each."""
    with patch('src.services.geospatial_service.get_session', mock_get_session(populated_db)):
        service = GeospatialService()
        
        # List all grids
        grids = service.list_grids()
        assert len(grids) == 4
        
        # Get metadata for each
        for grid_id in grids:
            metadata = service.get_grid_metadata(grid_id)
            assert metadata is not None
            assert metadata["grid_id"] == grid_id


# ============================================================================
# Performance Tests (Basic)
# ============================================================================

def test_assign_performance_multiple_calls(populated_db):
    """Test that multiple assignments are fast (cached polygons)."""
    import time
    
    with patch('src.services.geospatial_service.get_session', mock_get_session(populated_db)):
        service = GeospatialService()
        
        # Warm up
        service.assign_grid_id(24.8278, 67.0595)
        
        # Time 100 assignments
        start = time.time()
        for _ in range(100):
            service.assign_grid_id(24.8278, 67.0595)
        duration = time.time() - start
        
        # Should be very fast (< 100ms for 100 calls)
        assert duration < 0.1, f"100 assignments took {duration:.3f}s (should be < 0.1s)"


# ============================================================================
# Realistic Karachi Coordinates Tests
# ============================================================================

def test_realistic_karachi_coordinates_in_grid(populated_db):
    """Test with realistic Karachi coordinates that fall in a grid."""
    with patch('src.services.geospatial_service.get_session', mock_get_session(populated_db)):
        service = GeospatialService()
        
        # Realistic DHA Phase 2 coordinate (center of Cell-01)
        grid_id = service.assign_grid_id(24.8278, 67.0595)
        
        assert grid_id == "DHA-Phase2-Cell-01"


def test_realistic_karachi_coordinates_outside_grids(populated_db):
    """Test with realistic Karachi coordinates outside all grids."""
    with patch('src.services.geospatial_service.get_session', mock_get_session(populated_db)):
        service = GeospatialService()
        
        # Realistic Karachi coordinate but not in any test grid
        # Saddar area (outside our test grids)
        grid_id = service.assign_grid_id(24.8555, 67.0099)
        
        assert grid_id is None


# ============================================================================
# Summary
# ============================================================================

if __name__ == "__main__":
    """
    Run tests with:
        pytest tests/services/test_geospatial_service.py -v
        pytest tests/services/test_geospatial_service.py --cov=src.services.geospatial_service --cov-report=term-missing
    """
    pytest.main([__file__, "-v", "--tb=short"])
