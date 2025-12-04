"""
Comprehensive Places Adapter

Enhanced Google Places adapter using multiple search strategies to maximize
business extraction. Combines Nearby Search, Text Search, and grid-sweep
techniques to capture all businesses in an area.

Features:
- Grid-sweep with overlapping radius circles
- Text Search with category keywords
- Automatic deduplication by place_id
- Comprehensive business attribute extraction
- Rate limiting and retry logic

Usage:
    from src.adapters.comprehensive_places_adapter import ComprehensivePlacesAdapter
    
    adapter = ComprehensivePlacesAdapter(api_key="YOUR_API_KEY")
    businesses = adapter.fetch_all_businesses(
        bounds={...},
        category="Gym"
    )
"""

import time
import math
from typing import List, Dict, Optional, Set, Tuple, Any
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict

import googlemaps
from googlemaps.exceptions import ApiError, Timeout, TransportError

from contracts.models import Business, Category, Source
from src.utils.logger import get_logger, log_api_call


# ============================================================================
# Constants
# ============================================================================

# Category mapping for different search strategies
CATEGORY_MAPPING = {
    "Gym": {
        "type": "gym",
        "keywords": [
            "gym",
            "fitness center", 
            "fitness studio",
            "health club",
            "workout",
            "crossfit",
            "bodybuilding gym",
            "weight training",
            "yoga studio",
            "pilates studio"
        ]
    },
    "Cafe": {
        "type": "cafe",
        "keywords": [
            "cafe",
            "coffee shop",
            "coffee house",
            "bakery cafe",
            "tea house",
            "espresso bar",
            "coffee roasters"
        ]
    }
}

# API configuration
MAX_RESULTS_PER_NEARBY_CALL = 60
MAX_RESULTS_PER_TEXT_CALL = 60
SWEEP_RADIUS_METERS = 300  # Radius for each sweep circle
SWEEP_OVERLAP_FACTOR = 0.7  # 70% overlap between circles
MIN_REQUEST_INTERVAL = 0.1  # Seconds between API calls
MAX_RETRIES = 3
INITIAL_BACKOFF = 1.0

# Data storage
RAW_DATA_DIR = Path("data/raw/comprehensive_places")


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class ExtractedBusiness:
    """
    Raw business data extracted from Google Places.
    
    This is the intermediate format before conversion to our Business model.
    """
    place_id: str
    name: str
    lat: float
    lon: float
    address: Optional[str]
    rating: Optional[float]
    total_ratings: int
    price_level: Optional[int]
    types: List[str]
    business_status: str
    extracted_from: str  # "nearby" or "text"
    search_keyword: Optional[str]
    extracted_at: str
    
    def to_dict(self) -> Dict:
        return asdict(self)


# ============================================================================
# Comprehensive Places Adapter
# ============================================================================

