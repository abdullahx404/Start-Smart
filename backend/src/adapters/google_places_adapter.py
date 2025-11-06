"""
Google Places API Adapter

Fetches real business data from Google Places API and converts to our Business model.

Features:
- Extends BaseAdapter interface
- Handles pagination (max 60 results per call)
- Maps Google Place types to our category taxonomy
- Includes retry logic with exponential backoff
- Automatic grid assignment using GeospatialService
- Comprehensive logging and error handling

Usage:
    from src.adapters.google_places_adapter import GooglePlacesAdapter
    
    adapter = GooglePlacesAdapter(api_key="YOUR_API_KEY")
    businesses = adapter.fetch_businesses(
        category="Gym",
        bounds={
            "lat_north": 24.8320,
            "lat_south": 24.8260,
            "lon_east": 67.0640,
            "lon_west": 67.0580
        }
    )
"""

import time
import json
import os
from typing import List, Dict, Optional, Any
from datetime import datetime
from pathlib import Path

import googlemaps
from googlemaps.exceptions import ApiError, Timeout, TransportError

from contracts.base_adapter import BaseAdapter
from contracts.models import Business, Category, Source
from src.services.geospatial_service import assign_grid_id
from src.utils.logger import get_logger, log_api_call


# ============================================================================
# Constants
# ============================================================================

# Category mapping: Our taxonomy → Google Places types
CATEGORY_MAPPING = {
    "Gym": "gym",
    "Cafe": "cafe",
}

# Retry configuration
MAX_RETRIES = 3
INITIAL_BACKOFF = 1.0  # seconds
MAX_BACKOFF = 10.0  # seconds
BACKOFF_MULTIPLIER = 2

# Google Places API limits
MAX_RESULTS_PER_CALL = 60  # Google Places Nearby Search limit
DEFAULT_RADIUS_METERS = 500  # ~0.5 km (matches grid size)
MAX_REQUESTS_PER_SECOND = 10  # Google's rate limit

# Raw data storage path
RAW_DATA_DIR = Path("data/raw/google_places")

# Cache settings
CACHE_EXPIRY_HOURS = 24  # Cache data for 24 hours


# ============================================================================
# Google Places Adapter
# ============================================================================

