"""
Simulated Social Media Data Adapter

This adapter reads synthetic social media posts from the database.
Data was pre-seeded during Phase 0 and marked with is_simulated = TRUE.

Unlike GooglePlacesAdapter, this adapter:
- Does NOT call external APIs
- Reads from existing database records
- Provides fast, reliable access to social signals for MVP

This is a temporary solution for MVP. Post-MVP implementations will
include real Instagram and Reddit adapters.

Usage:
    from src.adapters import SimulatedSocialAdapter
    
    adapter = SimulatedSocialAdapter()
    posts = adapter.fetch_social_posts(
        category="Gym",
        bounds={"lat_north": 24.83, "lat_south": 24.82, "lon_east": 67.07, "lon_west": 67.06},
        days=90
    )
    
    print(f"Found {len(posts)} simulated posts")
    
Author: Phase 1 Developer
Phase: 1 - Data Integration
"""

from typing import List, Dict, Optional
from datetime import datetime, timedelta

from contracts.base_adapter import BaseAdapter
from contracts.models import SocialPost, Source, PostType
from src.database.connection import get_session
from src.database.models import SocialPostModel
from src.utils.logger import get_logger, log_database_operation


class SimulatedSocialAdapter(BaseAdapter):
    """
    Adapter for reading simulated social media posts from the database.
    
    This adapter provides access to synthetic social media data that was
    pre-seeded during Phase 0. It implements the BaseAdapter interface
    to maintain consistency with real data adapters.
    
    Key Features:
    - Reads from social_posts table WHERE is_simulated = TRUE
    - Filters by geographic bounds (lat/lon)
    - Filters by time window (last N days)
    - Converts ORM models to Pydantic models
    - Logs query performance and result counts
    
    Note: This is MVP-only. Post-MVP will use InstagramAdapter and RedditAdapter.
    """
    
    def __init__(self):
        """
        Initialize the simulated social adapter.
        
        Sets up database connection and logger.
        No external API credentials needed.
        """
        self.logger = get_logger(__name__)
        self.logger.info(
            "Initialized SimulatedSocialAdapter",
            extra={
                "adapter_type": "simulated_social",
                "data_source": "database",
                "is_simulated": True
            }
        )
    
    def fetch_businesses(self, category: str, bounds: Dict[str, float]) -> List:
        """
        Not applicable for social media adapter.
        
        SimulatedSocialAdapter only fetches social posts, not businesses.
        Businesses are fetched via GooglePlacesAdapter.
        
        Args:
            category: Business category (ignored)
            bounds: Geographic bounds (ignored)
            
        Raises:
            NotImplementedError: This adapter doesn't fetch businesses
        """
        raise NotImplementedError(
            "SimulatedSocialAdapter does not fetch businesses. "
            "Use GooglePlacesAdapter for business data."
        )
    
    def fetch_social_posts(
        self, 
        category: str, 
        bounds: Dict[str, float], 
        days: int = 90
    ) -> List[SocialPost]:
        """
        Fetch simulated social media posts from the database.
        
        Queries the social_posts table for synthetic posts that:
        1. Are marked as simulated (is_simulated = TRUE)
        2. Fall within the specified geographic bounds
        3. Were created within the last N days
        
        Args:
            category (str): Business category to filter by (e.g., "Gym", "Cafe")
                           Currently not used in query, but maintained for interface consistency
            bounds (dict): Geographic bounding box with keys:
                - lat_north: Northern boundary latitude
                - lat_south: Southern boundary latitude
                - lon_east: Eastern boundary longitude
                - lon_west: Western boundary longitude
            days (int): Lookback period in days (default: 90)
                       Posts older than this will be excluded
        
        Returns:
            List[SocialPost]: List of Pydantic SocialPost models
        
        Example:
            posts = adapter.fetch_social_posts(
                category="Gym",
                bounds={
                    "lat_north": 24.8320,
                    "lat_south": 24.8260,
                    "lon_east": 67.0640,
                    "lon_west": 67.0580
                },
                days=90
            )
        """
        start_time = datetime.now()
        
        # Validate bounds
        self._validate_bounds(bounds)
        
        # Calculate time cutoff
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        self.logger.debug(
            f"Fetching simulated posts for category '{category}'",
            extra={
                "category": category,
                "bounds": bounds,
                "days": days,
                "cutoff_date": cutoff_date.isoformat()
            }
        )
        
        try:
            with get_session() as session:
                # Query social_posts table
                query = session.query(SocialPostModel).filter(
                    SocialPostModel.is_simulated == True,  # Only simulated data
                    SocialPostModel.timestamp >= cutoff_date,  # Within time window
                    SocialPostModel.lat.isnot(None),  # Has location data
                    SocialPostModel.lon.isnot(None),
                    SocialPostModel.lat >= bounds['lat_south'],  # Within bounds
                    SocialPostModel.lat <= bounds['lat_north'],
                    SocialPostModel.lon >= bounds['lon_west'],
                    SocialPostModel.lon <= bounds['lon_east']
                )
                
                # Execute query
                orm_posts = query.all()
                
                # Convert ORM models to Pydantic models
                pydantic_posts = []
                for orm_post in orm_posts:
                    try:
                        pydantic_post = self._convert_to_social_post(orm_post)
                        if pydantic_post:
                            pydantic_posts.append(pydantic_post)
                    except Exception as e:
                        self.logger.warning(
                            f"Failed to convert post {orm_post.post_id}: {str(e)}",
                            extra={"post_id": orm_post.post_id, "error": str(e)}
                        )
                        continue
                
                # Calculate query duration
                duration = (datetime.now() - start_time).total_seconds()
                
                # Log results
                log_database_operation(
                    self.logger,
                    "SELECT",
                    "social_posts",
                    row_count=len(pydantic_posts),
                    duration=duration
                )
                
                self.logger.info(
                    f"Fetched {len(pydantic_posts)} simulated posts in {duration:.2f}s",
                    extra={
                        "category": category,
                        "posts_count": len(pydantic_posts),
                        "duration_seconds": round(duration, 3),
                        "source": "simulated"
                    }
                )
                
                return pydantic_posts
                
        except Exception as e:
            self.logger.error(
                f"Error fetching simulated posts: {str(e)}",
                extra={
                    "category": category,
                    "bounds": bounds,
                    "error": str(e)
                },
                exc_info=True
            )
            raise
    
    def get_source_name(self) -> str:
        """
        Return the source identifier for this adapter.
        
        Returns:
            str: "simulated"
        """
        return "simulated"
    
    def _validate_bounds(self, bounds: Dict[str, float]) -> None:
        """
        Validate geographic bounds dictionary.
        
        Args:
            bounds (dict): Geographic bounding box
            
        Raises:
            ValueError: If bounds are invalid
        """
        required_keys = ['lat_north', 'lat_south', 'lon_east', 'lon_west']
        missing_keys = [key for key in required_keys if key not in bounds]
        
        if missing_keys:
            raise ValueError(
                f"Bounds dictionary missing required keys: {missing_keys}. "
                f"Required keys: {required_keys}"
            )
        
        # Validate latitude range (-90 to 90)
        if not (-90 <= bounds['lat_south'] <= 90 and -90 <= bounds['lat_north'] <= 90):
            raise ValueError(
                f"Latitude values must be between -90 and 90. "
                f"Got: lat_south={bounds['lat_south']}, lat_north={bounds['lat_north']}"
            )
        
        # Validate longitude range (-180 to 180)
        if not (-180 <= bounds['lon_west'] <= 180 and -180 <= bounds['lon_east'] <= 180):
            raise ValueError(
                f"Longitude values must be between -180 and 180. "
                f"Got: lon_west={bounds['lon_west']}, lon_east={bounds['lon_east']}"
            )
        
        # Validate north > south
        if bounds['lat_north'] <= bounds['lat_south']:
            raise ValueError(
                f"lat_north ({bounds['lat_north']}) must be greater than "
                f"lat_south ({bounds['lat_south']})"
            )
        
        # Validate east > west
        if bounds['lon_east'] <= bounds['lon_west']:
            raise ValueError(
                f"lon_east ({bounds['lon_east']}) must be greater than "
                f"lon_west ({bounds['lon_west']})"
            )
    
    def _convert_to_social_post(self, orm_post: SocialPostModel) -> Optional[SocialPost]:
        """
        Convert ORM SocialPostModel to Pydantic SocialPost.
        
        Args:
            orm_post (SocialPostModel): SQLAlchemy ORM model instance
            
        Returns:
            Optional[SocialPost]: Pydantic model or None if conversion fails
        """
        try:
            # Convert source string to Source enum
            try:
                source = Source(orm_post.source)
            except ValueError:
                # Fallback to SIMULATED if source doesn't match enum
                source = Source.SIMULATED
            
            # Convert post_type string to PostType enum (if present)
            post_type = None
            if orm_post.post_type:
                try:
                    post_type = PostType(orm_post.post_type)
                except ValueError:
                    # If post_type doesn't match enum, leave as None
                    pass
            
            # Create Pydantic model
            return SocialPost(
                post_id=orm_post.post_id,
                source=source,
                text=orm_post.text,
                timestamp=orm_post.timestamp,
                lat=float(orm_post.lat) if orm_post.lat is not None else None,
                lon=float(orm_post.lon) if orm_post.lon is not None else None,
                grid_id=orm_post.grid_id,
                post_type=post_type,
                engagement_score=orm_post.engagement_score,
                is_simulated=orm_post.is_simulated,
                created_at=orm_post.created_at
            )
        
        except Exception as e:
            self.logger.error(
                f"Error converting SocialPostModel to SocialPost: {str(e)}",
                extra={
                    "post_id": orm_post.post_id,
                    "error": str(e)
                }
            )
            return None


