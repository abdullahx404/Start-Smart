# StartSmart Recommendation Engine

## Overview

The StartSmart Recommendation Engine is an advanced location intelligence system that evaluates business location suitability using a multi-layered approach combining real-time data, deterministic rules, and AI-powered analysis.

**Architecture**: `BEV → Rule Engine → LLM Evaluator → Score Combiner → Final Recommendation`

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        RECOMMENDATION PIPELINE                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌───────────┐ │
│  │   Google     │    │    Rule      │    │     LLM      │    │   Score   │ │
│  │   Places     │───▶│   Engine     │───▶│  Evaluator   │───▶│  Combiner │ │
│  │     API      │    │  (65% wt)    │    │  (35% wt)    │    │           │ │
│  └──────────────┘    └──────────────┘    └──────────────┘    └───────────┘ │
│         │                   │                   │                   │       │
│         ▼                   ▼                   ▼                   ▼       │
│   ┌──────────┐        ┌──────────┐        ┌──────────┐        ┌──────────┐ │
│   │   BEV    │        │  Rule    │        │   LLM    │        │  Final   │ │
│   │  Vector  │        │  Scores  │        │  Probs   │        │  Score   │ │
│   └──────────┘        └──────────┘        └──────────┘        └──────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Components

### 1. Business Environment Vector (BEV) Generator

**File**: `backend/src/services/bev_generator.py`

The BEV Generator creates a comprehensive feature vector representing the business environment around a location using Google Places API.

#### Features Computed

| Category | Features |
|----------|----------|
| **Density** | restaurants, cafes, gyms, offices, schools, universities, malls, healthcare, parks, transit_stations, banks, bars |
| **Distance** | distance_to_mall, distance_to_cinema, distance_to_university, distance_to_hospital, distance_to_transit, distance_to_park |
| **Economic** | avg_business_rating, avg_review_count, premium_to_economy_ratio, income_proxy (low/mid/high) |

#### Usage

```python
from src.services.bev_generator import BEVGenerator

bev_gen = BEVGenerator()
bev = bev_gen.generate_bev(
    center_lat=24.816,
    center_lon=67.028,
    radius_meters=500,
    grid_id="Clifton-Block2-007"
)

# Access features
print(f"Restaurants: {bev.density.restaurants}")
print(f"Distance to mall: {bev.distance.distance_to_mall}m")
print(f"Income proxy: {bev.economic.income_proxy}")
```

#### Output Structure

```python
@dataclass
class BusinessEnvironmentVector:
    grid_id: str
    center_lat: float
    center_lon: float
    radius_meters: int
    density: DensityFeatures      # POI counts
    distance: DistanceFeatures    # Distances to amenities
    economic: EconomicFeatures    # Economic indicators
    generated_at: str
    api_calls_used: int
```

---

### 2. Rule Engine

**File**: `backend/src/services/rule_engine.py`

The Rule Engine applies deterministic, configurable rules to score locations based on the BEV. Rules are designed to capture business location suitability patterns.

#### Gym Rules (12 rules)

| Rule | Condition | Score Delta | Rationale |
|------|-----------|-------------|-----------|
| office_heavy_area | offices > 30 | +0.25 | Working professionals need gym access |
| moderate_offices | 15 ≤ offices ≤ 30 | +0.15 | Good customer base |
| near_university | universities > 0 OR distance < 500m | +0.20 | Students are key gym demographic |
| high_income_area | income_proxy == "high" | +0.20 | High gym membership capacity |
| high_gym_competition | gyms ≥ 4 | -0.30 | Saturated market |
| low_income_area | income_proxy == "low" | -0.20 | Limited subscription capacity |
| ... | ... | ... | ... |

#### Cafe Rules (15 rules)

| Rule | Condition | Score Delta | Rationale |
|------|-----------|-------------|-----------|
| restaurant_synergy | restaurants > 20 | +0.20 | Food district attracts cafe visitors |
| near_university | universities > 0 | +0.25 | Students frequent cafes |
| near_mall | distance_to_mall < 500m | +0.20 | Shopping traffic |
| near_schools | schools > 3 | +0.15 | Parents visit cafes |
| high_cafe_competition | cafes ≥ 6 | -0.25 | Market saturation |
| ... | ... | ... | ... |

#### Usage

```python
from src.services.rule_engine import RuleEngine

engine = RuleEngine()
result = engine.evaluate(bev)

print(f"Gym Score: {result.gym_score}")      # 0.0 - 1.0
print(f"Cafe Score: {result.cafe_score}")    # 0.0 - 1.0
print(f"Applied Rules: {result.gym_rules_applied}")
```

#### Output Structure

```python
@dataclass
class RuleEvaluationResult:
    gym_score: float              # 0.0 - 1.0
    cafe_score: float             # 0.0 - 1.0
    gym_rules_applied: List[Dict] # Rules that fired
    cafe_rules_applied: List[Dict]
    evaluated_at: str
```

