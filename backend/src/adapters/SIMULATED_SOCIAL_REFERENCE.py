"""
SIMULATED SOCIAL ADAPTER - DEVELOPER REFERENCE
================================================

This guide provides examples and patterns for using the SimulatedSocialAdapter.

OVERVIEW
--------
SimulatedSocialAdapter reads synthetic social media posts from the database.
Unlike GooglePlacesAdapter, it does NOT call external APIs - data is already
pre-seeded in the social_posts table during Phase 0.

KEY FEATURES
------------
✓ Reads from database (no external API calls)
✓ Filters by geographic bounds (lat/lon)
✓ Filters by time window (last N days)
✓ Converts ORM models to Pydantic models
✓ Comprehensive logging
✓ Fast query performance (<100ms typical)

BASIC USAGE
-----------
"""

# Example 1: Basic fetch for a single grid
from src.adapters import SimulatedSocialAdapter, create_social_adapter

# Create adapter (recommended factory function)
adapter = create_social_adapter()

# Define bounds for a grid cell
bounds = {
    'lat_north': 24.8320,
    'lat_south': 24.8260,
    'lon_east': 67.0640,
    'lon_west': 67.0580
}

# Fetch posts for the last 90 days
posts = adapter.fetch_social_posts(
    category="Gym",
    bounds=bounds,
    days=90
)

print(f"Found {len(posts)} posts")
for post in posts[:5]:  # Show first 5
    print(f"- [{post.source}] {post.post_type}: {post.text[:60]}...")


"""
FETCHING FOR MULTIPLE GRIDS
----------------------------
Typical use case: Fetch posts for all grids in a neighborhood.
"""

# Example 2: Fetch for multiple grids
from src.database import get_session
from src.database.models import GridCellModel
from src.adapters import create_social_adapter

adapter = create_social_adapter()

with get_session() as session:
    # Get all grids in a neighborhood
    grids = session.query(GridCellModel).filter_by(
        neighborhood="DHA Phase 2"
    ).all()
    
    # Fetch posts for each grid
    for grid in grids:
        bounds = {
            'lat_north': float(grid.lat_north),
            'lat_south': float(grid.lat_south),
            'lon_east': float(grid.lon_east),
            'lon_west': float(grid.lon_west)
        }
        
        posts = adapter.fetch_social_posts("Gym", bounds, days=90)
        print(f"{grid.grid_id}: {len(posts)} posts")


"""
TIME WINDOW FILTERING
----------------------
The 'days' parameter controls how far back to look for posts.
"""

# Example 3: Different time windows
adapter = create_social_adapter()

# Last 30 days (recent activity)
recent_posts = adapter.fetch_social_posts("Gym", bounds, days=30)

# Last 90 days (default, recommended for MVP)
standard_posts = adapter.fetch_social_posts("Gym", bounds, days=90)

# Last 180 days (longer trend)
historical_posts = adapter.fetch_social_posts("Gym", bounds, days=180)

print(f"30 days: {len(recent_posts)} posts")
print(f"90 days: {len(standard_posts)} posts")
print(f"180 days: {len(historical_posts)} posts")


"""
POST TYPE FILTERING
-------------------
After fetching, you can filter by post_type for specific analysis.
"""

# Example 4: Filter by post type
posts = adapter.fetch_social_posts("Gym", bounds, days=90)

# Count by type
demand_posts = [p for p in posts if p.post_type and p.post_type.value == "demand"]
complaint_posts = [p for p in posts if p.post_type and p.post_type.value == "complaint"]
mention_posts = [p for p in posts if p.post_type and p.post_type.value == "mention"]

print(f"Demand: {len(demand_posts)}")
print(f"Complaints: {len(complaint_posts)}")
print(f"Mentions: {len(mention_posts)}")

# Calculate demand signals for GOS scoring
demand_signals = len(demand_posts) + len(complaint_posts)
print(f"Total demand signals: {demand_signals}")


"""
ENGAGEMENT ANALYSIS
-------------------
Posts have engagement_score (likes, upvotes, etc.).
"""

# Example 5: Top posts by engagement
posts = adapter.fetch_social_posts("Gym", bounds, days=90)

# Sort by engagement
sorted_posts = sorted(posts, key=lambda p: p.engagement_score, reverse=True)

print("Top 3 posts by engagement:")
for i, post in enumerate(sorted_posts[:3], 1):
    print(f"{i}. [{post.engagement_score} engagement] {post.text[:60]}...")


"""
ERROR HANDLING
--------------
Adapter raises exceptions for invalid inputs.
"""

# Example 6: Error handling
from src.adapters import create_social_adapter

adapter = create_social_adapter()

try:
    # Invalid bounds (missing keys)
    invalid_bounds = {'lat_north': 24.83, 'lat_south': 24.82}
    posts = adapter.fetch_social_posts("Gym", invalid_bounds, days=90)
except ValueError as e:
    print(f"Bounds validation error: {e}")

try:
    # Invalid bounds (north <= south)
    invalid_bounds = {
        'lat_north': 24.82,
        'lat_south': 24.83,  # South > North (invalid)
        'lon_east': 67.07,
        'lon_west': 67.06
    }
    posts = adapter.fetch_social_posts("Gym", invalid_bounds, days=90)
except ValueError as e:
    print(f"Bounds logic error: {e}")


"""
INTEGRATION WITH DATABASE
--------------------------
Typical pattern: Query grids from DB, fetch posts for each grid.
"""

# Example 7: Full integration
from src.database import get_session
from src.database.models import GridCellModel
from src.adapters import create_social_adapter

adapter = create_social_adapter()

