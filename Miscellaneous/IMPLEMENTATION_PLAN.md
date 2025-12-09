# StartSmart MVP — Implementation Plan

## Document Overview

This implementation plan provides a complete, phase-based roadmap for building the StartSmart location intelligence platform MVP. All product context, data sources, and business requirements are defined in `STARTUP_IDEA.md`. This document focuses exclusively on the technical execution strategy, development workflow, and delivery milestones.

**Target Audience**: Four-developer team building an AI-powered location recommendation engine for Karachi entrepreneurs.

---

## 1. Objective of the MVP

Deliver a functional, data-driven location intelligence platform that:

- Analyzes **5 pilot neighborhoods** in Karachi using **~60 grid cells** (~0.5 km² each)
- Supports **2 business categories**: Food and Fitness
- Produces **Top-3 ranked location recommendations** per neighborhood per category
- Displays a **Gap Opportunity Score (GOS)** with explainability (supporting evidence from social data and competitor analysis)
- Demonstrates **measurable recommendation precision** (≥60-70% validated by pilot users)

**Success Criteria**: Live deployed MVP with interactive map, recommendation panel, scoring engine, and validated pilot feedback — delivered in ~15 days.

---

## 2. Technology Stack & Environment Setup

### Core Technologies (LOCKED - No Changes Allowed)

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| **Frontend** | Flutter 3.x (Web + Mobile) | Cross-platform, single codebase, excellent map support |
| **Backend API** | Python 3.10+ with **FastAPI** | Type-safe, auto-docs (Swagger), async support, best for REST APIs |
| **Database** | **PostgreSQL 14+** (Production)<br>SQLite (Local dev/testing only) | PostGIS extension for geospatial, robust ACID guarantees |
| **State Management** | **Riverpod 2.x** | Better scalability than Provider, compile-time safety, easier testing |
| **Maps** | **flutter_map 6.x** with OpenStreetMap tiles | Open-source, no API costs, customizable heatmap overlays |
| **Authentication** | Firebase Auth (Email only for MVP) | Quick setup, handles tokens, optional for demo |
| **Hosting** | Backend: Render or Railway<br>Frontend: Firebase Hosting | Free tier sufficient, auto-deploy from GitHub |
| **Storage** | Local JSON files (MVP)<br>AWS S3 (future) | Simple for synthetic data, scalable for real data later |
| **CI/CD** | GitHub Actions | Automated testing + deploy on merge to main |
| **Geospatial** | PostGIS + Shapely (Python) | Point-in-polygon, distance calculations |

### Data Strategy (CRITICAL - Read Carefully)

**MVP Approach: Synthetic-First with Real Google Places API**

For the MVP, we will use a **hybrid data strategy**:

1. **Synthetic Data (80%)**:
   - Social media signals (Instagram posts, Reddit mentions) will be **simulated**
   - Rationale: API access risks, rate limits, legal constraints
   - Format: Pre-generated JSON files in `data/synthetic/`
   - Clearly labeled as `[SIMULATED]` in UI and documentation

2. **Real Data (20%)**:
   - **Google Places API**: Real business listings, counts, ratings, coordinates
   - Rationale: Stable API, affordable ($200 free credit/month), essential for credibility
   - This is the ONLY real-time data source for MVP

3. **Future Real-Time Integration (Post-MVP)**:
   - Final phase will add adapters for real Instagram/Reddit data
   - Code architecture MUST support easy swapping: synthetic → real adapters
   - All adapters will implement same `BaseAdapter` interface

**Why This Works**:
- Judges/investors see real business data (most critical signal)
- Social data adds context but doesn't break demo if unavailable
- Transparent about synthetic data = credibility, not weakness
- Fast, reliable demos with no API failures

### Environment Setup (All Developers)

**Prerequisites**:
- Python 3.10+ with `pip` and `virtualenv`
- Flutter SDK 3.16+
- PostgreSQL 14+ (Install via: `winget install PostgreSQL.PostgreSQL`)
- Docker Desktop (Optional but recommended)
- Git
- VS Code with extensions: Python, Flutter, PostgreSQL
- Firebase CLI: `npm install -g firebase-tools`

**Initial Setup Commands** (PowerShell):
```powershell
# Clone repo
git clone <repo-url>
cd cross_check_startsmart

# Backend setup
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Frontend setup
cd frontend
flutter pub get
cd ..

# Database initialization (Docker - recommended)
docker-compose up -d postgres

# OR use local PostgreSQL
# createdb startsmart_dev
# psql startsmart_dev < migrations/schema.sql

# Environment variables
cp .env.example .env
# Edit .env with:
#   GOOGLE_PLACES_API_KEY=<your-key>
#   DATABASE_URL=postgresql://user:pass@localhost:5432/startsmart_dev
```

**Shared Development Standards**:
- **Code Formatting**: 
  - Python: `black` (line length 100), `isort`, `flake8`
  - Dart: `dart format`
- **Pre-commit Hooks**: Run tests + linting before every commit
- **Branch Naming**: `phase-<N>/<short-description>` (e.g., `phase-1/google-places-adapter`)
- **Commit Messages**: Conventional Commits format (`feat:`, `fix:`, `docs:`)
- **PR Reviews**: Required before merging to `main` (1 approval minimum)
- **PHASE_LOG Updates**: MANDATORY at end of each phase (automated check in CI)

---

## 3. Interface Contracts & Pre-Development Lockdown

**CRITICAL: These contracts MUST be completed BEFORE Phase 1 begins.**

All developers will implement against these shared interfaces. No deviations allowed without team sync.

### 3.1 Database Schema Contract

**File**: `contracts/database_schema.sql`

**ALL tables, columns, types, and indexes defined here. No ad-hoc schema changes in phases.**

```sql
-- Grid Cells (computed once, static for MVP)
CREATE TABLE grid_cells (
    grid_id VARCHAR(50) PRIMARY KEY,
    neighborhood VARCHAR(100) NOT NULL,
    lat_center DECIMAL(10, 7) NOT NULL,
    lon_center DECIMAL(10, 7) NOT NULL,
    lat_north DECIMAL(10, 7) NOT NULL,
    lat_south DECIMAL(10, 7) NOT NULL,
    lon_east DECIMAL(10, 7) NOT NULL,
    lon_west DECIMAL(10, 7) NOT NULL,
    area_km2 DECIMAL(5, 2) DEFAULT 0.5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Businesses (from Google Places API)
CREATE TABLE businesses (
    business_id VARCHAR(100) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    lat DECIMAL(10, 7) NOT NULL,
    lon DECIMAL(10, 7) NOT NULL,
    category VARCHAR(50) NOT NULL, -- 'Gym', 'Cafe', etc.
    rating DECIMAL(2, 1), -- 0.0 to 5.0
    review_count INTEGER DEFAULT 0,
    source VARCHAR(50) DEFAULT 'google_places',
    grid_id VARCHAR(50) REFERENCES grid_cells(grid_id),
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_category (category),
    INDEX idx_grid_category (grid_id, category)
);

-- Social Posts (synthetic for MVP, real later)
CREATE TABLE social_posts (
    post_id VARCHAR(100) PRIMARY KEY,
    source VARCHAR(50) NOT NULL, -- 'instagram', 'reddit', 'simulated'
    text TEXT,
    timestamp TIMESTAMP,
    lat DECIMAL(10, 7),
    lon DECIMAL(10, 7),
    grid_id VARCHAR(50) REFERENCES grid_cells(grid_id),
    post_type VARCHAR(50), -- 'demand', 'complaint', 'mention'
    engagement_score INTEGER DEFAULT 0, -- likes, upvotes, etc.
    is_simulated BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_grid_type (grid_id, post_type),
    INDEX idx_source (source)
);

-- Grid Metrics (computed by scoring engine)
CREATE TABLE grid_metrics (
    id SERIAL PRIMARY KEY,
    grid_id VARCHAR(50) REFERENCES grid_cells(grid_id),
    category VARCHAR(50) NOT NULL,
    business_count INTEGER DEFAULT 0,
    instagram_volume INTEGER DEFAULT 0,
    reddit_mentions INTEGER DEFAULT 0,
    gos DECIMAL(4, 3), -- 0.000 to 1.000
    confidence DECIMAL(4, 3), -- 0.000 to 1.000
    top_posts_json JSONB, -- Top 3 posts with text + links
    competitors_json JSONB, -- List of nearby businesses
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (grid_id, category),
    INDEX idx_gos (gos DESC),
    INDEX idx_category_gos (category, gos DESC)
);

-- User Feedback (optional for MVP, prepare table)
CREATE TABLE user_feedback (
    id SERIAL PRIMARY KEY,
    grid_id VARCHAR(50) REFERENCES grid_cells(grid_id),
    category VARCHAR(50),
    rating INTEGER CHECK (rating IN (-1, 1)), -- thumbs down / thumbs up
    comment TEXT,
    user_email VARCHAR(255), -- nullable for guest users
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_grid (grid_id)
);
```

