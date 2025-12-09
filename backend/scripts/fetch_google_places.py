"""
Google Places Business Fetcher - CLI Script

This script fetches real business data from Google Places API and populates
the businesses table in the database.

Usage:
    python scripts/fetch_google_places.py --category Gym --neighborhood "DHA Phase 2"
    python scripts/fetch_google_places.py --category Cafe --neighborhood "DHA Phase 2" --force
    python scripts/fetch_google_places.py --category Gym --neighborhood "DHA Phase 2" --dry-run

Features:
    - Fetches businesses for all grids in a neighborhood
    - Uses smart caching (24-hour default)
    - Assigns grid_id to each business
    - Inserts into database with duplicate detection
    - Progress bars and detailed statistics
    - Dry-run mode for testing

Author: Phase 1 Developer
Phase: 1 - Data Integration
"""

import sys
import os
import argparse
import time
from pathlib import Path
from typing import List, Dict, Tuple
from datetime import datetime
from decimal import Decimal

# Add project root to path
project_root = Path(__file__).parent.parent.parent
backend_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(backend_root))

# Try to import tqdm, fallback to simple progress if not available
try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False
    print("Note: Install tqdm for better progress bars (pip install tqdm)")

from src.adapters import GooglePlacesAdapter, create_adapter
from src.database.connection import get_session
from src.database.models import GridCellModel, BusinessModel
from src.services.geospatial_service import assign_grid_id
from src.utils.logger import get_logger


# ============================================================================
# Configuration
# ============================================================================

VALID_CATEGORIES = ["Gym", "Cafe"]

logger = get_logger(__name__)


# ============================================================================
# Helper Functions
# ============================================================================

def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.
    
    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Fetch business data from Google Places API and populate the database.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Fetch gyms for DHA Phase 2
  python scripts/fetch_google_places.py --category Gym --neighborhood "DHA Phase 2"
  
  # Force refresh (bypass cache)
  python scripts/fetch_google_places.py --category Gym --neighborhood "DHA Phase 2" --force
  
  # Dry-run mode (don't insert into database)
  python scripts/fetch_google_places.py --category Gym --neighborhood "DHA Phase 2" --dry-run
  
  # Use custom API key
  python scripts/fetch_google_places.py --category Cafe --neighborhood "DHA Phase 2" --api-key YOUR_KEY
        """
    )
    
    parser.add_argument(
        "--category",
        type=str,
        required=True,
        choices=VALID_CATEGORIES,
        help=f"Business category to fetch. Choices: {', '.join(VALID_CATEGORIES)}"
    )
    
    parser.add_argument(
        "--neighborhood",
        type=str,
        required=True,
        help="Neighborhood name (e.g., 'DHA Phase 2')"
    )
    
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force refresh: bypass cache and fetch fresh data from API"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry-run mode: fetch from API but don't insert into database"
    )
    
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="Google Places API key (overrides GOOGLE_PLACES_API_KEY env var)"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging (DEBUG level)"
    )
    
    return parser.parse_args()


def get_available_neighborhoods() -> List[str]:
    """
    Get list of available neighborhoods from database.
    
    Returns:
        List[str]: List of unique neighborhood names
    """
    try:
        with get_session() as session:
            neighborhoods = session.query(GridCellModel.neighborhood).distinct().all()
            return sorted([n[0] for n in neighborhoods])
    except Exception as e:
        logger.error(f"Error querying neighborhoods: {e}")
        return []


def validate_neighborhood(neighborhood: str) -> Tuple[bool, str]:
    """
    Validate that the neighborhood exists in the database.
    
    Args:
        neighborhood (str): Neighborhood name to validate
        
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    available = get_available_neighborhoods()
    
    if not available:
        return False, "Could not retrieve neighborhoods from database. Check database connection."
    
    if neighborhood not in available:
        return False, (
            f"Neighborhood '{neighborhood}' not found.\n"
            f"Available neighborhoods: {', '.join(available)}"
        )
    
    return True, ""


def get_grid_cells(neighborhood: str) -> List[GridCellModel]:
    """
    Get all grid cells for a neighborhood.
    
    Args:
        neighborhood (str): Neighborhood name
        
    Returns:
        List[GridCellModel]: List of grid cell ORM models
    """
    with get_session() as session:
        grids = session.query(GridCellModel).filter_by(
            neighborhood=neighborhood
        ).order_by(GridCellModel.grid_id).all()
        
        # Detach from session (so we can use outside context manager)
        session.expunge_all()
        return grids


