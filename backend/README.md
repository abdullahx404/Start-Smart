# StartSmart Backend - Phase 1

This directory contains the backend implementation for StartSmart MVP.

## Quick Start

```powershell
# 1. Install dependencies
cd backend
pip install sqlalchemy python-dotenv psycopg2-binary pytest

# 2. Validate ORM models
python scripts/validate_models.py

# 3. Test database connection (requires PostgreSQL running)
python scripts/test_db_connection.py

# 4. Run tests
pytest tests/database/ -v
```

## Phase 1: Data Integration & Normalization

**Status**: IN PROGRESS  
**Owner**: [Developer A]

## Directory Structure

```
backend/
├── src/
│   ├── __init__.py                 # Package initialization ✅
│   ├── adapters/                   # Data source adapters
│   │   ├── __init__.py ✅
│   │   ├── google_places_adapter.py ✅ CREATED
│   │   ├── simulated_social_adapter.py ✅ CREATED
│   │   ├── GOOGLE_PLACES_REFERENCE.py ✅
│   │   └── SIMULATED_SOCIAL_REFERENCE.py ✅
│   ├── services/                   # Business logic services
│   │   ├── __init__.py ✅
│   │   └── geospatial_service.py ✅ CREATED
│   ├── database/                   # Database ORM and connection
│   │   ├── __init__.py ✅
│   │   ├── connection.py ✅ CREATED
│   │   ├── models.py ✅ CREATED
│   │   └── QUICK_REFERENCE.py ✅
│   └── utils/                      # Shared utilities
│       ├── __init__.py ✅
│       ├── logger.py ✅ CREATED
│       └── LOGGER_REFERENCE.py ✅
├── tests/                          # Unit and integration tests
│   ├── __init__.py ✅
│   ├── adapters/
│   │   └── __init__.py ✅
│   ├── services/
│   │   └── __init__.py ✅
│   ├── database/
│   │   ├── __init__.py ✅
│   │   ├── test_connection.py ✅ CREATED
│   │   └── test_models.py ✅ CREATED
│   └── utils/
│       ├── __init__.py ✅
│       └── test_logger.py ✅ CREATED
├── scripts/                        # CLI tools
│   ├── test_db_connection.py ✅ CREATED
│   └── validate_models.py ✅ CREATED
└── DATABASE_CONNECTION.md ✅ CREATED
│   ├── __init__.py
│   ├── adapters/
│   │   └── __init__.py
│   └── services/
│       └── __init__.py
└── scripts/                        # CLI tools
    └── fetch_google_places.py (TO BE CREATED)
```

## Setup

### Prerequisites

1. Python 3.10+
2. PostgreSQL 14+ (running locally)
3. Google Places API key

### Installation

```powershell
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r ../requirements.txt
```

### Environment Variables

Create a `.env` file in the project root (one level up) with:

```env
DATABASE_URL=postgresql://postgres:12113@localhost:5432/startsmart_dev
GOOGLE_PLACES_API_KEY=your_api_key_here
ENVIRONMENT=development
LOG_LEVEL=INFO
```

## Phase 1 Implementation Tasks

### 1. Database Layer ✅ COMPLETE
- [x] `src/database/connection.py` - SQLAlchemy engine and session factory
- [x] `src/database/models.py` - ORM models for all 5 tables

### 2. Utilities ✅ COMPLETE
- [x] `src/utils/logger.py` - Structured logging setup

### 3. Services ✅ COMPLETE
- [x] `src/services/geospatial_service.py` - Point-in-polygon grid assignment

### 4. Adapters (Priority: HIGH)
- [x] `src/adapters/google_places_adapter.py` - Google Places API integration ✅
- [x] `src/adapters/simulated_social_adapter.py` - Read synthetic posts from DB ✅

### 5. Scripts (Priority: HIGH)
- [x] `scripts/fetch_google_places.py` - CLI to populate businesses table ✅

### 6. Tests (Priority: MEDIUM)
- [ ] `tests/adapters/test_google_places_adapter.py`
- [x] `tests/services/test_geospatial_service.py` ✅

## Usage Examples

### Google Places Adapter

```python
# Fetch real business data from Google Places API
from src.adapters import GooglePlacesAdapter, create_adapter

# Option 1: Create adapter with API key from environment
adapter = create_adapter()  # Reads GOOGLE_PLACES_API_KEY from .env

# Option 2: Pass API key directly
adapter = GooglePlacesAdapter(api_key="YOUR_API_KEY")

# Fetch businesses for a grid cell (uses cache if available)
businesses = adapter.fetch_businesses(
    category="Gym",
    bounds={
        "lat_north": 24.8320,
        "lat_south": 24.8260,
        "lon_east": 67.0640,
        "lon_west": 67.0580
    }
)

# Force refresh (bypass cache)
businesses = adapter.fetch_businesses(
    category="Gym",
    bounds={...},
    force_refresh=True  # Always fetch from API
)

print(f"Found {len(businesses)} businesses")
for biz in businesses:
    print(f"- {biz.name} (rating: {biz.rating}, grid: {biz.grid_id})")
```