### 3.2 API Contract (OpenAPI 3.0)

**File**: `contracts/api_spec.yaml`

**ALL endpoints, request/response schemas locked here.**

```yaml
openapi: 3.0.0
info:
  title: StartSmart Location Intelligence API
  version: 1.0.0
  description: MVP API for location recommendations

servers:
  - url: http://localhost:8000/api/v1
    description: Local development
  - url: https://startsmart-api.onrender.com/api/v1
    description: Production

paths:
  /neighborhoods:
    get:
      summary: List all available neighborhoods
      responses:
        '200':
          description: Success
          content:
            application/json:
              schema:
                type: array
                items:
                  type: object
                  properties:
                    id:
                      type: string
                      example: "DHA-Phase2"
                    name:
                      type: string
                      example: "DHA Phase 2"
                    grid_count:
                      type: integer
                      example: 12

  /grids:
    get:
      summary: Get all grids for neighborhood + category
      parameters:
        - name: neighborhood
          in: query
          required: true
          schema:
            type: string
            example: "DHA-Phase2"
        - name: category
          in: query
          required: true
          schema:
            type: string
            enum: [Gym, Cafe]
      responses:
        '200':
          description: Grid list with GOS scores
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/GridSummary'

  /recommendations:
    get:
      summary: Get top-N recommendations
      parameters:
        - name: neighborhood
          in: query
          required: true
          schema:
            type: string
        - name: category
          in: query
          required: true
          schema:
            type: string
        - name: limit
          in: query
          schema:
            type: integer
            default: 3
      responses:
        '200':
          description: Top recommendations with explanations
          content:
            application/json:
              schema:
                type: object
                properties:
                  neighborhood:
                    type: string
                  category:
                    type: string
                  recommendations:
                    type: array
                    items:
                      $ref: '#/components/schemas/Recommendation'

  /grid/{grid_id}:
    get:
      summary: Detailed view of single grid
      parameters:
        - name: grid_id
          in: path
          required: true
          schema:
            type: string
        - name: category
          in: query
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Full grid details
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/GridDetail'

  /feedback:
    post:
      summary: Submit user feedback
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                grid_id:
                  type: string
                category:
                  type: string
                rating:
                  type: integer
                  enum: [-1, 1]
                comment:
                  type: string
      responses:
        '201':
          description: Feedback saved

components:
  schemas:
    GridSummary:
      type: object
      properties:
        grid_id:
          type: string
        lat_center:
          type: number
        lon_center:
          type: number
        gos:
          type: number
          format: float
        confidence:
          type: number
          format: float

    Recommendation:
      type: object
      properties:
        grid_id:
          type: string
        gos:
          type: number
        confidence:
          type: number
        rationale:
          type: string
          example: "High demand (48 posts), low competition (2 gyms)"
        lat_center:
          type: number
        lon_center:
          type: number

    GridDetail:
      type: object
      properties:
        grid_id:
          type: string
        gos:
          type: number
        confidence:
          type: number
        metrics:
          type: object
          properties:
            business_count:
              type: integer
            instagram_volume:
              type: integer
            reddit_mentions:
              type: integer
        top_posts:
          type: array
          items:
            type: object
            properties:
              source:
                type: string
              text:
                type: string
              timestamp:
                type: string
              link:
                type: string
        competitors:
          type: array
          items:
            type: object
            properties:
              name:
                type: string
              distance_km:
                type: number
              rating:
                type: number
```

### 3.3 Python Data Models Contract

**File**: `contracts/models.py`

**Pydantic models for type safety across all backend code.**

```python
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class Category(str, Enum):
    GYM = "Gym"
    CAFE = "Cafe"

class Source(str, Enum):
    GOOGLE_PLACES = "google_places"
    INSTAGRAM = "instagram"
    REDDIT = "reddit"
    SIMULATED = "simulated"

class PostType(str, Enum):
    DEMAND = "demand"
    COMPLAINT = "complaint"
    MENTION = "mention"

# ========== Database Models (SQLAlchemy ORM will match these) ==========

class GridCell(BaseModel):
    grid_id: str
    neighborhood: str
    lat_center: float
    lon_center: float
    lat_north: float
    lat_south: float
    lon_east: float
    lon_west: float
    area_km2: float = 0.5

class Business(BaseModel):
    business_id: str
    name: str
    lat: float
    lon: float
    category: Category
    rating: Optional[float] = None
    review_count: int = 0
    source: Source = Source.GOOGLE_PLACES
    grid_id: Optional[str] = None
    fetched_at: datetime

class SocialPost(BaseModel):
    post_id: str
    source: Source
    text: Optional[str] = None
    timestamp: datetime
    lat: Optional[float] = None
    lon: Optional[float] = None
    grid_id: Optional[str] = None
    post_type: Optional[PostType] = None
    engagement_score: int = 0
    is_simulated: bool = False

class GridMetrics(BaseModel):
    grid_id: str
    category: Category
    business_count: int = 0
    instagram_volume: int = 0
    reddit_mentions: int = 0
    gos: float
    confidence: float
    top_posts_json: Optional[dict] = None
    competitors_json: Optional[dict] = None
    last_updated: datetime

# ========== API Response Models ==========

class GridSummaryResponse(BaseModel):
    grid_id: str
    lat_center: float
    lon_center: float
    gos: float
    confidence: float

class RecommendationResponse(BaseModel):
    grid_id: str
    gos: float
    confidence: float
    rationale: str
    lat_center: float
    lon_center: float

class TopPostDetail(BaseModel):
    source: str
    text: str
    timestamp: str
    link: Optional[str] = None

class CompetitorDetail(BaseModel):
    name: str
    distance_km: float
    rating: Optional[float] = None

class GridDetailResponse(BaseModel):
    grid_id: str
    gos: float
    confidence: float
    metrics: dict
    top_posts: List[TopPostDetail]
    competitors: List[CompetitorDetail]

class NeighborhoodResponse(BaseModel):
    id: str
    name: str
    grid_count: int
```

### 3.4 Adapter Interface Contract

**File**: `contracts/base_adapter.py`

**ALL data adapters (Google Places, Instagram, Reddit, Simulated) MUST implement this.**

```python
from abc import ABC, abstractmethod
from typing import List
from contracts.models import Business, SocialPost

class BaseAdapter(ABC):
    """
    Base interface for all data source adapters.
    
    Phase 1 will implement:
    - GooglePlacesAdapter (real data)
    - SimulatedSocialAdapter (synthetic Instagram/Reddit)
    
    Future phases will add:
    - InstagramAdapter (real scraping)
    - RedditAdapter (PRAW API)
    """
    
    @abstractmethod
    def fetch_businesses(self, category: str, bounds: dict) -> List[Business]:
        """
        Fetch businesses within geographic bounds.
        
        Args:
            category: Business category (e.g., 'Gym', 'Cafe')
            bounds: dict with keys: lat_north, lat_south, lon_east, lon_west
            
        Returns:
            List of Business objects
        """
        pass
    
    @abstractmethod
    def fetch_social_posts(self, category: str, bounds: dict, days: int = 90) -> List[SocialPost]:
        """
        Fetch social media posts within geographic bounds.
        
        Args:
            category: Topic/category to search for
            bounds: Geographic bounding box
            days: Lookback period in days
            
        Returns:
            List of SocialPost objects
        """
        pass
    
    @abstractmethod
    def get_source_name(self) -> str:
        """Return source identifier (e.g., 'google_places', 'simulated')"""
        pass
```

---

## 4. Phase Breakdown

### **Phase 0: Contracts, Synthetic Data & Manual Validation** (2-3 days)

**CRITICAL: This phase sets the foundation. Everything breaks if done poorly.**

#### Goal
1. Lock down all interface contracts (database, API, models)
2. Create high-quality synthetic dataset for 12 grid cells × 1 category
3. Manually validate scoring formula with real-world spot checks

#### Deliverables

1. **Contracts Package** (`contracts/` directory):
   - `database_schema.sql` (see Section 3.1)
   - `api_spec.yaml` (see Section 3.2)
   - `models.py` (see Section 3.3)
   - `base_adapter.py` (see Section 3.4)

