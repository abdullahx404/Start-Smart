"""
Google Places Adapter - Quick Reference Guide

This guide provides quick code patterns for using the GooglePlacesAdapter.

NEW in v1.1.0:
- Smart caching (24-hour expiry)
- Request throttling (10 req/s limit)
- Enhanced metadata in raw data storage
- API key validation on initialization
- force_refresh parameter to bypass cache
"""

# ============================================================================
# BASIC USAGE
# ============================================================================

# 1. Import the adapter
from src.adapters import GooglePlacesAdapter, create_adapter

# 2. Create adapter instance (reads GOOGLE_PLACES_API_KEY from environment)
adapter = create_adapter()

# Or pass API key directly
adapter = GooglePlacesAdapter(api_key="YOUR_GOOGLE_PLACES_API_KEY")

# 3. Fetch businesses for a grid cell (uses cache if available)
businesses = adapter.fetch_businesses(
    category="Gym",
    bounds={
        "lat_north": 24.8320,
        "lat_south": 24.8260,
        "lon_east": 67.0640,
        "lon_west": 67.0580
    }
)

# 4. Process results
print(f"Found {len(businesses)} businesses")
for biz in businesses:
    print(f"{biz.name}: rating={biz.rating}, grid_id={biz.grid_id}")


# ============================================================================
# CACHING (NEW in v1.1.0)
# ============================================================================

from src.adapters import create_adapter

adapter = create_adapter()

# First call - fetches from API, saves to cache
businesses = adapter.fetch_businesses(
    category="Gym",
    bounds={"lat_north": 24.83, "lat_south": 24.82, "lon_east": 67.07, "lon_west": 67.06}
)
# Result: API call made, data cached for 24 hours

# Second call (within 24 hours) - loads from cache
businesses = adapter.fetch_businesses(
    category="Gym",
    bounds={"lat_north": 24.83, "lat_south": 24.82, "lon_east": 67.07, "lon_west": 67.06}
)
# Result: Instant response from cache, no API call

# Force refresh - bypass cache
businesses = adapter.fetch_businesses(
    category="Gym",
    bounds={"lat_north": 24.83, "lat_south": 24.82, "lon_east": 67.07, "lon_west": 67.06},
    force_refresh=True  # Always fetch fresh data
)
# Result: API call made, cache updated

# Cache benefits:
# - Faster responses (no network latency)
# - Reduced API quota usage
# - Lower costs
# - Offline capability (if cached data exists)


# ============================================================================
# FETCHING FOR MULTIPLE GRIDS
# ============================================================================

from src.database import get_session, GridCellModel
from src.adapters import create_adapter

adapter = create_adapter()

# Get all grids in a neighborhood
with get_session() as session:
    grids = session.query(GridCellModel).filter_by(
        neighborhood="DHA Phase 2"
    ).all()
    
    all_businesses = []
    for grid in grids:
        bounds = {
            "lat_north": float(grid.lat_north),
            "lat_south": float(grid.lat_south),
            "lon_east": float(grid.lon_east),
            "lon_west": float(grid.lon_west)
        }
        
        print(f"Fetching businesses for {grid.grid_id}...")
        businesses = adapter.fetch_businesses(category="Gym", bounds=bounds)
        all_businesses.extend(businesses)
        print(f"  Found {len(businesses)} businesses")
    
    print(f"\nTotal: {len(all_businesses)} businesses across {len(grids)} grids")


# ============================================================================
# SAVING BUSINESSES TO DATABASE
# ============================================================================

from src.database import get_session, BusinessModel
from src.adapters import create_adapter

adapter = create_adapter()

# Fetch businesses
businesses = adapter.fetch_businesses(
    category="Gym",
    bounds={"lat_north": 24.83, "lat_south": 24.82, "lon_east": 67.07, "lon_west": 67.06}
)

# Save to database
with get_session() as session:
    for biz in businesses:
        # Convert Pydantic model to ORM model
        db_business = BusinessModel.from_pydantic(biz)
        
        # Check if business already exists (avoid duplicates)
        existing = session.query(BusinessModel).filter_by(
            business_id=db_business.business_id
        ).first()
        
        if existing:
            print(f"Skipping duplicate: {biz.name}")
        else:
            session.add(db_business)
            print(f"Added: {biz.name}")
    
    session.commit()
    print(f"\nSaved {len(businesses)} businesses to database")


# ============================================================================
# ERROR HANDLING
# ============================================================================

from src.adapters import create_adapter
from googlemaps.exceptions import ApiError, Timeout

adapter = create_adapter()

try:
    businesses = adapter.fetch_businesses(
        category="Gym",
        bounds={"lat_north": 24.83, "lat_south": 24.82, "lon_east": 67.07, "lon_west": 67.06}
    )
    print(f"Success: {len(businesses)} businesses")
    
except ValueError as e:
    # Invalid category or bounds
    print(f"Validation error: {e}")
    
except ApiError as e:
    # Google API error (invalid key, quota exceeded, etc.)
    print(f"Google API error: {e}")
    