---

### 3. LLM Evaluator

**File**: `backend/src/services/llm_evaluator.py`

The LLM Evaluator uses Groq's LLM (llama-3.3-70b-versatile) to provide contextual reasoning and probabilistic assessments based on the BEV.

#### Model Configuration

| Setting | Value |
|---------|-------|
| Provider | Groq |
| Model | llama-3.3-70b-versatile |
| Fallback Model | llama-3.1-8b-instant |
| Temperature | 0.3 (deterministic) |
| Response Format | JSON |

#### Prompt Structure

The LLM receives a structured prompt containing:
1. BEV data (density, distance, economic features)
2. Location context (Karachi, Clifton area)
3. Task: Evaluate for GYM and CAFE suitability

#### Usage

```python
from src.services.llm_evaluator import LLMEvaluator

evaluator = LLMEvaluator()
result = evaluator.evaluate(bev)

print(f"Gym Probability: {result.gym_probability}")
print(f"Gym Reasoning: {result.gym_reasoning}")
print(f"Key Factors: {result.key_factors}")
```

#### Output Structure

```python
@dataclass
class LLMEvaluationResult:
    gym_probability: float        # 0.0 - 1.0
    cafe_probability: float       # 0.0 - 1.0
    gym_reasoning: str            # 2-3 sentence explanation
    cafe_reasoning: str
    key_factors: List[str]        # e.g., ["office workers", "low competition"]
    risks: List[str]              # e.g., ["market saturation"]
    recommendation: str           # Overall summary
    model_used: str
    tokens_used: int
```

---

### 4. Score Combiner

**File**: `backend/src/services/score_combiner.py`

The Score Combiner merges rule-based scores with LLM probabilities using a weighted ensemble approach.

#### Formula

```
final_score = (0.65 × rule_score) + (0.35 × llm_probability)
```

| Component | Weight | Rationale |
|-----------|--------|-----------|
| Rule Engine | 65% | Deterministic, data-driven, consistent |
| LLM | 35% | Contextual reasoning, pattern recognition |

#### Suitability Levels

| Score Range | Suitability | Recommendation |
|-------------|-------------|----------------|
| 0.80 - 1.00 | Excellent | Strong recommendation to proceed |
| 0.65 - 0.79 | Good | Recommended with minor considerations |
| 0.45 - 0.64 | Moderate | Further analysis recommended |
| 0.25 - 0.44 | Poor | Consider alternatives |
| 0.00 - 0.24 | Not Recommended | High risk |

#### Usage

```python
from src.services.score_combiner import ScoreCombiner

combiner = ScoreCombiner(rule_weight=0.65, llm_weight=0.35)
result = combiner.combine(
    grid_id="Clifton-Block2-007",
    rule_result=rule_result,
    llm_result=llm_result,
    bev=bev
)

print(f"Best Category: {result.best_category}")
print(f"Best Score: {result.best_score}")
print(f"Suitability: {result.best_suitability}")
```

---

### 5. Recommendation Pipeline

**File**: `backend/src/services/recommendation_pipeline.py`

The Recommendation Pipeline orchestrates all components into a unified workflow.

#### Pipeline Modes

| Mode | Components | Use Case |
|------|------------|----------|
| `full` | BEV + Rule + LLM | Complete analysis with AI reasoning |
| `fast` | BEV + Rule only | Quick scoring, no LLM calls |

#### Usage

```python
from src.services.recommendation_pipeline import RecommendationPipeline, PipelineMode

pipeline = RecommendationPipeline()

# Full mode (with LLM)
result = pipeline.recommend(
    lat=24.816,
    lon=67.028,
    grid_id="Clifton-Block2-007",
    mode=PipelineMode.FULL
)

# Fast mode (rule-only)
result = pipeline.recommend(
    lat=24.816,
    lon=67.028,
    mode=PipelineMode.FAST
)

# Get API response
print(result.to_api_response())
```

#### Timing Breakdown

The pipeline tracks timing for each stage:

```python
result.bev_time_ms      # BEV generation (~10-15s with API calls)
result.rule_time_ms     # Rule evaluation (~1-5ms)
result.llm_time_ms      # LLM call (~2-5s)
result.combine_time_ms  # Score combination (~1ms)
result.total_time_ms    # Total pipeline time
```

---

## API Endpoints

**File**: `backend/api/routers/recommendation_llm.py`

### GET /api/v1/recommendation_llm

Full LLM-powered recommendation.

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| lat | float | Yes | - | Latitude (-90 to 90) |
| lon | float | Yes | - | Longitude (-180 to 180) |
| grid_id | string | No | auto | Grid cell identifier |
| radius | int | No | 500 | Search radius in meters (100-2000) |

