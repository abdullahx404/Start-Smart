"""
Business Environment Vector (BEV) Generator

Computes structured, numerical features for each grid/sector based on
Google Places data. The BEV captures the business environment characteristics
that inform location suitability for different business types.

Features:
- Density features (counts of various POI types)
- Distance features (to key amenities)
- Economic proxy features (ratings, review counts, price levels)

Usage:
    from src.services.bev_generator import BEVGenerator
    
    generator = BEVGenerator(api_key="YOUR_API_KEY")
    bev = generator.generate_bev(
        center_lat=24.8150,
        center_lon=67.0280,
        radius_meters=500
    )
"""

import os
import math
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path

import googlemaps
from googlemaps.exceptions import ApiError, Timeout, TransportError

from src.utils.logger import get_logger


# ============================================================================
# Constants
# ============================================================================

# POI types to count for density features
DENSITY_POI_TYPES = {
    # Food & Beverage
    "restaurants": ["restaurant", "food"],
    "cafes": ["cafe", "coffee_shop"],
    "bakeries": ["bakery"],
    "bars": ["bar", "night_club"],
    
    # Fitness & Health
    "gyms": ["gym", "health"],
    "spas": ["spa", "beauty_salon"],
    "healthcare": ["hospital", "doctor", "dentist", "pharmacy", "physiotherapist"],
    
    # Education
    "schools": ["school", "primary_school", "secondary_school"],
    "universities": ["university"],
    "training_centers": ["training_center"],
    
    # Commerce
    "offices": ["office", "corporate_office"],
    "malls": ["shopping_mall"],
    "stores": ["store", "supermarket", "convenience_store"],
    "banks": ["bank", "atm"],
    
    # Entertainment
    "cinemas": ["movie_theater"],
    "parks": ["park", "amusement_park"],
    
    # Transport
    "transit_stations": ["transit_station", "bus_station", "subway_station"],
    "gas_stations": ["gas_station"],
    
    # Residential indicators
    "residential": ["apartment", "residential"],
}

# Key amenities for distance features
DISTANCE_AMENITIES = [
    "shopping_mall",
    "movie_theater", 
    "university",
    "hospital",
    "transit_station",
    "park",
]

# Income proxy thresholds
INCOME_THRESHOLDS = {
    "high": {"avg_rating": 4.3, "premium_ratio": 0.4},
    "mid": {"avg_rating": 3.8, "premium_ratio": 0.2},
    "low": {"avg_rating": 0, "premium_ratio": 0},
}

# Search radius configurations
DEFAULT_RADIUS = 500  # meters
EXTENDED_RADIUS = 1000  # for distance calculations


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class DensityFeatures:
    """Counts of various POI types in the area."""
    restaurants: int = 0
    cafes: int = 0
    bakeries: int = 0
    bars: int = 0
    gyms: int = 0
    spas: int = 0
    healthcare: int = 0
    schools: int = 0
    universities: int = 0
    training_centers: int = 0
    offices: int = 0
    malls: int = 0
    stores: int = 0
    banks: int = 0
    cinemas: int = 0
    parks: int = 0
    transit_stations: int = 0
    gas_stations: int = 0
    residential: int = 0
    
    def to_dict(self) -> Dict[str, int]:
        return asdict(self)


@dataclass
class DistanceFeatures:
    """Distances to key amenities in meters."""
    distance_to_mall: float = -1  # -1 means not found
    distance_to_cinema: float = -1
    distance_to_university: float = -1
    distance_to_hospital: float = -1
    distance_to_transit: float = -1
    distance_to_park: float = -1
    distance_to_main_road: float = -1  # Estimated based on transit
    
    def to_dict(self) -> Dict[str, float]:
        return asdict(self)


