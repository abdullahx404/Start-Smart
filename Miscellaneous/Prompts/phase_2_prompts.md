# Phase 2: Analytics & Scoring Engine

**PREREQUISITES**: Phase 1 must be complete with PHASE_LOG.md updated. Read Phase 1 handoff in PHASE_LOG.md before starting.

**READ THIS FIRST**: This file contains sequential prompts to implement Phase 2. Feed these to GitHub Copilot **one by one**, in order.

---

## Prompt 1: Read Phase 1 Handoff and Understand Data

```
I am implementing Phase 2 of the StartSmart MVP project (Analytics & Scoring Engine).

First, please read PHASE_LOG.md Phase 1 handoff to understand:
- What data is available in the database
- How to query businesses and social_posts
- Expected grid_id format and categories

Then run these verification queries to understand the data:

```powershell
# Total businesses per grid
psql startsmart_dev -c "SELECT grid_id, category, COUNT(*) as business_count FROM businesses GROUP BY grid_id, category ORDER BY grid_id;"

# Total social posts per grid
psql startsmart_dev -c "SELECT grid_id, post_type, COUNT(*) as post_count FROM social_posts GROUP BY grid_id, post_type ORDER BY grid_id;"

# Check for grids with zero businesses
psql startsmart_dev -c "SELECT gc.grid_id FROM grid_cells gc LEFT JOIN businesses b ON gc.grid_id = b.grid_id WHERE b.business_id IS NULL;"
```

Summarize the data distribution you observe (which grids have most businesses, which have most social posts).
```

---

## Prompt 2: Create Aggregator Service (Part 1 - Basic Aggregation)

```
Create the data aggregation service.

Please create `backend/src/services/aggregator.py`:

1. Function: aggregate_grid_metrics(grid_id: str, category: str) -> dict
   
   This function computes raw metrics for a single grid × category:
   
   a) business_count:
      - Query businesses table: COUNT(*) WHERE grid_id = ? AND category = ?
   
   b) instagram_volume:
      - Query social_posts table: COUNT(*) WHERE grid_id = ? AND source = 'simulated' AND post_type = 'mention'
      - For MVP, we treat simulated posts as "Instagram-like" mentions
   
   c) reddit_mentions:
      - Query social_posts table: COUNT(*) WHERE grid_id = ? AND source = 'simulated' AND post_type IN ('demand', 'complaint')
      - These represent demand signals
   
   d) avg_rating and total_reviews:
      - Query businesses table: AVG(rating), SUM(review_count) WHERE grid_id = ? AND category = ? AND rating IS NOT NULL
   
   Returns dict:
   {
     "grid_id": str,
     "category": str,
     "business_count": int,
     "instagram_volume": int,
     "reddit_mentions": int,
     "avg_rating": float or None,
     "total_reviews": int
   }

2. Function: aggregate_all_grids(category: str) -> List[dict]
   - Get all grid_ids from grid_cells table
   - For each grid, call aggregate_grid_metrics(grid_id, category)
   - Return list of all metrics

3. Include logging for:
   - Grids with zero businesses
   - Grids with zero social posts
   - Total processing time

Use database connection from src.database.connection (get_session()).
Import models from src.database.models.
```

---

## Prompt 3: Create Aggregator Service (Part 2 - Normalization)

```
Add normalization functions to the aggregator.

Update `backend/src/services/aggregator.py`:

1. Function: compute_max_values(metrics_list: List[dict]) -> dict
   
   Given a list of grid metrics (from aggregate_all_grids), compute:
   - max_business_count: max across all grids
   - max_instagram_volume: max across all grids
   - max_reddit_mentions: max across all grids
   
   Returns dict with these max values.
   
   Handle edge case: if all values are 0, return 1.0 to avoid division by zero.

2. Function: normalize_metrics(metrics: dict, max_values: dict) -> dict
   
   Normalize a single grid's metrics using max values:
   - supply_norm = business_count / max_business_count
   - demand_instagram_norm = instagram_volume / max_instagram_volume
   - demand_reddit_norm = reddit_mentions / max_reddit_mentions
   
   All values should be 0.0 to 1.0.
   
   Returns dict with normalized values:
   {
     "supply_norm": float,
     "demand_instagram_norm": float,
     "demand_reddit_norm": float
   }

3. Update aggregate_all_grids to also return max_values:
   - Return tuple: (metrics_list, max_values)

Include unit tests for edge cases (all zeros, single grid, etc.).
```

---

## Prompt 4: Create Scoring Service (Part 1 - GOS Calculation)

