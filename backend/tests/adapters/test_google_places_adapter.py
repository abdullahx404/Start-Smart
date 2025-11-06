"""
Unit tests for GooglePlacesAdapter

Tests all functionality of the Google Places API adapter including:
- Successful business fetching
- Pagination handling
- Empty results
- Rate limit retry logic
- Invalid API key handling
- Category mapping
- Raw data storage
- Cache functionality

Coverage target: ≥90%

Usage:
    pytest tests/adapters/test_google_places_adapter.py -v
    pytest tests/adapters/test_google_places_adapter.py -v --cov=src.adapters.google_places_adapter
"""

import pytest
import json
import os
import time
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch, mock_open
from typing import Dict, Any, List

from googlemaps.exceptions import ApiError, Timeout, TransportError

from src.adapters.google_places_adapter import (
    GooglePlacesAdapter,
    create_adapter,
    CATEGORY_MAPPING,
    RAW_DATA_DIR,
    CACHE_EXPIRY_HOURS
)
from contracts.models import Business, Category, Source


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def valid_api_key():
    """Valid Google Places API key for testing."""
    return "AIzaSyTest123456789_ValidKey"


@pytest.fixture
def test_bounds():
    """Standard test bounds for DHA Phase 2."""
    return {
        "lat_north": 24.8320,
        "lat_south": 24.8260,
        "lon_east": 67.0640,
        "lon_west": 67.0580
    }


@pytest.fixture
def mock_google_place_response():
    """Mock response from Google Places API for a single place."""
    return {
        "place_id": "ChIJTest123",
        "name": "Gold's Gym",
        "geometry": {
            "location": {
                "lat": 24.8290,
                "lng": 67.0610
            }
        },
        "rating": 4.5,
        "user_ratings_total": 120,
        "types": ["gym", "health", "point_of_interest"]
    }


@pytest.fixture
def mock_google_places_response_multiple():
    """Mock response with multiple places (for pagination test)."""
    return {
        "results": [
            {
                "place_id": "ChIJTest001",
                "name": "Fitness First",
                "geometry": {"location": {"lat": 24.8290, "lng": 67.0610}},
                "rating": 4.5,
                "user_ratings_total": 120
            },
            {
                "place_id": "ChIJTest002",
                "name": "Gold's Gym",
                "geometry": {"location": {"lat": 24.8300, "lng": 67.0620}},
                "rating": 4.7,
                "user_ratings_total": 85
            },
            {
                "place_id": "ChIJTest003",
                "name": "Anytime Fitness",
                "geometry": {"location": {"lat": 24.8280, "lng": 67.0600}},
                "rating": 4.2,
                "user_ratings_total": 45
            }
        ],
        "status": "OK"
    }


@pytest.fixture
def mock_google_places_response_with_pagination():
    """Mock response with pagination token."""
    return {
        "results": [
            {
                "place_id": "ChIJPage1_001",
                "name": "Gym Page 1",
                "geometry": {"location": {"lat": 24.8290, "lng": 67.0610}},
                "rating": 4.5,
                "user_ratings_total": 100
            }
        ],
        "next_page_token": "next_token_abc123",
        "status": "OK"
    }


@pytest.fixture
def mock_google_places_response_page_2():
    """Mock response for second page (no more pages)."""
    return {
        "results": [
            {
                "place_id": "ChIJPage2_001",
                "name": "Gym Page 2",
                "geometry": {"location": {"lat": 24.8300, "lng": 67.0620}},
                "rating": 4.3,
                "user_ratings_total": 80
            }
        ],
        "status": "OK"
    }


@pytest.fixture
def mock_google_places_empty_response():
    """Mock response with no results."""
    return {
        "results": [],
        "status": "ZERO_RESULTS"
    }


@pytest.fixture
def mock_googlemaps_client(mock_google_places_response_multiple):
    """Mock googlemaps.Client with standard response."""
    with patch('src.adapters.google_places_adapter.googlemaps.Client') as mock_client_class:
        mock_client = MagicMock()
        mock_client.places_nearby.return_value = mock_google_places_response_multiple
        mock_client_class.return_value = mock_client
        yield mock_client_class


@pytest.fixture
def mock_assign_grid_id():
    """Mock geospatial service grid assignment."""
    with patch('src.adapters.google_places_adapter.assign_grid_id') as mock_assign:
        mock_assign.return_value = "DHA-Phase2-Cell-07"
        yield mock_assign