with get_session() as session:
    # Query all grids
    grids = session.query(GridCellModel).all()
    
    print(f"Processing {len(grids)} grids...")
    
    total_posts = 0
    grid_stats = []
    
    for grid in grids:
        bounds = {
            'lat_north': float(grid.lat_north),
            'lat_south': float(grid.lat_south),
            'lon_east': float(grid.lon_east),
            'lon_west': float(grid.lon_west)
        }
        
        posts = adapter.fetch_social_posts("Gym", bounds, days=90)
        total_posts += len(posts)
        
        grid_stats.append({
            'grid_id': grid.grid_id,
            'posts': len(posts),
            'demand_signals': sum(1 for p in posts if p.post_type and p.post_type.value in ['demand', 'complaint'])
        })
    
    # Summary
    print(f"\nTotal posts across all grids: {total_posts}")
    print(f"Average posts per grid: {total_posts / len(grids):.1f}")
    
    # Top 5 grids by post volume
    top_grids = sorted(grid_stats, key=lambda x: x['posts'], reverse=True)[:5]
    print("\nTop 5 grids by post volume:")
    for i, grid in enumerate(top_grids, 1):
        print(f"{i}. {grid['grid_id']}: {grid['posts']} posts ({grid['demand_signals']} demand signals)")


"""
COMPARING WITH GOOGLE PLACES DATA
----------------------------------
Common pattern: Fetch both businesses and social posts for a grid.
"""

# Example 8: Combined analysis
from src.adapters import create_adapter, create_social_adapter

business_adapter = create_adapter()  # GooglePlacesAdapter
social_adapter = create_social_adapter()  # SimulatedSocialAdapter

bounds = {
    'lat_north': 24.8320,
    'lat_south': 24.8260,
    'lon_east': 67.0640,
    'lon_west': 67.0580
}

# Fetch data from both sources
businesses = business_adapter.fetch_businesses("Gym", bounds)
posts = social_adapter.fetch_social_posts("Gym", bounds, days=90)

# Calculate basic GOS components
supply = len(businesses)  # Competition
demand = sum(1 for p in posts if p.post_type and p.post_type.value in ['demand', 'complaint'])

print(f"Supply (businesses): {supply}")
print(f"Demand (signals): {demand}")
print(f"Demand/Supply ratio: {demand/supply if supply > 0 else 'N/A'}")


"""
PERFORMANCE CONSIDERATIONS
---------------------------
"""

# Example 9: Performance monitoring
import time
from src.adapters import create_social_adapter

adapter = create_social_adapter()

# Measure query time
start = time.time()
posts = adapter.fetch_social_posts("Gym", bounds, days=90)
duration = time.time() - start

print(f"Fetched {len(posts)} posts in {duration:.3f}s")
print(f"Avg: {(duration/len(posts)*1000):.2f}ms per post" if posts else "No posts")

# Typical performance:
# - Small grid (0-50 posts): <50ms
# - Medium grid (50-200 posts): <100ms
# - Large grid (200+ posts): <200ms


"""
LIMITATIONS & MVP NOTES
-----------------------
1. Data is SIMULATED (synthetic, not real social media)
   - All posts have is_simulated = TRUE
   - Good for MVP demo, not for production

2. No external API calls
   - Fast and reliable
   - No rate limits
   - No API costs

3. Data is STATIC (pre-seeded in Phase 0)
   - No new posts after seeding
   - Update requires re-running seed script

4. Post-MVP Migration
   - Replace with InstagramAdapter (real scraping)
   - Replace with RedditAdapter (PRAW API)
   - Same BaseAdapter interface = easy swap

TESTING
-------
Run built-in test suite:

    cd backend
    python -m src.adapters.simulated_social_adapter

Expected output:
    - Test 1: Fetch posts (90 days)
    - Test 2: Fetch posts (30 days)
    - Test 3: Post type distribution
    - Test 4: Data quality checks
    - Test 5: Verify fetch_businesses() raises error

TROUBLESHOOTING
---------------
Problem: "No posts found"
Solution: 
  - Check database has simulated posts (is_simulated = TRUE)
  - Verify bounds overlap with seeded post locations
  - Check time window (posts older than cutoff are excluded)

Problem: "DatabaseError: relation 'social_posts' does not exist"
Solution:
  - Run database migrations: alembic upgrade head
  - Or create tables: python -c "from src.database.connection import create_all_tables; create_all_tables()"

Problem: "ValueError: Bounds validation failed"
Solution:
  - Ensure all 4 keys present: lat_north, lat_south, lon_east, lon_west
  - Verify north > south and east > west
  - Check latitude (-90 to 90) and longitude (-180 to 180) ranges

NEXT STEPS (PHASE 2)
--------------------
Phase 2 developer will use this adapter to:
1. Query social posts for each grid
2. Count demand signals (demand + complaint posts)
3. Compute demand metrics for GOS formula
4. Store results in grid_metrics table

Example Phase 2 usage:
    from src.adapters import create_social_adapter
    from src.database import get_session
    from src.database.models import GridCellModel, GridMetricsModel
    
    social_adapter = create_social_adapter()
    
    with get_session() as session:
        grids = session.query(GridCellModel).all()
        
        for grid in grids:
            # Fetch posts
            posts = social_adapter.fetch_social_posts("Gym", grid_bounds, days=90)
            
            # Compute metrics
            instagram_volume = sum(1 for p in posts if p.source.value == 'simulated' and p.post_type.value == 'mention')
            reddit_mentions = sum(1 for p in posts if p.source.value == 'simulated' and p.post_type.value in ['demand', 'complaint'])
            
            # Create grid metrics record
            metrics = GridMetricsModel(
                grid_id=grid.grid_id,
                category="Gym",
                instagram_volume=instagram_volume,
                reddit_mentions=reddit_mentions,
                # ... other metrics
            )
            session.add(metrics)
        
        session.commit()
"""
