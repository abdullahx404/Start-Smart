#!/usr/bin/env python
"""
Extract All Businesses Script

CLI tool for comprehensive business extraction using multiple Google Places API strategies.

Usage:
    python scripts/extract_all_businesses.py [OPTIONS]

Options:
    --sector SECTOR_ID    Extract for specific sector only
    --category CATEGORY   Extract specific category only (Gym, Cafe)
    --no-text-search      Disable Text Search API (use only Nearby Search)
    --preview             Show what would be extracted without making API calls
    --force               Overwrite existing business data

Examples:
    # Extract all businesses for all Clifton sectors
    python scripts/extract_all_businesses.py
    
    # Extract gyms only from Block 2
    python scripts/extract_all_businesses.py --sector Clifton-Block2 --category Gym
    
    # Preview extraction scope
    python scripts/extract_all_businesses.py --preview
"""

import argparse
import json
import os
import sys
import math
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Add parent and backend directories to path for imports
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "backend"))


# ============================================================================
# Configuration
# ============================================================================

CONFIG_PATH = Path(__file__).parent.parent / "config" / "neighborhoods.json"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "extracted_businesses"
ENV_PATH = Path(__file__).parent.parent / ".env"


# ============================================================================
# Main Functions
# ============================================================================

def load_config():
    """Load neighborhoods configuration."""
    if not CONFIG_PATH.exists():
        print(f"Error: Config file not found: {CONFIG_PATH}")
        sys.exit(1)
    
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)


def get_api_key():
    """Load Google Places API key from environment."""
    load_dotenv(ENV_PATH)
    api_key = os.getenv("GOOGLE_PLACES_API_KEY")
    
    if not api_key:
        print("Error: GOOGLE_PLACES_API_KEY not found in environment")
        print(f"       Please add it to: {ENV_PATH}")
        sys.exit(1)
    
    return api_key


def get_sectors_to_process(config: dict, sector_filter: str = None):
    """Get list of sectors to process based on filter."""
    neighborhoods = config.get("neighborhoods", [])
    sectors = []
    
    for neighborhood in neighborhoods:
        for sector in neighborhood.get("sectors", []):
            sector_id = sector.get("id")
            bounds = sector.get("bounds")
            
            if not sector_id or not bounds:
                continue
            
            if sector_filter and sector_id != sector_filter:
                continue
            
            sectors.append({
                "id": sector_id,
                "name": sector.get("name", sector_id),
                "bounds": bounds,
                "neighborhood": neighborhood.get("id", "Unknown")
            })
    
    return sectors


def get_categories_to_process(config: dict, category_filter: str = None):
    """Get list of categories to process based on filter."""
    categories = config.get("categories", ["Gym", "Cafe"])
    
    if category_filter:
        if category_filter not in categories:
            print(f"Warning: Category '{category_filter}' not in config. Using anyway.")
        return [category_filter]
    
    return categories


def extract_businesses(
    sectors: list, 
    categories: list,
    api_key: str,
    include_text_search: bool = True
):
    """Extract businesses for all sectors and categories."""
    from src.adapters.comprehensive_places_adapter import ComprehensivePlacesAdapter
    
    adapter = ComprehensivePlacesAdapter(api_key)
    all_businesses = {}
    
    print(f"\n{'='*60}")
    print(f"COMPREHENSIVE BUSINESS EXTRACTION")
    print(f"{'='*60}")
    print(f"Sectors: {len(sectors)}")
    print(f"Categories: {categories}")
    print(f"Text Search: {'Enabled' if include_text_search else 'Disabled'}")
    print(f"{'='*60}\n")
    
    total_start_time = datetime.now()
    
    for category in categories:
        print(f"\n📂 Category: {category}")
        print(f"{'─'*40}")
        
        category_businesses = []
        
        for sector in sectors:
            print(f"\n  📍 {sector['name']} ({sector['id']})")
            
            try:
                businesses = adapter.fetch_all_businesses(
                    bounds=sector["bounds"],
                    category=category,
                    include_text_search=include_text_search,
                    save_raw=True
                )
                
                # Add sector info to each business
                for b in businesses:
                    b.sector_id = sector["id"]
                    b.neighborhood = sector["neighborhood"]
                
                print(f"     ✅ Found {len(businesses)} unique businesses")
                
                # Show sample
                if businesses:
                    print(f"     📊 Sample:")
                    for b in businesses[:3]:
                        rating_str = f"{b.rating}★" if b.rating else "N/A"
                        print(f"        • {b.name[:30]} ({rating_str}, {b.total_ratings} reviews)")
                
                category_businesses.extend(businesses)
                
            except Exception as e:
                print(f"     ❌ Error: {e}")
                continue
        
        # Deduplicate across sectors
        unique_businesses = {}
        for b in category_businesses:
            if b.place_id not in unique_businesses:
                unique_businesses[b.place_id] = b
        
        all_businesses[category] = list(unique_businesses.values())
        print(f"\n  📈 Total unique {category}: {len(all_businesses[category])}")
    
    elapsed = (datetime.now() - total_start_time).total_seconds()
    print(f"\n⏱️  Total extraction time: {elapsed:.1f} seconds")
    
    return all_businesses