@pytest.fixture
def clean_raw_data_dir():
    """Ensure raw data directory is clean before and after tests."""
    # Create directory if it doesn't exist
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # Clean up before test
    for file in RAW_DATA_DIR.glob("*.json"):
        file.unlink()
    
    yield RAW_DATA_DIR
    
    # Clean up after test
    for file in RAW_DATA_DIR.glob("*.json"):
        file.unlink()


# ============================================================================
# Initialization Tests
# ============================================================================

def test_adapter_initialization_success(valid_api_key, mock_googlemaps_client):
    """Test successful adapter initialization with valid API key."""
    adapter = GooglePlacesAdapter(api_key=valid_api_key)
    
    assert adapter is not None
    assert adapter.get_source_name() == "google_places"
    assert adapter.client is not None
    mock_googlemaps_client.assert_called_once_with(key=valid_api_key)


def test_adapter_initialization_empty_api_key(mock_googlemaps_client):
    """Test initialization fails with empty API key."""
    with pytest.raises(ValueError, match="Google Places API key is required"):
        GooglePlacesAdapter(api_key="")


def test_adapter_initialization_none_api_key(mock_googlemaps_client):
    """Test initialization fails with None API key."""
    with pytest.raises(ValueError, match="Google Places API key is required"):
        GooglePlacesAdapter(api_key=None)


def test_adapter_initialization_invalid_api_key():
    """Test initialization fails with invalid API key."""
    with patch('src.adapters.google_places_adapter.googlemaps.Client') as mock_client:
        mock_client.side_effect = Exception("Invalid API key")
        
        with pytest.raises(ValueError, match="Invalid Google Places API key"):
            GooglePlacesAdapter(api_key="invalid_key")


def test_create_adapter_with_api_key(mock_googlemaps_client):
    """Test create_adapter() factory function with explicit API key."""
    adapter = create_adapter(api_key="test_key_123")
    
    assert adapter is not None
    assert isinstance(adapter, GooglePlacesAdapter)


def test_create_adapter_from_environment(mock_googlemaps_client):
    """Test create_adapter() reads from environment variable."""
    with patch.dict(os.environ, {"GOOGLE_PLACES_API_KEY": "env_key_123"}):
        adapter = create_adapter()
        
        assert adapter is not None
        assert isinstance(adapter, GooglePlacesAdapter)


def test_create_adapter_no_api_key():
    """Test create_adapter() fails when no API key available."""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError, match="Google Places API key required"):
            create_adapter()


# ============================================================================
# fetch_businesses() Tests
# ============================================================================

def test_fetch_businesses_success(
    valid_api_key,
    test_bounds,
    mock_googlemaps_client,
    mock_assign_grid_id,
    clean_raw_data_dir
):
    """Test successful business fetching with valid response."""
    adapter = GooglePlacesAdapter(api_key=valid_api_key)
    businesses = adapter.fetch_businesses(category="Gym", bounds=test_bounds)
    
    # Verify results
    assert len(businesses) == 3
    assert all(isinstance(b, Business) for b in businesses)
    
    # Check first business
    first_biz = businesses[0]
    assert first_biz.name == "Fitness First"
    assert first_biz.business_id == "ChIJTest001"
    assert first_biz.category == Category.GYM
    assert first_biz.source == Source.GOOGLE_PLACES
    assert first_biz.rating == 4.5
    assert first_biz.review_count == 120
    assert first_biz.lat == 24.8290
    assert first_biz.lon == 67.0610
    assert first_biz.grid_id == "DHA-Phase2-Cell-07"
    
    # Verify API was called correctly
    mock_client = mock_googlemaps_client.return_value
    mock_client.places_nearby.assert_called_once()
    call_kwargs = mock_client.places_nearby.call_args[1]
    assert call_kwargs["type"] == "gym"
    assert "location" in call_kwargs
    assert "radius" in call_kwargs


def test_fetch_businesses_category_mapping(
    valid_api_key,
    test_bounds,
    mock_googlemaps_client,
    mock_assign_grid_id,
    clean_raw_data_dir
):
    """Test category mapping: 'Gym' -> 'gym', 'Cafe' -> 'cafe'."""
    adapter = GooglePlacesAdapter(api_key=valid_api_key)
    
    # Test Gym mapping
    adapter.fetch_businesses(category="Gym", bounds=test_bounds)
    mock_client = mock_googlemaps_client.return_value
    call_kwargs = mock_client.places_nearby.call_args[1]
    assert call_kwargs["type"] == "gym"
    
    # Reset mock
    mock_client.places_nearby.reset_mock()
    
    # Test Cafe mapping
    adapter.fetch_businesses(category="Cafe", bounds=test_bounds)
    call_kwargs = mock_client.places_nearby.call_args[1]
    assert call_kwargs["type"] == "cafe"


