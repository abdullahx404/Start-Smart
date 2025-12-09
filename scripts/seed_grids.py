#!/usr/bin/env python3
"""
Grid Cells Database Seeder for StartSmart MVP
Phase 0: Initialize grid_cells table from neighborhoods.json

This script reads neighborhood configurations and generates grid cells
with calculated lat/lon bounds, then inserts them into the database.

Usage:
    python scripts/seed_grids.py
    python scripts/seed_grids.py --config config/neighborhoods.json
    python scripts/seed_grids.py --dry-run
"""

import json
import math
import os
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

try:
    import psycopg2
    from psycopg2.extras import execute_batch
    from dotenv import load_dotenv
except ImportError:
    print("❌ Error: Required packages not installed")
    print("   Run: pip install psycopg2-binary python-dotenv")
    sys.exit(1)


# ============================================================================
# Grid Generation Functions
# ============================================================================

def calculate_grid_layout(total_grids: int) -> tuple:
    """Calculate optimal grid layout (rows x cols)."""
    cols = math.ceil(math.sqrt(total_grids))
    rows = math.ceil(total_grids / cols)
    return rows, cols


def generate_grid_cells(
    neighborhood_id: str,
    neighborhood_name: str,
    bounds: Dict[str, float],
    grid_count: int,
    grid_size_km2: float = 0.5
) -> List[Dict[str, Any]]:
    """
    Generate grid cells for a neighborhood.
    
    Args:
        neighborhood_id: Unique identifier (e.g., "DHA-Phase2")
        neighborhood_name: Human-readable name
        bounds: Dict with lat_north, lat_south, lon_east, lon_west
        grid_count: Number of grids to generate
        grid_size_km2: Target area per grid in km²
    
    Returns:
        List of grid cell dictionaries ready for database insertion
    """
    rows, cols = calculate_grid_layout(grid_count)
    
    # Calculate step sizes
    lat_range = bounds['lat_north'] - bounds['lat_south']
    lon_range = bounds['lon_east'] - bounds['lon_west']
    
    lat_step = lat_range / rows
    lon_step = lon_range / cols
    
    grids = []
    grid_index = 0
    
    for row in range(rows):
        for col in range(cols):
            if grid_index >= grid_count:
                break
            
            # Calculate grid bounds
            lat_south = bounds['lat_south'] + (row * lat_step)
            lat_north = bounds['lat_south'] + ((row + 1) * lat_step)
            lon_west = bounds['lon_west'] + (col * lon_step)
            lon_east = bounds['lon_west'] + ((col + 1) * lon_step)
            
            # Calculate center point
            lat_center = (lat_north + lat_south) / 2
            lon_center = (lon_east + lon_west) / 2
            
            # Generate grid ID (zero-padded for sorting)
            grid_id = f"{neighborhood_id}-Cell-{str(grid_index + 1).zfill(2)}"
            
            grid = {
                'grid_id': grid_id,
                'neighborhood': neighborhood_name,
                'lat_center': round(lat_center, 7),
                'lon_center': round(lon_center, 7),
                'lat_north': round(lat_north, 7),
                'lat_south': round(lat_south, 7),
                'lon_east': round(lon_east, 7),
                'lon_west': round(lon_west, 7),
                'area_km2': grid_size_km2
            }
            
            grids.append(grid)
            grid_index += 1
    
    return grids


# ============================================================================
# Database Operations
# ============================================================================

def get_database_connection(database_url: str):
    """
    Create database connection from DATABASE_URL.
    
    Args:
        database_url: PostgreSQL connection string
    
    Returns:
        psycopg2 connection object
    """
    try:
        conn = psycopg2.connect(database_url)
        return conn
    except psycopg2.Error as e:
        print(f"❌ Database connection failed: {e}")
        raise


def insert_grid_cells(conn, grids: List[Dict[str, Any]], dry_run: bool = False) -> int:
    """
    Insert grid cells into database.
    
    Args:
        conn: Database connection
        grids: List of grid cell dictionaries
        dry_run: If True, preview SQL without executing
    
    Returns:
        Number of rows inserted
    """
    if not grids:
        print("⚠️  No grids to insert")
        return 0
    
    insert_sql = """
        INSERT INTO grid_cells (
            grid_id, neighborhood, lat_center, lon_center,
            lat_north, lat_south, lon_east, lon_west, area_km2
        ) VALUES (
            %(grid_id)s, %(neighborhood)s, %(lat_center)s, %(lon_center)s,
            %(lat_north)s, %(lat_south)s, %(lon_east)s, %(lon_west)s, %(area_km2)s
        )
        ON CONFLICT (grid_id) DO UPDATE SET
            neighborhood = EXCLUDED.neighborhood,
            lat_center = EXCLUDED.lat_center,
            lon_center = EXCLUDED.lon_center,
            lat_north = EXCLUDED.lat_north,
            lat_south = EXCLUDED.lat_south,
            lon_east = EXCLUDED.lon_east,
            lon_west = EXCLUDED.lon_west,
            area_km2 = EXCLUDED.area_km2
    """
    
    if dry_run:
        print("\n🔍 DRY RUN - Preview SQL (first 3 grids):")
        print("-" * 70)
        print(insert_sql)
        print("\nSample data:")
        for i, grid in enumerate(grids[:3]):
            print(f"\n  Grid {i+1}: {grid['grid_id']}")
            print(f"    Center: ({grid['lat_center']}, {grid['lon_center']})")
            print(f"    Bounds: N:{grid['lat_north']}, S:{grid['lat_south']}, "
                  f"E:{grid['lon_east']}, W:{grid['lon_west']}")
        print(f"\n  ... and {len(grids) - 3} more grids")
        print("-" * 70)
        return len(grids)
    
    try:
        cursor = conn.cursor()
        
        # Use execute_batch for better performance
        execute_batch(cursor, insert_sql, grids, page_size=100)
        
        rows_inserted = cursor.rowcount
        cursor.close()
        
        return rows_inserted
        
    except psycopg2.Error as e:
        print(f"❌ Database insert failed: {e}")
        raise