**Production Features:**
- ✅ **Smart Caching**: Automatically caches API responses for 24 hours
- ✅ **Rate Limiting**: Respects 10 requests/second limit
- ✅ **Retry Logic**: Exponential backoff on failures (3 attempts)
- ✅ **Audit Trail**: Saves raw API responses to `data/raw/google_places/`
- ✅ **API Key Validation**: Validates key on initialization
- ✅ **Comprehensive Logging**: Logs all API calls, cache hits, errors

**Raw Data Storage:**
```
data/raw/google_places/
├── Gym_24.8290_67.0610_20251106_143000.json
└── Cafe_24.8250_67.0580_20251106_143030.json
```

Each file contains:
- Query metadata (category, bounds, timestamp)
- Statistics (rating averages, review counts)
- Raw Google Places API response
```

### Geospatial Service

```python
# Assign coordinates to grid cells
from src.services import GeospatialService

service = GeospatialService()
grid_id = service.assign_grid_id(24.8290, 67.0610)
print(f"Assigned to: {grid_id}")  # "DHA-Phase2-Cell-07"

# Get grid bounds
bounds = service.get_grid_bounds(grid_id)
print(f"Bounds: {bounds}")

# Or use convenience functions
from src.services import assign_grid_id, get_grid_bounds

grid_id = assign_grid_id(24.8290, 67.0610)
bounds = get_grid_bounds(grid_id)
```

### Simulated Social Adapter

```python
# Fetch synthetic social media posts from database
from src.adapters import SimulatedSocialAdapter, create_social_adapter

# Create adapter (recommended factory function)
adapter = create_social_adapter()

# Fetch posts for a grid cell (last 90 days)
posts = adapter.fetch_social_posts(
    category="Gym",
    bounds={
        "lat_north": 24.8320,
        "lat_south": 24.8260,
        "lon_east": 67.0640,
        "lon_west": 67.0580
    },
    days=90  # Lookback period (default: 90)
)

print(f"Found {len(posts)} simulated posts")
for post in posts[:5]:
    print(f"- [{post.source}] {post.post_type}: {post.text[:60]}...")

# Filter by post type for analysis
demand_posts = [p for p in posts if p.post_type and p.post_type.value == "demand"]
complaint_posts = [p for p in posts if p.post_type and p.post_type.value == "complaint"]
demand_signals = len(demand_posts) + len(complaint_posts)

print(f"Demand signals: {demand_signals}")
```

**Key Features:**
- ✅ **No External API**: Reads from database (fast and reliable)
- ✅ **Geographic Filtering**: Filters posts by bounds (lat/lon)
- ✅ **Time Window**: Configurable lookback period (days parameter)
- ✅ **Post Types**: Classifies as demand, complaint, or mention
- ✅ **Performance**: <100ms typical query time

**Note**: This adapter reads synthetic data pre-seeded during Phase 0. Post-MVP will add real Instagram/Reddit adapters.

See `src/adapters/SIMULATED_SOCIAL_REFERENCE.py` for more examples.

### Logging

```python
# Basic logging
from src.utils import get_logger

logger = get_logger(__name__)
logger.info("Application started")

# API call logging
from src.utils import log_api_call

log_api_call(
    logger,
    "Google Places API",
    params={"category": "Gym"},
    duration=1.23,
    status="success"
)

# Database operation logging
from src.utils import log_database_operation

log_database_operation(
    logger,
    "INSERT",
    "businesses",
    row_count=73,
    duration=0.45
)
```

See `src/utils/LOGGER_REFERENCE.py` for more examples.

### Fetch Business Data (CLI Script)

The `fetch_google_places.py` script fetches real business data from Google Places API and populates the database.

```powershell
# Basic usage: Fetch gyms for DHA Phase 2
cd backend
python scripts/fetch_google_places.py --category Gym --neighborhood "DHA Phase 2"

# Force refresh (bypass 24-hour cache)
python scripts/fetch_google_places.py --category Gym --neighborhood "DHA Phase 2" --force

# Dry-run mode (test without saving to database)
python scripts/fetch_google_places.py --category Gym --neighborhood "DHA Phase 2" --dry-run

# Use custom API key
python scripts/fetch_google_places.py --category Cafe --neighborhood "DHA Phase 2" --api-key YOUR_KEY