2. **Neighborhood & Grid Definitions** (`config/neighborhoods.json`):
   ```json
   {
     "neighborhoods": [
       {
         "id": "DHA-Phase2",
         "name": "DHA Phase 2",
         "bounds": {
           "lat_north": 24.8345,
           "lat_south": 24.8210,
           "lon_east": 67.0670,
           "lon_west": 67.0520
         },
         "grid_size_km": 0.5,
         "grid_count": 12
       }
     ],
     "categories": ["Gym", "Cafe"]
   }
   ```

3. **Synthetic Dataset Generator** (`scripts/generate_synthetic_data.py`):
   - Generates realistic simulated social posts for each grid
   - Distribution logic:
     - High-opportunity grids: Low business_count, high post_volume
     - Low-opportunity grids: High business_count, low post_volume
     - Medium grids: Balanced
   - Output: `data/synthetic/social_posts_v1.json` (500-1000 posts)

4. **Database Initialization**:
   - `migrations/001_schema.sql` (copy from contracts/database_schema.sql)
   - `scripts/seed_grids.py`: Populate `grid_cells` table from neighborhoods.json
   - `scripts/seed_synthetic_posts.py`: Load synthetic social posts into DB

5. **Manual Validation Report**:
   - Pick 3 grids manually from Google Maps
   - Count real businesses (Gym category)
   - Hand-calculate GOS using formula
   - Compare with 3 local entrepreneurs (informal chat/DM)
   - Document in `docs/phase0_validation.md`

6. **Environment Setup Scripts**:
   - `.env.example` with all required variables
   - `requirements.txt` (Python dependencies)
   - `frontend/pubspec.yaml` (Flutter dependencies)
   - `docker-compose.yml` (PostgreSQL container)

#### Dependencies
- Google Maps (manual browsing for validation)
- Access to 3-5 local entrepreneurs for quick feedback

#### Validation Criteria
- All 4 contract files created and reviewed by team
- Synthetic dataset contains ≥500 posts across 12 grids
- Database initialized with 12 grid cells
- Manual validation shows GOS formula is sensible (2/3 entrepreneurs agree high-GOS areas make sense)

#### Testing Approach
```powershell
# Generate synthetic data
python scripts/generate_synthetic_data.py --grids 12 --posts-per-grid 50 --output data/synthetic/

# Initialize database
docker-compose up -d postgres
python scripts/seed_grids.py --config config/neighborhoods.json
python scripts/seed_synthetic_posts.py --input data/synthetic/social_posts_v1.json

# Verify data
psql startsmart_dev -c "SELECT COUNT(*) FROM grid_cells;"  # Should return 12
psql startsmart_dev -c "SELECT COUNT(*) FROM social_posts WHERE is_simulated = TRUE;"  # Should return 500+
```

#### Handoff to Phase 1

**PHASE_LOG.md Entry (Developer must add this):**
```yaml
Phase: 0 - Contracts & Synthetic Data
Owner: [Your Name]
Completed: 2025-11-XX
Summary:
  - Created 4 contract files: database_schema.sql, api_spec.yaml, models.py, base_adapter.py
  - Generated synthetic dataset: 600 social posts across 12 grid cells (DHA Phase 2)
  - Seeded database: 12 rows in grid_cells table, 600 rows in social_posts table
  - Manual validation: 2/3 entrepreneurs confirmed high-GOS grids (Cell-07, Cell-03) are underserved for Gyms
Files Created:
  - contracts/database_schema.sql (150 lines)
  - contracts/api_spec.yaml (200 lines)
  - contracts/models.py (120 lines)
  - contracts/base_adapter.py (45 lines)
  - config/neighborhoods.json (30 lines)
  - scripts/generate_synthetic_data.py (180 lines)
  - scripts/seed_grids.py (80 lines)
  - scripts/seed_synthetic_posts.py (60 lines)
  - data/synthetic/social_posts_v1.json (600 records)
Database State:
  - Tables created: grid_cells, businesses, social_posts, grid_metrics, user_feedback
  - grid_cells: 12 rows (all DHA Phase 2)
  - social_posts: 600 rows (is_simulated = TRUE)
  - businesses: 0 rows (Phase 1 will populate via Google Places API)
Next Steps for Phase 1:
  1. Import BaseAdapter from contracts/base_adapter.py
  2. Implement GooglePlacesAdapter extending BaseAdapter
  3. Implement SimulatedSocialAdapter (no-op, data already in DB)
  4. Create Normalizer to ensure Google Places data matches contracts/models.py schema
  5. Populate businesses table with real Google Places data for DHA Phase 2
Known Issues:
  - Grid Cell-09 has unusual bounds (near neighborhood edge); may cause point-in-polygon errors
  - Synthetic data heavily weighted toward "demand" posts; future versions should balance post types
  - PostgreSQL Docker container uses default port 5432; may conflict if local PG already running
Testing:
  - Manual: Verified grid generation covers full neighborhood area
  - Manual: Spot-checked 20 synthetic posts for realism
  - Validation: 2/3 local gym owners confirmed Cell-07 is underserved area
```

**Critical Info for Next Developer:**
- Database connection string: `postgresql://postgres:postgres@localhost:5432/startsmart_dev` (see .env.example)
- All models defined in `contracts/models.py` — **import from there, don't redefine**
- Grid IDs follow format: `{neighborhood}-Cell-{01-12}` (e.g., "DHA-Phase2-Cell-07")
- Synthetic posts already in DB, marked with `is_simulated = TRUE`

---

### **Phase 1: Data Integration & Normalization** (4-5 days)

**Owner**: Developer A

#### Goal
Build production-ready data adapters that fetch **real business data** from Google Places API and ensure all data conforms to locked contracts from Phase 0.

#### Deliverables

1. **Project Structure Setup**:
   ```
   backend/
   ├── src/
   │   ├── __init__.py
   │   ├── adapters/
   │   │   ├── __init__.py
   │   │   ├── google_places_adapter.py (NEW - real API)
   │   │   ├── simulated_social_adapter.py (NEW - reads from DB)
   │   ├── services/
   │   │   ├── __init__.py
   │   │   ├── geospatial_service.py (NEW - point-in-polygon)
   │   ├── database/
   │   │   ├── __init__.py
   │   │   ├── connection.py (NEW - SQLAlchemy setup)
   │   │   ├── models.py (NEW - ORM models matching contracts)
   │   ├── utils/
   │       ├── __init__.py
   │       ├── logger.py (NEW - structured logging)
   ├── tests/
   │   ├── adapters/
   │   │   ├── test_google_places_adapter.py (NEW)
   │   │   ├── test_geospatial_service.py (NEW)
   ├── scripts/
   │   ├── fetch_google_places.py (NEW - CLI to populate businesses)
   ```

2. **GooglePlacesAdapter** (`src/adapters/google_places_adapter.py`):
   - Extends `BaseAdapter` from `contracts/base_adapter.py`
   - Uses `googlemaps` Python library
   - Methods:
     - `fetch_businesses(category, bounds)` → Returns List[Business]
     - Handles pagination (Google Places returns max 60 results per call)
     - Converts Google Place types → our category taxonomy (e.g., "gym" → "Gym")
     - Includes retry logic for rate limits (exponential backoff)
   - Outputs raw JSON to `data/raw/google_places/{grid_id}_{timestamp}.json` (audit trail)

3. **SimulatedSocialAdapter** (`src/adapters/simulated_social_adapter.py`):
   - Extends `BaseAdapter`
   - `fetch_social_posts()` → Reads from `social_posts` table WHERE `is_simulated = TRUE`
   - No external API calls (data already seeded in Phase 0)
   - Returns List[SocialPost] matching `contracts/models.py`

4. **Geospatial Service** (`src/services/geospatial_service.py`):
   - Function: `assign_grid_id(lat, lon) -> str`
   - Uses point-in-polygon logic (Shapely library)
   - Loads grid boundaries from `grid_cells` table at startup (cache in memory)
   - Handles edge cases (points outside all grids → return None)

5. **Database Layer** (`src/database/`):
   - `connection.py`: SQLAlchemy engine, session factory
   - `models.py`: ORM models for all tables (must match `contracts/database_schema.sql`)
     - GridCellModel, BusinessModel, SocialPostModel, GridMetricsModel, UserFeedbackModel
   - Uses Alembic for migrations (even though schema defined in Phase 0, Alembic tracks changes)

6. **Business Fetching Script** (`scripts/fetch_google_places.py`):
   - CLI tool to populate `businesses` table
   - Usage: `python scripts/fetch_google_places.py --category Gym --neighborhood DHA-Phase2`
   - For each grid in neighborhood:
     - Call GooglePlacesAdapter
     - Assign grid_id using GeospatialService
     - Insert into `businesses` table
     - Log results (businesses found per grid)

