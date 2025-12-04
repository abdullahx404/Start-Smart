#!/usr/bin/env python
"""
Generate Micro Grids Script

CLI tool for generating high-resolution micro-grids (100-150m cells) for Clifton sectors.

Usage:
    python scripts/generate_micro_grids.py [OPTIONS]

Options:
    --sector SECTOR_ID    Generate grids for specific sector only
    --cell-size METERS    Cell size in meters (default: 100)
    --preview             Preview without saving to database
    --force               Overwrite existing grids

Examples:
    # Generate all Clifton sectors with 100m grids
    python scripts/generate_micro_grids.py
    
    # Generate only Block 2 with 150m grids
    python scripts/generate_micro_grids.py --sector Clifton-Block2 --cell-size 150
    
    # Preview what would be generated
    python scripts/generate_micro_grids.py --preview
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

# Add parent and backend directories to path for imports
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "backend"))

try:
    from src.services.micro_grid_builder import MicroGridBuilder, MicroGrid
    from src.utils.logger import get_logger
except ImportError:
    # Fallback: create minimal implementations if modules not available
    print("Warning: Using fallback implementations (database features disabled)")
    
    import math
    from dataclasses import dataclass, asdict
    
    @dataclass
    class MicroGrid:
        grid_id: str
        sector_id: str
        neighborhood: str
        row_index: int
        col_index: int
        lat_center: float
        lon_center: float
        lat_north: float
        lat_south: float
        lon_east: float
        lon_west: float
        cell_size_m: int
        area_m2: float
        created_at: str
        
        def to_dict(self):
            return asdict(self)
    
    class MicroGridBuilder:
        def __init__(self, cell_size_meters=100):
            self.cell_size_meters = cell_size_meters
        
        def generate_grids_for_sector(self, sector_id, bounds, neighborhood=None):
            if neighborhood is None:
                neighborhood = sector_id.split("-")[0]
            
            lat_step = self.cell_size_meters / 111111
            center_lat = (bounds["lat_north"] + bounds["lat_south"]) / 2
            lon_step = self.cell_size_meters / (111320 * math.cos(math.radians(center_lat)))
            
            lat_span = bounds["lat_north"] - bounds["lat_south"]
            lon_span = bounds["lon_east"] - bounds["lon_west"]
            
            num_rows = max(1, math.ceil(lat_span / lat_step))
            num_cols = max(1, math.ceil(lon_span / lon_step))
            
            grids = []
            timestamp = datetime.utcnow().isoformat()
            
            for row in range(num_rows):
                for col in range(num_cols):
                    lat_south_cell = bounds["lat_south"] + row * lat_step
                    lat_north_cell = lat_south_cell + lat_step
                    lon_west_cell = bounds["lon_west"] + col * lon_step
                    lon_east_cell = lon_west_cell + lon_step
                    
                    lat_center = (lat_north_cell + lat_south_cell) / 2
                    lon_center = (lon_east_cell + lon_west_cell) / 2
                    
                    area_m2 = (lat_step * 111111) * (lon_step * 111320 * math.cos(math.radians(lat_center)))
                    
                    grid = MicroGrid(
                        grid_id=f"{sector_id}-{row:03d}-{col:03d}",
                        sector_id=sector_id,
                        neighborhood=neighborhood,
                        row_index=row,
                        col_index=col,
                        lat_center=round(lat_center, 7),
                        lon_center=round(lon_center, 7),
                        lat_north=round(lat_north_cell, 7),
                        lat_south=round(lat_south_cell, 7),
                        lon_east=round(lon_east_cell, 7),
                        lon_west=round(lon_west_cell, 7),
                        cell_size_m=self.cell_size_meters,
                        area_m2=round(area_m2, 2),
                        created_at=timestamp
                    )
                    grids.append(grid)
            
            return grids
        
        def get_grid_summary(self, grids):
            if not grids:
                return {"total_grids": 0}
            return {
                "total_grids": len(grids),
                "total_area_km2": round(sum(g.area_m2 for g in grids) / 1_000_000, 4),
                "max_row": max(g.row_index for g in grids),
                "max_col": max(g.col_index for g in grids)
            }
    
    def get_logger(name):
        import logging
        return logging.getLogger(name)


# ============================================================================
# Configuration
# ============================================================================

CONFIG_PATH = Path(__file__).parent.parent / "config" / "neighborhoods.json"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "micro_grids"


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


def generate_micro_grids(sectors: list, cell_size: int = 100, preview: bool = False):
    """Generate micro grids for all sectors."""
    builder = MicroGridBuilder(cell_size_meters=cell_size)
    all_grids = []
    
    print(f"\n{'='*60}")
    print(f"MICRO GRID GENERATION")
    print(f"{'='*60}")
    print(f"Cell size: {cell_size} meters")
    print(f"Sectors: {len(sectors)}")
    print(f"Mode: {'Preview' if preview else 'Generate'}")
    print(f"{'='*60}\n")
    
    for sector in sectors:
        print(f"\n📍 Processing: {sector['name']} ({sector['id']})")
        print(f"   Bounds: {sector['bounds']}")
        
        try:
            grids = builder.generate_grids_for_sector(
                sector_id=sector["id"],
                bounds=sector["bounds"],
                neighborhood=sector["neighborhood"]
            )
            
            summary = builder.get_grid_summary(grids)
            
            print(f"   ✅ Generated {len(grids)} grids")
            print(f"   📐 Total area: {summary['total_area_km2']:.3f} km²")
            print(f"   🗺️  Grid layout: {summary['max_row']+1} rows × {summary['max_col']+1} cols")
            
            all_grids.extend(grids)
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            continue
    
    return all_grids


def save_grids_to_file(grids: list, cell_size: int):
    """Save grids to JSON file."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"micro_grids_{cell_size}m_{timestamp}.json"
    filepath = OUTPUT_DIR / filename
    
    data = {
        "generated_at": datetime.utcnow().isoformat(),
        "cell_size_meters": cell_size,
        "total_grids": len(grids),
        "sectors": list(set(g.sector_id for g in grids)),
        "grids": [g.to_dict() for g in grids]
    }
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    
    print(f"\n💾 Saved to: {filepath}")
    return filepath