def test_fetch_businesses_invalid_category(
    valid_api_key,
    test_bounds,
    mock_googlemaps_client,
    clean_raw_data_dir
):
    """Test fetch_businesses raises error for unsupported category."""
    adapter = GooglePlacesAdapter(api_key=valid_api_key)
    
    with pytest.raises(ValueError, match="Unsupported category: Restaurant"):
        adapter.fetch_businesses(category="Restaurant", bounds=test_bounds)


def test_fetch_businesses_invalid_bounds(valid_api_key, mock_googlemaps_client):
    """Test fetch_businesses validates bounds correctly."""
    adapter = GooglePlacesAdapter(api_key=valid_api_key)
    
    # Missing required keys
    with pytest.raises(ValueError, match="Missing required bounds keys"):
        adapter.fetch_businesses(category="Gym", bounds={"lat_north": 24.83})
    
    # Invalid latitude range
    with pytest.raises(ValueError, match="Latitude must be between"):
        adapter.fetch_businesses(
            category="Gym",
            bounds={
                "lat_north": 91.0,  # Invalid
                "lat_south": 24.82,
                "lon_east": 67.06,
                "lon_west": 67.05
            }
        )
    
    # Invalid longitude range
    with pytest.raises(ValueError, match="Longitude must be between"):
        adapter.fetch_businesses(
            category="Gym",
            bounds={
                "lat_north": 24.83,
                "lat_south": 24.82,
                "lon_east": 181.0,  # Invalid
                "lon_west": 67.05
            }
        )
    
    # North <= South
    with pytest.raises(ValueError, match="lat_north must be greater than lat_south"):
        adapter.fetch_businesses(
            category="Gym",
            bounds={
                "lat_north": 24.82,
                "lat_south": 24.83,  # South > North (invalid)
                "lon_east": 67.06,
                "lon_west": 67.05
            }
        )
    
    # East <= West
    with pytest.raises(ValueError, match="lon_east must be greater than lon_west"):
        adapter.fetch_businesses(
            category="Gym",
            bounds={
                "lat_north": 24.83,
                "lat_south": 24.82,
                "lon_east": 67.05,
                "lon_west": 67.06  # West > East (invalid)
            }
        )


def test_fetch_businesses_empty_results(
    valid_api_key,
    test_bounds,
    mock_googlemaps_client,
    mock_google_places_empty_response,
    clean_raw_data_dir
):
    """Test fetch_businesses handles empty results gracefully."""
    # Configure mock to return empty results
    mock_client = mock_googlemaps_client.return_value
    mock_client.places_nearby.return_value = mock_google_places_empty_response
    
    adapter = GooglePlacesAdapter(api_key=valid_api_key)
    businesses = adapter.fetch_businesses(category="Gym", bounds=test_bounds)
    
    assert businesses == []
    assert len(businesses) == 0


def test_fetch_businesses_pagination(
    valid_api_key,
    test_bounds,
    mock_googlemaps_client,
    mock_google_places_response_with_pagination,
    mock_google_places_response_page_2,
    mock_assign_grid_id,
    clean_raw_data_dir
):
    """Test fetch_businesses handles pagination correctly."""
    # Configure mock to return paginated results
    mock_client = mock_googlemaps_client.return_value
    mock_client.places_nearby.side_effect = [
        mock_google_places_response_with_pagination,  # First page with next_page_token
        mock_google_places_response_page_2  # Second page without token
    ]
    
    adapter = GooglePlacesAdapter(api_key=valid_api_key)
    businesses = adapter.fetch_businesses(category="Gym", bounds=test_bounds)
    
    # Should fetch both pages
    assert len(businesses) == 2
    assert businesses[0].name == "Gym Page 1"
    assert businesses[1].name == "Gym Page 2"
    
    # Verify API called twice (once for each page)
    assert mock_client.places_nearby.call_count == 2
    
    # Verify second call used page_token
    second_call = mock_client.places_nearby.call_args_list[1]
    assert "page_token" in second_call[1]
    assert second_call[1]["page_token"] == "next_token_abc123"