class ComprehensivePlacesAdapter:
    """
    Enhanced Google Places adapter for comprehensive business extraction.
    
    Uses multiple strategies to maximize coverage:
    1. Grid-sweep Nearby Search: Divide area into overlapping circles
    2. Text Search with keywords: Search by category-specific keywords
    3. Deduplication: Remove duplicates by place_id
    
    Attributes:
        client: Google Maps API client
        logger: Logger instance
        api_key_masked: Masked API key for logging
    """
    
    def __init__(self, api_key: str):
        """
        Initialize the comprehensive places adapter.
        
        Args:
            api_key: Google Places API key
            
        Raises:
            ValueError: If API key is empty or invalid
        """
        if not api_key:
            raise ValueError("Google Places API key is required")
        
        self.client = googlemaps.Client(key=api_key)
        self.logger = get_logger(__name__)
        self.api_key_masked = api_key[:8] + "***" if len(api_key) > 8 else "***"
        
        self._last_request_time = 0.0
        self._api_calls_count = 0
        
        RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(
            "ComprehensivePlacesAdapter initialized",
            extra={"extra_fields": {"api_key": self.api_key_masked}}
        )
    
    def fetch_all_businesses(
        self,
        bounds: Dict[str, float],
        category: str,
        include_text_search: bool = True,
        save_raw: bool = True
    ) -> List[ExtractedBusiness]:
        """
        Fetch all businesses in bounds using multiple strategies.
        
        Combines grid-sweep Nearby Search with Text Search for comprehensive
        coverage. Automatically deduplicates results.
        
        Args:
            bounds: Geographic bounds (lat_north, lat_south, lon_east, lon_west)
            category: Business category ("Gym", "Cafe")
            include_text_search: Whether to also use Text Search API
            save_raw: Whether to save raw results to file
            
        Returns:
            List of ExtractedBusiness objects (deduplicated)
        """
        self.logger.info(
            f"Starting comprehensive extraction for {category}",
            extra={"extra_fields": {"bounds": bounds}}
        )
        
        start_time = time.time()
        all_results: Dict[str, ExtractedBusiness] = {}
        
        # Strategy 1: Grid-sweep Nearby Search
        nearby_results = self._grid_sweep_nearby_search(bounds, category)
        for business in nearby_results:
            if business.place_id not in all_results:
                all_results[business.place_id] = business
        
        self.logger.info(
            f"Grid-sweep found {len(nearby_results)} businesses, "
            f"{len(all_results)} unique"
        )
        
        # Strategy 2: Text Search with keywords
        if include_text_search:
            text_results = self._text_search_keywords(bounds, category)
            new_count = 0
            for business in text_results:
                if business.place_id not in all_results:
                    all_results[business.place_id] = business
                    new_count += 1
            
            self.logger.info(
                f"Text search found {len(text_results)} businesses, "
                f"{new_count} new unique"
            )
        
        # Convert to list
        businesses = list(all_results.values())
        
        elapsed = time.time() - start_time
        self.logger.info(
            f"Comprehensive extraction complete for {category}",
            extra={"extra_fields": {
                "total_unique": len(businesses),
                "api_calls": self._api_calls_count,
                "elapsed_seconds": round(elapsed, 2)
            }}
        )
        
        # Save raw results
        if save_raw and businesses:
            self._save_raw_results(businesses, category, bounds)
        
        return businesses
    
    def _grid_sweep_nearby_search(
        self,
        bounds: Dict[str, float],
        category: str
    ) -> List[ExtractedBusiness]:
        """
        Perform grid-sweep Nearby Search over the bounds.
        
        Divides the area into overlapping circles and searches each.
        
        Args:
            bounds: Geographic bounds
            category: Business category
            
        Returns:
            List of ExtractedBusiness objects (may contain duplicates)
        """
        # Get Google Places type for category
        category_config = CATEGORY_MAPPING.get(category)
        if not category_config:
            self.logger.warning(f"Unknown category: {category}")
            return []
        
        place_type = category_config["type"]
        
        # Calculate sweep grid
        sweep_points = self._calculate_sweep_points(bounds, SWEEP_RADIUS_METERS)
        
        self.logger.info(
            f"Grid-sweep with {len(sweep_points)} search points",
            extra={"extra_fields": {"radius_m": SWEEP_RADIUS_METERS}}
        )
        
        results = []
        
        for i, (lat, lon) in enumerate(sweep_points):
            try:
                self._rate_limit()
                
                response = self.client.places_nearby(
                    location=(lat, lon),
                    radius=SWEEP_RADIUS_METERS,
                    type=place_type
                )
                self._api_calls_count += 1
                
                places = response.get("results", [])
                
                # Handle pagination if available
                while "next_page_token" in response and len(places) < MAX_RESULTS_PER_NEARBY_CALL:
                    time.sleep(2)  # Google requires delay before using page token
                    self._rate_limit()
                    
                    response = self.client.places_nearby(
                        page_token=response["next_page_token"]
                    )
                    self._api_calls_count += 1
                    places.extend(response.get("results", []))
                
                # Convert to ExtractedBusiness
                for place in places:
                    business = self._convert_place_to_business(
                        place,
                        extracted_from="nearby"
                    )
                    if business:
                        results.append(business)
                
                if (i + 1) % 10 == 0:
                    self.logger.debug(
                        f"Sweep progress: {i + 1}/{len(sweep_points)} points, "
                        f"{len(results)} results"
                    )
                    
            except (ApiError, Timeout, TransportError) as e:
                self.logger.warning(f"API error at point ({lat}, {lon}): {e}")
                continue
            except Exception as e:
                self.logger.error(f"Unexpected error at point ({lat}, {lon}): {e}")
                continue
        
        return results
    
    def _text_search_keywords(
        self,
        bounds: Dict[str, float],
        category: str
    ) -> List[ExtractedBusiness]:
        """
        Perform Text Search with category-specific keywords.
        
        Uses multiple keywords to find businesses that might be missed
        by type-based Nearby Search.
        
        Args:
            bounds: Geographic bounds
            category: Business category
            
        Returns:
            List of ExtractedBusiness objects
        """
        category_config = CATEGORY_MAPPING.get(category)
        if not category_config:
            return []
        
        keywords = category_config["keywords"]
        
        # Calculate center and radius for location bias
        center_lat = (bounds["lat_north"] + bounds["lat_south"]) / 2
        center_lon = (bounds["lon_east"] + bounds["lon_west"]) / 2
        
        # Calculate approximate radius to cover bounds
        lat_span = bounds["lat_north"] - bounds["lat_south"]
        lon_span = bounds["lon_east"] - bounds["lon_west"]
        radius = int(max(lat_span * 111111, lon_span * 100900) / 2)
        radius = min(radius, 50000)  # Google max is 50km
        
        results = []
        
        for keyword in keywords:
            try:
                self._rate_limit()
                
                # Add location context to query
                query = f"{keyword} in Clifton Karachi"
                
                response = self.client.places(
                    query=query,
                    location=(center_lat, center_lon),
                    radius=radius
                )
                self._api_calls_count += 1
                
                places = response.get("results", [])
                
                # Handle pagination
                while "next_page_token" in response and len(places) < MAX_RESULTS_PER_TEXT_CALL:
                    time.sleep(2)
                    self._rate_limit()
                    
                    response = self.client.places(
                        page_token=response["next_page_token"]
                    )
                    self._api_calls_count += 1
                    places.extend(response.get("results", []))
                
                # Filter to bounds and convert
                for place in places:
                    business = self._convert_place_to_business(
                        place,
                        extracted_from="text",
                        search_keyword=keyword
                    )
                    if business and self._is_within_bounds(business, bounds):
                        results.append(business)
                
                self.logger.debug(
                    f"Keyword '{keyword}' found {len(places)} places, "
                    f"{sum(1 for b in results if b.search_keyword == keyword)} in bounds"
                )
                
            except (ApiError, Timeout, TransportError) as e:
                self.logger.warning(f"API error for keyword '{keyword}': {e}")
                continue
            except Exception as e:
                self.logger.error(f"Unexpected error for keyword '{keyword}': {e}")
                continue
        
        return results
    
    def _calculate_sweep_points(
        self,
        bounds: Dict[str, float],
        radius_meters: float
    ) -> List[Tuple[float, float]]:
        """
        Calculate grid of points for sweep search.
        
        Creates overlapping circles that cover the entire bounds.
        
        Args:
            bounds: Geographic bounds
            radius_meters: Search radius for each point
            
        Returns:
            List of (lat, lon) tuples
        """
        # Calculate step size (with overlap)
        step_meters = radius_meters * 2 * SWEEP_OVERLAP_FACTOR
        
        # Convert to degrees
        lat_step = step_meters / 111111  # ~111km per degree latitude
        center_lat = (bounds["lat_north"] + bounds["lat_south"]) / 2
        lon_step = step_meters / (111320 * math.cos(math.radians(center_lat)))
        
        points = []
        
        lat = bounds["lat_south"]
        while lat <= bounds["lat_north"]:
            lon = bounds["lon_west"]
            while lon <= bounds["lon_east"]:
                points.append((lat, lon))
                lon += lon_step
            lat += lat_step
        
        return points
    
    def _convert_place_to_business(
        self,
        place: Dict[str, Any],
        extracted_from: str,
        search_keyword: Optional[str] = None
    ) -> Optional[ExtractedBusiness]:
        """
        Convert Google Places result to ExtractedBusiness.
        
        Args:
            place: Google Places API result
            extracted_from: "nearby" or "text"
            search_keyword: Keyword used for text search
            
        Returns:
            ExtractedBusiness or None if conversion fails
        """
        try:
            geometry = place.get("geometry", {})
            location = geometry.get("location", {})
            
            if not location:
                return None
            
            return ExtractedBusiness(
                place_id=place.get("place_id", ""),
                name=place.get("name", "Unknown"),
                lat=location.get("lat", 0),
                lon=location.get("lng", 0),
                address=place.get("vicinity") or place.get("formatted_address"),
                rating=place.get("rating"),
                total_ratings=place.get("user_ratings_total", 0),
                price_level=place.get("price_level"),
                types=place.get("types", []),
                business_status=place.get("business_status", "UNKNOWN"),
                extracted_from=extracted_from,
                search_keyword=search_keyword,
                extracted_at=datetime.utcnow().isoformat()
            )
        except Exception as e:
            self.logger.warning(f"Failed to convert place: {e}")
            return None
    
    def _is_within_bounds(
        self,
        business: ExtractedBusiness,
        bounds: Dict[str, float]
    ) -> bool:
        """
        Check if business is within geographic bounds.
        
        Args:
            business: ExtractedBusiness to check
            bounds: Geographic bounds
            
        Returns:
            True if within bounds, False otherwise
        """
        return (
            bounds["lat_south"] <= business.lat <= bounds["lat_north"] and
            bounds["lon_west"] <= business.lon <= bounds["lon_east"]
        )
    
    def _rate_limit(self):
        """Enforce rate limiting between API calls."""
        elapsed = time.time() - self._last_request_time
        if elapsed < MIN_REQUEST_INTERVAL:
            time.sleep(MIN_REQUEST_INTERVAL - elapsed)
        self._last_request_time = time.time()
    
    def _save_raw_results(
        self,
        businesses: List[ExtractedBusiness],
        category: str,
        bounds: Dict[str, float]
    ):
        """Save raw results to JSON file for auditing."""
        import json
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{category.lower()}_{timestamp}.json"
        filepath = RAW_DATA_DIR / filename
        
        data = {
            "category": category,
            "bounds": bounds,
            "extraction_time": datetime.utcnow().isoformat(),
            "total_businesses": len(businesses),
            "api_calls": self._api_calls_count,
            "businesses": [b.to_dict() for b in businesses]
        }
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Saved raw results to {filepath}")
    
    def convert_to_business_models(
        self,
        extracted: List[ExtractedBusiness],
        category: str,
        assign_grid_fn=None
    ) -> List[Business]:
        """
        Convert ExtractedBusiness objects to our Business model.
        
        Args:
            extracted: List of ExtractedBusiness objects
            category: Category name
            assign_grid_fn: Optional function to assign grid_id from coordinates
            
        Returns:
            List of Business model objects
        """
        businesses = []
        
        for ext in extracted:
            try:
                grid_id = None
                if assign_grid_fn:
                    grid_id = assign_grid_fn(ext.lat, ext.lon)
                
                business = Business(
                    business_id=ext.place_id,
                    name=ext.name,
                    category=Category[category.upper()],
                    latitude=ext.lat,
                    longitude=ext.lon,
                    address=ext.address,
                    rating=ext.rating,
                    total_ratings=ext.total_ratings,
                    price_level=ext.price_level,
                    source=Source.GOOGLE_PLACES,
                    grid_id=grid_id,
                    raw_data={
                        "types": ext.types,
                        "business_status": ext.business_status,
                        "extracted_from": ext.extracted_from,
                        "search_keyword": ext.search_keyword
                    }
                )
                businesses.append(business)
                
            except Exception as e:
                self.logger.warning(f"Failed to convert {ext.name}: {e}")
                continue
        
        return businesses


