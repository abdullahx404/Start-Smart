"""
Micro Grid Builder Service

Generates high-resolution micro-grids (50-150 meters) for precise spatial analysis.

Features:
- Configurable cell size (default: 100 meters)
- Dynamic grid generation based on sector bounds
- No overlap between cells
- Grid ID format: {sector}-{row:03d}-{col:03d}
- Calculates area in square meters

Usage:
    from src.services.micro_grid_builder import MicroGridBuilder
    
    builder = MicroGridBuilder(cell_size_meters=100)
    grids = builder.generate_grids_for_sector(
        sector_id="Clifton-Block2",
        bounds={
            "lat_north": 24.8220,
            "lat_south": 24.8100,
            "lon_east": 67.0360,
            "lon_west": 67.0200
        }
    )
"""

import math
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

from src.utils.logger import get_logger


# ============================================================================
# Constants
# ============================================================================

# Earth's radius in meters (for coordinate calculations)
EARTH_RADIUS_METERS = 6371000

# Default configuration
DEFAULT_CELL_SIZE_METERS = 100
MIN_CELL_SIZE_METERS = 50
MAX_CELL_SIZE_METERS = 150

# Karachi approximate bounds for validation
KARACHI_BOUNDS = {
    "lat_min": 24.7,
    "lat_max": 25.1,
    "lon_min": 66.8,
    "lon_max": 67.5,
}


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class MicroGrid:
    """
    Represents a single micro-grid cell.
    
    Attributes:
        grid_id: Unique identifier (format: {sector}-{row:03d}-{col:03d})
        sector_id: Parent sector ID
        neighborhood: Parent neighborhood ID
        row_index: Row position in grid matrix
        col_index: Column position in grid matrix
        lat_center: Center latitude
        lon_center: Center longitude
        lat_north: Northern boundary
        lat_south: Southern boundary
        lon_east: Eastern boundary
        lon_west: Western boundary
        cell_size_m: Cell edge length in meters
        area_m2: Area in square meters
        created_at: Creation timestamp
    """
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
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)
    
    def to_db_dict(self) -> Dict:
        """Convert to database-compatible dictionary."""
        return {
            "grid_id": self.grid_id,
            "parent_sector": self.sector_id,
            "neighborhood": self.neighborhood,
            "row_index": self.row_index,
            "col_index": self.col_index,
            "lat_center": self.lat_center,
            "lon_center": self.lon_center,
            "lat_north": self.lat_north,
            "lat_south": self.lat_south,
            "lon_east": self.lon_east,
            "lon_west": self.lon_west,
            "cell_size_m": self.cell_size_m,
            "area_m2": self.area_m2,
            "created_at": self.created_at
        }


# ============================================================================
# Helper Functions
# ============================================================================

def meters_to_lat_degrees(meters: float) -> float:
    """
    Convert meters to latitude degrees.
    
    1 degree of latitude ≈ 111,111 meters
    
    Args:
        meters: Distance in meters
        
    Returns:
        Distance in latitude degrees
    """
    return meters / 111111.0


def meters_to_lon_degrees(meters: float, latitude: float) -> float:
    """
    Convert meters to longitude degrees at a given latitude.
    
    The length of 1 degree of longitude varies with latitude:
    - At equator: ~111,321 meters
    - At 25° latitude (Karachi): ~100,900 meters
    
    Args:
        meters: Distance in meters
        latitude: Reference latitude (affects conversion)
        
    Returns:
        Distance in longitude degrees
    """
    # Longitude degrees shrink as latitude increases
    lat_radians = math.radians(latitude)
    meters_per_degree = 111320 * math.cos(lat_radians)
    return meters / meters_per_degree


def calculate_grid_area(lat_north: float, lat_south: float, 
                        lon_east: float, lon_west: float) -> float:
    """
    Calculate area of a grid cell in square meters.
    
    Uses Haversine-based approximation suitable for small areas.
    
    Args:
        lat_north, lat_south: Latitude bounds
        lon_east, lon_west: Longitude bounds
        
    Returns:
        Area in square meters
    """
    # Calculate height in meters
    lat_diff = lat_north - lat_south
    height_m = lat_diff * 111111
    
    # Calculate width at center latitude
    center_lat = (lat_north + lat_south) / 2
    lon_diff = lon_east - lon_west
    width_m = lon_diff * 111320 * math.cos(math.radians(center_lat))
    
    return abs(height_m * width_m)