def save_grids_to_database(grids: list, force: bool = False):
    """Save grids to PostgreSQL database."""
    try:
        from src.database.connection import get_session
        from src.database.models import GridCellModel
        
        session = get_session()
        
        # Check for existing grids
        existing_count = session.query(GridCellModel).count()
        
        if existing_count > 0 and not force:
            print(f"\n⚠️  Database already has {existing_count} grid cells.")
            print("   Use --force to overwrite existing grids.")
            return False
        
        if force and existing_count > 0:
            print(f"\n🗑️  Deleting {existing_count} existing grid cells...")
            session.query(GridCellModel).delete()
            session.commit()
        
        # Insert new grids
        print(f"\n📥 Inserting {len(grids)} micro grids to database...")
        
        for grid in grids:
            model = GridCellModel(
                grid_id=grid.grid_id,
                neighborhood=grid.sector_id,  # Use sector_id as neighborhood for now
                lat_center=grid.lat_center,
                lon_center=grid.lon_center,
                lat_north=grid.lat_north,
                lat_south=grid.lat_south,
                lon_east=grid.lon_east,
                lon_west=grid.lon_west
            )
            session.add(model)
        
        session.commit()
        print(f"✅ Successfully inserted {len(grids)} grids to database.")
        return True
        
    except ImportError as e:
        print(f"\n⚠️  Database modules not available: {e}")
        print("   Grids saved to file only.")
        return False
    except Exception as e:
        print(f"\n❌ Database error: {e}")
        return False


def print_summary(grids: list):
    """Print summary of generated grids."""
    if not grids:
        print("\n⚠️  No grids generated.")
        return
    
    sectors = {}
    for grid in grids:
        sector = grid.sector_id
        if sector not in sectors:
            sectors[sector] = {"count": 0, "area": 0}
        sectors[sector]["count"] += 1
        sectors[sector]["area"] += grid.area_m2
    
    print(f"\n{'='*60}")
    print("GENERATION SUMMARY")
    print(f"{'='*60}")
    print(f"\nTotal grids: {len(grids)}")
    print(f"Total area: {sum(g.area_m2 for g in grids) / 1_000_000:.3f} km²")
    print(f"Cell size: {grids[0].cell_size_m} meters")
    
    print(f"\nBy sector:")
    for sector_id, data in sorted(sectors.items()):
        print(f"  • {sector_id}: {data['count']} grids ({data['area']/1_000_000:.3f} km²)")
    
    print(f"\nSample grid IDs:")
    for grid in grids[:5]:
        print(f"  • {grid.grid_id}")
    if len(grids) > 5:
        print(f"  ... and {len(grids) - 5} more")
    
    print(f"{'='*60}\n")


# ============================================================================
# CLI Entry Point
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Generate high-resolution micro-grids for Clifton sectors",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--sector",
        type=str,
        help="Generate grids for specific sector only (e.g., Clifton-Block2)"
    )
    parser.add_argument(
        "--cell-size",
        type=int,
        default=100,
        help="Cell size in meters (default: 100, range: 50-150)"
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Preview without saving to database"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing grids in database"
    )
    parser.add_argument(
        "--no-db",
        action="store_true",
        help="Skip database insert, only save to file"
    )
    
    args = parser.parse_args()
    
    # Validate cell size
    if args.cell_size < 50 or args.cell_size > 150:
        print(f"Error: Cell size must be between 50 and 150 meters")
        sys.exit(1)
    
    # Load config
    config = load_config()
    
    # Get sectors to process
    sectors = get_sectors_to_process(config, args.sector)
    
    if not sectors:
        if args.sector:
            print(f"Error: Sector '{args.sector}' not found in config")
        else:
            print("Error: No sectors found in config")
        sys.exit(1)
    
    # Generate grids
    grids = generate_micro_grids(
        sectors=sectors,
        cell_size=args.cell_size,
        preview=args.preview
    )
    
    # Print summary
    print_summary(grids)
    
    if args.preview:
        print("🔍 Preview mode - no data saved.")
        return
    
    # Save to file
    filepath = save_grids_to_file(grids, args.cell_size)
    
    # Save to database
    if not args.no_db:
        save_grids_to_database(grids, args.force)
    
    print("\n✅ Micro grid generation complete!")


if __name__ == "__main__":
    main()