def test_fetch_businesses_rate_limit_retry(
    valid_api_key,
    test_bounds,
    mock_googlemaps_client,
    mock_google_places_response_multiple,
    mock_assign_grid_id,
    clean_raw_data_dir
):
    """Test fetch_businesses retries on rate limit error."""
    # Configure mock to fail twice then succeed
    mock_client = mock_googlemaps_client.return_value
    mock_client.places_nearby.side_effect = [
        ApiError("OVER_QUERY_LIMIT"),  # First attempt fails
        ApiError("OVER_QUERY_LIMIT"),  # Second attempt fails
        mock_google_places_response_multiple  # Third attempt succeeds
    ]
    
    adapter = GooglePlacesAdapter(api_key=valid_api_key)
    
    # Should succeed after retries
    businesses = adapter.fetch_businesses(category="Gym", bounds=test_bounds)
    
    assert len(businesses) == 3
    assert mock_client.places_nearby.call_count == 3


def test_fetch_businesses_max_retries_exceeded(
    valid_api_key,
    test_bounds,
    mock_googlemaps_client,
    clean_raw_data_dir
):
    """Test fetch_businesses raises error after max retries."""
    # Configure mock to always fail
    mock_client = mock_googlemaps_client.return_value
    mock_client.places_nearby.side_effect = ApiError("OVER_QUERY_LIMIT")
    
    adapter = GooglePlacesAdapter(api_key=valid_api_key)
    
    # Should raise after max retries (3)
    with pytest.raises(ApiError):
        adapter.fetch_businesses(category="Gym", bounds=test_bounds)
    
    # Verify retries happened
    assert mock_client.places_nearby.call_count == 3


def test_fetch_businesses_timeout_error(
    valid_api_key,
    test_bounds,
    mock_googlemaps_client,
    mock_google_places_response_multiple,
    mock_assign_grid_id,
    clean_raw_data_dir
):
    """Test fetch_businesses handles timeout errors with retry."""
    # Configure mock to timeout once then succeed
    mock_client = mock_googlemaps_client.return_value
    mock_client.places_nearby.side_effect = [
        Timeout("Request timed out"),
        mock_google_places_response_multiple
    ]
    
    adapter = GooglePlacesAdapter(api_key=valid_api_key)
    businesses = adapter.fetch_businesses(category="Gym", bounds=test_bounds)
    
    assert len(businesses) == 3
    assert mock_client.places_nearby.call_count == 2


def test_fetch_businesses_transport_error(
    valid_api_key,
    test_bounds,
    mock_googlemaps_client,
    mock_google_places_response_multiple,
    mock_assign_grid_id,
    clean_raw_data_dir
):
    """Test fetch_businesses handles transport errors with retry."""
    # Configure mock to have transport error then succeed
    mock_client = mock_googlemaps_client.return_value
    mock_client.places_nearby.side_effect = [
        TransportError("Network error"),
        mock_google_places_response_multiple
    ]
    
    adapter = GooglePlacesAdapter(api_key=valid_api_key)
    businesses = adapter.fetch_businesses(category="Gym", bounds=test_bounds)
    
    assert len(businesses) == 3
    assert mock_client.places_nearby.call_count == 2


# ============================================================================
# Raw Data Storage Tests
# ============================================================================

def test_raw_data_storage(
    valid_api_key,
    test_bounds,
    mock_googlemaps_client,
    mock_assign_grid_id,
    clean_raw_data_dir
):
    """Test that raw API responses are saved to disk."""
    adapter = GooglePlacesAdapter(api_key=valid_api_key)
    adapter.fetch_businesses(category="Gym", bounds=test_bounds)
    
    # Check that JSON file was created
    json_files = list(clean_raw_data_dir.glob("Gym_*.json"))
    assert len(json_files) == 1
    
    # Verify file contents
    with open(json_files[0], "r", encoding="utf-8") as f:
        data = json.load(f)
    
    assert "metadata" in data
    assert "places" in data
    assert data["metadata"]["category"] == "Gym"
    assert data["metadata"]["google_type"] == "gym"
    assert data["metadata"]["total_results"] == 3
    assert len(data["places"]) == 3