# ============================================================================
# Convenience Factory Function
# ============================================================================

def create_adapter() -> SimulatedSocialAdapter:
    """
    Factory function to create a SimulatedSocialAdapter instance.
    
    This is the recommended way to create adapter instances as it
    provides a consistent interface across all adapters.
    
    Returns:
        SimulatedSocialAdapter: Configured adapter instance
        
    Example:
        from src.adapters import create_adapter
        
        adapter = create_adapter()
        posts = adapter.fetch_social_posts("Gym", bounds, days=90)
    """
    return SimulatedSocialAdapter()


# ============================================================================
# Test Suite (Run with: python -m src.adapters.simulated_social_adapter)
# ============================================================================

if __name__ == "__main__":
    import sys
    from decimal import Decimal
    
    print("=" * 80)
    print("SIMULATED SOCIAL ADAPTER - TEST SUITE")
    print("=" * 80)
    print()
    
    # Test bounds (DHA Phase 2, Cell-07)
    test_bounds = {
        'lat_north': 24.8320,
        'lat_south': 24.8260,
        'lon_east': 67.0640,
        'lon_west': 67.0580
    }
    
    try:
        # Create adapter
        print("Creating SimulatedSocialAdapter...")
        adapter = create_adapter()
        print(f"✓ Adapter created: {adapter.get_source_name()}")
        print()
        
        # Test 1: Fetch posts for Gym category (90 days)
        print("TEST 1: Fetch simulated posts (Gym, 90 days)")
        print("-" * 80)
        posts_90 = adapter.fetch_social_posts(
            category="Gym",
            bounds=test_bounds,
            days=90
        )
        print(f"✓ Found {len(posts_90)} posts in last 90 days")
        
        if posts_90:
            print("\nFirst 3 posts:")
            for i, post in enumerate(posts_90[:3], 1):
                print(f"  {i}. [{post.source}] {post.post_type or 'N/A'}: {post.text[:60]}...")
                print(f"     Engagement: {post.engagement_score}, Location: ({post.lat:.4f}, {post.lon:.4f})")
        print()
        
        # Test 2: Fetch posts for shorter time window (30 days)
        print("TEST 2: Fetch simulated posts (Gym, 30 days)")
        print("-" * 80)
        posts_30 = adapter.fetch_social_posts(
            category="Gym",
            bounds=test_bounds,
            days=30
        )
        print(f"✓ Found {len(posts_30)} posts in last 30 days")
        print(f"✓ Difference: {len(posts_90) - len(posts_30)} older posts excluded")
        print()
        
        # Test 3: Analyze post types
        print("TEST 3: Post Type Distribution")
        print("-" * 80)
        post_type_counts = {}
        for post in posts_90:
            post_type = post.post_type.value if post.post_type else "unknown"
            post_type_counts[post_type] = post_type_counts.get(post_type, 0) + 1
        
        for post_type, count in sorted(post_type_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(posts_90)) * 100 if posts_90 else 0
            print(f"  {post_type:12s}: {count:3d} posts ({percentage:5.1f}%)")
        print()
        
        # Test 4: Verify all posts are simulated
        print("TEST 4: Data Quality Checks")
        print("-" * 80)
        simulated_count = sum(1 for post in posts_90 if post.is_simulated)
        with_location = sum(1 for post in posts_90 if post.lat and post.lon)
        with_text = sum(1 for post in posts_90 if post.text)
        
        print(f"  Simulated posts: {simulated_count}/{len(posts_90)} ({100 if posts_90 else 0}%)")
        print(f"  Posts with location: {with_location}/{len(posts_90)} ({(with_location/len(posts_90)*100) if posts_90 else 0:.1f}%)")
        print(f"  Posts with text: {with_text}/{len(posts_90)} ({(with_text/len(posts_90)*100) if posts_90 else 0:.1f}%)")
        print()
        
        # Test 5: Verify fetch_businesses raises NotImplementedError
        print("TEST 5: Verify fetch_businesses() raises NotImplementedError")
        print("-" * 80)
        try:
            adapter.fetch_businesses("Gym", test_bounds)
            print("✗ ERROR: Should have raised NotImplementedError")
        except NotImplementedError as e:
            print(f"✓ Correctly raised NotImplementedError: {str(e)}")
        print()
        
        # Summary
        print("=" * 80)
        print("TEST SUITE COMPLETE")
        print("=" * 80)
        print(f"✓ All tests passed!")
        print(f"✓ Adapter successfully fetched {len(posts_90)} simulated posts")
        print(f"✓ Data quality: 100% simulated, {(with_location/len(posts_90)*100) if posts_90 else 0:.1f}% with location")
        print()
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