def save_business_to_db(business, session) -> Tuple[str, bool]:
    """
    Save a business to the database.
    
    Args:
        business: Pydantic Business model
        session: SQLAlchemy session
        
    Returns:
        Tuple[str, bool]: (action, success) where action is "inserted", "updated", or "skipped"
    """
    try:
        # Check if business already exists
        existing = session.query(BusinessModel).filter_by(
            business_id=business.business_id
        ).first()
        
        if existing:
            # Update existing business
            existing.name = business.name
            existing.lat = Decimal(str(business.lat))
            existing.lon = Decimal(str(business.lon))
            existing.category = business.category.value if hasattr(business.category, 'value') else business.category
            existing.rating = Decimal(str(business.rating)) if business.rating is not None else None
            existing.review_count = business.review_count
            existing.grid_id = business.grid_id
            existing.fetched_at = business.fetched_at
            return "updated", True
        else:
            # Insert new business
            db_business = BusinessModel.from_pydantic(business)
            session.add(db_business)
            return "inserted", True
            
    except Exception as e:
        logger.error(f"Error saving business {business.business_id}: {e}")
        return "error", False


# ============================================================================
# Main Fetch Logic
# ============================================================================

def fetch_and_populate(
    category: str,
    neighborhood: str,
    force_refresh: bool = False,
    dry_run: bool = False,
    api_key: str = None
) -> Dict:
    """
    Main function to fetch businesses and populate database.
    
    Args:
        category (str): Business category
        neighborhood (str): Neighborhood name
        force_refresh (bool): Bypass cache
        dry_run (bool): Don't insert into database
        api_key (str): Optional API key override
        
    Returns:
        Dict: Statistics about the fetch operation
    """
    start_time = time.time()
    
    # Initialize statistics
    stats = {
        "total_grids": 0,
        "total_businesses": 0,
        "businesses_per_grid": {},
        "inserted": 0,
        "updated": 0,
        "skipped": 0,
        "errors": 0,
        "grids_with_zero": [],
        "api_calls_made": 0,
        "cache_hits": 0,
        "duration": 0.0
    }
    
    # Get grid cells
    logger.info(f"Loading grid cells for {neighborhood}...")
    grids = get_grid_cells(neighborhood)
    stats["total_grids"] = len(grids)
    
    if not grids:
        raise ValueError(f"No grid cells found for neighborhood '{neighborhood}'")
    
    print(f"\n{'=' * 80}")
    print(f"Fetching {category} businesses for {neighborhood}")
    print(f"{'=' * 80}")
    print(f"Grid cells to process: {len(grids)}")
    print(f"Force refresh: {force_refresh}")
    print(f"Dry-run mode: {dry_run}")
    print()
    
    # Create adapter
    try:
        if api_key:
            adapter = GooglePlacesAdapter(api_key=api_key)
        else:
            adapter = create_adapter()
    except Exception as e:
        raise ValueError(f"Failed to create Google Places adapter: {e}")
    
    # Process each grid
    if HAS_TQDM:
        grid_iterator = tqdm(grids, desc="Processing grids", unit="grid")
    else:
        grid_iterator = grids
        print("Processing grids:")
    
    for i, grid in enumerate(grid_iterator, 1):
        if not HAS_TQDM:
            print(f"  Grid {i}/{len(grids)}: {grid.grid_id}", end=" ... ")
        
        # Prepare bounds
        bounds = {
            'lat_north': float(grid.lat_north),
            'lat_south': float(grid.lat_south),
            'lon_east': float(grid.lon_east),
            'lon_west': float(grid.lon_west)
        }
        
        try:
            # Fetch businesses from API
            businesses = adapter.fetch_businesses(
                category=category,
                bounds=bounds,
                force_refresh=force_refresh
            )
            
            # Track if this was a cache hit or API call
            # (This is a simplification - in reality, adapter logs this)
            if not force_refresh and businesses:
                stats["cache_hits"] += 1
            else:
                stats["api_calls_made"] += 1
            
            stats["businesses_per_grid"][grid.grid_id] = len(businesses)
            stats["total_businesses"] += len(businesses)
            
            if len(businesses) == 0:
                stats["grids_with_zero"].append(grid.grid_id)
                if not HAS_TQDM:
                    print(f"0 businesses")
                continue
            
            # Save to database (if not dry-run)
            if not dry_run:
                with get_session() as session:
                    for business in businesses:
                        action, success = save_business_to_db(business, session)
                        
                        if success:
                            if action == "inserted":
                                stats["inserted"] += 1
                            elif action == "updated":
                                stats["updated"] += 1
                            else:
                                stats["skipped"] += 1
                        else:
                            stats["errors"] += 1
                    
                    session.commit()
            
            if not HAS_TQDM:
                print(f"{len(businesses)} businesses")
                
        except Exception as e:
            logger.error(f"Error processing grid {grid.grid_id}: {e}")
            stats["errors"] += 1
            if not HAS_TQDM:
                print(f"ERROR: {str(e)[:50]}")
    
    # Calculate duration
    stats["duration"] = time.time() - start_time
    
    return stats


# ============================================================================
# Display Functions
# ============================================================================