# ============================================================================
# Module-level convenience function
# ============================================================================

def fetch_comprehensive_businesses(
    api_key: str,
    bounds: Dict[str, float],
    category: str
) -> List[ExtractedBusiness]:
    """
    Convenience function for comprehensive business extraction.
    
    Args:
        api_key: Google Places API key
        bounds: Geographic bounds
        category: Business category
        
    Returns:
        List of ExtractedBusiness objects
    """
    adapter = ComprehensivePlacesAdapter(api_key)
    return adapter.fetch_all_businesses(bounds, category)


# ============================================================================
# Testing
# ============================================================================

if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    api_key = os.getenv("GOOGLE_PLACES_API_KEY")
    
    if not api_key:
        print("Error: GOOGLE_PLACES_API_KEY not found in environment")
        exit(1)
    
    # Test with Clifton-Block2
    test_bounds = {
        "lat_north": 24.8220,
        "lat_south": 24.8100,
        "lon_east": 67.0360,
        "lon_west": 67.0200
    }
    
    adapter = ComprehensivePlacesAdapter(api_key)
    businesses = adapter.fetch_all_businesses(test_bounds, "Gym")
    
    print(f"\n=== Comprehensive Extraction Test ===")
    print(f"Found {len(businesses)} unique businesses")
    
    for b in businesses[:5]:
        print(f"  - {b.name} ({b.rating}★, {b.total_ratings} reviews)")