class GooglePlacesAdapter(BaseAdapter):
    """
    Adapter for fetching real business data from Google Places API.
    
    Implements the BaseAdapter interface for consistent data fetching
    across all data sources.
    
    Attributes:
        client: Google Maps API client
        logger: Logger instance for structured logging
        api_key: Google Places API key (for logging purposes only)
    """
    
    def __init__(self, api_key: str):
        """
        Initialize Google Places adapter.
        
        Args:
            api_key: Google Places API key (get from Google Cloud Console)
            
        Raises:
            ValueError: If api_key is empty or None
            ApiError: If API key is invalid
        """
        if not api_key:
            raise ValueError("Google Places API key is required")
        
        # Validate API key by attempting to create client
        try:
            self.client = googlemaps.Client(key=api_key)
        except Exception as e:
            raise ValueError(f"Invalid Google Places API key: {e}")
        
        self.logger = get_logger(__name__)
        self.api_key = api_key[:8] + "***" if len(api_key) > 8 else "***"  # Masked for logging
        
        # Request throttling
        self._last_request_time = 0.0
        self._min_request_interval = 1.0 / MAX_REQUESTS_PER_SECOND  # 0.1 seconds between requests
        
        # Create raw data directory if it doesn't exist
        RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(
            "GooglePlacesAdapter initialized",
            extra={"extra_fields": {
                "api_key": self.api_key,
                "rate_limit": f"{MAX_REQUESTS_PER_SECOND} req/s",
                "cache_expiry": f"{CACHE_EXPIRY_HOURS}h"
            }}
        )
    
    def fetch_businesses(
        self,
        category: str,
        bounds: Dict[str, float],
        force_refresh: bool = False
    ) -> List[Business]:
        """
        Fetch businesses within specified geographic bounds.
        
        Implements BaseAdapter.fetch_businesses(). Queries Google Places API
        for businesses matching the category within the bounding box.
        
        Uses cache-aware fetching: checks for recent cached data before making API calls.
        
        Args:
            category: Business category ("Gym", "Cafe")
            bounds: Geographic bounding box with keys:
                - lat_north: Northern boundary latitude
                - lat_south: Southern boundary latitude
                - lon_east: Eastern boundary longitude
                - lon_west: Western boundary longitude
            force_refresh: If True, bypass cache and fetch fresh data from API
                
        Returns:
            List of Business objects with assigned grid_ids
            
        Raises:
            ValueError: If category is not supported or bounds are invalid
            ApiError: If Google Places API returns an error
            
        Example:
            >>> adapter = GooglePlacesAdapter(api_key="...")
            >>> businesses = adapter.fetch_businesses(
            ...     category="Gym",
            ...     bounds={"lat_north": 24.83, "lat_south": 24.82, "lon_east": 67.07, "lon_west": 67.06}
            ... )
            >>> len(businesses)
            5
        """
        start_time = time.time()
        
        # Validate category
        if category not in CATEGORY_MAPPING:
            raise ValueError(
                f"Unsupported category: {category}. "
                f"Supported categories: {list(CATEGORY_MAPPING.keys())}"
            )
        
        # Validate bounds
        self._validate_bounds(bounds)
        
        # Check cache first (unless force_refresh is True)
        if not force_refresh:
            cached_data = self._load_from_cache(category, bounds)
            if cached_data is not None:
                self.logger.info(
                    f"Using cached data for {category}",
                    extra={"extra_fields": {
                        "category": category,
                        "cached": True,
                        "business_count": len(cached_data)
                    }}
                )
                return cached_data
        
        # Map category to Google Places type
        google_type = CATEGORY_MAPPING[category]
        
        # Calculate center point and radius from bounds
        center_lat, center_lon = self._calculate_center(bounds)
        radius = self._calculate_radius(bounds)
        
        self.logger.info(
            f"Fetching businesses: category={category}, center=({center_lat:.4f}, {center_lon:.4f}), radius={radius}m",
            extra={"extra_fields": {
                "category": category,
                "google_type": google_type,
                "center_lat": center_lat,
                "center_lon": center_lon,
                "radius_meters": radius,
                "bounds": bounds
            }}
        )
        
        # Fetch places from Google Places API with retry logic
        places_data = self._fetch_with_retry(
            location=(center_lat, center_lon),
            radius=radius,
            place_type=google_type
        )
        
        # Convert Google Places responses to Business objects
        businesses = []
        for place in places_data:
            try:
                business = self._convert_to_business(place, category)
                if business:
                    businesses.append(business)
            except Exception as e:
                self.logger.warning(
                    f"Failed to convert place to business: {e}",
                    extra={"extra_fields": {
                        "place_id": place.get("place_id"),
                        "error": str(e)
                    }}
                )
        
        duration = time.time() - start_time
        
        # Log results
        log_api_call(
            self.logger,
            "Google Places API - fetch_businesses",
            params={
                "category": category,
                "google_type": google_type,
                "center": f"{center_lat:.4f},{center_lon:.4f}",
                "radius": radius
            },
            duration=duration,
            status="success"
        )
        
        self.logger.info(
            f"Fetched {len(businesses)} businesses in {duration:.2f}s",
            extra={"extra_fields": {
                "business_count": len(businesses),
                "category": category,
                "duration_seconds": round(duration, 3)
            }}
        )
        
        # Save raw data for audit trail
        self._save_raw_data(category, bounds, places_data)
        
        return businesses
    
    def fetch_social_posts(self, category: str, bounds: Dict[str, float], days: int = 90):
        """
        Not implemented for Google Places adapter.
        
        Google Places API does not provide social media posts.
        Use SimulatedSocialAdapter for social data.
        
        Raises:
            NotImplementedError: Always raises (adapter doesn't support social posts)
        """
        raise NotImplementedError(
            "GooglePlacesAdapter does not support social post fetching. "
            "Use SimulatedSocialAdapter instead."
        )
    
    def get_source_name(self) -> str:
        """
        Return data source identifier.
        
        Returns:
            "google_places"
        """
        return "google_places"
    
    # ========================================================================
    # Private Helper Methods
    # ========================================================================
    
    def _throttle_request(self) -> None:
        """
        Throttle API requests to stay within rate limits.
        
        Ensures minimum time between requests (100ms for 10 req/s limit).
        Sleeps if necessary to maintain rate limit compliance.
        """
        current_time = time.time()
        time_since_last_request = current_time - self._last_request_time
        
        if time_since_last_request < self._min_request_interval:
            sleep_time = self._min_request_interval - time_since_last_request
            self.logger.debug(
                f"Throttling: sleeping {sleep_time:.3f}s to maintain rate limit",
                extra={"extra_fields": {"sleep_seconds": round(sleep_time, 3)}}
            )
            time.sleep(sleep_time)
        
        self._last_request_time = time.time()
    
    def _load_from_cache(
        self,
        category: str,
        bounds: Dict[str, float]
    ) -> Optional[List[Business]]:
        """
        Load businesses from cache if recent data exists.
        
        Searches for cached JSON files matching the category and bounds.
        Returns cached data if found and not expired (< CACHE_EXPIRY_HOURS old).
        
        Args:
            category: Business category
            bounds: Geographic bounds
            
        Returns:
            List of Business objects from cache, or None if cache miss/expired
        """
        try:
            center_lat, center_lon = self._calculate_center(bounds)
            
            # Find matching cache files (ignore timestamp, check all files)
            pattern = f"{category}_{center_lat:.4f}_{center_lon:.4f}_*.json"
            cache_files = list(RAW_DATA_DIR.glob(pattern))
            
            if not cache_files:
                self.logger.debug(
                    f"Cache miss: no cached data for {category} at ({center_lat:.4f}, {center_lon:.4f})",
                    extra={"extra_fields": {"category": category, "cache_hit": False}}
                )
                return None
            
            # Sort by timestamp (newest first)
            cache_files.sort(reverse=True)
            latest_cache = cache_files[0]
            
            # Check if cache is still valid (not expired)
            cache_age_seconds = time.time() - latest_cache.stat().st_mtime
            cache_age_hours = cache_age_seconds / 3600
            
            if cache_age_hours > CACHE_EXPIRY_HOURS:
                self.logger.debug(
                    f"Cache expired: {latest_cache.name} is {cache_age_hours:.1f}h old (max {CACHE_EXPIRY_HOURS}h)",
                    extra={"extra_fields": {
                        "cache_file": latest_cache.name,
                        "age_hours": round(cache_age_hours, 2),
                        "cache_hit": False
                    }}
                )
                return None
            
            # Load and parse cached data
            with open(latest_cache, "r", encoding="utf-8") as f:
                cached_data = json.load(f)
            
            # Convert cached places to Business objects
            businesses = []
            for place in cached_data.get("places", []):
                try:
                    business = self._convert_to_business(place, category)
                    if business:
                        businesses.append(business)
                except Exception as e:
                    self.logger.warning(
                        f"Failed to convert cached place: {e}",
                        extra={"extra_fields": {"place_id": place.get("place_id"), "error": str(e)}}
                    )
            
            self.logger.info(
                f"Cache hit: loaded {len(businesses)} businesses from {latest_cache.name} (age: {cache_age_hours:.1f}h)",
                extra={"extra_fields": {
                    "cache_file": latest_cache.name,
                    "business_count": len(businesses),
                    "age_hours": round(cache_age_hours, 2),
                    "cache_hit": True
                }}
            )
            
            return businesses
            
        except Exception as e:
            self.logger.warning(
                f"Error loading from cache: {e}",
                extra={"extra_fields": {"error": str(e), "cache_hit": False}}
            )
            return None
    
    def _validate_bounds(self, bounds: Dict[str, float]) -> None:
        """
        Validate bounds dictionary has required keys and valid values.
        
        Args:
            bounds: Bounding box dictionary
            
        Raises:
            ValueError: If bounds are invalid or missing required keys
        """
        required_keys = ["lat_north", "lat_south", "lon_east", "lon_west"]
        missing_keys = [key for key in required_keys if key not in bounds]
        
        if missing_keys:
            raise ValueError(f"Missing required bounds keys: {missing_keys}")
        
        # Validate latitude range
        if not (-90 <= bounds["lat_north"] <= 90) or not (-90 <= bounds["lat_south"] <= 90):
            raise ValueError("Latitude must be between -90 and 90")
        
        # Validate longitude range
        if not (-180 <= bounds["lon_east"] <= 180) or not (-180 <= bounds["lon_west"] <= 180):
            raise ValueError("Longitude must be between -180 and 180")
        
        # Validate north > south
        if bounds["lat_north"] <= bounds["lat_south"]:
            raise ValueError("lat_north must be greater than lat_south")
        
        # Validate east > west (simplified, doesn't handle 180° crossing)
        if bounds["lon_east"] <= bounds["lon_west"]:
            raise ValueError("lon_east must be greater than lon_west")
    
    def _calculate_center(self, bounds: Dict[str, float]) -> tuple[float, float]:
        """
        Calculate center point from bounding box.
        
        Args:
            bounds: Bounding box dictionary
            
        Returns:
            Tuple of (latitude, longitude)
        """
        center_lat = (bounds["lat_north"] + bounds["lat_south"]) / 2
        center_lon = (bounds["lon_east"] + bounds["lon_west"]) / 2
        return center_lat, center_lon
    
    def _calculate_radius(self, bounds: Dict[str, float]) -> int:
        """
        Calculate approximate radius from bounding box.
        
        Uses Haversine-like approximation for small distances.
        
        Args:
            bounds: Bounding box dictionary
            
        Returns:
            Radius in meters (rounded to nearest integer)
        """
        from math import radians, cos, sqrt
        
        # Calculate dimensions
        lat_diff = bounds["lat_north"] - bounds["lat_south"]
        lon_diff = bounds["lon_east"] - bounds["lon_west"]
        
        # Average latitude for longitude distance calculation
        avg_lat = (bounds["lat_north"] + bounds["lat_south"]) / 2
        
        # Approximate distance in degrees to meters
        # 1 degree latitude ≈ 111 km
        # 1 degree longitude ≈ 111 km * cos(latitude)
        lat_meters = lat_diff * 111_000
        lon_meters = lon_diff * 111_000 * cos(radians(avg_lat))
        
        # Diagonal distance / 2 (to cover full bounding box from center)
        diagonal = sqrt(lat_meters**2 + lon_meters**2)
        radius = int(diagonal / 2)
        
        # Ensure minimum radius
        return max(radius, DEFAULT_RADIUS_METERS)
    
    def _fetch_with_retry(
        self,
        location: tuple[float, float],
        radius: int,
        place_type: str
    ) -> List[Dict[str, Any]]:
        """
        Fetch places from Google Places API with retry logic.
        
        Handles pagination and implements exponential backoff for rate limits.
        
        Args:
            location: (latitude, longitude) tuple
            radius: Search radius in meters
            place_type: Google Places type (e.g., "gym", "cafe")
            
        Returns:
            List of place dictionaries from Google Places API
            
        Raises:
            ApiError: If all retries fail
        """
        all_places = []
        next_page_token = None
        page_count = 0
        
        while True:
            page_count += 1
            retry_count = 0
            backoff = INITIAL_BACKOFF
            
            while retry_count < MAX_RETRIES:
                try:
                    # Throttle request to stay within rate limits
                    self._throttle_request()
                    
                    # Call Google Places API
                    if next_page_token:
                        # Wait before fetching next page (Google requires delay)
                        time.sleep(2)
                        response = self.client.places_nearby(page_token=next_page_token)
                    else:
                        response = self.client.places_nearby(
                            location=location,
                            radius=radius,
                            type=place_type
                        )
                    
                    # Extract results
                    places = response.get("results", [])
                    all_places.extend(places)
                    
                    self.logger.debug(
                        f"Fetched page {page_count}: {len(places)} places",
                        extra={"extra_fields": {
                            "page": page_count,
                            "places_count": len(places),
                            "has_next_page": "next_page_token" in response
                        }}
                    )
                    
                    # Check for next page
                    next_page_token = response.get("next_page_token")
                    if not next_page_token:
                        # No more pages
                        return all_places
                    
                    # Break retry loop on success
                    break
                    
                except (ApiError, Timeout, TransportError) as e:
                    retry_count += 1
                    
                    if retry_count >= MAX_RETRIES:
                        # Max retries exceeded
                        log_api_call(
                            self.logger,
                            "Google Places API - fetch_with_retry",
                            params={
                                "location": f"{location[0]:.4f},{location[1]:.4f}",
                                "radius": radius,
                                "type": place_type,
                                "page": page_count
                            },
                            status="error",
                            error=str(e)
                        )
                        raise
                    
                    # Log retry
                    self.logger.warning(
                        f"API call failed, retrying ({retry_count}/{MAX_RETRIES}): {e}",
                        extra={"extra_fields": {
                            "retry_count": retry_count,
                            "max_retries": MAX_RETRIES,
                            "backoff_seconds": backoff,
                            "error": str(e)
                        }}
                    )
                    
                    # Wait before retry (exponential backoff)
                    time.sleep(backoff)
                    backoff = min(backoff * BACKOFF_MULTIPLIER, MAX_BACKOFF)
            
            # Safety limit: max 3 pages (180 results)
            if page_count >= 3:
                self.logger.warning(
                    "Reached maximum page limit (3), stopping pagination",
                    extra={"extra_fields": {"total_places": len(all_places)}}
                )
                break
        
        return all_places
    
    def _convert_to_business(self, place: Dict[str, Any], category: str) -> Optional[Business]:
        """
        Convert Google Places API response to Business model.
        
        Args:
            place: Place dictionary from Google Places API
            category: Our category name ("Gym", "Cafe")
            
        Returns:
            Business object or None if conversion fails
        """
        try:
            # Extract coordinates
            location = place.get("geometry", {}).get("location", {})
            lat = location.get("lat")
            lon = location.get("lng")
            
            if lat is None or lon is None:
                self.logger.warning(
                    f"Place missing coordinates: {place.get('name')}",
                    extra={"extra_fields": {"place_id": place.get("place_id")}}
                )
                return None
            
            # Assign grid_id using geospatial service
            grid_id = assign_grid_id(lat, lon)
            
            if grid_id is None:
                self.logger.warning(
                    f"Could not assign grid_id for place: {place.get('name')} at ({lat}, {lon})",
                    extra={"extra_fields": {
                        "place_id": place.get("place_id"),
                        "lat": lat,
                        "lon": lon
                    }}
                )
                # Still create business but with grid_id=None
            
            # Extract rating (may be None for new businesses)
            rating = place.get("rating")
            if rating is not None:
                rating = float(rating)
            
            # Create Business object
            business = Business(
                business_id=place.get("place_id", ""),
                name=place.get("name", "Unknown"),
                lat=lat,
                lon=lon,
                category=Category(category),
                rating=rating,
                review_count=place.get("user_ratings_total", 0),
                source=Source.GOOGLE_PLACES,
                grid_id=grid_id,
                fetched_at=datetime.utcnow()
            )
            
            return business
            
        except Exception as e:
            self.logger.error(
                f"Error converting place to business: {e}",
                extra={"extra_fields": {
                    "place_id": place.get("place_id"),
                    "error": str(e),
                    "place_data": place
                }}
            )
            return None
    
    def _save_raw_data(
        self,
        category: str,
        bounds: Dict[str, float],
        places_data: List[Dict[str, Any]]
    ) -> None:
        """
        Save raw Google Places API responses to disk for audit trail.
        
        Saves complete metadata including query parameters, timestamps,
        result counts, and the raw API response. This creates an audit
        trail for debugging and data provenance.
        
        Args:
            category: Business category
            bounds: Geographic bounds
            places_data: Raw place dictionaries from API
        """
        try:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            center_lat, center_lon = self._calculate_center(bounds)
            
            filename = f"{category}_{center_lat:.4f}_{center_lon:.4f}_{timestamp}.json"
            filepath = RAW_DATA_DIR / filename
            
            # Calculate statistics
            places_with_ratings = sum(1 for p in places_data if p.get("rating") is not None)
            avg_rating = None
            if places_with_ratings > 0:
                ratings = [p["rating"] for p in places_data if p.get("rating") is not None]
                avg_rating = sum(ratings) / len(ratings)
            
            data = {
                "metadata": {
                    "timestamp": datetime.utcnow().isoformat(),
                    "category": category,
                    "google_type": CATEGORY_MAPPING.get(category),
                    "bounds": bounds,
                    "center": {
                        "lat": center_lat,
                        "lon": center_lon
                    },
                    "radius_meters": self._calculate_radius(bounds),
                    "total_results": len(places_data),
                    "statistics": {
                        "places_with_ratings": places_with_ratings,
                        "places_without_ratings": len(places_data) - places_with_ratings,
                        "average_rating": round(avg_rating, 2) if avg_rating else None,
                        "total_reviews": sum(p.get("user_ratings_total", 0) for p in places_data)
                    },
                    "source": "google_places_api",
                    "adapter_version": "1.1.0",
                    "cache_expiry_hours": CACHE_EXPIRY_HOURS
                },
                "places": places_data
            }
            
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.logger.debug(
                f"Saved raw data to {filepath}",
                extra={"extra_fields": {
                    "filepath": str(filepath),
                    "place_count": len(places_data),
                    "file_size_kb": round(filepath.stat().st_size / 1024, 2)
                }}
            )
            
        except Exception as e:
            self.logger.warning(
                f"Failed to save raw data: {e}",
                extra={"extra_fields": {"error": str(e)}}
            )


