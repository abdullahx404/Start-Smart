"""
Geospatial Service for Grid Assignment

Provides fast point-in-polygon grid assignment using Shapely and in-memory caching.

Features:
- Load grid boundaries from database on initialization
- Cache as Shapely Polygon objects for fast lookups
- assign_grid_id() for coordinate → grid_id mapping
- Comprehensive validation and error handling
- Performance optimized for frequent lookups

Usage:
    from src.services.geospatial_service import GeospatialService
    
    service = GeospatialService()
    grid_id = service.assign_grid_id(24.8290, 67.0610)
    
    if grid_id:
        bounds = service.get_grid_bounds(grid_id)
"""

from typing import Optional, Dict, List, Tuple
from decimal import Decimal
from shapely.geometry import Point, Polygon
from shapely.errors import ShapelyError

from src.database.connection import get_session
from src.database.models import GridCellModel
from src.utils.logger import get_logger, log_database_operation


# ============================================================================
# Constants
# ============================================================================

# Karachi approximate bounds for validation
KARACHI_BOUNDS = {
    "lat_min": 24.7,
    "lat_max": 25.1,
    "lon_min": 66.8,
    "lon_max": 67.4,
}

# Tolerance for coordinate precision (degrees)
COORDINATE_PRECISION = 7  # Matches database DECIMAL(10,7)


# ============================================================================
# Geospatial Service Class
# ============================================================================