def preview_extraction(sectors: list, categories: list):
    """Preview what would be extracted without making API calls."""
    print(f"\n{'='*60}")
    print(f"EXTRACTION PREVIEW (No API calls)")
    print(f"{'='*60}")
    
    print(f"\nSectors to process ({len(sectors)}):")
    for sector in sectors:
        bounds = sector["bounds"]
        lat_span = bounds["lat_north"] - bounds["lat_south"]
        lon_span = bounds["lon_east"] - bounds["lon_west"]
        approx_area = lat_span * 111 * lon_span * 100  # Very rough km² estimate
        print(f"  • {sector['id']}: ~{approx_area:.2f} km²")
    
    print(f"\nCategories to extract:")
    for category in categories:
        print(f"  • {category}")
    
    print(f"\nEstimated API calls:")
    # Estimate based on sweep points
    total_sweep_points = 0
    for sector in sectors:
        bounds = sector["bounds"]
        lat_span = (bounds["lat_north"] - bounds["lat_south"]) * 111000  # meters
        lon_span = (bounds["lon_east"] - bounds["lon_west"]) * 100000  # meters
        
        # With 300m radius and 0.7 overlap
        step = 300 * 2 * 0.7
        rows = max(1, int(lat_span / step) + 1)
        cols = max(1, int(lon_span / step) + 1)
        total_sweep_points += rows * cols
    
    nearby_calls = total_sweep_points * len(categories)
    text_calls = 10 * len(sectors) * len(categories)  # ~10 keywords per category
    
    print(f"  • Nearby Search: ~{nearby_calls} calls")
    print(f"  • Text Search: ~{text_calls} calls")
    print(f"  • Total: ~{nearby_calls + text_calls} calls")
    
    print(f"\nEstimated cost (at $17/1000 Nearby, $32/1000 Text):")
    nearby_cost = (nearby_calls / 1000) * 17
    text_cost = (text_calls / 1000) * 32
    print(f"  • Nearby: ${nearby_cost:.2f}")
    print(f"  • Text: ${text_cost:.2f}")
    print(f"  • Total: ${nearby_cost + text_cost:.2f}")
    
    print(f"\n{'='*60}")


