# Phase 1: Data Integration & Normalization

**PREREQUISITES**: Phase 0 must be complete with PHASE_LOG.md updated. Read PHASE_LOG.md before starting.

**READ THIS FIRST**: This file contains sequential prompts to implement Phase 1. Feed these to GitHub Copilot **one by one**, in order.

---

## Prompt 1: Read Phase 0 Handoff and Set Up Project Structure

```
I am implementing Phase 1 of the StartSmart MVP project (Data Integration).

First, please read PHASE_LOG.md to understand what Phase 0 delivered.

Then create the following directory structure under backend/:

backend/
├── src/
│   ├── __init__.py
│   ├── adapters/
│   │   ├── __init__.py
│   │   ├── google_places_adapter.py (WILL CREATE)
│   │   ├── simulated_social_adapter.py (WILL CREATE)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── geospatial_service.py (WILL CREATE)
│   ├── database/
│   │   ├── __init__.py
│   │   ├── connection.py (WILL CREATE)
│   │   ├── models.py (WILL CREATE)
│   ├── utils/
│       ├── __init__.py
│       ├── logger.py (WILL CREATE)
├── tests/
│   ├── __init__.py
│   ├── adapters/
│   │   ├── __init__.py
│   ├── services/
│       ├── __init__.py
├── scripts/
│   ├── fetch_google_places.py (WILL CREATE)

Create all __init__.py files and the directory structure.
```

---

## Prompt 2: Create Database Connection Layer

```
Create the database connection and ORM setup.

Please create `backend/src/database/connection.py`:

1. Use SQLAlchemy 2.0 syntax
2. Read DATABASE_URL from environment variables (use python-dotenv)
3. Create engine with connection pooling (pool_size=5, max_overflow=10)
4. Create declarative_base for ORM models
5. Create get_session() function that returns a SQLAlchemy Session (use context manager pattern)
6. Include proper error handling and logging
7. Add create_all_tables() function for testing (creates tables from ORM models)

Requirements:
- Must work with PostgreSQL (from DATABASE_URL)
- Should support SQLite for testing (detect from URL)
- Thread-safe session management
- Proper connection cleanup

Dependencies: sqlalchemy, python-dotenv
```

---

## Prompt 3: Create ORM Models

```
Create SQLAlchemy ORM models matching the database schema.

Please create `backend/src/database/models.py`:

1. Import Base from src.database.connection
2. Create ORM models for all tables defined in contracts/database_schema.sql:
   - GridCellModel (table name: grid_cells)
   - BusinessModel (table name: businesses)
   - SocialPostModel (table name: social_posts)
   - GridMetricsModel (table name: grid_metrics)
   - UserFeedbackModel (table name: user_feedback)

3. Each model must:
   - Match EXACTLY the schema in contracts/database_schema.sql (column names, types, constraints)
   - Include proper relationships (ForeignKey references)
   - Have __repr__ method for debugging
   - Use appropriate SQLAlchemy types (String, Integer, Float, DateTime, Boolean, DECIMAL, JSON)

4. Add helper methods:
   - to_dict() on each model (converts to dictionary for JSON serialization)
   - from_pydantic() class method (creates ORM instance from Pydantic model in contracts/models.py)

CRITICAL: Column names and types must match the SQL schema EXACTLY. Grid_id format: "DHA-Phase2-Cell-07" (string, not int).
```

---

## Prompt 4: Create Structured Logger

```
Create a structured logging utility for the project.

Please create `backend/src/utils/logger.py`:

1. Set up Python logging with:
   - JSON formatter for production logs
   - Colorized console output for development
   - Log level from environment variable LOG_LEVEL (default: INFO)
   - Separate loggers for different modules (adapters, services, database)

2. Include functions:
   - get_logger(name) -> returns configured logger
   - log_api_call(logger, endpoint, params, duration) -> helper for logging API calls
   - log_database_operation(logger, operation, table, row_count) -> helper for DB ops

3. Format:
   - Development: Human-readable with colors
   - Production: JSON lines for log aggregation

Use Python's standard logging library. No external dependencies.
```