def test_raw_data_filename_format(
    valid_api_key,
    test_bounds,
    mock_googlemaps_client,
    mock_assign_grid_id,
    clean_raw_data_dir
):
    """Test raw data filename follows expected format."""
    adapter = GooglePlacesAdapter(api_key=valid_api_key)
    adapter.fetch_businesses(category="Gym", bounds=test_bounds)
    
    json_files = list(clean_raw_data_dir.glob("*.json"))
    assert len(json_files) == 1
    
    filename = json_files[0].name
    # Format: {category}_{lat}_{lon}_{timestamp}.json
    assert filename.startswith("Gym_")
    assert filename.endswith(".json")
    assert "_24.8290_67.0610_" in filename  # Center coordinates


def test_raw_data_storage_failure_handled(
    valid_api_key,
    test_bounds,
    mock_googlemaps_client,
    mock_assign_grid_id
):
    """Test that raw data storage failures don't crash adapter."""
    with patch('src.adapters.google_places_adapter.open', side_effect=IOError("Disk full")):
        adapter = GooglePlacesAdapter(api_key=valid_api_key)
        
        # Should complete successfully despite storage failure
        businesses = adapter.fetch_businesses(category="Gym", bounds=test_bounds)
        assert len(businesses) == 3


# ============================================================================
# Cache Tests
# ============================================================================

def test_cache_hit(
    valid_api_key,
    test_bounds,
    mock_googlemaps_client,
    mock_assign_grid_id,
    clean_raw_data_dir
):
    """Test that cache is used for recent requests."""
    adapter = GooglePlacesAdapter(api_key=valid_api_key)
    
    # First fetch - creates cache
    businesses_1 = adapter.fetch_businesses(category="Gym", bounds=test_bounds)
    assert len(businesses_1) == 3
    
    # Reset mock to track second call
    mock_client = mock_googlemaps_client.return_value
    call_count_before = mock_client.places_nearby.call_count
    
    # Second fetch - should use cache (no API call)
    businesses_2 = adapter.fetch_businesses(category="Gym", bounds=test_bounds)
    assert len(businesses_2) == 3
    
    # Verify API was NOT called again
    assert mock_client.places_nearby.call_count == call_count_before


def test_cache_force_refresh(
    valid_api_key,
    test_bounds,
    mock_googlemaps_client,
    mock_assign_grid_id,
    clean_raw_data_dir
):
    """Test force_refresh bypasses cache."""
    adapter = GooglePlacesAdapter(api_key=valid_api_key)
    
    # First fetch - creates cache
    businesses_1 = adapter.fetch_businesses(category="Gym", bounds=test_bounds)
    assert len(businesses_1) == 3
    
    # Track API calls
    mock_client = mock_googlemaps_client.return_value
    call_count_before = mock_client.places_nearby.call_count
    
    # Second fetch with force_refresh - should call API again
    businesses_2 = adapter.fetch_businesses(
        category="Gym",
        bounds=test_bounds,
        force_refresh=True
    )
    assert len(businesses_2) == 3
    
    # Verify API was called again
    assert mock_client.places_nearby.call_count > call_count_before


def test_cache_expiry(
    valid_api_key,
    test_bounds,
    mock_googlemaps_client,
    mock_assign_grid_id,
    clean_raw_data_dir
):
    """Test expired cache is not used."""
    adapter = GooglePlacesAdapter(api_key=valid_api_key)
    
    # First fetch - creates cache
    businesses_1 = adapter.fetch_businesses(category="Gym", bounds=test_bounds)
    assert len(businesses_1) == 3
    
    # Find cache file and modify its timestamp to be old
    json_files = list(clean_raw_data_dir.glob("Gym_*.json"))
    assert len(json_files) == 1
    cache_file = json_files[0]
    
    # Set file modification time to 25 hours ago (beyond CACHE_EXPIRY_HOURS)
    old_time = time.time() - (CACHE_EXPIRY_HOURS + 1) * 3600
    os.utime(cache_file, (old_time, old_time))
    
    # Track API calls
    mock_client = mock_googlemaps_client.return_value
    call_count_before = mock_client.places_nearby.call_count
    
    # Second fetch - should call API again (cache expired)
    businesses_2 = adapter.fetch_businesses(category="Gym", bounds=test_bounds)
    assert len(businesses_2) == 3
    
    # Verify API was called again
    assert mock_client.places_nearby.call_count > call_count_before


# ============================================================================
# Business Conversion Tests
# ============================================================================