7. **Comprehensive Tests**:
   - `tests/adapters/test_google_places_adapter.py`:
     - Mock Google Places API responses (use `responses` library)
     - Test category mapping (Google "gym" → our "Gym")
     - Test pagination handling
     - Test rate limit retry logic
   - `tests/services/test_geospatial_service.py`:
     - Known lat/lon → expected grid_id
     - Edge case: point outside all grids
   - Target: **≥85% code coverage** for all new modules

#### Dependencies
- Phase 0 completed (contracts locked, database initialized, synthetic data loaded)
- Google Places API key (get free $200/month credit)
- `googlemaps` Python package: `pip install googlemaps`
- `shapely` for geospatial: `pip install shapely`

#### Validation Criteria
- GooglePlacesAdapter successfully fetches ≥5 businesses per grid (average across 12 grids)
- All fetched businesses assigned to correct grid_id (manual spot-check 10 businesses)
- `businesses` table contains ≥60 total records (12 grids × ~5 businesses)
- Unit tests: All passing, ≥85% coverage
- No API quota errors (under free tier limit)

#### Testing & Running
```powershell
# Activate venv
.\venv\Scripts\Activate.ps1

# Run unit tests
pytest tests/adapters/ -v --cov=src/adapters --cov-report=term

# Fetch real business data for DHA Phase 2
python scripts/fetch_google_places.py --category Gym --neighborhood DHA-Phase2

# Verify data in DB
psql startsmart_dev -c "SELECT grid_id, COUNT(*) FROM businesses GROUP BY grid_id;"

# Check sample business
psql startsmart_dev -c "SELECT name, category, rating, grid_id FROM businesses LIMIT 5;"
```

#### Handoff to Phase 2

**PHASE_LOG.md Entry (MUST ADD THIS):**
```yaml
Phase: 1 - Data Integration
Owner: [Your Name]
Completed: 2025-11-XX
Summary:
  - Implemented GooglePlacesAdapter (real API integration)
  - Implemented SimulatedSocialAdapter (reads synthetic data from DB)
  - Built GeospatialService for point-in-polygon grid assignment
  - Populated businesses table: 73 businesses across 12 grids (DHA Phase 2, Gym category)
  - All code follows contracts from Phase 0

Files Created:
  - backend/src/adapters/google_places_adapter.py (180 lines)
    - Class: GooglePlacesAdapter(BaseAdapter)
    - Key method: fetch_businesses(category: str, bounds: dict) -> List[Business]
  - backend/src/adapters/simulated_social_adapter.py (60 lines)
    - Class: SimulatedSocialAdapter(BaseAdapter)
    - Key method: fetch_social_posts(category, bounds, days) -> List[SocialPost]
  - backend/src/services/geospatial_service.py (95 lines)
    - Function: assign_grid_id(lat: float, lon: float) -> Optional[str]
  - backend/src/database/connection.py (40 lines)
    - Function: get_session() -> SQLAlchemy Session
  - backend/src/database/models.py (150 lines)
    - ORM models: GridCellModel, BusinessModel, SocialPostModel, GridMetricsModel
  - backend/scripts/fetch_google_places.py (120 lines)
  - backend/tests/adapters/test_google_places_adapter.py (95 lines)
  - backend/tests/services/test_geospatial_service.py (60 lines)

Database State After Phase 1:
  - businesses table: 73 rows
    - All assigned to grid_id correctly
    - Categories: 73 "Gym", 0 "Cafe" (will add in future)
    - Average rating: 4.1 (from Google Places)
  - social_posts table: 600 rows (unchanged from Phase 0)
  - grid_metrics table: 0 rows (Phase 2 will populate)

Key Imports for Phase 2:
  ```python
  # To query businesses
  from src.database.connection import get_session
  from src.database.models import BusinessModel, SocialPostModel, GridMetricsModel
  
  # To use Pydantic models
  from contracts.models import Business, SocialPost, GridMetrics, Category
  
  # Example query:
  session = get_session()
  gyms_in_grid = session.query(BusinessModel).filter_by(
      grid_id="DHA-Phase2-Cell-07",
      category="Gym"
  ).all()
  ```

How to Run Integration (for Phase 2 testing):
  ```powershell
  # Get all businesses for a grid
  python -c "from src.database.connection import get_session; from src.database.models import BusinessModel; session = get_session(); print(session.query(BusinessModel).filter_by(grid_id='DHA-Phase2-Cell-07').count())"
  
  # Get all social posts for a grid
  python -c "from src.database.connection import get_session; from src.database.models import SocialPostModel; session = get_session(); print(session.query(SocialPostModel).filter_by(grid_id='DHA-Phase2-Cell-07').count())"
```

Environment Variables Used:
  - GOOGLE_PLACES_API_KEY: <your-key>
  - DATABASE_URL: postgresql://postgres:postgres@localhost:5432/startsmart_dev

Next Steps for Phase 2 Developer:
  1. Create backend/src/services/aggregator.py
  2. Query BusinessModel and SocialPostModel from database
  3. Group by grid_id and category
  4. Compute metrics:
     - business_count = COUNT(businesses)
     - instagram_volume = COUNT(social_posts WHERE source='simulated' AND post_type='mention')
     - reddit_mentions = COUNT(social_posts WHERE source='simulated' AND post_type IN ('demand', 'complaint'))
  5. Create backend/src/services/scoring_service.py
  6. Implement GOS formula from STARTUP_IDEA.md Section 8
  7. Write results to grid_metrics table

Known Issues:
  - Grid DHA-Phase2-Cell-09: Only 2 businesses (edge of neighborhood, less coverage)
  - Google Places API quota: Used 12 requests (one per grid), ~240 remaining today
  - Some businesses missing ratings (10% have rating=None); handle in aggregation
  - GeospatialService edge case: Businesses on exact grid boundary assigned to first matching grid (acceptable for MVP)

Testing Results:
  - Unit tests: 23 tests, all passing
  - Coverage: 87% (adapters), 92% (geospatial service)
  - Integration test: Fetched 73 real businesses from Google Places API
  - Manual validation: Spot-checked 5 businesses on Google Maps, all locations correct

Data Quality:
  - Business names cleaned (removed extra whitespace)
  - Ratings: 66/73 have ratings, 7 are None (new businesses)
  - All coordinates within expected bounds (verified)


**Critical Information:**
- Database ORM models in `backend/src/database/models.py` — use these, not raw SQL
- Session management: Always use `get_session()` from `src/database/connection.py`
- Grid IDs are strings like "DHA-Phase2-Cell-07" (zero-padded, 2 digits)
- Category values must match enum: "Gym" or "Cafe" (case-sensitive)

**Common Errors to Avoid:**
- Don't create new Business/SocialPost classes — import from `contracts/models.py`
- Don't hardcode database connection — use `get_session()`
- Don't forget to close sessions: use context manager `with get_session() as session:`

---

### **Phase 2: Analytics & Scoring Engine** (Days 4-8)

**Owner**: Developer B

#### Goal
Implement the core intelligence layer that aggregates normalized data, computes the Gap Opportunity Score (GOS), generates confidence metrics, and attaches explainability metadata.

#### Deliverables

1. **Aggregator Module** (`src/aggregator.py`):
   - Per `grid_id` × `category`, compute:
     - `business_count`: Number of competitors
     - `instagram_volume`: Post count (last 90 days)
     - `reddit_mentions`: Demand/complaint mentions (keyword-based classification)
     - `avg_rating`, `review_count`: Weighted averages from businesses

2. **Scoring Engine** (`src/scoring.py`):
   - Normalize metrics:
     ```
     supply_norm = business_count / max(business_count across all grids)
     demand_instagram_norm = instagram_volume / max(instagram_volume)
     demand_reddit_norm = reddit_mentions / max(reddit_mentions)
     ```
   - Compute GOS:
     ```
     GOS = (1 - supply_norm) * 0.4 + demand_instagram_norm * 0.25 + demand_reddit_norm * 0.35
     ```
   - Output range: 0.0 – 1.0 (higher = better opportunity)

3. **Confidence Calculator** (`src/confidence.py`):
   - Formula:
     ```
     confidence = min(1.0, 
       log(1 + instagram_volume) / k1 + 
       log(1 + reddit_mentions) / k2 + 
       source_diversity_bonus
     )
     ```
   - Constants: `k1=5`, `k2=3`, `source_diversity_bonus=0.2` if both sources present

4. **Explainability Module** (`src/explainer.py`):
   - For each grid × category, attach:
     - **Top 3 demand posts**: Highest engagement/relevance (stored as JSON with text + link)
     - **Competitor list**: Names and distances of nearest businesses
     - **Data provenance**: Timestamp, sources used, sample size

5. **Database Updates**:
   - Populate `grid_metrics` table with:
     ```sql
     grid_id, category, business_count, instagram_volume, reddit_mentions, 
     gos, confidence, top_posts_json, last_updated
     ```

6. **Scoring Service** (`src/services/scoring_service.py`):
   - High-level API for frontend/API layer:
     - `get_top_recommendations(neighborhood, category, limit=3)`
     - `get_grid_details(grid_id, category)`
     - `recalculate_scores(neighborhood=None)` (batch processing)

7. **Automated Tests**:
   - **Synthetic data tests**: Known inputs → expected GOS (e.g., high demand + zero supply = GOS ≥ 0.8)
   - **Edge cases**: Empty grids, single-source data, outlier values
   - **Regression tests**: Lock baseline GOS for 5 reference grids; alert if formula changes results

#### Dependencies
- Completed Phase 1 (populated `businesses` and `social_posts` tables)
- Access to `grid_cells` metadata (max values for normalization)

#### Validation Criteria
- GOS scores computed for **all 60 grid cells** across 2 categories (120 scored combinations)
- **Top-3 recommendations** per neighborhood match manual validation results (≥70% agreement)
- Explainability JSON includes valid links/text for ≥90% of scored grids
- Scoring service responds in **<2 seconds** for single neighborhood query

#### Testing Approach
```powershell
# Run scoring engine with synthetic data
python src/scoring.py --mode test --input tests/fixtures/synthetic_grid_data.json