class GeospatialService:
    """
    Service for assigning coordinates to grid cells using point-in-polygon logic.
    
    Loads grid boundaries from database on initialization and caches them
    as Shapely Polygon objects for fast lookups.
    
    Attributes:
        grids: Dict mapping grid_id to Polygon object
        grid_metadata: Dict mapping grid_id to full grid data
        logger: Logger instance for debugging
    """
    
    def __init__(self, auto_load: bool = True):
        """
        Initialize the geospatial service.
        
        Args:
            auto_load: If True, automatically load grids from database on init.
                      Set to False if you want to load manually later.
        
        Raises:
            RuntimeError: If database connection fails or no grids found
        """
        self.logger = get_logger(__name__)
        self.grids: Dict[str, Polygon] = {}
        self.grid_metadata: Dict[str, Dict] = {}
        self._grid_list: List[Tuple[str, Polygon]] = []  # For efficient iteration
        
        if auto_load:
            self.load_grids()
    
    def load_grids(self) -> int:
        """
        Load all grid cells from database and create Polygon objects.
        
        Returns:
            Number of grids loaded
            
        Raises:
            RuntimeError: If database query fails or no grids found
        """
        self.logger.info("Loading grid cells from database...")
        
        import time
        start_time = time.time()
        
        try:
            with get_session() as session:
                # Query all grid cells
                grid_cells = session.query(GridCellModel).all()
                
                duration = time.time() - start_time
                
                if not grid_cells:
                    self.logger.error("No grid cells found in database. Run seed_grids.py first.")
                    raise RuntimeError(
                        "No grid cells in database. Please run 'python scripts/seed_grids.py' to initialize grids."
                    )
                
                log_database_operation(
                    self.logger,
                    "SELECT",
                    "grid_cells",
                    row_count=len(grid_cells),
                    duration=duration
                )
                
                # Convert to Shapely polygons
                loaded_count = 0
                for grid in grid_cells:
                    try:
                        polygon = self._create_polygon_from_grid(grid)
                        
                        # Cache polygon
                        self.grids[grid.grid_id] = polygon
                        
                        # Cache metadata
                        self.grid_metadata[grid.grid_id] = {
                            "grid_id": grid.grid_id,
                            "neighborhood": grid.neighborhood,
                            "lat_center": float(grid.lat_center),
                            "lon_center": float(grid.lon_center),
                            "lat_north": float(grid.lat_north),
                            "lat_south": float(grid.lat_south),
                            "lon_east": float(grid.lon_east),
                            "lon_west": float(grid.lon_west),
                            "area_km2": float(grid.area_km2) if grid.area_km2 else 0.5,
                        }
                        
                        loaded_count += 1
                        
                    except Exception as e:
                        self.logger.warning(
                            f"Failed to create polygon for grid {grid.grid_id}: {e}"
                        )
                        continue
                
                # Create list for efficient iteration (avoid dict iteration overhead)
                self._grid_list = list(self.grids.items())
                
                total_duration = time.time() - start_time
                self.logger.info(
                    f"Loaded {loaded_count} grid cells in {total_duration:.3f}s",
                    extra={"extra_fields": {
                        "grid_count": loaded_count,
                        "duration_seconds": round(total_duration, 3)
                    }}
                )
                
                return loaded_count
                
        except Exception as e:
            self.logger.error(f"Failed to load grids from database: {e}")
            raise RuntimeError(f"Database error while loading grids: {e}")
    
    def _create_polygon_from_grid(self, grid: GridCellModel) -> Polygon:
        """
        Create a Shapely Polygon from grid boundary coordinates.
        
        Args:
            grid: GridCellModel instance
            
        Returns:
            Shapely Polygon representing the grid boundary
            
        Raises:
            ValueError: If coordinates are invalid
        """
        try:
            # Grid is a rectangle defined by north/south/east/west bounds
            # Create polygon vertices in counter-clockwise order
            vertices = [
                (float(grid.lon_west), float(grid.lat_north)),   # NW corner
                (float(grid.lon_east), float(grid.lat_north)),   # NE corner
                (float(grid.lon_east), float(grid.lat_south)),   # SE corner
                (float(grid.lon_west), float(grid.lat_south)),   # SW corner
                (float(grid.lon_west), float(grid.lat_north)),   # Close polygon
            ]
            
            polygon = Polygon(vertices)
            
            if not polygon.is_valid:
                raise ValueError(f"Invalid polygon for grid {grid.grid_id}")
            
            return polygon
            
        except (ValueError, TypeError, AttributeError) as e:
            raise ValueError(f"Invalid grid coordinates for {grid.grid_id}: {e}")
    
    def assign_grid_id(self, lat: float, lon: float) -> Optional[str]:
        """
        Assign a coordinate to a grid cell using point-in-polygon logic.
        
        Args:
            lat: Latitude (degrees, -90 to 90)
            lon: Longitude (degrees, -180 to 180)
            
        Returns:
            Grid ID string if point falls within a grid, None otherwise
            
        Raises:
            ValueError: If coordinates are invalid or out of Karachi bounds
        """
        # Validate inputs
        self._validate_coordinates(lat, lon)
        
        # Check if grids are loaded
        if not self.grids:
            self.logger.error("No grids loaded. Call load_grids() first.")
            raise RuntimeError("Grid cache is empty. Service not initialized properly.")
        
        # Create point
        try:
            point = Point(lon, lat)  # Note: Shapely uses (x, y) = (lon, lat)
        except ShapelyError as e:
            self.logger.error(f"Failed to create Point({lon}, {lat}): {e}")
            raise ValueError(f"Invalid coordinates: {e}")
        
        # Check each grid (using cached list for performance)
        for grid_id, polygon in self._grid_list:
            try:
                if polygon.contains(point):
                    self.logger.debug(
                        f"Point ({lat}, {lon}) assigned to grid {grid_id}",
                        extra={"extra_fields": {
                            "lat": lat,
                            "lon": lon,
                            "grid_id": grid_id
                        }}
                    )
                    return grid_id
            except ShapelyError as e:
                self.logger.warning(
                    f"Point-in-polygon check failed for grid {grid_id}: {e}"
                )
                continue
        
        # Point not in any grid
        self.logger.warning(
            f"Point ({lat}, {lon}) does not fall within any grid cell",
            extra={"extra_fields": {
                "lat": lat,
                "lon": lon,
                "grids_checked": len(self.grids)
            }}
        )
        return None
    
    def get_grid_bounds(self, grid_id: str) -> Optional[Dict[str, float]]:
        """
        Get boundary coordinates for a grid cell.
        
        Args:
            grid_id: Grid identifier (e.g., "DHA-Phase2-Cell-07")
            
        Returns:
            Dict with keys: lat_north, lat_south, lon_east, lon_west, lat_center, lon_center
            Returns None if grid_id not found
        """
        if grid_id not in self.grid_metadata:
            self.logger.warning(f"Grid {grid_id} not found in cache")
            return None
        
        metadata = self.grid_metadata[grid_id]
        return {
            "lat_north": metadata["lat_north"],
            "lat_south": metadata["lat_south"],
            "lon_east": metadata["lon_east"],
            "lon_west": metadata["lon_west"],
            "lat_center": metadata["lat_center"],
            "lon_center": metadata["lon_center"],
        }
    
    def get_grid_metadata(self, grid_id: str) -> Optional[Dict]:
        """
        Get full metadata for a grid cell.
        
        Args:
            grid_id: Grid identifier
            
        Returns:
            Dict with all grid data (neighborhood, bounds, area, etc.)
            Returns None if grid_id not found
        """
        return self.grid_metadata.get(grid_id)
    
    def list_grids(self, neighborhood: Optional[str] = None) -> List[str]:
        """
        List all grid IDs, optionally filtered by neighborhood.
        
        Args:
            neighborhood: Filter by neighborhood name (case-insensitive)
            
        Returns:
            List of grid IDs
        """
        if neighborhood:
            neighborhood_lower = neighborhood.lower()
            return [
                grid_id for grid_id, meta in self.grid_metadata.items()
                if meta["neighborhood"].lower() == neighborhood_lower
            ]
        else:
            return list(self.grids.keys())
    
    def get_neighborhoods(self) -> List[str]:
        """
        Get list of unique neighborhoods.
        
        Returns:
            List of neighborhood names
        """
        neighborhoods = set(
            meta["neighborhood"] for meta in self.grid_metadata.values()
        )
        return sorted(neighborhoods)
    
    def _validate_coordinates(self, lat: float, lon: float) -> None:
        """
        Validate latitude and longitude values.
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Raises:
            ValueError: If coordinates are invalid or out of bounds
        """
        # Type check
        if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
            raise ValueError(f"Coordinates must be numeric. Got lat={type(lat)}, lon={type(lon)}")
        
        # Range check (global)
        if not -90 <= lat <= 90:
            raise ValueError(f"Latitude must be between -90 and 90. Got {lat}")
        
        if not -180 <= lon <= 180:
            raise ValueError(f"Longitude must be between -180 and 180. Got {lon}")
        
        # Karachi bounds check (warning only)
        if not (KARACHI_BOUNDS["lat_min"] <= lat <= KARACHI_BOUNDS["lat_max"]):
            self.logger.warning(
                f"Latitude {lat} outside Karachi bounds "
                f"({KARACHI_BOUNDS['lat_min']}, {KARACHI_BOUNDS['lat_max']})"
            )
        
        if not (KARACHI_BOUNDS["lon_min"] <= lon <= KARACHI_BOUNDS["lon_max"]):
            self.logger.warning(
                f"Longitude {lon} outside Karachi bounds "
                f"({KARACHI_BOUNDS['lon_min']}, {KARACHI_BOUNDS['lon_max']})"
            )
    
    def reload_grids(self) -> int:
        """
        Reload grids from database (useful if grids updated).
        
        Returns:
            Number of grids loaded
        """
        self.logger.info("Reloading grids from database...")
        self.grids.clear()
        self.grid_metadata.clear()
        self._grid_list.clear()
        return self.load_grids()
    
    def is_initialized(self) -> bool:
        """
        Check if service is initialized with grids.
        
        Returns:
            True if grids are loaded, False otherwise
        """
        return len(self.grids) > 0
    
    def get_stats(self) -> Dict:
        """
        Get service statistics.
        
        Returns:
            Dict with stats: total_grids, neighborhoods, cache_size_kb
        """
        import sys
        
        return {
            "total_grids": len(self.grids),
            "neighborhoods": len(self.get_neighborhoods()),
            "cache_size_bytes": sum(
                sys.getsizeof(polygon) for polygon in self.grids.values()
            ),
            "initialized": self.is_initialized(),
        }