def verify_insertion(conn, expected_count: int) -> Dict[str, Any]:
    """
    Verify that grids were inserted correctly.
    
    Returns:
        Dictionary with verification statistics
    """
    try:
        cursor = conn.cursor()
        
        # Count total grids
        cursor.execute("SELECT COUNT(*) FROM grid_cells")
        total_count = cursor.fetchone()[0]
        
        # Get grid details
        cursor.execute("""
            SELECT neighborhood, COUNT(*) as grid_count
            FROM grid_cells
            GROUP BY neighborhood
            ORDER BY neighborhood
        """)
        neighborhoods = cursor.fetchall()
        
        cursor.close()
        
        return {
            'total_grids': total_count,
            'expected_grids': expected_count,
            'match': total_count == expected_count,
            'neighborhoods': neighborhoods
        }
        
    except psycopg2.Error as e:
        print(f"⚠️  Verification query failed: {e}")
        return {'total_grids': 0, 'expected_grids': expected_count, 'match': False}


# ============================================================================
# Main Execution
# ============================================================================

def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description='Seed grid_cells table from neighborhoods.json',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default='config/neighborhoods.json',
        help='Path to neighborhoods configuration file (default: config/neighborhoods.json)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview SQL without executing (no database changes)'
    )
    
    parser.add_argument(
        '--database-url',
        type=str,
        default=None,
        help='PostgreSQL connection string (default: from DATABASE_URL env var)'
    )
    
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Get database URL (not required for dry-run)
    database_url = args.database_url or os.getenv('DATABASE_URL')
    if not database_url and not args.dry_run:
        print("❌ Error: DATABASE_URL not found")
        print("   Set DATABASE_URL environment variable or use --database-url")
        print("   Example: DATABASE_URL=postgresql://user:pass@localhost:5432/startsmart_dev")
        return 1
    
    print("=" * 70)
    print("StartSmart Grid Cells Seeder - Phase 0")
    print("=" * 70)
    print()
    
    if args.dry_run:
        print("🔍 DRY RUN MODE - No database changes will be made")
        print()
    
    # Load configuration
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"❌ Error: Config file not found: {config_path}")
        return 1
    
    print(f"📄 Loading configuration from: {config_path}")
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in config file: {e}")
        return 1
    
    neighborhoods = config.get('neighborhoods', [])
    if not neighborhoods:
        print("❌ Error: No neighborhoods found in config")
        return 1
    
    print(f"   Found {len(neighborhoods)} neighborhood(s)")
    print()
    
    # Generate grid cells for all neighborhoods
    all_grids = []
    
    for neighborhood in neighborhoods:
        name = neighborhood.get('name', 'Unknown')
        neighborhood_id = neighborhood.get('id', 'unknown')
        bounds = neighborhood.get('bounds', {})
        grid_count = neighborhood.get('grid_count', 0)
        grid_size_km2 = neighborhood.get('grid_size_km', 0.5)
        
        print(f"🗺️  Processing: {name} ({neighborhood_id})")
        print(f"   Target grids: {grid_count}")
        
        grids = generate_grid_cells(
            neighborhood_id=neighborhood_id,
            neighborhood_name=name,
            bounds=bounds,
            grid_count=grid_count,
            grid_size_km2=grid_size_km2
        )
        
        print(f"   Generated: {len(grids)} grid cells")
        
        # Preview first grid
        if grids:
            first = grids[0]
            print(f"   Sample: {first['grid_id']} at ({first['lat_center']}, {first['lon_center']})")
        
        all_grids.extend(grids)
        print()
    
    print(f"📊 Total grids to insert: {len(all_grids)}")
    print()
    
    # Connect to database (unless dry-run)
    conn = None
    if not args.dry_run:
        print(f"🔌 Connecting to database...")
        try:
            conn = get_database_connection(database_url)
            print("   ✓ Connected successfully")
            print()
        except Exception as e:
            print(f"   ✗ Connection failed: {e}")
            return 1
    
    # Insert grids
    try:
        print(f"💾 Inserting grid cells...")
        
        if not args.dry_run and conn:
            # Start transaction
            conn.autocommit = False
            
        rows_affected = insert_grid_cells(conn, all_grids, dry_run=args.dry_run)
        
        if not args.dry_run and conn:
            # Commit transaction
            conn.commit()
            print(f"   ✓ Inserted {rows_affected} rows")
            print()
            
            # Verify insertion
            print("🔍 Verifying insertion...")
            verification = verify_insertion(conn, len(all_grids))
            
            print(f"   Database total: {verification['total_grids']} grids")
            print(f"   Expected: {verification['expected_grids']} grids")
            
            if verification['match']:
                print("   ✓ Verification PASSED")
            else:
                print("   ⚠️  Verification FAILED - count mismatch")
            
            print()
            print("   Grids by neighborhood:")
            for neighborhood, count in verification['neighborhoods']:
                print(f"     - {neighborhood}: {count} grids")
            
        else:
            print(f"   Would insert {rows_affected} rows (dry-run)")
        
        print()
        print("=" * 70)
        print("✅ Grid seeding complete!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Error during insertion: {e}")
        if conn and not args.dry_run:
            conn.rollback()
            print("   Transaction rolled back")
        return 1
        
    finally:
        if conn:
            conn.close()
            print("\n🔌 Database connection closed")
    
    return 0


if __name__ == "__main__":
    exit(main())