# ============================================================================
# Module-level convenience functions
# ============================================================================

def create_adapter(api_key: Optional[str] = None) -> GooglePlacesAdapter:
    """
    Create GooglePlacesAdapter with API key from environment or parameter.
    
    Args:
        api_key: Google Places API key (if None, reads from GOOGLE_PLACES_API_KEY env var)
        
    Returns:
        GooglePlacesAdapter instance
        
    Raises:
        ValueError: If no API key provided or found in environment
        
    Example:
        >>> adapter = create_adapter()  # Uses GOOGLE_PLACES_API_KEY from .env
        >>> businesses = adapter.fetch_businesses("Gym", bounds)
    """
    if api_key is None:
        api_key = os.getenv("GOOGLE_PLACES_API_KEY")
    
    if not api_key:
        raise ValueError(
            "Google Places API key required. "
            "Set GOOGLE_PLACES_API_KEY environment variable or pass api_key parameter."
        )
    
    return GooglePlacesAdapter(api_key=api_key)


# ============================================================================
# Test/Demo Code
# ============================================================================

if __name__ == "__main__":
    """
    Quick test of GooglePlacesAdapter.
    
    Usage:
        python -m src.adapters.google_places_adapter
    """
    import sys
    
    # Check for API key
    api_key = os.getenv("GOOGLE_PLACES_API_KEY")
    if not api_key:
        print("ERROR: GOOGLE_PLACES_API_KEY environment variable not set")
        print("Set it in your .env file or environment:")
        print("  export GOOGLE_PLACES_API_KEY=your_key_here")
        sys.exit(1)
    
    # Create adapter
    print("Creating GooglePlacesAdapter...")
    try:
        adapter = GooglePlacesAdapter(api_key=api_key)
    except ValueError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    
    # Test with DHA Phase 2 Cell-07 bounds (from documentation)
    print("\nFetching businesses for DHA Phase 2 Cell-07 (Gym category)...")
    print("First fetch will query API, second fetch will use cache...\n")
    
    test_bounds = {
        "lat_north": 24.8320,
        "lat_south": 24.8260,
        "lon_east": 67.0640,
        "lon_west": 67.0580
    }
    
    try:
        # First fetch - will query API
        print("=" * 80)
        print("TEST 1: Fresh API call")
        print("=" * 80)
        businesses = adapter.fetch_businesses(category="Gym", bounds=test_bounds)
        
        print(f"\nResults: {len(businesses)} businesses found")
        print("-" * 80)
        
        for i, biz in enumerate(businesses[:5], 1):  # Show first 5
            print(f"{i}. {biz.name}")
            print(f"   Location: ({biz.lat:.4f}, {biz.lon:.4f})")
            print(f"   Rating: {biz.rating if biz.rating else 'N/A'} ({biz.review_count} reviews)")
            print(f"   Grid ID: {biz.grid_id}")
            print()
        
        if len(businesses) > 5:
            print(f"... and {len(businesses) - 5} more")
        
        # Second fetch - should use cache
        print("\n" + "=" * 80)
        print("TEST 2: Cache test (should load from cache)")
        print("=" * 80)
        businesses_cached = adapter.fetch_businesses(category="Gym", bounds=test_bounds)
        print(f"Results: {len(businesses_cached)} businesses (from cache)")
        
        # Third fetch - force refresh
        print("\n" + "=" * 80)
        print("TEST 3: Force refresh (bypass cache)")
        print("=" * 80)
        businesses_fresh = adapter.fetch_businesses(
            category="Gym",
            bounds=test_bounds,
            force_refresh=True
        )
        print(f"Results: {len(businesses_fresh)} businesses (fresh from API)")
        
        print("\n" + "=" * 80)
        print("✓ All tests completed successfully")
        print("=" * 80)
        print(f"✓ Raw data saved to {RAW_DATA_DIR}")
        print(f"✓ Cache expiry: {CACHE_EXPIRY_HOURS} hours")
        print(f"✓ Rate limit: {MAX_REQUESTS_PER_SECOND} requests/second")
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