# Validate GOS computation
pytest tests/test_scoring.py -v

# Generate recommendations for pilot neighborhoods
python src/services/scoring_service.py --neighborhood "DHA Phase 2" --category Gym --top 3
```

#### Handoff Summary (for PHASE_LOG.md)
```yaml
Phase: 2 - Analytics & Scoring
Owner: Developer B
Completed:
  - Aggregator processes 60 grid cells × 2 categories
  - GOS formula implemented with configurable weights
  - Confidence scoring accounts for data volume and source diversity
  - Explainability metadata attached (top posts + competitor lists)
  - grid_metrics table populated with 120 scored records
Tests:
  - Synthetic data tests: 15 scenarios, all passing
  - Baseline regression: 5 reference grids locked
  - Performance: avg query time 1.2s for neighborhood-level aggregation
Next Steps:
  - Developer C to consume scoring_service API for frontend display
  - API layer (Phase 4) will expose REST endpoints wrapping scoring_service
Known Issues:
  - Normalization breaks if max_value = 0 (no businesses in category); added fallback to global max
  - Reddit mentions sparse for Fitness category in Saddar; GOS relies heavily on Instagram
  - Explainability JSON exceeds 10KB for high-volume grids; may need truncation for API responses
```

---

### **Phase 3: Frontend MVP Interface** (Days 8-12)

**Owner**: Developer C

#### Goal
Build an intuitive, mobile-first Flutter application that visualizes scoring results, displays recommendations, and enables user interaction with minimal backend dependencies.

#### Deliverables

1. **Flutter Project Structure**:
   ```
   frontend/
   ├── lib/
   │   ├── main.dart
   │   ├── screens/
   │   │   ├── landing_screen.dart
   │   │   ├── map_screen.dart
   │   │   ├── recommendations_screen.dart
   │   │   ├── grid_detail_screen.dart
   │   ├── widgets/
   │   │   ├── heatmap_overlay.dart
   │   │   ├── recommendation_card.dart
   │   │   ├── explanation_panel.dart
   │   ├── services/
   │   │   ├── api_service.dart (REST client)
   │   │   ├── local_data_service.dart (fallback for offline/demo mode)
   │   ├── models/
   │   │   ├── grid.dart
   │   │   ├── recommendation.dart
   ```

2. **Screen Implementations**:

   **A. Landing Screen**:
   - Welcome message + app description (1-2 sentences)
   - Category selector: Dropdown with Food/Fitness
   - Neighborhood selector: Multi-select for 1-5 neighborhoods
   - Optional: Email login via Firebase Auth
   - CTA: "Find Locations" → Navigate to Map Screen

   **B. Map Screen**:
   - **Interactive map** centered on Karachi (Flutter map plugin)
   - **Heatmap overlay**: Color-coded grid cells by GOS (red=low, green=high)
   - **Filter panel**: Category, time window (30/90 days — future feature, static for MVP)
   - **Tap interaction**: Tap grid → highlight + show quick stats (GOS, confidence)
   - **Legend**: Color scale + GOS explanation tooltip

   **C. Recommendations Panel** (bottom sheet or side panel):
   - **Top-3 grid cards** per neighborhood:
     - Grid name/ID (e.g., "DHA Phase 2 — Cell 12")
     - GOS badge (large, color-coded)
     - Confidence score (small badge)
     - 1-sentence rationale (e.g., "High demand, low competition")
   - **"View Details" button** → Navigate to Grid Detail Screen

   **D. Grid Detail Screen**:
   - **Map thumbnail**: Zoomed-in view of selected grid
   - **Metrics section**:
     - Business count + list of competitor names
     - Instagram/Reddit mention counts
     - GOS + confidence breakdown
   - **"Why this area?" panel**:
     - Top 3 social posts (text snippet + source icon + timestamp)
     - Expandable post detail (full text + link)
   - **Action buttons**:
     - "Save Location" (stores to local/Firebase for logged-in users)
     - "Give Feedback" (thumbs up/down + optional comment)

3. **API Integration** (`lib/services/api_service.dart`):
   - REST client using `http` or `dio` package
   - Endpoints (to be provided by Phase 4):
     - `GET /api/v1/grids?neighborhood=...&category=...`
     - `GET /api/v1/recommendations?neighborhood=...&category=...`
     - `GET /api/v1/grid/{grid_id}`
     - `POST /api/v1/feedback`
   - Offline mode: Load pre-exported JSON from `assets/demo_data.json`

4. **State Management**:
   - Use `Provider` or `Riverpod` for app-wide state
   - States: selected category, neighborhoods, current grid focus, recommendations cache

5. **Authentication** (minimal):
   - Firebase Auth email login (optional for MVP)
   - Guest mode: Full read access, no save/feedback features

6. **Responsive Design**:
   - Mobile-first (320px – 480px width)
   - Tablet support (landscape mode for map)
   - Web build for demo purposes (not production-critical)

#### Dependencies
- Phase 2 completed (scoring data available)
- REST API endpoints defined (can use mock responses initially)
- Firebase project created with Auth enabled

#### Validation Criteria
- App builds without errors on Android/iOS simulators
- All 4 screens navigate correctly with sample data
- Heatmap displays 60 grid cells with color gradients
- Top-3 recommendations load in **<3 seconds** (with cached backend data)
- Feedback submission succeeds (POST request logged)

#### Testing Approach
```powershell
# Run Flutter app in debug mode
cd frontend; flutter run -d chrome  # or -d android

# Widget tests for key components
flutter test test/widgets/recommendation_card_test.dart

# Integration test: full user journey
flutter test integration_test/app_test.dart

# Build for web (demo)
flutter build web --release
```

#### Handoff Summary (for PHASE_LOG.md)
```yaml
Phase: 3 - Frontend MVP
Owner: Developer C
Completed:
  - 4 screens implemented: Landing, Map, Recommendations, Grid Detail
  - Heatmap overlay with color-coded GOS visualization
  - API service with offline fallback to demo JSON
  - Firebase Auth integration (email login + guest mode)
  - Responsive design tested on mobile (360x640) and tablet (768x1024)
Tests:
  - Widget tests: 18 passing
  - Integration test: full user journey (select category → view recommendation → give feedback)
  - Manual testing: Android emulator + Chrome web build
Next Steps:
  - Developer D to implement REST API backend matching api_service.dart contracts
  - Replace demo_data.json with live API calls once endpoints are deployed
Known Issues:
  - Heatmap rendering slow (>2s) for 60 grids on low-end Android devices; needs optimization (use cached tiles)
  - Grid Detail screen shows placeholder for "Top Posts" if explainability JSON missing; add fallback UI
  - Firebase Auth logout not implemented (trivial, skipped for MVP)