# ============================================================================
# Micro Grid Builder Class
# ============================================================================

class MicroGridBuilder:
    """
    Service for generating high-resolution micro-grids.
    
    Creates a grid of cells covering a sector or neighborhood bounds.
    Each cell is assigned a unique ID based on its position.
    
    Attributes:
        cell_size_meters: Size of each cell edge in meters
        logger: Logger instance
    """
    
    def __init__(self, cell_size_meters: int = DEFAULT_CELL_SIZE_METERS):
        """
        Initialize the micro grid builder.
        
        Args:
            cell_size_meters: Size of each cell edge in meters (50-150)
            
        Raises:
            ValueError: If cell_size_meters is outside valid range
        """
        if cell_size_meters < MIN_CELL_SIZE_METERS:
            raise ValueError(f"Cell size must be at least {MIN_CELL_SIZE_METERS} meters")
        if cell_size_meters > MAX_CELL_SIZE_METERS:
            raise ValueError(f"Cell size must be at most {MAX_CELL_SIZE_METERS} meters")
        
        self.cell_size_meters = cell_size_meters
        self.logger = get_logger(__name__)
        
        self.logger.info(
            "MicroGridBuilder initialized",
            extra={"extra_fields": {"cell_size_m": cell_size_meters}}
        )
    
    def generate_grids_for_sector(
        self,
        sector_id: str,
        bounds: Dict[str, float],
        neighborhood: str = None
    ) -> List[MicroGrid]:
        """
        Generate micro-grids for a sector.
        
        Creates a regular grid of cells covering the sector bounds.
        Cells on the edges may extend slightly beyond bounds.
        
        Args:
            sector_id: Sector identifier (e.g., "Clifton-Block2")
            bounds: Dictionary with lat_north, lat_south, lon_east, lon_west
            neighborhood: Parent neighborhood ID (extracted from sector_id if None)
            
        Returns:
            List of MicroGrid objects
            
        Raises:
            ValueError: If bounds are invalid
        """
        # Validate bounds
        self._validate_bounds(bounds)
        
        # Extract neighborhood from sector_id if not provided
        if neighborhood is None:
            neighborhood = sector_id.split("-")[0] if "-" in sector_id else sector_id
        
        # Calculate grid dimensions
        lat_span = bounds["lat_north"] - bounds["lat_south"]
        lon_span = bounds["lon_east"] - bounds["lon_west"]
        
        # Convert cell size to degrees
        center_lat = (bounds["lat_north"] + bounds["lat_south"]) / 2
        lat_step = meters_to_lat_degrees(self.cell_size_meters)
        lon_step = meters_to_lon_degrees(self.cell_size_meters, center_lat)
        
        # Calculate number of rows and columns
        num_rows = max(1, math.ceil(lat_span / lat_step))
        num_cols = max(1, math.ceil(lon_span / lon_step))
        
        self.logger.info(
            f"Generating micro-grids for {sector_id}",
            extra={"extra_fields": {
                "rows": num_rows,
                "cols": num_cols,
                "total_grids": num_rows * num_cols,
                "cell_size_m": self.cell_size_meters
            }}
        )
        
        # Generate grids
        grids = []
        timestamp = datetime.utcnow().isoformat()
        
        for row in range(num_rows):
            for col in range(num_cols):
                # Calculate cell bounds
                lat_south = bounds["lat_south"] + row * lat_step
                lat_north = lat_south + lat_step
                lon_west = bounds["lon_west"] + col * lon_step
                lon_east = lon_west + lon_step
                
                # Clamp to sector bounds (optional, can extend slightly)
                lat_north = min(lat_north, bounds["lat_north"] + lat_step * 0.1)
                lon_east = min(lon_east, bounds["lon_east"] + lon_step * 0.1)
                
                # Calculate center
                lat_center = (lat_north + lat_south) / 2
                lon_center = (lon_east + lon_west) / 2
                
                # Calculate area
                area_m2 = calculate_grid_area(lat_north, lat_south, lon_east, lon_west)
                
                # Create grid ID
                grid_id = f"{sector_id}-{row:03d}-{col:03d}"
                
                grid = MicroGrid(
                    grid_id=grid_id,
                    sector_id=sector_id,
                    neighborhood=neighborhood,
                    row_index=row,
                    col_index=col,
                    lat_center=round(lat_center, 7),
                    lon_center=round(lon_center, 7),
                    lat_north=round(lat_north, 7),
                    lat_south=round(lat_south, 7),
                    lon_east=round(lon_east, 7),
                    lon_west=round(lon_west, 7),
                    cell_size_m=self.cell_size_meters,
                    area_m2=round(area_m2, 2),
                    created_at=timestamp
                )
                grids.append(grid)
        
        self.logger.info(
            f"Generated {len(grids)} micro-grids for {sector_id}",
            extra={"extra_fields": {"total_area_m2": sum(g.area_m2 for g in grids)}}
        )
        
        return grids
    
    def generate_grids_for_neighborhood(
        self,
        neighborhood_config: Dict
    ) -> Dict[str, List[MicroGrid]]:
        """
        Generate micro-grids for all sectors in a neighborhood.
        
        Args:
            neighborhood_config: Neighborhood configuration with sectors
            
        Returns:
            Dictionary mapping sector_id to list of MicroGrid objects
        """
        neighborhood_id = neighborhood_config.get("id", "Unknown")
        sectors = neighborhood_config.get("sectors", [])
        
        if not sectors:
            self.logger.warning(f"No sectors defined for {neighborhood_id}")
            return {}
        
        result = {}
        total_grids = 0
        
        for sector in sectors:
            sector_id = sector.get("id")
            bounds = sector.get("bounds")
            
            if not sector_id or not bounds:
                self.logger.warning(f"Skipping sector with missing id or bounds: {sector}")
                continue
            
            grids = self.generate_grids_for_sector(
                sector_id=sector_id,
                bounds=bounds,
                neighborhood=neighborhood_id
            )
            result[sector_id] = grids
            total_grids += len(grids)
        
        self.logger.info(
            f"Generated micro-grids for {neighborhood_id}",
            extra={"extra_fields": {
                "sectors": len(result),
                "total_grids": total_grids
            }}
        )
        
        return result
    
    def validate_no_overlap(self, grids: List[MicroGrid]) -> bool:
        """
        Validate that grids don't overlap.
        
        Since we generate grids with fixed step sizes and no random placement,
        overlaps should not occur. This method is for verification.
        
        Args:
            grids: List of MicroGrid objects
            
        Returns:
            True if no overlaps, False otherwise
        """
        from shapely.geometry import box
        
        for i, grid1 in enumerate(grids):
            poly1 = box(grid1.lon_west, grid1.lat_south, grid1.lon_east, grid1.lat_north)
            
            for grid2 in grids[i+1:]:
                poly2 = box(grid2.lon_west, grid2.lat_south, grid2.lon_east, grid2.lat_north)
                
                # Check for overlap (intersection area > 0)
                if poly1.intersects(poly2):
                    intersection = poly1.intersection(poly2)
                    if intersection.area > 1e-12:  # Small tolerance for floating point
                        self.logger.warning(
                            f"Overlap detected between {grid1.grid_id} and {grid2.grid_id}"
                        )
                        return False
        
        return True
    
    def calculate_coverage(
        self,
        grids: List[MicroGrid],
        bounds: Dict[str, float]
    ) -> float:
        """
        Calculate what percentage of bounds is covered by grids.
        
        Args:
            grids: List of MicroGrid objects
            bounds: Sector bounds dictionary
            
        Returns:
            Coverage percentage (0-100)
        """
        # Calculate total sector area
        sector_area = calculate_grid_area(
            bounds["lat_north"], bounds["lat_south"],
            bounds["lon_east"], bounds["lon_west"]
        )
        
        # Calculate total grid area (sum of all cells)
        grid_area = sum(g.area_m2 for g in grids)
        
        coverage = (grid_area / sector_area) * 100 if sector_area > 0 else 0
        return round(coverage, 2)
    
    def _validate_bounds(self, bounds: Dict[str, float]) -> None:
        """
        Validate geographic bounds.
        
        Args:
            bounds: Dictionary with lat_north, lat_south, lon_east, lon_west
            
        Raises:
            ValueError: If bounds are invalid
        """
        required_keys = ["lat_north", "lat_south", "lon_east", "lon_west"]
        
        for key in required_keys:
            if key not in bounds:
                raise ValueError(f"Missing required bound: {key}")
        
        if bounds["lat_north"] <= bounds["lat_south"]:
            raise ValueError("lat_north must be greater than lat_south")
        
        if bounds["lon_east"] <= bounds["lon_west"]:
            raise ValueError("lon_east must be greater than lon_west")
        
        # Validate within Karachi bounds (optional)
        center_lat = (bounds["lat_north"] + bounds["lat_south"]) / 2
        center_lon = (bounds["lon_east"] + bounds["lon_west"]) / 2
        
        if not (KARACHI_BOUNDS["lat_min"] <= center_lat <= KARACHI_BOUNDS["lat_max"]):
            self.logger.warning(f"Latitude {center_lat} may be outside Karachi bounds")
        
        if not (KARACHI_BOUNDS["lon_min"] <= center_lon <= KARACHI_BOUNDS["lon_max"]):
            self.logger.warning(f"Longitude {center_lon} may be outside Karachi bounds")
    
    def get_grid_summary(self, grids: List[MicroGrid]) -> Dict:
        """
        Get summary statistics for a list of grids.
        
        Args:
            grids: List of MicroGrid objects
            
        Returns:
            Dictionary with summary statistics
        """
        if not grids:
            return {"total_grids": 0}
        
        areas = [g.area_m2 for g in grids]
        sectors = set(g.sector_id for g in grids)
        
        return {
            "total_grids": len(grids),
            "sectors": list(sectors),
            "total_area_m2": sum(areas),
            "total_area_km2": round(sum(areas) / 1_000_000, 4),
            "avg_area_m2": round(sum(areas) / len(areas), 2),
            "cell_size_m": grids[0].cell_size_m,
            "min_row": min(g.row_index for g in grids),
            "max_row": max(g.row_index for g in grids),
            "min_col": min(g.col_index for g in grids),
            "max_col": max(g.col_index for g in grids)
        }