def save_to_file(all_businesses: dict):
    """Save extracted businesses to JSON files."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    for category, businesses in all_businesses.items():
        filename = f"{category.lower()}_businesses_{timestamp}.json"
        filepath = OUTPUT_DIR / filename
        
        data = {
            "category": category,
            "extracted_at": datetime.utcnow().isoformat(),
            "total_businesses": len(businesses),
            "businesses": [b.to_dict() for b in businesses]
        }
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Saved {len(businesses)} {category} to: {filepath}")
    
    return OUTPUT_DIR


def save_to_database(all_businesses: dict, force: bool = False):
    """Save extracted businesses to PostgreSQL database."""
    try:
        from src.database.connection import get_session
        from src.database.models import BusinessModel
        from contracts.models import Category, Source
        
        session = get_session()
        
        # Check for existing businesses
        existing_count = session.query(BusinessModel).count()
        
        if existing_count > 0 and not force:
            print(f"\n⚠️  Database already has {existing_count} businesses.")
            print("   Use --force to add to existing data.")
            return False
        
        # Insert new businesses
        total_inserted = 0
        
        for category_name, businesses in all_businesses.items():
            print(f"\n📥 Inserting {len(businesses)} {category_name} businesses...")
            
            for b in businesses:
                try:
                    # Check if already exists
                    existing = session.query(BusinessModel).filter_by(
                        business_id=b.place_id
                    ).first()
                    
                    if existing:
                        continue
                    
                    model = BusinessModel(
                        business_id=b.place_id,
                        name=b.name,
                        category=Category[category_name.upper()].value,
                        latitude=b.lat,
                        longitude=b.lon,
                        address=b.address,
                        rating=b.rating,
                        total_ratings=b.total_ratings,
                        price_level=b.price_level,
                        source=Source.GOOGLE_PLACES.value,
                        grid_id=None  # Will be assigned later
                    )
                    session.add(model)
                    total_inserted += 1
                    
                except Exception as e:
                    print(f"   ⚠️  Skipped {b.name}: {e}")
                    continue
            
            session.commit()
        
        print(f"\n✅ Inserted {total_inserted} new businesses to database.")
        return True
        
    except ImportError as e:
        print(f"\n⚠️  Database modules not available: {e}")
        print("   Businesses saved to file only.")
        return False
    except Exception as e:
        print(f"\n❌ Database error: {e}")
        return False


def print_summary(all_businesses: dict):
    """Print extraction summary."""
    if not all_businesses:
        print("\n⚠️  No businesses extracted.")
        return
    
    print(f"\n{'='*60}")
    print("EXTRACTION SUMMARY")
    print(f"{'='*60}")
    
    total = 0
    for category, businesses in all_businesses.items():
        total += len(businesses)
        
        print(f"\n{category}:")
        print(f"  • Total businesses: {len(businesses)}")
        
        if businesses:
            # Calculate stats
            rated = [b for b in businesses if b.rating is not None]
            if rated:
                avg_rating = sum(b.rating for b in rated) / len(rated)
                total_reviews = sum(b.total_ratings for b in businesses)
                print(f"  • Average rating: {avg_rating:.2f}★")
                print(f"  • Total reviews: {total_reviews:,}")
            
            # Count by sector
            sectors = {}
            for b in businesses:
                sector = getattr(b, 'sector_id', 'Unknown')
                sectors[sector] = sectors.get(sector, 0) + 1
            
            print(f"  • By sector:")
            for sector, count in sorted(sectors.items()):
                print(f"      {sector}: {count}")
    
    print(f"\n{'─'*40}")
    print(f"TOTAL: {total} unique businesses extracted")
    print(f"{'='*60}\n")


# ============================================================================
# CLI Entry Point
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Extract all businesses from Google Places for Clifton sectors",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--sector",
        type=str,
        help="Extract for specific sector only (e.g., Clifton-Block2)"
    )
    parser.add_argument(
        "--category",
        type=str,
        help="Extract specific category only (Gym, Cafe)"
    )
    parser.add_argument(
        "--no-text-search",
        action="store_true",
        help="Disable Text Search API (use only Nearby Search)"
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Preview extraction scope without making API calls"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force add to existing business data"
    )
    parser.add_argument(
        "--no-db",
        action="store_true",
        help="Skip database insert, only save to file"
    )
    
    args = parser.parse_args()
    
    # Load config
    config = load_config()
    
    # Get sectors and categories to process
    sectors = get_sectors_to_process(config, args.sector)
    categories = get_categories_to_process(config, args.category)
    
    if not sectors:
        if args.sector:
            print(f"Error: Sector '{args.sector}' not found in config")
        else:
            print("Error: No sectors found in config")
        sys.exit(1)
    
    # Preview mode
    if args.preview:
        preview_extraction(sectors, categories)
        return
    
    # Get API key
    api_key = get_api_key()
    
    # Extract businesses
    all_businesses = extract_businesses(
        sectors=sectors,
        categories=categories,
        api_key=api_key,
        include_text_search=not args.no_text_search
    )
    
    # Print summary
    print_summary(all_businesses)
    
    # Save to file
    save_to_file(all_businesses)
    
    # Save to database
    if not args.no_db:
        save_to_database(all_businesses, args.force)
    
    print("\n✅ Business extraction complete!")


if __name__ == "__main__":
    main()
