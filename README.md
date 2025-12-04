# StartSmart MVP

**Location-based business opportunity finder for aspiring entrepreneurs in Karachi, Pakistan**

[![Phase 0](https://img.shields.io/badge/Phase%200-Complete-success)](PHASE_LOG.md)
[![Python](https://img.shields.io/badge/Python-3.10+-blue)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14+-blue)](https://www.postgresql.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green)](https://fastapi.tiangolo.com/)
[![Flutter](https://img.shields.io/badge/Flutter-3.0+-blue)](https://flutter.dev/)

---

## 🎯 Project Vision

StartSmart helps aspiring entrepreneurs in Karachi identify high-opportunity locations to open new businesses (Gyms and Cafes) by analyzing:
- **Business density** from Google Places API
- **Social media demand signals** from platforms like Instagram and Reddit
- **Geographic opportunity scores** calculated for 0.5 km² grid cells

**Target User**: First-time entrepreneurs seeking data-driven insights for business location decisions.

---

## 📐 Architecture Overview

### System Design
```
┌─────────────────────────────────────────────────────────┐
│                    Flutter Mobile App                    │
│              (Phase 4 - User Interface)                  │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│                  FastAPI REST API                        │
│         (Phase 3 - Backend Server on Render)             │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│              Opportunity Scoring Engine                  │
│    (Phase 2 - Calculate GOS from business + social)      │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│                 PostgreSQL Database                      │
│          (PostGIS - Grid cells, businesses,              │
│           social posts, metrics, feedback)               │
└──────────┬──────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────┐
│                   Data Adapters                          │
│      (Phase 1 - Google Places + Social Media)            │
│   ┌─────────────────┐      ┌──────────────────┐         │
│   │ Google Places   │      │ Simulated Social │         │
│   │    Adapter      │      │     Adapter      │         │
│   └─────────────────┘      └──────────────────┘         │
└─────────────────────────────────────────────────────────┘
```

### Technology Stack

**Backend**:
- Python 3.10+ with FastAPI
- PostgreSQL 14+ with PostGIS extension
- Pydantic v2 for data validation
- SQLAlchemy for ORM

**Data Sources** (Phase 1):
- Google Places API (business locations)
- Simulated social media posts (synthetic dataset for testing)

**Frontend** (Phase 4):
- Flutter 3.0+ for cross-platform mobile app
- Responsive UI with map integration

**Infrastructure**:
- Database: PostgreSQL on local/cloud
- Backend API: Render.com deployment
- Version Control: GitHub

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10 or higher
- PostgreSQL 14+ (or use Docker)
- Git

### 1. Clone Repository
```bash
git clone https://github.com/Danish-Ahmed007/Start-Smart.git
cd Start-Smart
```

### 2. Set Up Environment
### 2. Set Up Environment
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings
# DATABASE_URL=postgresql://postgres:your_password@localhost:5432/startsmart_dev
# GOOGLE_PLACES_API_KEY=your_key_here (for Phase 1)
# GROQ_API_KEY=your_groq_key_here (for LLM recommendations)
```

### 3. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 4. Database Setup

**Note**: Phase 0 database is already set up with:
- ✅ 5 tables created (grid_cells, businesses, social_posts, grid_metrics, user_feedback)
- ✅ 9 grid cells populated (DHA Phase 2)
- ✅ 460 synthetic social posts loaded
- ✅ PostgreSQL 14+ with PostGIS running locally

**To verify your setup:**
```bash
# Check grid cells (should return 9)
python -c "import psycopg2; from dotenv import load_dotenv; import os; load_dotenv(); conn = psycopg2.connect(os.getenv('DATABASE_URL')); cur = conn.cursor(); cur.execute('SELECT COUNT(*) FROM grid_cells'); print(f'Grid cells: {cur.fetchone()[0]}'); conn.close()"

# Check social posts (should return 460)
python -c "import psycopg2; from dotenv import load_dotenv; import os; load_dotenv(); conn = psycopg2.connect(os.getenv('DATABASE_URL')); cur = conn.cursor(); cur.execute('SELECT COUNT(*) FROM social_posts'); print(f'Social posts: {cur.fetchone()[0]}'); conn.close()"
```

---

## 📂 Project Structure

```
Start-Smart/
├── contracts/               # 🔒 LOCKED - Interface contracts (Phase 0)
│   ├── database_schema.sql  # PostgreSQL schema with PostGIS
│   ├── api_spec.yaml        # OpenAPI 3.0 REST API specification
│   ├── models.py            # Pydantic data models
│   └── base_adapter.py      # Abstract adapter interface
├── config/
│   └── neighborhoods.json   # Neighborhood definitions (DHA Phase 2)
├── scripts/
│   ├── calculate_grid_count.py      # Grid calculation validator
│   ├── generate_synthetic_data.py   # Synthetic post generator
│   ├── init_db.py                   # Database initializer
│   ├── seed_grids.py                # Grid cell seeder
│   └── seed_synthetic_posts.py      # Social posts seeder
├── docs/
│   ├── phase0_validation.md         # Validation methodology
│   └── RECOMMENDATION_ENGINE.md     # LLM Recommendation Engine docs
├── data/
│   └── synthetic/
│       └── social_posts_v1.json     # 460 synthetic posts (163 KB)
├── .env.example             # Environment variables template
├── requirements.txt         # Python dependencies
├── docker-compose.yml       # PostgreSQL + pgAdmin setup
├── .gitignore
├── PHASE_LOG.md            # Phase completion handoff
├── PHASE_0_COMPLETE.md     # Phase 0 summary
└── README.md               # This file
```

---

## 🗺️ Current Scope (MVP)

### Geographic Coverage
- **Neighborhood**: DHA Phase 2, Karachi
- **Bounds**: 24.8210°N - 24.8345°N, 67.0520°E - 67.0670°E
- **Grid Layout**: 3×3 (9 cells), each 0.5 km²
- **Opportunity Levels**: High (2 grids), Medium (4 grids), Low (3 grids)

### Business Categories
- Gyms
- Cafes

### Data Sources
- Google Places API (real business locations)
- Simulated social media (synthetic posts for testing)

---

## 🏗️ Implementation Phases

### ✅ Phase 0: Interface Contracts & Data Generation (COMPLETE)
**Status**: Complete (November 6, 2025)  
**Developer**: GitHub Copilot + Danish Ahmed  
**Database**: Local PostgreSQL (startsmart_dev)  

**Deliverables**:
- ✅ Database schema with 5 tables (142 lines)
- ✅ OpenAPI 3.0 REST API specification (612 lines)
- ✅ Pydantic models and adapter interfaces (408 + 330 lines)
- ✅ Grid configuration for DHA Phase 2 (9 grids)
- ✅ Synthetic data generator (460 posts)
- ✅ Database initialized and seeded
  - 9 grid cells populated
  - 460 social posts loaded
  - All tables created and verified

**Details**: See [PHASE_LOG.md](PHASE_LOG.md)

### ⏳ Phase 1: Data Adapters (NEXT)
**Goal**: Fetch and store business and social media data  
**Tasks**:
1. Implement `GooglePlacesAdapter` (extends `BaseAdapter`)
2. Implement `SimulatedSocialAdapter` (queries synthetic posts)
3. Create data pipeline script (`scripts/fetch_and_store.py`)
4. Add duplicate detection and error handling

**Dependencies**: Phase 0 complete, Google Places API key required

### 🔜 Phase 2: Opportunity Scoring
**Goal**: Calculate Grid Opportunity Score (GOS)  
**Tasks**:
1. Implement GOS calculation algorithm
2. Populate `grid_metrics` table
3. Create scoring script with periodic updates
4. Add business recommendation logic

**Formula**: `GOS = (business_density × 0.4) + (avg_social_score × 0.3) + (demand_signal × 0.3)`

### 🔜 Phase 3: REST API
**Goal**: Build FastAPI backend matching contracts/api_spec.yaml  
**Tasks**:
1. Implement 5 API endpoints
2. Add database query optimization
3. Deploy to Render.com
4. Set up CORS for Flutter app

### 🔜 Phase 4: Flutter Frontend
**Goal**: Mobile app for entrepreneurs  
**Tasks**:
1. Build map view with grid cells
2. Create recommendation cards UI
3. Add feedback submission
4. Deploy to Play Store (Android)

---

## 🧪 Testing

### Database Scripts (Dry-Run Mode)
```bash
# Test grid seeding without database changes
python scripts/seed_grids.py --dry-run

# Test post seeding with validation
python scripts/seed_synthetic_posts.py --input data/synthetic/social_posts_v1.json --dry-run
```

### Unit Tests (Phase 1+)
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html
```

### Validation
See `docs/phase0_validation.md` for manual validation procedures including:
- Hand-calculated grid bounds verification
- GOS formula testing with sample data
- Entrepreneur feedback collection

---

## 📊 Database Schema

### Tables (5)
1. **grid_cells** - Geographic grid cells (0.5 km² each)
2. **businesses** - Business locations from Google Places
3. **social_posts** - Social media posts with geotags
4. **grid_metrics** - Calculated opportunity scores
5. **user_feedback** - User ratings of recommendations

### Key Relationships
- `social_posts.grid_id` → `grid_cells.grid_id`
- `businesses.grid_id` → `grid_cells.grid_id`
- `grid_metrics.grid_id` → `grid_cells.grid_id`
- `user_feedback.grid_id` → `grid_cells.grid_id`

**Schema Details**: See `contracts/database_schema.sql`

---

## 🔌 API Endpoints (Phase 3)

### Base URL
- **Local**: `http://localhost:8000/api/v1`
- **Production**: `https://startsmart-api.onrender.com/api/v1`

### Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/neighborhoods` | List all neighborhoods |
| GET | `/grids` | Get grid cells for neighborhood |
| GET | `/recommendations` | Get business recommendations |
| GET | `/grid/{grid_id}` | Get detailed grid information |
| POST | `/feedback` | Submit user feedback |

**API Specification**: See `contracts/api_spec.yaml`

---

## 🤝 Contributing

### Workflow
1. **Branch**: Create feature branch from `main`
2. **Develop**: Implement changes
3. **Test**: Run tests and validation
4. **Commit**: Use conventional commit messages
5. **Pull Request**: Submit PR to `danish-dev` branch

### Important Rules
- 🔒 **DO NOT modify files in `contracts/`** during MVP (they are LOCKED)
- Document any contract issues in GitHub Issues for post-MVP
- Follow existing code style (Black formatter, flake8 linting)
- Write tests for new features

### Code Style
```bash
# Format code
black .

# Lint code
flake8 .

# Type checking
mypy .
```

---

## 📖 Documentation

- **Phase Handoff**: [PHASE_LOG.md](PHASE_LOG.md) - Complete technical handoff and status
- **API Spec**: [contracts/api_spec.yaml](contracts/api_spec.yaml) - OpenAPI 3.0 specification
- **Database Schema**: [contracts/database_schema.sql](contracts/database_schema.sql) - PostgreSQL DDL

---

## 🐛 Known Issues

1. **Synthetic Data Only**: Currently using simulated social posts (Phase 1 will add real sources)
2. **Single Neighborhood**: Only DHA Phase 2 configured (expandable post-MVP)
3. **Limited Categories**: Only Gym and Cafe (can add more later)

See [PHASE_LOG.md](PHASE_LOG.md) for complete list.

---

## 📄 License

[To be determined]

---

## 👥 Team

**Project Lead**: Danish Ahmed  
**Phase 0 Development**: GitHub Copilot (AI Agent)  
**Repository**: https://github.com/Danish-Ahmed007/Start-Smart

---

## 🙏 Acknowledgments

- PostgreSQL & PostGIS for geospatial capabilities
- FastAPI for modern Python web framework
- Google Places API for business location data
- Flutter for cross-platform mobile development

---

## 📞 Support

**Issues**: [GitHub Issues](https://github.com/Danish-Ahmed007/Start-Smart/issues)  
**Documentation**: [PHASE_LOG.md](PHASE_LOG.md)

---

**Current Status**: Phase 0 Complete ✅ | Phase 1 Next ⏳  
**Database**: Local PostgreSQL (9 grids, 460 posts) ✅