```
Create the Gap Opportunity Score (GOS) calculation service.

Please create `backend/src/services/scoring_service.py`:

1. Define scoring weights as constants (configurable later):
   ```python
   WEIGHT_SUPPLY = 0.4
   WEIGHT_INSTAGRAM = 0.25
   WEIGHT_REDDIT = 0.35
   ```

2. Function: calculate_gos(normalized_metrics: dict) -> float
   
   Implements the GOS formula from STARTUP_IDEA.md Section 8:
   
   GOS = (1 - supply_norm) * WEIGHT_SUPPLY + 
         demand_instagram_norm * WEIGHT_INSTAGRAM + 
         demand_reddit_norm * WEIGHT_REDDIT
   
   Result should be 0.0 to 1.0 (higher = better opportunity).
   
   Return float rounded to 3 decimal places.

3. Function: calculate_confidence(raw_metrics: dict) -> float
   
   Confidence formula:
   - k1 = 5.0 (Instagram scaling factor)
   - k2 = 3.0 (Reddit scaling factor)
   - source_diversity_bonus = 0.2 if BOTH instagram_volume > 0 AND reddit_mentions > 0
   
   confidence = min(1.0, 
                    log(1 + instagram_volume) / k1 + 
                    log(1 + reddit_mentions) / k2 + 
                    source_diversity_bonus)
   
   Use math.log for natural logarithm.
   
   Return float rounded to 3 decimal places.

4. Include comprehensive docstrings explaining the formulas.

Dependencies: math (standard library)
```

---

## Prompt 5: Create Scoring Service (Part 2 - Explainability)

```
Add explainability features to the scoring service.

Update `backend/src/services/scoring_service.py`:

1. Function: get_top_posts(grid_id: str, category: str, limit: int = 3) -> List[dict]
   
   Query social_posts table:
   - WHERE grid_id = ? AND post_type IN ('demand', 'complaint', 'mention')
   - ORDER BY engagement_score DESC
   - LIMIT limit
   
   For each post, return:
   {
     "source": str (e.g., "simulated"),
     "text": str (truncate to 200 chars if needed),
     "timestamp": str (ISO format),
     "link": str or None (construct fake link for simulated data: f"https://simulated.example/{post_id}")
   }

2. Function: get_competitors(grid_id: str, category: str, limit: int = 5) -> List[dict]
   
   Query businesses table:
   - WHERE grid_id = ? AND category = ?
   - ORDER BY rating DESC NULLS LAST
   - LIMIT limit
   
   For each business, return:
   {
     "name": str,
     "distance_km": float (calculate from grid center using Haversine formula),
     "rating": float or None
   }
   
   Use geopy library for distance calculation or implement Haversine manually.

3. Function: generate_rationale(metrics: dict, gos: float) -> str
   
   Create a 1-sentence human-readable explanation.
   
   Logic:
   - If gos >= 0.7: "High demand ({instagram + reddit} posts), low competition ({business_count} businesses)"
   - If 0.4 <= gos < 0.7: "Moderate opportunity with {business_count} competitors and {total_posts} demand signals"
   - If gos < 0.4: "Saturated market with {business_count} businesses and limited demand"
   
   Return string with actual values filled in.

Dependencies: geopy (or manual Haversine)
```

---

## Prompt 6: Create End-to-End Scoring Pipeline

```
Create the main scoring pipeline that ties everything together.

Update `backend/src/services/scoring_service.py`:

1. Function: score_all_grids(category: str) -> List[dict]
   
   This is the main entry point. It:
   - Calls aggregator.aggregate_all_grids(category) to get raw metrics
   - Normalizes all metrics
   - Calculates GOS and confidence for each grid
   - Gets top posts and competitors for each grid
   - Generates rationale for each grid
   - Inserts results into grid_metrics table
   - Returns list of scored grids
   
   Each returned dict should match GridMetrics model from contracts/models.py:
   {
     "grid_id": str,
     "category": str,
     "business_count": int,
     "instagram_volume": int,
     "reddit_mentions": int,
     "gos": float,
     "confidence": float,
     "top_posts_json": List[dict],
     "competitors_json": List[dict],
     "last_updated": datetime (now)
   }

2. Function: get_top_recommendations(neighborhood: str, category: str, limit: int = 3) -> List[dict]
   
   - Query grid_metrics table:
     * JOIN with grid_cells ON grid_id
     * WHERE neighborhood = ? AND category = ?
     * ORDER BY gos DESC
     * LIMIT limit
   
   - For each grid, return recommendation dict:
   {
     "grid_id": str,
     "gos": float,
     "confidence": float,
     "rationale": str,
     "lat_center": float,
     "lon_center": float
   }

3. Include transaction management (commit after all inserts).

4. Include logging for:
   - Total grids scored
   - Time taken
   - Top 3 grids by GOS

Import aggregator from src.services.aggregator.
Use database connection from src.database.connection.
```