```

---

### **Phase 4: API, Deployment & End-to-End Testing** (Days 12-15)

**Owner**: Developer D

#### Goal
Expose Phase 2 scoring logic via a production-ready REST API, deploy the full stack to cloud infrastructure, and validate the system end-to-end with pilot users.

#### Deliverables

1. **REST API Implementation** (`backend/api/`):

   **Framework**: FastAPI (preferred) or Flask

   **Endpoints**:

   ```python
   # GET /api/v1/neighborhoods
   # Returns: [{ "id": "DHA-Phase2", "name": "DHA Phase 2", "grid_count": 12 }]
   
   # GET /api/v1/grids?neighborhood=DHA-Phase2&category=Gym
   # Returns: [{ "grid_id": "...", "gos": 0.82, "confidence": 0.78, ... }]
   
   # GET /api/v1/recommendations?neighborhood=DHA-Phase2&category=Gym&limit=3
   # Returns top-3 grids sorted by GOS with explainability JSON
   
   # GET /api/v1/grid/{grid_id}?category=Gym
   # Returns detailed metrics + top posts + competitor list
   
   # POST /api/v1/feedback
   # Body: { "grid_id": "...", "rating": 1/-1, "comment": "..." }
   # Stores feedback in `user_feedback` table
   ```

   **Middleware**:
   - CORS (allow frontend domain)
   - Rate limiting (10 req/min per IP for free tier)
   - Request logging (JSON format to stdout)

   **Authentication**:
   - Optional: Firebase token verification for `/feedback` endpoint
   - Public read access for all GET endpoints (MVP simplification)

2. **Database Connection**:
   - Connection pooling (SQLAlchemy or psycopg2)
   - Read-only replicas for GET endpoints (if using managed DB)
   - Environment-based config (dev: SQLite, prod: PostgreSQL)

3. **API Tests**:
   - **Unit tests**: Each endpoint with mocked database
   - **Integration tests**: Full stack (DB + API) using test fixtures
   - **Load tests**: `locust` or `hey` for 100 concurrent requests

4. **Deployment Configuration**:

   **Backend** (Python API):
   - Platform: Render, GCP Cloud Run, or Heroku
   - Docker container:
     ```dockerfile
     FROM python:3.9-slim
     COPY requirements.txt .
     RUN pip install --no-cache-dir -r requirements.txt
     COPY . /app
     WORKDIR /app
     CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8080"]
     ```
   - Environment variables: `DATABASE_URL`, `FIREBASE_CONFIG`, `API_SECRET_KEY`
   - Health check endpoint: `GET /health` (returns `{"status": "ok"}`)

   **Frontend** (Flutter):
   - Web build deployed to Firebase Hosting
   - Mobile builds (optional): TestFlight (iOS) / Internal Testing (Android)

   **Database**:
   - Managed PostgreSQL (Render PostgreSQL, GCP Cloud SQL, or Supabase)
   - Automated backups enabled
   - Read-only user for analytics queries

5. **CI/CD Pipeline** (GitHub Actions):
   ```yaml
   # .github/workflows/deploy.yml
   on:
     push:
       branches: [main]
   jobs:
     test:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v3
         - name: Run backend tests
           run: pytest tests/
         - name: Run Flutter tests
           run: flutter test
     deploy:
       needs: test
       runs-on: ubuntu-latest
       steps:
         - name: Deploy to Render
           run: curl -X POST ${{ secrets.RENDER_DEPLOY_HOOK }}
   ```

6. **Monitoring & Logging**:
   - Backend: Log aggregation (Render logs or GCP Logging)
   - Frontend: Firebase Analytics for user events (page views, recommendation clicks)
   - Alerting: Simple uptime monitor (UptimeRobot or GCP Monitoring)

7. **Pilot Validation**:
   - **10 in-field validations**: Contact local entrepreneurs/users to test Top-3 recommendations
   - Survey questions:
     1. Does this location make sense for this business? (Yes/Somewhat/No)
     2. Are the reasons convincing? (Yes/No)
     3. Would you consider this location? (Yes/Maybe/No)
   - Target: ≥60% "Yes" or "Somewhat" on Q1

8. **PHASE_LOG Maintenance**:
   - Consolidate all phase handoffs into final state
   - Document deployment URLs, credentials (in secure vault), and runbook

#### Dependencies
- All prior phases completed
- Cloud accounts created (Render, Firebase, GCP)
- Domain/subdomain configured (optional: `api.startsmart.app`)

#### Validation Criteria
- API responds to all 5 endpoints with valid JSON (no 500 errors)
- Load test: 100 concurrent users → avg response time **<500ms**
- Frontend successfully loads live data from deployed API
- Pilot validation: ≥6 out of 10 users confirm recommendations are sensible
- Health check endpoint returns 200 OK for 99.9% of pings (24h test)

#### Testing Approach
```powershell
# Local API testing
uvicorn api.main:app --reload
curl http://localhost:8000/api/v1/neighborhoods

# Integration test (backend + DB)
pytest tests/integration/ -v

# Load testing
locust -f tests/load_test.py --host https://api.startsmart.app

# End-to-end test (frontend + backend)
flutter drive --driver=test_driver/integration_test.dart
```

#### Handoff Summary (for PHASE_LOG.md)
```yaml
Phase: 4 - API & Deployment
Owner: Developer D
Completed:
  - REST API implemented (5 endpoints, FastAPI)
  - Deployed to Render: https://startsmart-api.onrender.com
  - Frontend deployed to Firebase Hosting: https://startsmart-mvp.web.app
  - Database: Managed PostgreSQL on Render
  - CI/CD pipeline: GitHub Actions auto-deploy on main branch push
  - Pilot validation: 7/10 users confirmed recommendations sensible (70% precision)
Tests:
  - API unit tests: 32 passing
  - Integration tests: 8 passing
  - Load test: 100 concurrent users, avg 420ms response time
  - End-to-end: Full user journey tested on web + Android
Known Issues:
  - /api/v1/grid/{grid_id} endpoint slow (1.2s) due to join query; needs indexing optimization
  - Firebase Hosting cache aggressive; users see stale data for ~5min after backend update
  - Pilot feedback: 2 users requested "walking distance from metro" filter (future feature)
Deployment URLs:
  - API: https://startsmart-api.onrender.com
  - Frontend (web): https://startsmart-mvp.web.app
  - Docs: https://startsmart-api.onrender.com/docs (Swagger UI)
Next Steps:
  - Post-demo: Implement feedback-driven model refinement (Phase 5)
  - Scale to additional neighborhoods based on pilot learnings
```

---

## 4. Multi-Developer Collaboration Strategy

### Responsibility Matrix

| Developer | Primary Phase | Secondary Responsibilities |
|-----------|---------------|----------------------------|
| **Developer A** | Phase 1 (Data Integration) | Code reviews for Phase 2 aggregation logic |
| **Developer B** | Phase 2 (Scoring Engine) | Algorithm documentation, parameter tuning support |
| **Developer C** | Phase 3 (Frontend) | UX/UI design, user testing coordination |
| **Developer D** | Phase 4 (API & Deployment) | DevOps, PHASE_LOG maintenance, integration testing |

### Collaboration Workflow

1. **Daily Standups** (async via Slack/Discord):
   - What I completed yesterday
   - What I'm working on today
   - Blockers / help needed

2. **Phase Handoffs**:
   - Developer completes phase → updates `PHASE_LOG.md` → creates PR
   - Next developer reviews PR + PHASE_LOG → begins next phase
   - **No phase starts until previous phase PR is merged**

3. **Shared Resources**:
   - **PHASE_LOG.md**: Single source of truth for progress (read by all devs + Copilot)
   - **Shared Notion/Docs**: API contracts, data schemas, design mockups
   - **Slack channels**: `#dev-backend`, `#dev-frontend`, `#blockers`

4. **Conflict Resolution**:
   - Interface contracts (API endpoints, database schemas) locked before Phase 2 begins
   - Breaking changes require team sync + PHASE_LOG note

### Parallel Work Opportunities

While phases are sequential, some tasks can overlap:

- **Phase 1 + 2**: Developer B can start writing scoring unit tests while Developer A finalizes adapters
- **Phase 2 + 3**: Developer C can build UI with mock data while Developer B tunes scoring parameters
- **Phase 3 + 4**: Developer D can set up deployment infrastructure while Developer C finalizes frontend

**Critical Path**: Phase 1 → Phase 2 → Phase 4 (backend dependencies)  
**Parallel Track**: Phase 3 can start with mock data after Phase 1 completes

---

## 5. PHASE_LOG.md — Format, Maintenance & Critical Importance

### What is PHASE_LOG.md?

`PHASE_LOG.md` is the **single source of truth** for project state and progress. It serves as:
- **Memory** for Copilot/LLMs across sessions
- **Handoff documentation** between developers
- **Audit trail** for instructors and judges
- **Integration guide** for continuity across phases

### CRITICAL: Auto-Update Requirement

