"""
StartSmart MVP - Data Adapter Interface Contract
Phase 0: Interface Contracts

This module defines the abstract base class that all data source adapters
must implement. This contract is LOCKED for MVP.

Adapter Pattern Benefits:
1. Allows easy swapping between real and synthetic data sources
2. Enables testing with mock adapters
3. Supports future expansion to new data sources
4. Enforces consistent interface across all data fetching

Phase 1 Implementations:
- GooglePlacesAdapter: Real business data from Google Places API
- SimulatedSocialAdapter: Synthetic social media posts from JSON files

Post-MVP Implementations:
- InstagramAdapter: Real Instagram data via scraping (Playwright)
- RedditAdapter: Real Reddit data via PRAW API
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from contracts.models import Business, SocialPost


class BaseAdapter(ABC):
    """
    Abstract base class for all data source adapters.
    
    All concrete adapters (Google Places, Instagram, Reddit, Simulated)
    MUST inherit from this class and implement all abstract methods.
    
    This ensures a consistent interface for data fetching across the
    entire application, regardless of the underlying data source.
    """
    
    @abstractmethod
    def fetch_businesses(self, category: str, bounds: Dict[str, float]) -> List[Business]:
        """
        Fetch businesses within specified geographic bounds.
        
        This method retrieves business listings that match the given category
        and fall within the specified bounding box coordinates.
        
        Args:
            category (str): Business category to search for.
                           Must be one of: 'Gym', 'Cafe'
                           Example: "Gym"
            
            bounds (dict): Geographic bounding box with keys:
                          - 'lat_north' (float): Northern boundary latitude
                          - 'lat_south' (float): Southern boundary latitude
                          - 'lon_east' (float): Eastern boundary longitude
                          - 'lon_west' (float): Western boundary longitude
                          Example: {
                              'lat_north': 24.8320,
                              'lat_south': 24.8260,
                              'lon_east': 67.0640,
                              'lon_west': 67.0580
                          }
        
        Returns:
            List[Business]: List of Business objects found within bounds.
                           Empty list if no businesses found.
                           Each Business object must conform to contracts.models.Business schema.
        
        Raises:
            ValueError: If category is not supported or bounds are invalid
            ConnectionError: If API/data source is unreachable
            RuntimeError: If data fetching fails for any other reason
        
        Implementation Notes:
            - GooglePlacesAdapter: Uses Google Places API Nearby Search
            - SimulatedAdapter: Returns empty list (businesses come from DB, not adapter)
            - InstagramAdapter (future): Not applicable, returns empty list
            - RedditAdapter (future): Not applicable, returns empty list
        
        Example:
            >>> adapter = GooglePlacesAdapter(api_key="...")
            >>> bounds = {
            ...     'lat_north': 24.8320,
            ...     'lat_south': 24.8260,
            ...     'lon_east': 67.0640,
            ...     'lon_west': 67.0580
            ... }
            >>> businesses = adapter.fetch_businesses("Gym", bounds)
            >>> len(businesses)
            5
            >>> businesses[0].name
            'FitZone Personal Training'
        """
        pass
    
    @abstractmethod
    def fetch_social_posts(
        self, 
        category: str, 
        bounds: Dict[str, float], 
        days: int = 90
    ) -> List[SocialPost]:
        """
        Fetch social media posts within geographic bounds and time window.
        
        This method retrieves social media posts (Instagram, Reddit, etc.)
        that are relevant to the given category, fall within the bounding box,
        and were created within the specified lookback period.
        
        Args:
            category (str): Topic/category to search for in posts.
                           Must be one of: 'Gym', 'Cafe'
                           Example: "Gym"
            
            bounds (dict): Geographic bounding box (same format as fetch_businesses).
                          Posts must be geotagged and fall within these coordinates.
                          Example: {
                              'lat_north': 24.8320,
                              'lat_south': 24.8260,
                              'lon_east': 67.0640,
                              'lon_west': 67.0580
                          }
            
            days (int, optional): Lookback period in days. Defaults to 90.
                                 Only posts created within the last N days are returned.
                                 Example: 90 (last 3 months)
        
        Returns:
            List[SocialPost]: List of SocialPost objects matching criteria.
                             Empty list if no posts found.
                             Each SocialPost must conform to contracts.models.SocialPost schema.
        
        Raises:
            ValueError: If category is not supported, bounds are invalid, or days < 1
            ConnectionError: If API/data source is unreachable
            RuntimeError: If data fetching fails (rate limits, scraping errors, etc.)
        
        Implementation Notes:
            - GooglePlacesAdapter: Returns empty list (not applicable)
            - SimulatedAdapter: Loads from pre-generated JSON files or database
            - InstagramAdapter (future): Scrapes location pages and hashtags
            - RedditAdapter (future): Uses PRAW to search r/Karachi, r/Pakistan
        
        Post Classification:
            Adapters should attempt to classify posts into PostType:
            - 'demand': Explicit requests ("need a gym", "looking for cafe")
            - 'complaint': Complaints about lack of service ("no good gyms here")
            - 'mention': General mentions or discussions
        
        Example:
            >>> adapter = SimulatedSocialAdapter(data_path="data/synthetic/")
            >>> bounds = {
            ...     'lat_north': 24.8320,
            ...     'lat_south': 24.8260,
            ...     'lon_east': 67.0640,
            ...     'lon_west': 67.0580
            ... }
            >>> posts = adapter.fetch_social_posts("Gym", bounds, days=90)
            >>> len(posts)
            48
            >>> posts[0].post_type
            <PostType.DEMAND: 'demand'>
            >>> posts[0].text
            'We need a proper gym in Phase 2, all we have is tiny PT places'
        """
        pass
    
    @abstractmethod
    def get_source_name(self) -> str:
        """
        Return the identifier for this data source.
        
        This identifier is used for:
        1. Logging and debugging (track which adapter fetched which data)
        2. Database storage (Business.source, SocialPost.source columns)
        3. UI display (show users where data came from)
        
        Returns:
            str: Source identifier matching contracts.models.Source enum values.
                Must be one of: 'google_places', 'instagram', 'reddit', 'simulated'
        
        Implementation Examples:
            - GooglePlacesAdapter: Returns "google_places"
            - SimulatedSocialAdapter: Returns "simulated"
            - InstagramAdapter (future): Returns "instagram"
            - RedditAdapter (future): Returns "reddit"
        
        Example:
            >>> adapter = GooglePlacesAdapter(api_key="...")
            >>> adapter.get_source_name()
            'google_places'
            
            >>> sim_adapter = SimulatedSocialAdapter()
            >>> sim_adapter.get_source_name()
            'simulated'
        """
        pass
    
    # ========================================================================
    # Optional Helper Methods (Not Required, But Recommended)
    # ========================================================================
    
    def validate_bounds(self, bounds: Dict[str, float]) -> None:
        """
        Validate that bounds dictionary contains required keys and valid values.
        
        Concrete adapters can call this helper method to ensure bounds
        are properly formatted before making API calls.
        
        Args:
            bounds (dict): Bounding box to validate
        
        Raises:
            ValueError: If bounds are missing keys or contain invalid coordinates
        """
        required_keys = {'lat_north', 'lat_south', 'lon_east', 'lon_west'}
        if not all(k in bounds for k in required_keys):
            raise ValueError(f"Bounds must contain all keys: {required_keys}")
        
        if not (-90 <= bounds['lat_north'] <= 90):
            raise ValueError(f"Invalid lat_north: {bounds['lat_north']}")
        if not (-90 <= bounds['lat_south'] <= 90):
            raise ValueError(f"Invalid lat_south: {bounds['lat_south']}")
        if not (-180 <= bounds['lon_east'] <= 180):
            raise ValueError(f"Invalid lon_east: {bounds['lon_east']}")
        if not (-180 <= bounds['lon_west'] <= 180):
            raise ValueError(f"Invalid lon_west: {bounds['lon_west']}")
        
        if bounds['lat_north'] <= bounds['lat_south']:
            raise ValueError("lat_north must be greater than lat_south")
        if bounds['lon_east'] <= bounds['lon_west']:
            raise ValueError("lon_east must be greater than lon_west")
    
    def validate_category(self, category: str) -> None:
        """
        Validate that category is supported by the MVP.
        
        Args:
            category (str): Category to validate
        
        Raises:
            ValueError: If category is not in supported list
        """
        supported_categories = {'Gym', 'Cafe'}
        if category not in supported_categories:
            raise ValueError(
                f"Unsupported category: '{category}'. "
                f"Must be one of: {supported_categories}"
            )


# ============================================================================
# Usage Example (For Documentation Purposes)
# ============================================================================

"""
Example: Implementing a concrete adapter for Google Places API