# Verbose logging
python scripts/fetch_google_places.py --category Gym --neighborhood "DHA Phase 2" --verbose
```

**Features:**
- ✅ **Progress tracking**: Shows grid-by-grid progress (with tqdm if installed)
- ✅ **Smart caching**: Uses adapter's 24-hour cache by default
- ✅ **Statistics**: Displays detailed summary (total businesses, avg per grid, API calls, etc.)
- ✅ **Error handling**: Validates neighborhood, handles API errors gracefully
- ✅ **Dry-run mode**: Test before actually inserting data
- ✅ **Duplicate detection**: Updates existing businesses instead of creating duplicates

**Sample Output:**
```
================================================================================
GOOGLE PLACES BUSINESS FETCHER
================================================================================

Validating neighborhood: DHA Phase 2
✓ Neighborhood 'DHA Phase 2' found in database

✓ API key configured (length: 39 chars)

================================================================================
Fetching Gym businesses for DHA Phase 2
================================================================================
Grid cells to process: 12
Force refresh: False
Dry-run mode: False

Processing grids: 100%|██████████████████████| 12/12 [00:15<00:00,  1.25s/grid]

================================================================================
FETCH COMPLETE - SUMMARY STATISTICS
================================================================================

Overview:
  Total grids processed:    12
  Total businesses found:   73
  Average per grid:         6.1
  Duration:                 15.23s

API Usage:
  API calls made:           0
  Cache hits:               12
  Cache hit rate:           100.0%

Database Operations:
  Businesses inserted:      73
  Businesses updated:       0
  Errors:                   0

Top 5 grids by business count:
  DHA-Phase2-Cell-03              9 businesses
  DHA-Phase2-Cell-07              8 businesses
  DHA-Phase2-Cell-05              7 businesses
  DHA-Phase2-Cell-11              7 businesses
  DHA-Phase2-Cell-01              6 businesses

================================================================================

✓ Data successfully fetched and saved to database!
  73 businesses inserted, 0 updated.

Verify data in database:
  psql startsmart_dev -c "SELECT grid_id, COUNT(*) FROM businesses WHERE category='Gym' GROUP BY grid_id;"
```

### Fetch Business Data

```powershell
# Fetch gyms in DHA Phase 2
python scripts/fetch_google_places.py --category Gym --neighborhood "DHA Phase 2"

# Verify data in database
python -c "from src.database.connection import get_session; from src.database.models import BusinessModel; session = get_session(); print(f'Total businesses: {session.query(BusinessModel).count()}')"
```

### Run Tests

```powershell
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=src --cov-report=term

# Run specific test file
pytest tests/adapters/test_google_places_adapter.py -v
```

## Database Schema

All ORM models must match `contracts/database_schema.sql`:

- `grid_cells` - Geographic grid cells
- `businesses` - Business location data (populated in Phase 1)
- `social_posts` - Social media posts (already seeded with synthetic data)
- `grid_metrics` - Opportunity scores (Phase 2)
- `user_feedback` - User ratings (Phase 4)

## Important Notes

### Contracts are LOCKED
Do NOT modify files in `contracts/` folder. All adapters must extend `BaseAdapter` from `contracts/base_adapter.py`.

### Import Paths
```python
# Correct imports
from contracts.base_adapter import BaseAdapter
from contracts.models import Business, SocialPost, Category, Source
from src.database.connection import get_session
from src.database.models import BusinessModel, SocialPostModel

# Incorrect - DO NOT create new classes
# class Business:  # ❌ Already defined in contracts/models.py
```

### Grid ID Format
- Format: `{neighborhood}-Cell-{01-09}` (zero-padded)
- Example: `"DHA-Phase2-Cell-07"`

### Category Values
Must match enum in `contracts/models.py`:
- `"Gym"` (case-sensitive)
- `"Cafe"` (case-sensitive)

## Phase 1 Success Criteria

- [ ] GooglePlacesAdapter fetches ≥5 businesses per grid (average)
- [ ] All businesses correctly assigned to grid_id
- [ ] `businesses` table contains ≥60 total records
- [ ] Unit tests: All passing, ≥85% coverage
- [ ] No Google API quota errors
- [ ] Database state documented in PHASE_LOG.md

## Next Phase

**Phase 2: Analytics & Scoring Engine**
- Implement aggregation logic
- Calculate GOS (Grid Opportunity Score)
- Populate `grid_metrics` table

## References

- [PHASE_LOG.md](../PHASE_LOG.md) - Phase 0 deliverables and handoff
- [IMPLEMENTATION_PLAN.md](../Miscellaneous/IMPLEMENTATION_PLAN.md) - Full MVP plan
- [contracts/](../contracts/) - Locked interface contracts