# ============================================================================
# Module-Level Singleton (Optional Convenience)
# ============================================================================

# Global service instance (lazy-loaded)
_service_instance: Optional[GeospatialService] = None


def get_geospatial_service() -> GeospatialService:
    """
    Get the singleton geospatial service instance.
    
    Lazy-loads the service on first call. Subsequent calls return cached instance.
    
    Returns:
        GeospatialService instance
        
    Example:
        >>> from src.services.geospatial_service import get_geospatial_service
        >>> service = get_geospatial_service()
        >>> grid_id = service.assign_grid_id(24.8290, 67.0610)
    """
    global _service_instance
    
    if _service_instance is None:
        _service_instance = GeospatialService(auto_load=True)
    
    return _service_instance


def assign_grid_id(lat: float, lon: float) -> Optional[str]:
    """
    Convenience function to assign grid ID using singleton service.
    
    Args:
        lat: Latitude
        lon: Longitude
        
    Returns:
        Grid ID or None
        
    Example:
        >>> from src.services.geospatial_service import assign_grid_id
        >>> grid_id = assign_grid_id(24.8290, 67.0610)
        >>> print(grid_id)  # "DHA-Phase2-Cell-07"
    """
    service = get_geospatial_service()
    return service.assign_grid_id(lat, lon)