**At the end of EACH phase**, the developer MUST update `PHASE_LOG.md` with a comprehensive handoff entry. This is NOT optional.

**How to ensure updates**: Each phase's final prompt (in `phase_N_prompts.md`) includes explicit instructions to update PHASE_LOG.

### Required Format for Each Phase Entry

```yaml
# PHASE_LOG.md

## Phase 0: Contracts, Synthetic Data & Manual Validation
Owner: [Developer Name]
Completed: 2025-11-XX
Status: ✅ Complete

### Summary
- Created 4 contract files (database schema, API spec, models, base adapter)
- Generated synthetic dataset: 600 social posts across 12 grids
- Seeded database with grid cells and synthetic posts
- Manual validation: 2/3 entrepreneurs confirmed high-GOS grids are underserved

### Files Created
```
contracts/
  database_schema.sql (150 lines) - PostgreSQL schema for all tables
  api_spec.yaml (200 lines) - OpenAPI 3.0 specification
  models.py (120 lines) - Pydantic models for type safety
  base_adapter.py (45 lines) - Abstract adapter interface

config/
  neighborhoods.json (30 lines) - Grid definitions for DHA Phase 2

scripts/
  generate_synthetic_data.py (180 lines) - Synthetic post generator
  seed_grids.py (80 lines) - Populate grid_cells table
  seed_synthetic_posts.py (60 lines) - Load synthetic posts into DB

data/synthetic/
  social_posts_v1.json (600 records) - Simulated social media data
```

### Database State
- Tables created: grid_cells, businesses, social_posts, grid_metrics, user_feedback
- grid_cells: 12 rows (DHA Phase 2 only)
- social_posts: 600 rows (is_simulated = TRUE)
- businesses: 0 rows (Phase 1 will populate)

### Key Decisions & Configurations
- Grid size: 0.5 km²
- Categories: Gym, Cafe (locked for MVP)
- Grid ID format: "{neighborhood}-Cell-{01-12}" (e.g., "DHA-Phase2-Cell-07")
- Database: PostgreSQL (connection string in .env)

### Exact Imports for Next Phase
```python
# Import contracts
from contracts.models import Business, SocialPost, GridCell, Category, Source
from contracts.base_adapter import BaseAdapter

# Database connection
from src.database.connection import get_session

# Example query
session = get_session()
grids = session.query(GridCellModel).filter_by(neighborhood='DHA-Phase2').all()
```

### How to Run/Test
```powershell
# Initialize database
python scripts/init_db.py

# Generate synthetic data
python scripts/generate_synthetic_data.py --grids 12 --posts-per-grid 50

# Seed database
python scripts/seed_grids.py --config config/neighborhoods.json
python scripts/seed_synthetic_posts.py --input data/synthetic/social_posts_v1.json

# Verify
psql startsmart_dev -c "SELECT COUNT(*) FROM grid_cells;"  # Should return 12
psql startsmart_dev -c "SELECT COUNT(*) FROM social_posts;"  # Should return 600+
```

### Environment Variables
```
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/startsmart_dev
LOG_LEVEL=INFO
```

### Next Steps for Phase 1 Developer
1. Create backend/src/adapters/ directory structure
2. Implement GooglePlacesAdapter extending BaseAdapter
3. Implement SimulatedSocialAdapter (reads from social_posts table)
4. Create GeospatialService for point-in-polygon grid assignment
5. Populate businesses table with real Google Places data
6. Target: ≥60 businesses across 12 grids

### Known Issues & Workarounds
- Grid DHA-Phase2-Cell-09 near neighborhood edge; point-in-polygon may have 2% error margin
- Synthetic data heavily weighted toward "demand" posts; future versions should balance
- PostgreSQL Docker container uses port 5432; may conflict with local installations
  * Workaround: Change docker-compose port mapping to 5433:5432

### Testing Completed
- Manual: Verified grid generation covers full neighborhood area
- Manual: Spot-checked 20 synthetic posts for realism
- Validation: 2/3 local gym owners confirmed Cell-07 is underserved (high GOS expected)

### Performance Metrics
- Synthetic data generation: 3 seconds for 600 posts
- Database seeding: <1 second for all tables
- Total Phase 0 duration: 2.5 days (including manual validation)

---

## Phase 1: Data Integration & Normalization
Owner: [Developer Name]
Completed: 2025-11-XX
Status: ✅ Complete

[Follow same format as Phase 0...]

---
```

### Update Triggers

Developers **MUST** update PHASE_LOG.md when:

1. **Completing a phase** (most critical)
   - Use the template from IMPLEMENTATION_PLAN.md for that phase
   - Fill in ALL sections (no placeholders)
   - Include actual line counts, row counts, test results

2. **Discovering critical blockers**
   - Add to "Known Issues" immediately
   - Document workaround if found

3. **Making architectural changes**
   - Example: Switching from SQLite to PostgreSQL
   - Document in "Key Decisions"

4. **Adding new dependencies**
   - Update requirements.txt
   - Document why needed in PHASE_LOG

### How Copilot/LLMs Use PHASE_LOG

When starting a new phase, the prompt will instruct Copilot to:

1. **Read PHASE_LOG.md first**
2. **Identify the last completed phase**
3. **Read the "Next Steps" section** of that phase
4. **Check "Known Issues"** to avoid assumptions
5. **Use "Exact Imports"** to maintain consistency
6. **Follow "How to Run/Test"** to verify progress

**Example Copilot prompt (built into phase_N_prompts.md)**:
> "Read PHASE_LOG.md to understand the current state. Phase 1 is complete. I am implementing Phase 2. Use the database models and imports documented in Phase 1 handoff."

### PHASE_LOG vs. Phase Prompts Files

| File | Purpose | Updated When | Read By |
|------|---------|--------------|---------|
| **PHASE_LOG.md** | Project state & handoffs | After each phase complete | All developers + Copilot |
| **phase_N_prompts.md** | Step-by-step implementation instructions | Never (static guide) | Developer implementing phase N |
| **IMPLEMENTATION_PLAN.md** | Overall strategy & architecture | Rarely (major scope changes) | All team members initially |

---

## 6. Testing & Integration Strategy

### Phase-Level Validation (Continuous)

Each phase includes built-in validation criteria (see phase sections above). General principles:

1. **Unit Tests**: Cover individual functions/classes in isolation
   - Target: ≥80% code coverage
   - Tools: `pytest` (Python), `flutter test` (Dart)

2. **Integration Tests**: Verify module interactions
   - Example: Normalizer + Database write
   - Example: API endpoint + Scoring service

3. **Smoke Tests**: Quick end-to-end checks
   - Can the app load?
   - Does the API return 200 OK?

### Final Integration Testing (End of Phase 4)

**Objective**: Validate complete user journeys with real data flow.

#### Test Scenarios

1. **Happy Path**:
   - User selects "Gym" + "DHA Phase 2"
   - Map displays heatmap
   - Recommendations panel shows Top-3 grids
   - User clicks grid → Detail screen loads
   - User submits feedback → Success toast

2. **Edge Cases**:
   - Empty category (no businesses) → Show "No data" message
   - Network failure → Offline mode with cached data
   - Invalid grid_id → 404 error with user-friendly message

3. **Performance**:
   - Map with 60 grids loads in <3s
   - API response time <500ms (p95)
   - Frontend memory usage <150MB

#### Automated E2E Tests

```powershell
# Backend E2E
pytest tests/e2e/test_full_pipeline.py --live-db

# Frontend E2E (Flutter Driver)
flutter drive --target=test_driver/app.dart
```

#### Manual Testing Checklist

- [ ] Install app on 2 physical devices (Android + iOS or web)
- [ ] Test all 4 screens with live backend
- [ ] Submit feedback → verify in database
- [ ] Test with slow network (3G simulation)
- [ ] Check accessibility (screen reader, font scaling)

### Pilot User Testing

**Timeline**: Days 13-14 (during Phase 4)

**Process**:
1. Recruit 10 local entrepreneurs (via LinkedIn, WhatsApp groups, university entrepreneurship club)
2. Send app link + 5-minute demo video
3. Ask them to test 2 categories in their preferred neighborhood
4. Collect feedback via Google Form:
   - Does the top recommendation make sense? (1-5 scale)
   - Would you visit this location to scout? (Yes/No)
   - Any missing information? (Free text)

**Success Metric**: ≥60% rate Top-1 recommendation as 4 or 5 (sensible/very sensible)

---

## 7. Future Architectural Considerations

### Design Patterns & SOLID Principles (Post-MVP)

While MVP prioritizes speed and pragmatism, the architecture is designed to accommodate principled refactoring:

#### Current Simplifications → Future Patterns

| Current (MVP) | Future Refactor | Pattern/Principle |
|---------------|-----------------|-------------------|
| Hardcoded adapter list in normalizer | Adapter registry with dependency injection | **Factory Pattern**, **DIP** |
| Single scoring formula in `scoring.py` | Pluggable scoring strategies | **Strategy Pattern**, **OCP** |
| Direct database queries in API | Repository layer + business logic services | **Repository Pattern**, **SRP** |
| Static grid definitions | Dynamic grid generation from shapefiles | **Builder Pattern** |
| Monolithic API in `main.py` | Modular routers (neighborhoods, grids, feedback) | **Separation of Concerns** |

#### Extensibility Points

1. **Multi-City Expansion**:
   - Current: Grid cells hardcoded for Karachi neighborhoods
   - Future: Abstract `CityConfig` class with city-specific grid generators and data sources
   - Pattern: **Template Method** for city initialization

2. **Advanced Analytics**:
   - Current: Simple weighted sum for GOS
   - Future: ML model (XGBoost, neural net) trained on historical business success data
   - Pattern: **Strategy Pattern** for swappable scoring algorithms

3. **Real-Time Data**:
   - Current: Batch processing (manual refresh)
   - Future: Streaming ingestion from social APIs + incremental scoring updates
   - Pattern: **Observer Pattern** for score invalidation on new data

4. **Multi-Tenancy**:
   - Current: Single shared database
   - Future: Per-organization data isolation for B2B customers
   - Pattern: **Tenant Context** middleware + row-level security

### Modularity Checkpoints

To ensure refactoring readiness, each module should follow:

- **Single Responsibility**: Each file/class has one clear purpose
- **Interface Segregation**: APIs expose minimal required methods (e.g., adapter interface: `fetch()`, `normalize()`)
- **Dependency Inversion**: High-level modules (scoring) depend on abstractions (data interfaces), not concrete adapters

**Example (Python)**:
```python
# Bad (MVP but tightly coupled)
from adapters.google_places import GooglePlacesAdapter
def get_businesses():
    return GooglePlacesAdapter().fetch()

# Good (interface-based, testable)
from adapters.base import DataAdapter
def get_businesses(adapter: DataAdapter):
    return adapter.fetch()
```

---

## 8. Deployment & Operational Runbook

### Pre-Deployment Checklist

- [ ] All tests passing (unit + integration + E2E)
- [ ] Environment variables configured in hosting platform
- [ ] Database migrations applied to production DB
- [ ] API rate limits configured
- [ ] Firebase project quota checked (auth, hosting)
- [ ] Backup strategy confirmed (daily DB snapshots)

### Deployment Steps (Phase 4)

#### Backend Deployment (Render / GCP Cloud Run)

```powershell
# Option 1: Render (Git-based deploy)
git push origin main  # Render auto-deploys from main branch

# Option 2: GCP Cloud Run (Docker)
docker build -t gcr.io/startsmart/api:latest .
docker push gcr.io/startsmart/api:latest
gcloud run deploy startsmart-api --image gcr.io/startsmart/api:latest --region us-central1
```

#### Frontend Deployment (Firebase Hosting)

```powershell
cd frontend
flutter build web --release
firebase deploy --only hosting
```

#### Database Setup (Managed PostgreSQL)

```powershell
# Create database on Render/GCP
# Copy connection string to .env as DATABASE_URL

# Run migrations
python -m alembic upgrade head

# Seed with grid definitions
python scripts/seed_grids.py --neighborhoods config/neighborhoods.json
```

### Monitoring & Alerts

**Uptime Monitoring**:
- Tool: UptimeRobot (free tier)
- Checks: `/health` endpoint every 5 minutes
- Alert: Email + Slack if downtime >2 minutes

**Error Tracking**:
- Backend: Sentry (Python SDK)
- Frontend: Firebase Crashlytics

**Usage Metrics**:
- Firebase Analytics: Track events (`recommendation_viewed`, `feedback_submitted`)
- API logs: Daily request counts by endpoint

### Rollback Procedure

If deployment fails:
1. Revert Git commit: `git revert <commit-hash>`
2. Redeploy previous version
3. Check database migrations (may need manual rollback)
4. Notify team in `#incidents` Slack channel

---

## 9. MVP Success Criteria (Final)

At the end of Phase 4, the MVP is considered **complete** if:

### Functional Requirements
- ✅ Live deployed app accessible via public URL (web + mobile)
- ✅ Supports 2 categories (Food, Fitness) × 5 neighborhoods × ~60 grids
- ✅ Displays interactive heatmap with color-coded GOS
- ✅ Shows Top-3 recommendations per neighborhood with explainability
- ✅ Users can view grid details (competitors, social posts, metrics)
- ✅ Feedback submission works and data persists in database

### Quality Requirements
- ✅ Recommendation precision: ≥60% validated by pilot users
- ✅ API response time: p95 <500ms
- ✅ Frontend load time: <3s on 4G mobile
- ✅ Test coverage: ≥80% for backend, ≥70% for frontend
- ✅ Zero critical bugs (crashes, data corruption) in pilot testing

### Documentation Requirements
- ✅ `PHASE_LOG.md` updated with all 4 phases
- ✅ API documentation (Swagger/Postman collection)
- ✅ README with setup instructions for new developers
- ✅ Pilot validation results documented (survey responses)

### Demo Readiness
- ✅ 5-minute live demo script prepared
- ✅ Demo data pre-loaded (avoid live API latency during presentation)
- ✅ Backup video recording in case of network issues
- ✅ Slide deck explaining architecture + validation results

---

## 10. Post-MVP Roadmap (Phase 5+)

### Immediate Enhancements (Week 3-4)
1. **Feedback Loop**: Use collected feedback to retrain/tune scoring weights
2. **Additional Categories**: Retail, Health & Beauty (3 more categories)
3. **Temporal Analysis**: Show GOS trends over time (e.g., "opportunity increased 15% last month")
4. **Export Features**: PDF reports of top recommendations for offline use

### Medium-Term (Month 2-3)
1. **Multi-City Expansion**: Lahore, Islamabad (replicate pipeline)
2. **Advanced Filters**: Budget constraints, proximity to transit, foot traffic estimates
3. **ML-Based Scoring**: Replace manual weights with trained model (historical success data)
4. **B2B Portal**: Dashboard for real estate consultants to generate reports for clients

### Long-Term (Month 4+)
1. **Predictive Analytics**: Forecast future opportunity based on development trends
2. **Partnership Integrations**: Real estate listings, business loan providers
3. **Community Features**: User-contributed reviews, location scouting photos
4. **White-Label Solution**: Customizable platform for other cities/countries

---

## 11. Appendix

### A. Key Configuration Files

**`.env` (Backend)**:
```bash
DATABASE_URL=postgresql://user:pass@host:5432/startsmart
GOOGLE_PLACES_API_KEY=AIza...
FIREBASE_CONFIG={"projectId":"startsmart-mvp",...}
API_SECRET_KEY=<random-256-bit-key>
ENVIRONMENT=production
```

**`config/neighborhoods.json`**:
```json
[
  {
    "id": "DHA-Phase2",
    "name": "DHA Phase 2",
    "bounds": {
      "north": 24.8345,
      "south": 24.8210,
      "east": 67.0670,
      "west": 67.0520
    },
    "grid_size_km": 0.5
  }
]
```

### B. API Response Examples

**GET /api/v1/recommendations?neighborhood=DHA-Phase2&category=Gym&limit=3**:
```json
{
  "neighborhood": "DHA Phase 2",
  "category": "Gym",
  "recommendations": [
    {
      "grid_id": "DHA-Phase2-Cell-12",
      "gos": 0.82,
      "confidence": 0.78,
      "rationale": "High demand (48 Instagram posts), low competition (2 gyms)",
      "lat_center": 24.8275,
      "lon_center": 67.0595
    }
  ]
}
```

### C. Testing Data Fixtures

**`tests/fixtures/synthetic_grid_data.json`**:
```json
{
  "grid_id": "Test-Grid-1",
  "business_count": 0,
  "instagram_volume": 50,
  "reddit_mentions": 10,
  "expected_gos": 0.85
}
```

---

## Document Maintenance

**Owner**: Developer D (Phase 4)  
**Last Updated**: 2025-11-04  
**Version**: 1.0 (MVP)  

**Change Log**:
- 2025-11-04: Initial implementation plan created
- Future updates: Document all major architectural changes here

---

**Next Steps**: Begin Phase 0 (Manual Validation) and update `PHASE_LOG.md` upon completion.