**Example Request:**
```bash
curl "http://localhost:8000/api/v1/recommendation_llm?lat=24.816&lon=67.028"
```

**Example Response:**
```json
{
  "grid_id": "custom-24.8160-67.0280",
  "recommendation": {
    "best_category": "cafe",
    "score": 0.80,
    "suitability": "excellent",
    "message": "This location is EXCELLENT for a CAFE. Strong recommendation to proceed."
  },
  "gym": {
    "score": 0.39,
    "suitability": "poor",
    "reasoning": "The location has a high number of existing gyms, indicating a saturated market.",
    "positive_factors": ["University students are key gym demographic"],
    "concerns": ["Too many existing gyms - saturated market"]
  },
  "cafe": {
    "score": 0.80,
    "suitability": "excellent",
    "reasoning": "The low number of cafes combined with restaurants and universities suggests demand.",
    "positive_factors": ["University students are frequent cafe visitors", "Mall proximity"],
    "concerns": ["Low income areas have limited cafe spending"]
  },
  "analysis": {
    "model_used": "llama-3.3-70b-versatile",
    "total_businesses_nearby": 81,
    "key_factors": ["low cafe competition", "high gym competition"],
    "processing_time_ms": 17813.72
  }
}
```

### GET /api/v1/recommendation_fast

Fast rule-based recommendation (no LLM).

**Parameters:** Same as `/recommendation_llm`

**Differences:**
- No LLM API call (~10x faster)
- `model_used: "none"`
- Reasoning says "Fast mode - using rule scores"

### GET /api/v1/recommendation_debug

Detailed pipeline output for debugging.

**Additional Response Fields:**
- Full BEV data
- Rule scores breakdown
- LLM scores breakdown
- Final scores
- Timing for each stage

### POST /api/v1/recommendation_batch

Batch recommendations for multiple locations.

**Request Body:**
```json
[
  {"lat": 24.816, "lon": 67.028, "grid_id": "grid-1"},
  {"lat": 24.820, "lon": 67.030, "grid_id": "grid-2"}
]
```

---

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GOOGLE_PLACES_API_KEY` | Yes | Google Maps/Places API key |
| `GROQ_API_KEY` | Yes (for full mode) | Groq LLM API key |
| `DATABASE_URL` | Yes | PostgreSQL connection string |

### .env Example

```env
# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/startsmart_dev

# Google Places API
GOOGLE_PLACES_API_KEY=AIzaSy...

# Groq LLM API
GROQ_API_KEY=gsk_...

# Environment
ENVIRONMENT=development
LOG_LEVEL=INFO
```

---

## Dependencies

Add to `requirements.txt`:

```
# Google Maps API
googlemaps>=4.10.0

# LLM (Groq)
groq>=0.4.0
```

---

## File Structure

```
backend/
├── api/
│   ├── main.py                      # FastAPI app with dotenv loading
│   └── routers/
│       └── recommendation_llm.py    # New LLM recommendation endpoints
├── src/
│   └── services/
│       ├── bev_generator.py         # Business Environment Vector
│       ├── rule_engine.py           # Deterministic rule scoring
│       ├── llm_evaluator.py         # Groq LLM integration
│       ├── score_combiner.py        # Weighted score combination
│       └── recommendation_pipeline.py # Pipeline orchestrator
└── .env                             # Environment variables
```

---

## Performance Metrics

| Stage | Typical Time | Notes |
|-------|--------------|-------|
| BEV Generation | 10-15s | Depends on Google API response |
| Rule Engine | 1-5ms | Very fast, no I/O |
| LLM Evaluation | 2-5s | Groq API call |
| Score Combination | <1ms | Pure computation |
| **Total (full)** | **12-20s** | With LLM |
| **Total (fast)** | **10-15s** | Without LLM |

---

## Future Enhancements

1. **Caching**: Cache BEV results for frequently queried locations
2. **Batch BEV**: Generate BEVs for all micro-grids in advance
3. **More Categories**: Extend to restaurants, retail, salons, etc.
4. **Custom Rules**: Allow users to define custom scoring rules
5. **Historical Trends**: Incorporate time-series data for demand prediction
6. **Confidence Intervals**: Add uncertainty quantification to scores

---

## Changelog

### v2.0.0 (December 2025)

- ✅ Added BEV Generator with Google Places integration
- ✅ Added Rule Engine with 27 configurable rules (12 gym, 15 cafe)
- ✅ Added LLM Evaluator with Groq (llama-3.3-70b-versatile)
- ✅ Added Score Combiner with weighted ensemble (65/35)
- ✅ Added Recommendation Pipeline orchestrator
- ✅ Added 4 new API endpoints
- ✅ Added dotenv support for environment variables

---

*Last Updated: December 4, 2025*
