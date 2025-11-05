# Phase 0: Contracts, Synthetic Data & Manual Validation

**READ THIS FIRST**: This file contains sequential prompts to implement Phase 0. Feed these to GitHub Copilot **one by one**, in order. After completing all prompts, update `PHASE_LOG.md` with the handoff template from `IMPLEMENTATION_PLAN.md` (Phase 0 section).

---

## Prompt 1: Create Contract Files (Database Schema & API Spec)

```
I am implementing Phase 0 of the StartSmart MVP project. This phase establishes all interface contracts that later phases will implement against.

Please create the following files exactly as specified:

1. Create `contracts/database_schema.sql` with the complete PostgreSQL schema including:
   - grid_cells table (grid_id PK, neighborhood, lat/lon bounds, area_km2)
   - businesses table (business_id PK, name, lat, lon, category, rating, review_count, source, grid_id FK, fetched_at)
   - social_posts table (post_id PK, source, text, timestamp, lat, lon, grid_id FK, post_type, engagement_score, is_simulated, created_at)
   - grid_metrics table (id SERIAL PK, grid_id FK, category, business_count, instagram_volume, reddit_mentions, gos, confidence, top_posts_json JSONB, competitors_json JSONB, last_updated)
   - user_feedback table (id SERIAL PK, grid_id FK, category, rating CHECK IN (-1,1), comment, user_email, created_at)
   - All necessary indexes for performance

2. Create `contracts/api_spec.yaml` as an OpenAPI 3.0 specification with:
   - 5 endpoints: GET /neighborhoods, GET /grids, GET /recommendations, GET /grid/{grid_id}, POST /feedback
   - Complete request/response schemas
   - Example values for all fields

Use the exact specifications from Section 3 of IMPLEMENTATION_PLAN.md. These contracts are LOCKED and cannot be changed in later phases.
```

---

## Prompt 2: Create Pydantic Models and Base Adapter Interface

```
Continuing Phase 0 implementation.

Please create:

1. `contracts/models.py` containing:
   - Enums: Category (Gym, Cafe), Source (google_places, instagram, reddit, simulated), PostType (demand, complaint, mention)
   - Pydantic models matching the database schema: GridCell, Business, SocialPost, GridMetrics
   - API response models: GridSummaryResponse, RecommendationResponse, GridDetailResponse, NeighborhoodResponse, TopPostDetail, CompetitorDetail
   - All models must use proper type hints (Optional, List, etc.)
   - Include Field validators where appropriate (e.g., rating between 0-5)

2. `contracts/base_adapter.py` containing:
   - Abstract base class BaseAdapter with ABC
   - Abstract methods: fetch_businesses(category, bounds) -> List[Business], fetch_social_posts(category, bounds, days) -> List[SocialPost], get_source_name() -> str
   - Comprehensive docstrings explaining each method's contract

All code must follow Python 3.10+ standards with type hints.
```

---

## Prompt 3: Create Neighborhood Configuration

```
Create the neighborhood and grid configuration file.

Please create `config/neighborhoods.json` with:
- Single neighborhood for MVP: DHA Phase 2, Karachi
- Bounds: lat_north 24.8345, lat_south 24.8210, lon_east 67.0670, lon_west 67.0520
- Grid size: 0.5 km²
- Calculate and specify grid_count (should be ~12 grids)
- Categories: ["Gym", "Cafe"]

The file should be structured as a JSON object with a "neighborhoods" array and a "categories" array.

Also create a simple Python script `scripts/calculate_grid_count.py` that:
- Reads the neighborhoods.json file
- Calculates how many 0.5km² grids fit in the given bounds
- Prints the result to verify our 12-grid estimate is correct
```

---

## Prompt 4: Create Synthetic Data Generator

```
Create a realistic synthetic data generator for social media posts.

Please create `scripts/generate_synthetic_data.py` that:

1. Accepts command-line arguments:
   --grids (number of grid cells, default 12)
   --posts-per-grid (average posts per grid, default 50)
   --output (output directory, default data/synthetic/)

2. Generates synthetic social posts with realistic distribution:
   - 60% "mention" type posts (general discussion about category)
   - 25% "demand" type posts (explicit requests for businesses)
   - 15% "complaint" type posts (complaints about lack of options)

3. For each grid, vary the distribution to create opportunity signals:
   - High-opportunity grids (25%): More demand/complaint posts, higher engagement
   - Medium grids (50%): Balanced distribution
   - Low-opportunity grids (25%): Fewer posts overall

4. Each post should have:
   - post_id (UUID)
   - source (always "simulated" for MVP)
   - text (realistic text mentioning the category, e.g., "Looking for a good gym in Phase 2")
   - timestamp (random date within last 90 days)
   - lat/lon (random point within grid bounds)
   - grid_id (assigned grid)
   - post_type (demand/complaint/mention)
   - engagement_score (random 0-100, weighted higher for high-opportunity grids)
   - is_simulated (always TRUE)

5. Output format: JSON array of posts saved to specified output path

6. Include seed for reproducibility

Use Python with standard libraries (json, random, datetime, argparse, uuid). Include helpful logging to show progress.
```