def test_convert_to_business_missing_coordinates(
    valid_api_key,
    test_bounds,
    mock_googlemaps_client,
    mock_assign_grid_id,
    clean_raw_data_dir
):
    """Test business conversion handles missing coordinates."""
    # Configure mock to return place without coordinates
    mock_client = mock_googlemaps_client.return_value
    mock_client.places_nearby.return_value = {
        "results": [
            {
                "place_id": "ChIJNoCoords",
                "name": "Incomplete Gym",
                "geometry": {}  # Missing location
            }
        ],
        "status": "OK"
    }
    
    adapter = GooglePlacesAdapter(api_key=valid_api_key)
    businesses = adapter.fetch_businesses(category="Gym", bounds=test_bounds)
    
    # Should skip place with missing coordinates
    assert len(businesses) == 0


def test_convert_to_business_missing_rating(
    valid_api_key,
    test_bounds,
    mock_googlemaps_client,
    mock_assign_grid_id,
    clean_raw_data_dir
):
    """Test business conversion handles missing rating."""
    # Configure mock to return place without rating
    mock_client = mock_googlemaps_client.return_value
    mock_client.places_nearby.return_value = {
        "results": [
            {
                "place_id": "ChIJNoRating",
                "name": "New Gym",
                "geometry": {"location": {"lat": 24.8290, "lng": 67.0610}}
                # No rating or review_count
            }
        ],
        "status": "OK"
    }
    
    adapter = GooglePlacesAdapter(api_key=valid_api_key)
    businesses = adapter.fetch_businesses(category="Gym", bounds=test_bounds)
    
    assert len(businesses) == 1
    assert businesses[0].rating is None
    assert businesses[0].review_count == 0


def test_convert_to_business_grid_assignment_fails(
    valid_api_key,
    test_bounds,
    mock_googlemaps_client,
    clean_raw_data_dir
):
    """Test business conversion handles grid assignment failure."""
    # Configure grid assignment to return None
    with patch('src.adapters.google_places_adapter.assign_grid_id', return_value=None):
        adapter = GooglePlacesAdapter(api_key=valid_api_key)
        businesses = adapter.fetch_businesses(category="Gym", bounds=test_bounds)
        
        # Should still create business but with grid_id=None
        assert len(businesses) == 3
        assert all(b.grid_id is None for b in businesses)


# ============================================================================
# fetch_social_posts() Tests
# ============================================================================

def test_fetch_social_posts_not_implemented(valid_api_key, test_bounds, mock_googlemaps_client):
    """Test that fetch_social_posts raises NotImplementedError."""
    adapter = GooglePlacesAdapter(api_key=valid_api_key)
    
    with pytest.raises(NotImplementedError, match="does not support social post fetching"):
        adapter.fetch_social_posts(category="Gym", bounds=test_bounds, days=90)


# ============================================================================
# Helper Methods Tests
# ============================================================================

def test_calculate_center(valid_api_key, test_bounds, mock_googlemaps_client):
    """Test center point calculation from bounds."""
    adapter = GooglePlacesAdapter(api_key=valid_api_key)
    center_lat, center_lon = adapter._calculate_center(test_bounds)
    
    expected_lat = (24.8320 + 24.8260) / 2
    expected_lon = (67.0640 + 67.0580) / 2
    
    assert center_lat == pytest.approx(expected_lat, abs=1e-6)
    assert center_lon == pytest.approx(expected_lon, abs=1e-6)


def test_calculate_radius(valid_api_key, test_bounds, mock_googlemaps_client):
    """Test radius calculation from bounds."""
    adapter = GooglePlacesAdapter(api_key=valid_api_key)
    radius = adapter._calculate_radius(test_bounds)
    
    # Should return reasonable radius (in meters)
    assert radius > 0
    assert isinstance(radius, int)
    # For ~0.5km² grid, radius should be in range 400-800m
    assert 400 <= radius <= 800


def test_get_source_name(valid_api_key, mock_googlemaps_client):
    """Test get_source_name returns correct identifier."""
    adapter = GooglePlacesAdapter(api_key=valid_api_key)
    assert adapter.get_source_name() == "google_places"


def test_api_key_masking_in_logs(valid_api_key, mock_googlemaps_client):
    """Test that API key is masked in log output."""
    adapter = GooglePlacesAdapter(api_key=valid_api_key)
    
    # API key should be masked (only first 8 chars visible)
    assert adapter.api_key == "AIzaSyTe***"
    assert valid_api_key not in adapter.api_key