```python
import os
import googlemaps
from typing import List, Dict
from datetime import datetime
from contracts.base_adapter import BaseAdapter
from contracts.models import Business, SocialPost, Source, Category

class GooglePlacesAdapter(BaseAdapter):
    '''Adapter for fetching real business data from Google Places API.'''
    
    def __init__(self, api_key: str):
        self.client = googlemaps.Client(key=api_key)
    
    def fetch_businesses(self, category: str, bounds: Dict[str, float]) -> List[Business]:
        self.validate_category(category)
        self.validate_bounds(bounds)
        
        # Calculate center point and radius
        lat_center = (bounds['lat_north'] + bounds['lat_south']) / 2
        lon_center = (bounds['lon_east'] + bounds['lon_west']) / 2
        
        # Map our categories to Google Places types
        type_mapping = {
            'Gym': 'gym',
            'Cafe': 'cafe'
        }
        
        # Call Google Places Nearby Search
        results = self.client.places_nearby(
            location=(lat_center, lon_center),
            radius=500,  # ~0.5 km
            type=type_mapping[category]
        )
        
        # Convert to Business objects
        businesses = []
        for place in results.get('results', []):
            business = Business(
                business_id=place['place_id'],
                name=place['name'],
                lat=place['geometry']['location']['lat'],
                lon=place['geometry']['location']['lng'],
                category=Category(category),
                rating=place.get('rating'),
                review_count=place.get('user_ratings_total', 0),
                source=Source.GOOGLE_PLACES,
                grid_id=None,  # Will be assigned later
                fetched_at=datetime.utcnow()
            )
            businesses.append(business)
        
        return businesses
    
    def fetch_social_posts(self, category: str, bounds: Dict[str, float], days: int = 90) -> List[SocialPost]:
        # Google Places API doesn't provide social posts
        return []
    
    def get_source_name(self) -> str:
        return "google_places"
```

Example: Using the adapter in Phase 1

```python
from contracts.base_adapter import BaseAdapter
from adapters.google_places_adapter import GooglePlacesAdapter

# Initialize adapter
adapter: BaseAdapter = GooglePlacesAdapter(api_key=os.getenv("GOOGLE_PLACES_API_KEY"))

# Fetch businesses for a grid cell
bounds = {
    'lat_north': 24.8320,
    'lat_south': 24.8260,
    'lon_east': 67.0640,
    'lon_west': 67.0580
}

businesses = adapter.fetch_businesses(category="Gym", bounds=bounds)

# Store in database
for business in businesses:
    # Assign to grid cell
    business.grid_id = assign_to_grid(business.lat, business.lon)
    # Save to database
    db.session.add(business)

db.session.commit()
```
"""