# ============================================================================
# Module-level function for convenience
# ============================================================================

def generate_micro_grids(
    sector_id: str,
    bounds: Dict[str, float],
    cell_size_meters: int = DEFAULT_CELL_SIZE_METERS
) -> List[MicroGrid]:
    """
    Convenience function to generate micro-grids for a sector.
    
    Args:
        sector_id: Sector identifier
        bounds: Geographic bounds dictionary
        cell_size_meters: Cell size in meters
        
    Returns:
        List of MicroGrid objects
    """
    builder = MicroGridBuilder(cell_size_meters=cell_size_meters)
    return builder.generate_grids_for_sector(sector_id, bounds)


# ============================================================================
# Testing
# ============================================================================

if __name__ == "__main__":
    # Test with Clifton-Block2 bounds
    test_bounds = {
        "lat_north": 24.8220,
        "lat_south": 24.8100,
        "lon_east": 67.0360,
        "lon_west": 67.0200
    }
    
    builder = MicroGridBuilder(cell_size_meters=100)
    grids = builder.generate_grids_for_sector("Clifton-Block2", test_bounds)
    
    print(f"\n=== Micro Grid Test ===")
    print(f"Generated {len(grids)} grids")
    print(f"Summary: {builder.get_grid_summary(grids)}")
    print(f"\nFirst grid: {grids[0].to_dict()}")
    print(f"Last grid: {grids[-1].to_dict()}")