# ============================================================================
# Integration-like Tests
# ============================================================================

def test_full_fetch_workflow(
    valid_api_key,
    test_bounds,
    mock_googlemaps_client,
    mock_assign_grid_id,
    clean_raw_data_dir
):
    """Test complete workflow: fetch -> convert -> cache -> raw data storage."""
    adapter = GooglePlacesAdapter(api_key=valid_api_key)
    
    # Fetch businesses
    businesses = adapter.fetch_businesses(category="Gym", bounds=test_bounds)
    
    # Verify businesses created
    assert len(businesses) == 3
    assert all(isinstance(b, Business) for b in businesses)
    assert all(b.category == Category.GYM for b in businesses)
    assert all(b.source == Source.GOOGLE_PLACES for b in businesses)
    assert all(b.grid_id == "DHA-Phase2-Cell-07" for b in businesses)
    
    # Verify raw data saved
    json_files = list(clean_raw_data_dir.glob("*.json"))
    assert len(json_files) == 1
    
    # Verify cache works on second fetch
    mock_client = mock_googlemaps_client.return_value
    call_count_before = mock_client.places_nearby.call_count
    
    businesses_cached = adapter.fetch_businesses(category="Gym", bounds=test_bounds)
    assert len(businesses_cached) == 3
    assert mock_client.places_nearby.call_count == call_count_before  # No new API calls


def test_multiple_categories(
    valid_api_key,
    test_bounds,
    mock_googlemaps_client,
    mock_assign_grid_id,
    clean_raw_data_dir
):
    """Test fetching multiple categories creates separate cache files."""
    adapter = GooglePlacesAdapter(api_key=valid_api_key)
    
    # Fetch Gym
    gyms = adapter.fetch_businesses(category="Gym", bounds=test_bounds)
    assert len(gyms) == 3
    
    # Fetch Cafe
    cafes = adapter.fetch_businesses(category="Cafe", bounds=test_bounds)
    assert len(cafes) == 3
    
    # Should have 2 cache files
    json_files = list(clean_raw_data_dir.glob("*.json"))
    assert len(json_files) == 2
    
    # Verify filenames
    gym_files = list(clean_raw_data_dir.glob("Gym_*.json"))
    cafe_files = list(clean_raw_data_dir.glob("Cafe_*.json"))
    assert len(gym_files) == 1
    assert len(cafe_files) == 1


# ============================================================================
# Edge Cases
# ============================================================================

def test_throttle_request_timing(valid_api_key, mock_googlemaps_client):
    """Test request throttling maintains minimum interval."""
    adapter = GooglePlacesAdapter(api_key=valid_api_key)
    
    # Record time before throttle
    start_time = time.time()
    adapter._throttle_request()
    first_call_time = time.time() - start_time
    
    # Immediate second call should be throttled
    start_time = time.time()
    adapter._throttle_request()
    second_call_time = time.time() - start_time
    
    # Second call should have delay (min_request_interval)
    assert second_call_time >= adapter._min_request_interval * 0.9  # Allow 10% tolerance


def test_pagination_safety_limit(
    valid_api_key,
    test_bounds,
    mock_googlemaps_client,
    mock_assign_grid_id,
    clean_raw_data_dir
):
    """Test pagination stops after max pages (safety limit)."""
    # Configure mock to always return next_page_token (infinite pagination)
    mock_client = mock_googlemaps_client.return_value
    mock_client.places_nearby.return_value = {
        "results": [{"place_id": "test", "name": "Test", "geometry": {"location": {"lat": 24.83, "lng": 67.06}}}],
        "next_page_token": "infinite_token",
        "status": "OK"
    }
    
    adapter = GooglePlacesAdapter(api_key=valid_api_key)
    businesses = adapter.fetch_businesses(category="Gym", bounds=test_bounds)
    
    # Should stop at 3 pages (safety limit)
    assert mock_client.places_nearby.call_count == 3
    assert len(businesses) == 3  # 1 result per page × 3 pages


# ============================================================================
# Summary
# ============================================================================

if __name__ == "__main__":
    """
    Run tests with:
        pytest tests/adapters/test_google_places_adapter.py -v
        pytest tests/adapters/test_google_places_adapter.py -v --cov=src.adapters.google_places_adapter --cov-report=term-missing
    """
    pytest.main([__file__, "-v", "--tb=short"])