---

## Prompt 5: Create Geospatial Service

```
Create the geospatial assignment service.

Please create `backend/src/services/geospatial_service.py`:

1. On initialization:
   - Load all grid cells from database (grid_id, bounds)
   - Cache in memory as shapely Polygon objects for fast lookups
   - Use shapely for point-in-polygon operations

2. Main function: assign_grid_id(lat: float, lon: float) -> Optional[str]
   - Takes a coordinate
   - Returns grid_id if point falls within any grid
   - Returns None if point outside all grids
   - Should be very fast (in-memory lookup)

3. Helper function: get_grid_bounds(grid_id: str) -> dict
   - Returns bounds dict: {lat_north, lat_south, lon_east, lon_west}

4. Include comprehensive error handling:
   - Invalid coordinates (out of Karachi bounds ~24.8-25.0 lat, 66.9-67.3 lon)
   - Empty grid cache (database not seeded)

5. Add logging for edge cases (points outside grids)

Dependencies: shapely
Use the database connection from src.database.connection (get_session())
Import GridCellModel from src.database.models
```

---

## Prompt 6: Create Google Places Adapter (Part 1 - Core Logic)

```
Create the Google Places API adapter.

Please create `backend/src/adapters/google_places_adapter.py`:

1. Import BaseAdapter from contracts/base_adapter
2. Import Business from contracts/models
3. Create class GooglePlacesAdapter(BaseAdapter)

4. Implement __init__(self, api_key: str):
   - Initialize googlemaps.Client
   - Set up logger (from src.utils.logger)

5. Implement fetch_businesses(self, category: str, bounds: dict) -> List[Business]:
   - Convert our category ("Gym") to Google Places type ("gym")
   - Calculate center point from bounds
   - Calculate radius from bounds (approx diagonal / 2)
   - Call places_nearby() with center, radius, type
   - Handle pagination (max 60 results, use next_page_token)
   - Map Google Place response to our Business model:
     * place_id -> business_id
     * name -> name
     * geometry.location.lat -> lat
     * geometry.location.lng -> lon
     * category (our input) -> category
     * rating -> rating (or None)
     * user_ratings_total -> review_count
     * source = "google_places"
   - Include retry logic with exponential backoff for rate limits

6. Implement get_source_name() -> str:
   - Return "google_places"

7. Category mapping:
   - "Gym" -> "gym"
   - "Cafe" -> "cafe"
   - Add more as needed

Dependencies: googlemaps
Include comprehensive error handling and logging.
```

---

## Prompt 7: Create Google Places Adapter (Part 2 - Error Handling & Raw Storage)

```
Enhance the Google Places Adapter with production features.

Update `backend/src/adapters/google_places_adapter.py`:

1. Add raw data storage:
   - Save raw Google Places API responses to data/raw/google_places/{grid_id}_{timestamp}.json
   - This creates an audit trail
   - Include metadata (query params, timestamp, result count)

2. Add robust error handling:
   - API key invalid -> clear error message
   - Rate limit exceeded -> exponential backoff retry (max 3 attempts)
   - Network errors -> retry with backoff
   - Invalid bounds -> validate before API call
   - Empty results -> log warning, return empty list (not error)

3. Add request throttling:
   - Max 10 requests per second (Google's limit)
   - Use time.sleep() between requests if needed

4. Add logging:
   - Log each API call (category, bounds, result count)
   - Log cache hits if you implement caching
   - Log errors with full context

5. Make fetch_businesses cache-aware (optional but recommended):
   - Check if we already fetched this grid+category today
   - If yes, load from data/raw/ instead of calling API
   - Include --force flag bypass in CLI script

Ensure thread-safety if needed (though MVP is single-threaded).
```

---

## Prompt 8: Create Simulated Social Adapter

