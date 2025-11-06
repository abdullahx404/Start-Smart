"""
Services Module

This module contains business logic services that operate on data
retrieved by adapters. Services handle geospatial operations, data
aggregation, and scoring computations.

Available Services:
    - GeospatialService: Point-in-polygon grid assignment
    - (Phase 2) AggregatorService: Data aggregation per grid
    - (Phase 2) ScoringService: GOS calculation
"""

# Import geospatial services
from src.services.geospatial_service import (
    GeospatialService,
    get_geospatial_service,
    assign_grid_id,
    get_grid_bounds,
)

__all__ = [
    "GeospatialService",
    "get_geospatial_service",
    "assign_grid_id",
    "get_grid_bounds",
]