@dataclass
class EconomicFeatures:
    """Economic proxy features derived from business data."""
    avg_business_rating: float = 0.0
    avg_review_count: float = 0.0
    total_businesses: int = 0
    premium_business_count: int = 0  # Price level 3-4
    economy_business_count: int = 0  # Price level 1-2
    premium_to_economy_ratio: float = 0.0
    income_proxy: str = "unknown"  # low/mid/high
    competition_density: float = 0.0  # businesses per 100m²
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class BusinessEnvironmentVector:
    """
    Complete Business Environment Vector for a location.
    
    Combines density, distance, and economic features into a single
    structured representation of the business environment.
    """
    # Location info
    grid_id: Optional[str] = None
    center_lat: float = 0.0
    center_lon: float = 0.0
    radius_meters: int = DEFAULT_RADIUS
    
    # Feature groups
    density: DensityFeatures = field(default_factory=DensityFeatures)
    distance: DistanceFeatures = field(default_factory=DistanceFeatures)
    economic: EconomicFeatures = field(default_factory=EconomicFeatures)
    
    # Metadata
    generated_at: str = ""
    api_calls_used: int = 0
    
    def __post_init__(self):
        if not self.generated_at:
            self.generated_at = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to flat dictionary for API response."""
        result = {
            "grid_id": self.grid_id,
            "center_lat": self.center_lat,
            "center_lon": self.center_lon,
            "radius_meters": self.radius_meters,
            "generated_at": self.generated_at,
            "api_calls_used": self.api_calls_used,
        }
        result.update(self.density.to_dict())
        result.update(self.distance.to_dict())
        result.update(self.economic.to_dict())
        return result
    
    def to_prompt_format(self) -> str:
        """Format BEV for LLM prompt."""
        lines = [
            "[Business Environment Vector]",
            f"Location: ({self.center_lat:.6f}, {self.center_lon:.6f})",
            f"Analysis radius: {self.radius_meters}m",
            "",
            "=== Density Features ===",
            f"Restaurants: {self.density.restaurants}",
            f"Cafes: {self.density.cafes}",
            f"Gyms: {self.density.gyms}",
            f"Schools: {self.density.schools}",
            f"Universities: {self.density.universities}",
            f"Offices: {self.density.offices}",
            f"Malls: {self.density.malls}",
            f"Stores: {self.density.stores}",
            f"Parks: {self.density.parks}",
            f"Transit Stations: {self.density.transit_stations}",
            f"Healthcare: {self.density.healthcare}",
            f"Bars/Nightlife: {self.density.bars}",
            "",
            "=== Distance Features ===",
            f"Distance to nearest mall: {self._format_distance(self.distance.distance_to_mall)}",
            f"Distance to nearest cinema: {self._format_distance(self.distance.distance_to_cinema)}",
            f"Distance to nearest university: {self._format_distance(self.distance.distance_to_university)}",
            f"Distance to transit station: {self._format_distance(self.distance.distance_to_transit)}",
            f"Distance to park: {self._format_distance(self.distance.distance_to_park)}",
            "",
            "=== Economic Indicators ===",
            f"Average business rating: {self.economic.avg_business_rating:.2f}/5.0",
            f"Average review count: {self.economic.avg_review_count:.0f}",
            f"Total businesses in area: {self.economic.total_businesses}",
            f"Premium to economy ratio: {self.economic.premium_to_economy_ratio:.2f}",
            f"Income proxy: {self.economic.income_proxy}",
            f"Competition density: {self.economic.competition_density:.2f} businesses per 100m²",
        ]
        return "\n".join(lines)
    
    def _format_distance(self, distance: float) -> str:
        if distance < 0:
            return "Not found within search radius"
        elif distance < 100:
            return f"{distance:.0f}m (very close)"
        elif distance < 300:
            return f"{distance:.0f}m (close)"
        elif distance < 500:
            return f"{distance:.0f}m (moderate)"
        else:
            return f"{distance:.0f}m (far)"


# ============================================================================
# BEV Generator Class
# ============================================================================

class BEVGenerator:
    """
    Generates Business Environment Vectors from Google Places data.
    
    Uses Google Places API to gather POI data and compute structured
    features for location analysis.
    """
    
    def __init__(self, api_key: str = None):
        """
        Initialize BEV generator.
        
        Args:
            api_key: Google Places API key. If None, reads from environment.
        """
        self.api_key = api_key or os.getenv("GOOGLE_PLACES_API_KEY")
        if not self.api_key:
            raise ValueError("Google Places API key is required")
        
        self.client = googlemaps.Client(key=self.api_key)
        self.logger = get_logger(__name__)
        self._api_calls = 0
        
        self.logger.info("BEVGenerator initialized")
    
    def generate_bev(
        self,
        center_lat: float,
        center_lon: float,
        radius_meters: int = DEFAULT_RADIUS,
        grid_id: str = None
    ) -> BusinessEnvironmentVector:
        """
        Generate complete BEV for a location.
        
        Args:
            center_lat: Center latitude
            center_lon: Center longitude
            radius_meters: Search radius in meters
            grid_id: Optional grid identifier
            
        Returns:
            BusinessEnvironmentVector with all computed features
        """
        self._api_calls = 0
        
        self.logger.info(
            f"Generating BEV for ({center_lat:.6f}, {center_lon:.6f})",
            extra={"extra_fields": {"radius": radius_meters, "grid_id": grid_id}}
        )
        
        # Fetch all nearby places
        all_places = self._fetch_all_nearby_places(center_lat, center_lon, radius_meters)
        
        # Compute density features
        density = self._compute_density_features(all_places)
        
        # Compute distance features
        distance = self._compute_distance_features(
            center_lat, center_lon, all_places, radius_meters
        )
        
        # Compute economic features
        economic = self._compute_economic_features(all_places, radius_meters)
        
        bev = BusinessEnvironmentVector(
            grid_id=grid_id,
            center_lat=center_lat,
            center_lon=center_lon,
            radius_meters=radius_meters,
            density=density,
            distance=distance,
            economic=economic,
            api_calls_used=self._api_calls
        )
        
        self.logger.info(
            f"BEV generated successfully",
            extra={"extra_fields": {
                "total_businesses": economic.total_businesses,
                "api_calls": self._api_calls
            }}
        )
        
        return bev
    
    def generate_bev_for_grid(
        self,
        grid_bounds: Dict[str, float],
        grid_id: str = None
    ) -> BusinessEnvironmentVector:
        """
        Generate BEV for a grid cell using its bounds.
        
        Args:
            grid_bounds: Dict with lat_north, lat_south, lon_east, lon_west
            grid_id: Grid identifier
            
        Returns:
            BusinessEnvironmentVector
        """
        # Calculate center
        center_lat = (grid_bounds["lat_north"] + grid_bounds["lat_south"]) / 2
        center_lon = (grid_bounds["lon_east"] + grid_bounds["lon_west"]) / 2
        
        # Calculate approximate radius
        lat_span = grid_bounds["lat_north"] - grid_bounds["lat_south"]
        lon_span = grid_bounds["lon_east"] - grid_bounds["lon_west"]
        radius = max(
            lat_span * 111000 / 2,  # Convert lat degrees to meters
            lon_span * 100000 / 2   # Approximate lon degrees to meters
        )
        radius = int(min(radius * 1.5, 1000))  # Extend slightly, cap at 1km
        
        return self.generate_bev(center_lat, center_lon, radius, grid_id)
    
    def _fetch_all_nearby_places(
        self,
        lat: float,
        lon: float,
        radius: int
    ) -> List[Dict]:
        """Fetch all nearby places using multiple type queries."""
        all_places = []
        seen_ids = set()
        
        # Query for each POI type group
        types_to_query = [
            "restaurant", "cafe", "gym", "school", "university",
            "shopping_mall", "store", "hospital", "bank",
            "transit_station", "park", "movie_theater", "bar"
        ]
        
        for place_type in types_to_query:
            try:
                results = self._nearby_search(lat, lon, radius, place_type)
                
                for place in results:
                    place_id = place.get("place_id")
                    if place_id and place_id not in seen_ids:
                        seen_ids.add(place_id)
                        all_places.append(place)
                        
            except Exception as e:
                self.logger.warning(f"Error fetching {place_type}: {e}")
                continue
        
        self.logger.debug(f"Fetched {len(all_places)} unique places")
        return all_places
    
    def _nearby_search(
        self,
        lat: float,
        lon: float,
        radius: int,
        place_type: str
    ) -> List[Dict]:
        """Perform a single nearby search with pagination."""
        results = []
        
        try:
            response = self.client.places_nearby(
                location=(lat, lon),
                radius=radius,
                type=place_type
            )
            self._api_calls += 1
            
            results.extend(response.get("results", []))
            
            # Handle pagination (up to 2 more pages)
            page_count = 0
            while "next_page_token" in response and page_count < 2:
                import time
                time.sleep(2)  # Required delay for page token
                
                response = self.client.places_nearby(
                    page_token=response["next_page_token"]
                )
                self._api_calls += 1
                results.extend(response.get("results", []))
                page_count += 1
                
        except (ApiError, Timeout, TransportError) as e:
            self.logger.warning(f"API error in nearby search: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error in nearby search: {e}")
        
        return results
    
    def _compute_density_features(self, places: List[Dict]) -> DensityFeatures:
        """Count POIs by category."""
        density = DensityFeatures()
        
        for place in places:
            place_types = set(place.get("types", []))
            
            # Check each density category
            for category, type_list in DENSITY_POI_TYPES.items():
                if any(t in place_types for t in type_list):
                    current = getattr(density, category, 0)
                    setattr(density, category, current + 1)
        
        return density
    
    def _compute_distance_features(
        self,
        center_lat: float,
        center_lon: float,
        places: List[Dict],
        radius: int
    ) -> DistanceFeatures:
        """Calculate distances to nearest key amenities."""
        distance = DistanceFeatures()
        
        # Type to attribute mapping
        type_mapping = {
            "shopping_mall": "distance_to_mall",
            "movie_theater": "distance_to_cinema",
            "university": "distance_to_university",
            "hospital": "distance_to_hospital",
            "transit_station": "distance_to_transit",
            "bus_station": "distance_to_transit",
            "subway_station": "distance_to_transit",
            "park": "distance_to_park",
        }
        
        # Find nearest of each type
        for place in places:
            place_types = set(place.get("types", []))
            geometry = place.get("geometry", {})
            location = geometry.get("location", {})
            
            if not location:
                continue
            
            place_lat = location.get("lat", 0)
            place_lon = location.get("lng", 0)
            dist = self._haversine_distance(
                center_lat, center_lon, place_lat, place_lon
            )
            
            for poi_type, attr in type_mapping.items():
                if poi_type in place_types:
                    current = getattr(distance, attr)
                    if current < 0 or dist < current:
                        setattr(distance, attr, round(dist, 1))
        
        # Estimate main road distance from transit
        if distance.distance_to_transit >= 0:
            distance.distance_to_main_road = max(50, distance.distance_to_transit - 50)
        
        return distance
    
    def _compute_economic_features(
        self,
        places: List[Dict],
        radius: int
    ) -> EconomicFeatures:
        """Compute economic proxy features."""
        economic = EconomicFeatures()
        
        ratings = []
        review_counts = []
        premium_count = 0
        economy_count = 0
        
        for place in places:
            rating = place.get("rating")
            reviews = place.get("user_ratings_total", 0)
            price_level = place.get("price_level")
            
            if rating:
                ratings.append(rating)
            if reviews:
                review_counts.append(reviews)
            
            if price_level is not None:
                if price_level >= 3:
                    premium_count += 1
                elif price_level <= 2:
                    economy_count += 1
        
        economic.total_businesses = len(places)
        
        if ratings:
            economic.avg_business_rating = round(sum(ratings) / len(ratings), 2)
        
        if review_counts:
            economic.avg_review_count = round(sum(review_counts) / len(review_counts), 1)
        
        economic.premium_business_count = premium_count
        economic.economy_business_count = economy_count
        
        if economy_count > 0:
            economic.premium_to_economy_ratio = round(premium_count / economy_count, 2)
        elif premium_count > 0:
            economic.premium_to_economy_ratio = 2.0  # All premium
        
        # Determine income proxy
        if (economic.avg_business_rating >= INCOME_THRESHOLDS["high"]["avg_rating"] and
            economic.premium_to_economy_ratio >= INCOME_THRESHOLDS["high"]["premium_ratio"]):
            economic.income_proxy = "high"
        elif (economic.avg_business_rating >= INCOME_THRESHOLDS["mid"]["avg_rating"] and
              economic.premium_to_economy_ratio >= INCOME_THRESHOLDS["mid"]["premium_ratio"]):
            economic.income_proxy = "mid"
        else:
            economic.income_proxy = "low"
        
        # Competition density (per 100m²)
        area_100m2 = (math.pi * radius * radius) / 100
        if area_100m2 > 0:
            economic.competition_density = round(len(places) / area_100m2, 4)
        
        return economic
    
    def _haversine_distance(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float
    ) -> float:
        """Calculate distance between two points in meters."""
        R = 6371000  # Earth radius in meters
        
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_phi / 2) ** 2 +
             math.cos(phi1) * math.cos(phi2) *
             math.sin(delta_lambda / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c


# ============================================================================
# Convenience Functions
# ============================================================================

def generate_bev(
    lat: float,
    lon: float,
    radius: int = DEFAULT_RADIUS,
    grid_id: str = None
) -> BusinessEnvironmentVector:
    """Convenience function to generate BEV."""
    generator = BEVGenerator()
    return generator.generate_bev(lat, lon, radius, grid_id)


# ============================================================================
# Testing
# ============================================================================

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    # Test with Clifton Block 2 center
    generator = BEVGenerator()
    bev = generator.generate_bev(
        center_lat=24.8160,
        center_lon=67.0280,
        radius_meters=500,
        grid_id="Clifton-Block2-007-008"
    )
    
    print("\n" + "="*60)
    print("BEV GENERATION TEST")
    print("="*60)
    print(bev.to_prompt_format())
    print("\n" + "="*60)
    print(f"API calls used: {bev.api_calls_used}")
