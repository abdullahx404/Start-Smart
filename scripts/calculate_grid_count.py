#!/usr/bin/env python3
"""
Grid Count Calculator for StartSmart MVP
Phase 0: Neighborhood Configuration Validation

This script calculates how many grid cells of a specified size fit within
the geographic bounds of each neighborhood defined in neighborhoods.json.

Usage:
    python scripts/calculate_grid_count.py
    python scripts/calculate_grid_count.py --config config/neighborhoods.json
"""

import json
import math
import sys
from pathlib import Path
from typing import Dict, Tuple


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points on Earth.
    
    Args:
        lat1, lon1: First point coordinates (degrees)
        lat2, lon2: Second point coordinates (degrees)
    
    Returns:
        Distance in kilometers
    """
    # Earth's radius in kilometers
    R = 6371.0
    
    # Convert degrees to radians
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    # Haversine formula
    a = (math.sin(delta_lat / 2) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) *
         math.sin(delta_lon / 2) ** 2)
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c


def calculate_area_km2(bounds: Dict[str, float]) -> Tuple[float, float, float]:
    """
    Calculate the approximate area of a geographic bounding box.
    
    Args:
        bounds: Dictionary with lat_north, lat_south, lon_east, lon_west
    
    Returns:
        Tuple of (area_km2, width_km, height_km)
    """
    lat_north = bounds['lat_north']
    lat_south = bounds['lat_south']
    lon_east = bounds['lon_east']
    lon_west = bounds['lon_west']
    
    # Calculate height (north-south distance)
    height_km = haversine_distance(lat_south, lon_west, lat_north, lon_west)
    
    # Calculate width at the center latitude (east-west distance)
    lat_center = (lat_north + lat_south) / 2
    width_km = haversine_distance(lat_center, lon_west, lat_center, lon_east)
    
    # Approximate area (this assumes a rectangular projection)
    area_km2 = width_km * height_km
    
    return area_km2, width_km, height_km


def calculate_grid_count(area_km2: float, grid_size_km2: float) -> int:
    """
    Calculate how many grid cells fit in the neighborhood.
    
    Args:
        area_km2: Total neighborhood area in km²
        grid_size_km2: Size of each grid cell in km²
    
    Returns:
        Number of grid cells (rounded)
    """
    return round(area_km2 / grid_size_km2)


def calculate_grid_dimensions(grid_size_km2: float) -> Tuple[float, float]:
    """
    Calculate the side length of a square grid cell.
    
    Args:
        grid_size_km2: Grid area in km²
    
    Returns:
        Tuple of (side_length_km, side_length_degrees_approx)
    """
    side_length_km = math.sqrt(grid_size_km2)
    
    # Approximate conversion: 1 degree latitude ≈ 111 km
    # 1 degree longitude ≈ 111 km * cos(latitude)
    # Using rough approximation for Karachi (lat ~24.8°)
    side_length_degrees = side_length_km / 111.0
    
    return side_length_km, side_length_degrees


def main():
    """Main execution function."""
    
    # Default config path
    config_path = Path("config/neighborhoods.json")
    
    # Allow custom config path from command line
    if len(sys.argv) > 1:
        config_path = Path(sys.argv[1])
    
    # Check if config file exists
    if not config_path.exists():
        print(f"❌ Error: Config file not found at {config_path}")
        print(f"   Current working directory: {Path.cwd()}")
        sys.exit(1)
    
    # Load configuration
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in config file: {e}")
        sys.exit(1)
    
    print("=" * 70)
    print("StartSmart Grid Count Calculator - Phase 0 Validation")
    print("=" * 70)
    print()
    
    # Process each neighborhood
    neighborhoods = config.get('neighborhoods', [])
    if not neighborhoods:
        print("❌ Error: No neighborhoods found in config")
        sys.exit(1)
    
    total_grids = 0
    
    for i, neighborhood in enumerate(neighborhoods, 1):
        name = neighborhood.get('name', 'Unknown')
        neighborhood_id = neighborhood.get('id', 'unknown')
        bounds = neighborhood.get('bounds', {})
        grid_size_km2 = neighborhood.get('grid_size_km', 0.5)
        declared_count = neighborhood.get('grid_count', 0)
        
        print(f"Neighborhood {i}: {name} ({neighborhood_id})")
        print("-" * 70)
        
        # Validate bounds
        required_keys = {'lat_north', 'lat_south', 'lon_east', 'lon_west'}
        if not all(k in bounds for k in required_keys):
            print(f"❌ Error: Missing required bounds keys")
            continue
        
        # Display bounds
        print(f"  Geographic Bounds:")
        print(f"    Latitude:  {bounds['lat_south']:.4f}° S → {bounds['lat_north']:.4f}° N")
        print(f"    Longitude: {bounds['lon_west']:.4f}° W → {bounds['lon_east']:.4f}° E")
        print()
        
        # Calculate area
        area_km2, width_km, height_km = calculate_area_km2(bounds)
        print(f"  Neighborhood Dimensions:")
        print(f"    Width:  {width_km:.3f} km")
        print(f"    Height: {height_km:.3f} km")
        print(f"    Area:   {area_km2:.3f} km²")
        print()
        
        # Calculate grid dimensions
        side_km, side_deg = calculate_grid_dimensions(grid_size_km2)
        print(f"  Grid Cell Specifications:")
        print(f"    Target area: {grid_size_km2} km²")
        print(f"    Side length: {side_km:.3f} km ({side_km * 1000:.0f} meters)")
        print(f"    Approx degrees: {side_deg:.5f}° per side")
        print()
        
        # Calculate grid count
        calculated_count = calculate_grid_count(area_km2, grid_size_km2)
        print(f"  Grid Count Analysis:")
        print(f"    Calculated: {calculated_count} grids")
        print(f"    Declared:   {declared_count} grids")
        
        if calculated_count == declared_count:
            print(f"    Status:     ✅ MATCH - Configuration is correct")
        else:
            diff = abs(calculated_count - declared_count)
            print(f"    Status:     ⚠️  MISMATCH - Difference of {diff} grid(s)")
            print(f"    Suggestion: Update grid_count to {calculated_count} in config file")
        
        print()
        
        # Calculate grid layout suggestions
        grids_per_row = math.ceil(width_km / side_km)
        grids_per_col = math.ceil(height_km / side_km)
        suggested_layout_count = grids_per_row * grids_per_col
        
        print(f"  Suggested Grid Layout:")
        print(f"    Rows:    {grids_per_col} grids (north-south)")
        print(f"    Columns: {grids_per_row} grids (east-west)")
        print(f"    Total:   {suggested_layout_count} grids ({grids_per_col} × {grids_per_row})")
        print()
        
        total_grids += calculated_count
        print()
    
    # Summary
    print("=" * 70)
    print(f"Summary:")
    print(f"  Total Neighborhoods: {len(neighborhoods)}")
    print(f"  Total Grid Cells:    {total_grids}")
    print(f"  Categories:          {', '.join(config.get('categories', []))}")
    print("=" * 70)
    print()
    
    # Additional calculations for database sizing
    categories_count = len(config.get('categories', []))
    total_metrics_rows = total_grids * categories_count
    print(f"Database Sizing Estimates:")
    print(f"  grid_cells table:   ~{total_grids} rows")
    print(f"  grid_metrics table: ~{total_metrics_rows} rows ({total_grids} grids × {categories_count} categories)")
    print(f"  social_posts table: ~{total_grids * 50} rows (assuming 50 posts/grid)")
    print()
    
    print("✅ Grid count calculation complete!")


if __name__ == "__main__":
    main()