except Timeout as e:
    # Request timeout
    print(f"Request timeout: {e}")
    
except Exception as e:
    # Other errors
    print(f"Unexpected error: {e}")


# ============================================================================
# CATEGORY HANDLING
# ============================================================================

from src.adapters import create_adapter

adapter = create_adapter()

# Supported categories
SUPPORTED_CATEGORIES = ["Gym", "Cafe"]

for category in SUPPORTED_CATEGORIES:
    print(f"\nFetching {category} businesses...")
    
    businesses = adapter.fetch_businesses(
        category=category,
        bounds={"lat_north": 24.83, "lat_south": 24.82, "lon_east": 67.07, "lon_west": 67.06}
    )
    
    print(f"  Found {len(businesses)} {category.lower()}s")


# ============================================================================
# FILTERING BUSINESSES WITH RATINGS
# ============================================================================

from src.adapters import create_adapter

adapter = create_adapter()

businesses = adapter.fetch_businesses(
    category="Gym",
    bounds={"lat_north": 24.83, "lat_south": 24.82, "lon_east": 67.07, "lon_west": 67.06}
)

# Filter businesses with ratings ≥ 4.0
high_rated = [biz for biz in businesses if biz.rating and biz.rating >= 4.0]
print(f"High-rated businesses: {len(high_rated)}/{len(businesses)}")

# Filter businesses with ≥ 50 reviews
popular = [biz for biz in businesses if biz.review_count >= 50]
print(f"Popular businesses: {len(popular)}/{len(businesses)}")

# Businesses with no ratings (new businesses)
unrated = [biz for biz in businesses if biz.rating is None]
print(f"Unrated businesses: {len(unrated)}/{len(businesses)}")


# ============================================================================
# CHECKING GRID ASSIGNMENT
# ============================================================================

from src.adapters import create_adapter

adapter = create_adapter()

businesses = adapter.fetch_businesses(
    category="Gym",
    bounds={"lat_north": 24.83, "lat_south": 24.82, "lon_east": 67.07, "lon_west": 67.06}
)

# Count businesses per grid
from collections import Counter
grid_counts = Counter(biz.grid_id for biz in businesses)

print("\nBusinesses per grid:")
for grid_id, count in grid_counts.most_common():
    if grid_id:
        print(f"  {grid_id}: {count} businesses")
    else:
        print(f"  No grid assigned: {count} businesses")


# ============================================================================
# ENVIRONMENT CONFIGURATION
# ============================================================================

# 1. Create .env file in project root
"""
# Google Places API Configuration
GOOGLE_PLACES_API_KEY=AIzaSyB...your_key_here

# Other settings
DATABASE_URL=postgresql://postgres:12113@localhost:5432/startsmart_dev
ENVIRONMENT=development
LOG_LEVEL=INFO
"""

# 2. Load environment variables
import os
from dotenv import load_dotenv

load_dotenv()

# 3. Create adapter (automatically reads from environment)
from src.adapters import create_adapter

adapter = create_adapter()  # Uses GOOGLE_PLACES_API_KEY from .env


# ============================================================================
# LOGGING AND DEBUGGING
# ============================================================================

import logging
from src.utils.logger import get_logger
from src.adapters import create_adapter

# Enable DEBUG logging to see detailed API calls
logger = get_logger(__name__)
logger.setLevel(logging.DEBUG)

adapter = create_adapter()

# Fetch with detailed logging
businesses = adapter.fetch_businesses(
    category="Gym",
    bounds={"lat_north": 24.83, "lat_south": 24.82, "lon_east": 67.07, "lon_west": 67.06}
)

# Check logs for:
# - API call duration
# - Pagination details
# - Grid assignment results
# - Any warnings or errors


# ============================================================================
# RAW DATA AUDIT TRAIL
# ============================================================================

# GooglePlacesAdapter automatically saves raw API responses to:
# data/raw/google_places/{category}_{lat}_{lon}_{timestamp}.json

# Example: data/raw/google_places/Gym_24.8290_67.0610_20251106_143000.json

# Contents:
"""
{
  "metadata": {
    "timestamp": "2025-11-06T14:30:00Z",
    "category": "Gym",
    "bounds": {...},
    "center": {"lat": 24.8290, "lon": 67.0610},
    "total_results": 5
  },
  "places": [
    {
      "place_id": "ChIJ...",
      "name": "FitZone",
      "geometry": {...},
      "rating": 4.2,
      ...
    }
  ]
}
"""


# ============================================================================
# TESTING THE ADAPTER
# ============================================================================

# Run the built-in test
"""
$ cd backend
$ python -m src.adapters.google_places_adapter

Creating GooglePlacesAdapter...

Fetching businesses for DHA Phase 2 Cell-07 (Gym category)...

Results: 5 businesses found
--------------------------------------------------------------------------------
1. FitZone Personal Training
   Location: (24.8285, 67.0605)
   Rating: 3.8 (42 reviews)
   Grid ID: DHA-Phase2-Cell-07

...

✓ Test completed successfully
✓ Raw data saved to data/raw/google_places
"""