def display_statistics(stats: Dict, dry_run: bool = False):
    """
    Display fetch statistics in a formatted table.
    
    Args:
        stats (Dict): Statistics dictionary
        dry_run (bool): Whether this was a dry-run
    """
    print(f"\n{'=' * 80}")
    print("FETCH COMPLETE - SUMMARY STATISTICS")
    print(f"{'=' * 80}\n")
    
    # Overview
    print("Overview:")
    print(f"  Total grids processed:    {stats['total_grids']}")
    print(f"  Total businesses found:   {stats['total_businesses']}")
    print(f"  Average per grid:         {stats['total_businesses'] / stats['total_grids']:.1f}")
    print(f"  Duration:                 {stats['duration']:.2f}s")
    print()
    
    # API Usage
    print("API Usage:")
    print(f"  API calls made:           {stats['api_calls_made']}")
    print(f"  Cache hits:               {stats['cache_hits']}")
    cache_rate = (stats['cache_hits'] / max(stats['total_grids'], 1)) * 100
    print(f"  Cache hit rate:           {cache_rate:.1f}%")
    print()
    
    # Database operations (skip if dry-run)
    if not dry_run:
        print("Database Operations:")
        print(f"  Businesses inserted:      {stats['inserted']}")
        print(f"  Businesses updated:       {stats['updated']}")
        print(f"  Errors:                   {stats['errors']}")
        print()
    else:
        print("Database Operations:")
        print("  DRY-RUN MODE - No data inserted")
        print()
    
    # Warnings
    if stats['grids_with_zero']:
        print(f"⚠ Warning: {len(stats['grids_with_zero'])} grid(s) with 0 businesses:")
        for grid_id in stats['grids_with_zero'][:5]:  # Show first 5
            print(f"  - {grid_id}")
        if len(stats['grids_with_zero']) > 5:
            print(f"  ... and {len(stats['grids_with_zero']) - 5} more")
        print()
    
    # Top grids
    if stats['businesses_per_grid']:
        print("Top 5 grids by business count:")
        sorted_grids = sorted(
            stats['businesses_per_grid'].items(),
            key=lambda x: x[1],
            reverse=True
        )
        for grid_id, count in sorted_grids[:5]:
            print(f"  {grid_id:30s} {count:3d} businesses")
        print()
    
    print(f"{'=' * 80}\n")


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Main entry point for the script."""
    # Parse arguments
    args = parse_arguments()
    
    # Set logging level
    if args.verbose:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
    
    print(f"\n{'=' * 80}")
    print("GOOGLE PLACES BUSINESS FETCHER")
    print(f"{'=' * 80}\n")
    
    # Validate neighborhood
    print(f"Validating neighborhood: {args.neighborhood}")
    is_valid, error_msg = validate_neighborhood(args.neighborhood)
    
    if not is_valid:
        print(f"✗ Error: {error_msg}\n")
        sys.exit(1)
    
    print(f"✓ Neighborhood '{args.neighborhood}' found in database\n")
    
    # Check API key
    api_key = args.api_key or os.getenv("GOOGLE_PLACES_API_KEY")
    if not api_key:
        print("✗ Error: Google Places API key not found.")
        print("  Set GOOGLE_PLACES_API_KEY environment variable or use --api-key option.\n")
        sys.exit(1)
    
    print(f"✓ API key configured (length: {len(api_key)} chars)\n")
    
    # Confirmation prompt (if not dry-run)
    if not args.dry_run and not args.force:
        response = input(f"Ready to fetch {args.category} businesses. Continue? [y/N]: ")
        if response.lower() not in ['y', 'yes']:
            print("Aborted by user.\n")
            sys.exit(0)
        print()
    
    # Execute fetch
    try:
        stats = fetch_and_populate(
            category=args.category,
            neighborhood=args.neighborhood,
            force_refresh=args.force,
            dry_run=args.dry_run,
            api_key=api_key
        )
        
        # Display statistics
        display_statistics(stats, dry_run=args.dry_run)
        
        # Success message
        if args.dry_run:
            print("✓ Dry-run completed successfully!")
            print("  Re-run without --dry-run to insert data into database.\n")
        else:
            print("✓ Data successfully fetched and saved to database!")
            print(f"  {stats['inserted']} businesses inserted, {stats['updated']} updated.\n")
        
        # Verification command
        if not args.dry_run:
            print("Verify data in database:")
            print(f"  psql startsmart_dev -c \"SELECT grid_id, COUNT(*) FROM businesses WHERE category='{args.category}' GROUP BY grid_id;\"")
            print()
        
    except KeyboardInterrupt:
        print("\n\n✗ Interrupted by user. Partial data may have been saved.\n")
        sys.exit(1)
    
    except Exception as e:
        print(f"\n✗ Error: {str(e)}\n")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