---

## Prompt 7: Create Scoring CLI Script

```
Create a command-line tool to run the scoring engine.

Please create `backend/scripts/run_scoring.py`:

1. Use argparse for arguments:
   --category (required): Gym or Cafe
   --neighborhood (optional): Filter recommendations to specific neighborhood
   --top (optional, default 3): Number of recommendations to show

2. Main logic:
   - Run score_all_grids(category)
   - Print summary statistics:
     * Total grids scored
     * GOS range (min, max, average)
     * Top 3 grids by GOS
   - If --neighborhood specified, call get_top_recommendations(neighborhood, category, top)
   - Print recommendations in readable format:
     ```
     Top 3 Recommendations for Gym in DHA Phase 2:
     
     1. DHA-Phase2-Cell-07 (GOS: 0.82, Confidence: 0.78)
        Rationale: High demand (48 posts), low competition (2 businesses)
        Location: 24.8275, 67.0595
     
     2. DHA-Phase2-Cell-03 (GOS: 0.76, Confidence: 0.71)
        ...
     ```

3. Include --recompute flag:
   - Force recomputation even if grid_metrics already populated
   - Useful for testing formula changes

4. Include progress indicators for long-running operations.

Make output colorful and easy to read (use colorama library).

Dependencies: argparse, colorama
```

---

## Prompt 8: Create Unit Tests for Scoring Logic

```
Create comprehensive unit tests for the scoring service.

Please create `backend/tests/services/test_scoring_service.py`:

1. Test GOS calculation:
   - test_calculate_gos_high_opportunity: supply_norm=0.1, demand high -> GOS ~0.8
   - test_calculate_gos_saturated: supply_norm=0.9, demand low -> GOS ~0.2
   - test_calculate_gos_balanced: All norms = 0.5 -> GOS should match weights
   - test_calculate_gos_edge_cases: All zeros, all ones

2. Test confidence calculation:
   - test_confidence_high_volume: Lots of posts -> confidence near 1.0
   - test_confidence_low_volume: Few posts -> confidence < 0.5
   - test_confidence_diversity_bonus: Both sources -> bonus applied
   - test_confidence_single_source: Only one source -> no bonus

3. Test normalization:
   - test_normalize_metrics: Known max values -> correct normalized values
   - test_normalize_all_zeros: Handle division by zero

4. Test explainability:
   - test_generate_rationale: Different GOS values -> appropriate messages
   - test_get_top_posts: Verify correct ordering and truncation
   - test_get_competitors: Verify distance calculation

5. Use pytest fixtures for sample data:
   - Sample raw metrics
   - Sample normalized metrics
   - Mock database with test grids

Coverage target: ≥90%

Use pytest-mock for database mocking.
```

---

## Prompt 9: Create Integration Test for Full Scoring Pipeline

```
Create an integration test for the complete scoring flow.

Please create `backend/tests/test_integration_phase2.py`:

1. Set up test database with:
   - 3 grid cells
   - 10-15 businesses (distributed unevenly across grids)
   - 50 social posts (varied distribution)

2. Test flow:
   - Run aggregator.aggregate_all_grids('Gym')
   - Verify raw metrics computed correctly
   - Run scoring_service.score_all_grids('Gym')
   - Verify grid_metrics table populated
   - Query top recommendations
   - Verify ranking is correct (high GOS first)

3. Verify:
   - All grids have GOS between 0.0 and 1.0
   - Grid with most demand + least businesses has highest GOS
   - Grid with most businesses + least demand has lowest GOS
   - Confidence scores are reasonable (0.0 to 1.0)
   - Top posts and competitors JSON is valid

4. Test edge cases:
   - Grid with zero businesses
   - Grid with zero social posts
   - Grid with businesses but no ratings

After test passes, run actual scoring:

```powershell
# Score all grids for Gym category
python backend/scripts/run_scoring.py --category Gym

# View results
psql startsmart_dev -c "SELECT grid_id, gos, confidence, business_count, instagram_volume, reddit_mentions FROM grid_metrics WHERE category='Gym' ORDER BY gos DESC;"