```
Create the adapter for simulated social media data.

Please create `backend/src/adapters/simulated_social_adapter.py`:

1. Import BaseAdapter from contracts/base_adapter
2. Import SocialPost from contracts/models
3. Create class SimulatedSocialAdapter(BaseAdapter)

4. Implement __init__(self):
   - Set up database connection (use get_session from src.database.connection)
   - Set up logger

5. Implement fetch_social_posts(self, category: str, bounds: dict, days: int = 90) -> List[SocialPost]:
   - Query social_posts table WHERE:
     * is_simulated = TRUE
     * timestamp >= (now - days)
     * Optionally filter by bounds (lat/lon within bounds)
   - Convert SocialPostModel (ORM) to SocialPost (Pydantic) for each result
   - Return list

6. Implement get_source_name() -> str:
   - Return "simulated"

7. This adapter is simple because:
   - Data already in database (seeded in Phase 0)
   - No external API calls
   - Just database query

Include logging for row counts and query performance.
```

---

## Prompt 9: Create Business Fetching CLI Script

```
Create the CLI script to populate the businesses table.

Please create `backend/scripts/fetch_google_places.py`:

1. Use argparse for command-line arguments:
   --category (required): Gym or Cafe
   --neighborhood (required): e.g., DHA-Phase2
   --force: Force refetch even if data exists
   --api-key: Override GOOGLE_PLACES_API_KEY from env

2. Main logic:
   - Load grid cells for specified neighborhood from database
   - For each grid:
     * Get bounds from grid_cells table
     * Use GooglePlacesAdapter to fetch businesses
     * Use GeospatialService to assign grid_id to each business
     * Insert into businesses table (or update if exists)
     * Log progress (e.g., "Grid 3/12: Found 6 businesses")
   
3. Include summary statistics:
   - Total businesses fetched
   - Average per grid
   - Grids with 0 businesses (log warning)
   - API calls made
   - Time taken

4. Error handling:
   - Invalid neighborhood -> list available neighborhoods
   - API key missing -> clear error message
   - Database connection failure -> helpful error

5. Dry-run mode (--dry-run):
   - Fetch from API but don't insert into database
   - Print what would be inserted

Make it user-friendly with progress bars (use tqdm library).

Dependencies: argparse, tqdm
```

---

## Prompt 10: Create Unit Tests for Google Places Adapter

```
Create comprehensive unit tests for GooglePlacesAdapter.

Please create `backend/tests/adapters/test_google_places_adapter.py`:

1. Use pytest
2. Mock the googlemaps.Client (use unittest.mock or pytest-mock)

3. Test cases:
   - test_fetch_businesses_success: Mock API response, verify Business objects created correctly
   - test_fetch_businesses_pagination: Mock response with next_page_token, verify all results fetched
   - test_fetch_businesses_empty: Mock empty results, verify returns empty list
   - test_fetch_businesses_rate_limit: Mock rate limit error, verify retry logic
   - test_fetch_businesses_invalid_api_key: Mock auth error, verify exception raised
   - test_category_mapping: Verify "Gym" -> "gym", "Cafe" -> "cafe"
   - test_raw_data_storage: Verify JSON file created in data/raw/

4. Use fixtures for:
   - Mock Google Places API responses (realistic JSON structure)
   - Test bounds dict
   - Mock API key

5. Coverage target: ≥90% for google_places_adapter.py

Use responses library or unittest.mock.patch for mocking HTTP calls.
```

---

## Prompt 11: Create Unit Tests for Geospatial Service