---

## Prompt 5: Create Database Seeding Scripts

```
Create scripts to initialize and populate the database.

Please create:

1. `scripts/seed_grids.py`:
   - Reads config/neighborhoods.json
   - For each neighborhood, generates grid cells (0.5km² each)
   - Calculates lat/lon bounds for each grid
   - Assigns grid_id in format: "{neighborhood}-Cell-{01-12}"
   - Inserts into grid_cells table using PostgreSQL connection
   - Accepts --config argument for config file path
   - Includes proper error handling and transaction management

2. `scripts/seed_synthetic_posts.py`:
   - Reads JSON file from --input argument
   - Validates each post against the schema
   - Bulk inserts into social_posts table
   - Prints summary statistics (total posts, posts per grid, distribution by type)
   - Includes progress bar for large datasets

Both scripts should:
- Use environment variables for DATABASE_URL
- Include proper connection handling (psycopg2 or SQLAlchemy)
- Have --dry-run option to preview without inserting
- Log all operations clearly

Dependencies: psycopg2-binary, python-dotenv
```

---

## Prompt 6: Create Environment Setup Files

```
Create the development environment setup files.

Please create:

1. `.env.example` with all required environment variables:
   ```
   DATABASE_URL=postgresql://postgres:postgres@localhost:5432/startsmart_dev
   GOOGLE_PLACES_API_KEY=your_key_here
   ENVIRONMENT=development
   LOG_LEVEL=INFO
   ```

2. `requirements.txt` for Python dependencies (Phase 0 only):
   ```
   fastapi==0.104.1
   uvicorn[standard]==0.24.0
   sqlalchemy==2.0.23
   psycopg2-binary==2.9.9
   pydantic==2.5.0
   python-dotenv==1.0.0
   googlemaps==4.10.0
   shapely==2.0.2
   pytest==7.4.3
   pytest-cov==4.1.0
   black==23.11.0
   flake8==6.1.0
   ```

3. `docker-compose.yml` for local PostgreSQL:
   - PostgreSQL 14 image
   - Port 5432
   - Volume for data persistence
   - Default credentials: postgres/postgres
   - Database name: startsmart_dev

4. `.gitignore` for Python project:
   - Include: __pycache__, .env, venv/, *.pyc, .pytest_cache/, .coverage, data/raw/, data/synthetic/
```

---

## Prompt 7: Initialize Database and Run Validation

```
Create database initialization script and validation documentation.

Please create:

1. `scripts/init_db.py`:
   - Reads contracts/database_schema.sql
   - Connects to PostgreSQL using DATABASE_URL from .env
   - Executes the schema to create all tables
   - Includes --drop-existing flag to drop all tables first (for clean resets)
   - Verifies tables created successfully
   - Prints summary of all tables and row counts

2. `docs/phase0_validation.md`:
   - Template for manual validation results
   - Sections for:
     * Validation methodology (how you picked grids, counted businesses)
     * 3 sample grids with manual business counts
     * Hand-calculated GOS for each grid
     * Feedback from local entrepreneurs (template for interview notes)
     * Conclusions about GOS formula accuracy
   - Include instructions for future validators

After creating these files, you should:
1. Run docker-compose up -d postgres
2. Run python scripts/init_db.py
3. Run python scripts/generate_synthetic_data.py --grids 12 --posts-per-grid 50
4. Run python scripts/seed_grids.py --config config/neighborhoods.json
5. Run python scripts/seed_synthetic_posts.py --input data/synthetic/social_posts_v1.json
6. Verify data: psql startsmart_dev -c "SELECT COUNT(*) FROM grid_cells;"

Document the results in phase0_validation.md.
```

---

## Prompt 8: Update PHASE_LOG.md

```
Phase 0 is now complete. Create the PHASE_LOG.md file with the handoff entry.

Please create `PHASE_LOG.md` following the exact format from IMPLEMENTATION_PLAN.md Phase 0 "Handoff to Phase 1" section.

Fill in:
- Your name as owner
- Today's date as completion date
- Actual file names and line counts (use wc -l or similar)
- Actual database row counts (query the database)
- Any issues you encountered
- Exact import statements for Phase 1 developer
- Clear next steps

This file will be the single source of truth for all future phases. Be comprehensive and precise.
```

---

## Phase 0 Completion Checklist

Before moving to Phase 1, verify:

- [ ] All contract files created in `contracts/` directory
- [ ] Neighborhood configuration in `config/neighborhoods.json`
- [ ] Synthetic data generator working and produces 500+ posts
- [ ] Database initialized with all 5 tables
- [ ] grid_cells table has 12 rows
- [ ] social_posts table has 500+ rows with is_simulated = TRUE
- [ ] All scripts have --help documentation
- [ ] PHASE_LOG.md created with comprehensive handoff
- [ ] .env file created from .env.example with real values
- [ ] Docker PostgreSQL running and accessible
- [ ] Manual validation documented in docs/phase0_validation.md

**IMPORTANT**: Do NOT proceed to Phase 1 until PHASE_LOG.md is complete and reviewed by team.