def get_grid_bounds(grid_id: str) -> Optional[Dict[str, float]]:
    """
    Convenience function to get grid bounds using singleton service.
    
    Args:
        grid_id: Grid identifier
        
    Returns:
        Bounds dict or None
    """
    service = get_geospatial_service()
    return service.get_grid_bounds(grid_id)


# ============================================================================
# Testing & Demo
# ============================================================================

if __name__ == "__main__":
    """
    Test the geospatial service.
    
    Run: python backend/src/services/geospatial_service.py
    """
    import sys
    
    print("=" * 70)
    print("GEOSPATIAL SERVICE TEST")
    print("=" * 70)
    print()
    
    try:
        # Initialize service
        print("1. Initializing service...")
        service = GeospatialService()
        
        stats = service.get_stats()
        print(f"   ✅ Loaded {stats['total_grids']} grids")
        print(f"   ✅ Neighborhoods: {stats['neighborhoods']}")
        print(f"   ✅ Cache size: {stats['cache_size_bytes']:,} bytes")
        print()
        
        # List neighborhoods
        print("2. Available neighborhoods:")
        for neighborhood in service.get_neighborhoods():
            grid_count = len(service.list_grids(neighborhood))
            print(f"   - {neighborhood}: {grid_count} grids")
        print()
        
        # Test point assignment
        print("3. Testing point assignment...")
        
        test_points = [
            (24.8290, 67.0610, "DHA Phase 2 center"),
            (24.8320, 67.0580, "DHA Phase 2 north"),
            (24.8260, 67.0640, "DHA Phase 2 south"),
            (24.7500, 67.0000, "Outside all grids (Saddar area)"),
            (25.0000, 67.3000, "Outside all grids (North Karachi)"),
        ]
        
        for lat, lon, description in test_points:
            grid_id = service.assign_grid_id(lat, lon)
            
            if grid_id:
                print(f"   ✅ ({lat}, {lon}) → {grid_id}")
                print(f"      Description: {description}")
                
                # Get bounds
                bounds = service.get_grid_bounds(grid_id)
                if bounds:
                    print(f"      Bounds: N={bounds['lat_north']:.4f}, S={bounds['lat_south']:.4f}, "
                          f"E={bounds['lon_east']:.4f}, W={bounds['lon_west']:.4f}")
            else:
                print(f"   ⚠️  ({lat}, {lon}) → No grid assigned")
                print(f"      Description: {description}")
            
            print()
        
        # Test error handling
        print("4. Testing error handling...")
        
        try:
            service.assign_grid_id(100, 200)  # Invalid coordinates
            print("   ❌ Should have raised ValueError")
        except ValueError as e:
            print(f"   ✅ Caught ValueError: {e}")
        
        try:
            service.assign_grid_id("invalid", "coords")  # Type error
            print("   ❌ Should have raised ValueError")
        except (ValueError, TypeError) as e:
            print(f"   ✅ Caught error: {e}")
        
        print()
        
        # Test convenience functions
        print("5. Testing convenience functions...")
        grid_id = assign_grid_id(24.8290, 67.0610)
        print(f"   assign_grid_id(24.8290, 67.0610) → {grid_id}")
        
        bounds = get_grid_bounds(grid_id) if grid_id else None
        if bounds:
            print(f"   get_grid_bounds('{grid_id}') → {bounds}")
        
        print()
        print("=" * 70)
        print("✅ ALL TESTS PASSED")
        print("=" * 70)
        print()
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