```
Create unit tests for geospatial assignment.

Please create `backend/tests/services/test_geospatial_service.py`:

1. Use pytest
2. Use an in-memory SQLite database for tests (create test grid cells)

3. Test cases:
   - test_assign_grid_id_center: Point in center of grid -> correct grid_id
   - test_assign_grid_id_edge: Point on grid boundary -> returns a valid grid_id
   - test_assign_grid_id_outside: Point outside all grids -> returns None
   - test_assign_grid_id_multiple_grids: Overlapping grids (edge case) -> returns first match
   - test_get_grid_bounds: Verify bounds dict returned correctly
   - test_empty_database: No grids in DB -> returns None gracefully

4. Use fixtures:
   - Test database with 3-4 sample grids (known bounds)
   - Sample coordinates (center, edge, outside)

5. Test with realistic Karachi coordinates:
   - Grid center: (24.8278, 67.0595)
   - Outside point: (25.0000, 68.0000)

Coverage target: ≥95%
```

---

## Prompt 12: Integration Test & Final Verification

```
Create an integration test and run the full Phase 1 pipeline.

Please create `backend/tests/test_integration_phase1.py:

1. Test the full data flow:
   - Use test database (SQLite in-memory or test PostgreSQL)
   - Seed with 2-3 grid cells
   - Mock Google Places API
   - Run GooglePlacesAdapter.fetch_businesses()
   - Verify businesses inserted into database
   - Verify grid_id assigned correctly by GeospatialService
   - Query database and verify:
     * Row count matches expected
     * All required fields populated
     * grid_id matches expected grid

2. This test verifies:
   - Adapter -> GeospatialService -> Database flow
   - ORM models work correctly
   - No serialization errors

After creating this test, run the following commands:

```
powershell
# Run all unit tests
pytest backend/tests/ -v --cov=backend/src --cov-report=term

# Run the actual business fetching (ONLY if you have Google Places API key)
python backend/scripts/fetch_google_places.py --category Gym --neighborhood DHA-Phase2

# Verify data
psql startsmart_dev -c "SELECT grid_id, COUNT(*) FROM businesses WHERE category='Gym' GROUP BY grid_id ORDER BY grid_id;"
```

Document the results (test coverage %, businesses fetched, any issues) in PHASE_LOG.md.
```

---

## Prompt 13: Update PHASE_LOG.md with Phase 1 Handoff

```
Phase 1 is complete. Update PHASE_LOG.md with the Phase 1 handoff entry.

Append to PHASE_LOG.md following the exact format from IMPLEMENTATION_PLAN.md Phase 1 "Handoff to Phase 2" section.

Fill in:
- Your name as owner
- Completion date
- All files created with actual line counts (use: Get-ChildItem -Recurse -Include *.py | Measure-Object -Line)
- Actual database row counts (query: SELECT COUNT(*) FROM businesses)
- Test results (pytest output)
- Any issues encountered
- Exact imports for Phase 2 developer
- Example queries for Phase 2

Be comprehensive. This handoff is CRITICAL for Phase 2 success.

Include:
- Database state summary
- Environment variables used
- Known issues
- Performance metrics (if available)
```

---

## Phase 1 Completion Checklist

Before moving to Phase 2, verify:

- [ ] All files created under backend/src/
- [ ] GooglePlacesAdapter implements BaseAdapter interface
- [ ] SimulatedSocialAdapter implements BaseAdapter interface
- [ ] GeospatialService assigns grid_id correctly
- [ ] Database ORM models match schema exactly
- [ ] Unit tests pass with ≥85% coverage
- [ ] Integration test passes
- [ ] businesses table populated (≥50 rows)
- [ ] All businesses have grid_id assigned
- [ ] PHASE_LOG.md updated with comprehensive handoff
- [ ] No linting errors (run: black backend/src/ and flake8 backend/src/)
- [ ] Example queries documented for Phase 2

**CRITICAL REVIEW POINTS**:
1. Verify grid_id format is correct: "DHA-Phase2-Cell-07" (not Cell-7)
2. Verify category is exactly "Gym" or "Cafe" (case-sensitive)
3. Verify all Business objects have lat/lon within expected bounds
4. Check API quota usage (should be <20 requests for 12 grids)

**IMPORTANT**: Do NOT proceed to Phase 2 until PHASE_LOG.md is updated and reviewed.