# Get recommendations
python backend/scripts/run_scoring.py --category Gym --neighborhood DHA-Phase2 --top 3
```

Document results in PHASE_LOG.md.
```

---

## Prompt 10: Create Scoring Validation Script

```
Create a validation script to verify scoring makes sense.

Please create `backend/scripts/validate_scoring.py`:

1. For each grid with computed GOS:
   - Print grid_id, GOS, confidence
   - Print business_count, instagram_volume, reddit_mentions
   - Print rationale
   - Print top 3 posts (text snippets)
   - Print top 3 competitors (names)

2. Highlight anomalies:
   - High GOS but high business_count (shouldn't happen)
   - Low GOS but low business_count + high demand (shouldn't happen)
   - Confidence < 0.5 (flag for review)

3. Generate summary:
   - Distribution of GOS scores (histogram bins: 0-0.3, 0.3-0.6, 0.6-1.0)
   - Average confidence
   - Grids flagged as anomalies

4. Export to CSV for manual review:
   - columns: grid_id, neighborhood, gos, confidence, business_count, demand_total, rationale
   - Sorted by GOS descending

Use pandas for CSV export.

Dependencies: pandas

This helps catch formula errors before Phase 3.
```

---

## Prompt 11: Create Synthetic Scenario Tests

```
Create tests with synthetic scenarios to verify formula correctness.

Please create `backend/tests/test_synthetic_scenarios.py`:

1. Scenario 1: Perfect Opportunity (should have GOS ~0.9-1.0):
   - Grid: 0 businesses, 100 Instagram posts, 50 Reddit mentions
   - Expected: GOS >= 0.85

2. Scenario 2: Saturated Market (should have GOS ~0.0-0.2):
   - Grid: 20 businesses, 5 Instagram posts, 2 Reddit mentions
   - Expected: GOS <= 0.25

3. Scenario 3: Balanced Market (should have GOS ~0.5):
   - Grid: 5 businesses (mid-range), 30 Instagram posts, 15 Reddit mentions
   - Expected: 0.45 <= GOS <= 0.65

4. Scenario 4: No Data (should handle gracefully):
   - Grid: 0 businesses, 0 posts
   - Expected: GOS should be computed (likely mid-range since supply_norm = 0)

5. For each scenario:
   - Insert test data into test database
   - Run scoring
   - Assert GOS in expected range
   - Assert confidence makes sense

These tests ensure the formula behaves as intended.

Run these tests before finalizing Phase 2.
```

---

## Prompt 12: Update PHASE_LOG.md with Phase 2 Handoff

```
Phase 2 is complete. Update PHASE_LOG.md with the Phase 2 handoff entry.

Append to PHASE_LOG.md following the exact format from IMPLEMENTATION_PLAN.md Phase 2 "Handoff to Phase 3" section.

Fill in:
- Your name as owner
- Completion date
- All files created with line counts
- Database state (row counts in grid_metrics table)
- Test results (coverage, synthetic scenario results)
- Validation script output (anomalies found, GOS distribution)
- Example queries for Phase 3
- API endpoints Phase 3 should implement

Include:
- GOS formula parameters used (weights)
- Performance metrics (time to score 12 grids)
- Known issues (grids with unusual scores)
- Exact function signatures Phase 3 will call:
  * get_top_recommendations(neighborhood, category, limit)
  * score_all_grids(category)

Be comprehensive. Phase 3 frontend depends on this.
```

---

## Phase 2 Completion Checklist

Before moving to Phase 3, verify:

- [ ] Aggregator service computes correct metrics for all grids
- [ ] Scoring service calculates GOS and confidence
- [ ] Explainability: top posts and competitors extracted
- [ ] grid_metrics table populated (12 rows × 1 category = 12 rows minimum)
- [ ] All GOS scores between 0.0 and 1.0
- [ ] All confidence scores between 0.0 and 1.0
- [ ] Unit tests pass with ≥90% coverage
- [ ] Integration test passes
- [ ] Synthetic scenario tests pass
- [ ] Validation script shows no critical anomalies
- [ ] PHASE_LOG.md updated with comprehensive handoff
- [ ] CLI script produces readable recommendations

**CRITICAL VALIDATION**:
1. Manually verify top-3 grids make sense:
   - Grid with highest GOS should have low business_count OR high demand
   - Grid with lowest GOS should have high business_count OR low demand
2. Check confidence scores: grids with more data should have higher confidence
3. Verify JSON fields (top_posts_json, competitors_json) are valid JSON

**IMPORTANT**: Do NOT proceed to Phase 3 until scoring logic is validated and documented.
