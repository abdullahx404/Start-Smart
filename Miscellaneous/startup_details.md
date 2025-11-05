STARTUP_IDEA.md
StartSmart — Location Intelligence for Entrepreneurs (Detailed Reference)
1. Executive Summary

StartSmart is an AI-powered location intelligence platform whose MVP objective is to recommend high-probability business locations to aspiring entrepreneurs in a single dense city (Karachi). The MVP is deliberately narrow and pragmatic:

City: Karachi (initially; architecture supports multi-city later)

Neighborhoods: 5 (pilot set) — each subdivided into ~0.5 km² grid cells (~60 total)

Categories: 2 prioritized categories for MVP — Food (cafés, juice/smoothie bars, fast-casual) and Fitness (gyms, yoga studios)

Goal: Produce high-quality, explainable recommendations (top-3 per neighborhood) with a measurable Location Opportunity Score (GOS) and supporting evidence (data sources and rationale) for judges, mentors, and pilot customers.

This document contains everything the implementation team needs to understand scope, data, architecture, algorithms, UX, validation, deployment, and operational constraints.

2. Problem Statement (concise)

Entrepreneurs in dense urban markets choose locations based on guesswork, anecdotal advice, or visible foot-traffic. This leads to frequent failures, wasted capital, and poor servicing of local demand. There is no accessible, affordable tool that synthesizes local supply/demand signals into a single, explainable recommendation for where to start a small business.

3. Value Proposition

StartSmart converts publicly observable signals into actionable location recommendations by:

Measuring competition (existing business density by category)

Measuring demand (social mentions, search interest, expressed complaints/wishes)

Scoring gap/opportunity (normalized combination showing where demand is high and supply is low)

Presenting ranked, explainable recommendations (Top-3 areas per search with reasons and confidence)

Result: entrepreneurs can choose locations with less risk and better ROI probability.

4. MVP Scope (explicit)

City: Karachi

Neighborhoods (pilot): Choose five diverse neighborhoods (example: DHA Phase 2, Clifton Block 5, Gulshan-e-Iqbal, Bahadurabad, Saddar) — team to finalize.

Grids: ~0.5 km² grid cells within each neighborhood (approx. 60 cells)

Categories: Food (3 subtypes) and Fitness (2 subtypes)

Outputs:

Heatmap of opportunity across selected neighborhoods

Top 3 ranked location suggestions per neighborhood per category

Short explanation for each recommendation (data-backed)

Confidence score (0–1)

Data: Real APIs where possible; simulated data allowed for initial demo with clear provenance.

5. Data Sources & Access Model
Primary data sources (preferred)

Google Places API: business listings, types, counts, coordinates, ratings.

Instagram public location pages / hashtags: post counts, hashtags, geo-location tags ( scraped via Playwright or other headless tooling; legal and rate-limit constraints considered).

Reddit: local subreddit threads (r/Karachi, r/Pakistan) — posts/comments for demand and complaints via Pushshift/PRAW where accessible.

Google Trends (if accessible for local queries): search interest by region/topic.

Secondary (optional / fallback)

Local Facebook groups (manual sample scraping), Twitter/X (if usable), Local classifieds/plats.

Public open data: census, transport hubs, population density shapefiles if available.

Simulated / synthetic data

For controlled tests or demo, a simulated dataset will be used. Must be labeled as simulated in UI and PHASE_LOG.

Data constraints

Rate limits, scraping fragility, and legal restrictions (TOS) may block some sources. MVP must be designed to operate with combinations of available sources (fallback strategy).

6. Data Pipeline — High Level
Ingest Layer (Phase 1)

Source adapters: modular connectors for each external source (Google Places adapter, Instagram adapter, Reddit adapter, optional CSV loader for Day-1 simulated dataset).

Scheduler/Fetcher: single-shot harvest jobs for MVP (not continuous). Each job writes raw JSON to raw/ storage.

Raw store: JSON files in repo or cloud storage (for MVP) to persist raw inputs with timestamps.

Processing Layer (Phase 2)

Normalizer: maps raw source schemas into canonical models: Location, Business, Post, Mention, GridCell.

Geospatial joiner: assigns each entity to a GridCell using point-in-polygon or bounding-box assign.

Aggregator: per grid and per category compute:

business_count

instagram_post_volume

reddit_demand_mentions (explicit demand + complaint counts)

avg_rating and review_count (if available)

Caching: At MVP scale, SQLite or PostgreSQL used for processed data.

Scoring & Intelligence Layer (Phase 2 core)

Compute normalized metrics and GOS (see Section 8).

Attach explainability metadata (which posts, which businesses influenced score).

API & Presentation Layer (Phase 3)

Lightweight REST API: endpoints for querying map tiles, grid scores, recommended areas, explanations, history.

Frontend (Flutter) consumes API or local processing outputs.

7. Canonical Data Models (tables / schemas)

(These are high-level; implementers should translate to chosen DB)

GridCell

grid_id (string)

neighborhood (string)

lat_center, lon_center

area_km2

max_supply (derived across grid set)

max_demand (derived across grid set)

Business

business_id

name

lat, lon

category (standardized)

rating, review_count

source (GooglePlaces, manual)

SocialPost

post_id

source (instagram/reddit)

text

timestamp

lat, lon (if geotagged, else null)

grid_id (nullable)

type (mention, complaint, wishlist)

GridMetrics (per run)

grid_id, category, business_count, instagram_volume, reddit_mentions, gos, confidence, last_updated

8. Scoring: Gap Opportunity Score (GOS)
Concept:

GOS aims to quantify opportunity = demand / (1 + supply) but with more nuance; normalize across grids and sources and add confidence.

Pre-normalization:

supply = business_count (category-specific)

demand_instagram = instagram_post_volume (posts in last 90 days)

demand_reddit = reddit_demand_mentions (explicit demand + complaint counts)

demand_total = w_i * norm_instagram + w_r * norm_reddit (weights)

supply_norm = business_count / max_business_count (per city/category)

Example normalization and weights (MVP defaults; configurable)

norm_instagram = instagram_volume / max_instagram_volume

norm_reddit = reddit_mentions / max_reddit_mentions

weights: w_i = 0.25, w_r = 0.35, w_supply = 0.4 (supply is inverse)

Composite:

GOS = (1 - supply_norm) * 0.4 + norm_instagram * 0.25 + norm_reddit * 0.35


GOS scaled to 0..1. Higher → stronger opportunity.

Confidence:

Confidence = f(number_of_posts, source_diversity, recency). Example:

confidence = min(1, log(1 + instagram_volume) / k1 + log(1 + reddit_mentions) / k2 + bonus_if_multiple_sources)

Explainability:

For every GOS, store:

Top 3 posts that drove demand score (text + link)

Business_count detail (names of nearest competitors)

Timestamp and data sources used

9. API Surface (MVP; high-level)

GET /api/v1/neighborhoods — list neighborhoods + summary stats

GET /api/v1/grids?neighborhood=...&category=... — returns grid list + GOS per grid

GET /api/v1/recommendations?neighborhood=...&category=... — top-3 recommended grid ids + explanations

GET /api/v1/grid/{grid_id} — detail page: metrics, driving posts, competitor list

POST /api/v1/feedback — user feedback on a recommendation (used for future model refinement)

Authentication: mild (email-based or Firebase auth for MVP).

10. Frontend UX Flow (MVP)

Landing / Onboarding — short explanation, ask user to pick category and neighborhood. Lightweight login optional.

Map/Search Screen — city map with heatmap overlay. Filters: category, time window (last 30/90 days).

Recommendations Panel — Top 3 areas with GOS, confidence, and a 1-sentence rationale.

Drill-down — Grid detail showing businesses, top social mentions, and "why" cards.

Save / Feedback — user can save an area or submit feedback about usefulness (simple thumbs-up/down + short comment).

Design constraints: simple, clean, mobile-first, maps via Leaflet or Flutter map plugin.

11. Deployment & Tech Stack (MVP)

Frontend: Flutter (mobile-first; web-hosted build optional)

Backend: Python Flask/FastAPI for scoring + simple REST API (host on Render/GCP Cloud Run). For prototypes, a local Python module outputting JSON consumed by Flutter is acceptable.

Database: PostgreSQL (preferred) or SQLite for small-scale prototype

Storage: Cloud Storage / Git LFS for raw JSON dumps if needed

Auth: Firebase Auth (email) for quick integration

Hosting: Firebase Hosting (if web) / Play Store testflight style for mobile, backend on Heroku/Render/GCP

CICD: GitHub Actions for basic build/test/deploy pipeline (MVP: manual deploy acceptable)

Local dev: Docker-compose definitions to run API + DB locally for each developer

12. Testing & Validation Plan
Phase 0: Manual Pattern Validation (1–3 days)

Manually collect 10 locations × 3 categories and compute GOS by hand using small sample of reddit/instagram + Google Maps counts.

Validate top picks with 5 local entrepreneurs (quick interviews/DMs).

Phase-level validations (end of each phase)

Phase 1 (Data Integration): Unit tests for adapters, canonicalization checks, sample-run using known inputs → expected normalized outputs.

Phase 2 (Scoring): Create automated tests with synthetic datasets where expected GOS outcomes are known (e.g., high demand + zero supply should give high GOS).

Phase 3 (Frontend): Integration tests for API + display (Smoke tests that show map and top-3 recommendations).

Phase 4 (Feedback & Deployment): E2E tests with user journeys and feedback ingestion.

Pilot validation (pre-demo)

Run 10 in-field local validations: contact store owners or local users to ask if recommendation is sensible (rapid survey). Document results in PHASE_LOG.

13. Metrics & KPIs (MVP-focused)

Engagement Metric: % users who click into at least one recommended area (primary)

Recommendation Precision: % of top-3 recommendations validated as "sensible" by quick human checks (target >= 70% for MVP)

Data Coverage: % grids with non-zero demand signals

Processing Latency: time to compute and load recommendations (target < 5s)

Adoption: number of saved areas / returning users during pilots

14. Team Roles (4 developers mapped)

Developer A — Phase 1 (Data Integration): adapters, raw storage, normalizer; unit tests

Developer B — Phase 2 (Scoring/Analytics): aggregator, scoring engine, confidence, explainability

Developer C — Phase 3 (Frontend / UX): Flutter app, Map UI, recommendation panels, minimal auth

Developer D — Phase 4 (API, Deployment & QA): REST API, DB, deployment, PHASE_LOG maintenance, end-to-end testing

Each dev owns one phase but must update PHASE_LOG.md after their phase completion. Cross-code reviews are mandatory.

15. PHASE_LOG.md — Format & Usage

PHASE_LOG.md is the single source of truth for Copilot/LLMs to understand repository progress. It must be updated whenever a phase is completed or a significant change occurs.

Suggested format (YAML-like or markdown, consistent):

# PHASE_LOG

## Phase 1 — Data Integration
- Owner: Dev A
- Completed: 2025-11-05
- Summary:
  - Implemented GooglePlaces adapter (local mock)
  - Implemented Instagram scraping stub (Playwright script saved to raw/instagram.json)
  - Normalizer mapping raw -> canonical models
- Known issues:
  - Instagram scraping rate-limited; currently uses simulated samples.
  - Geo-join edge cases for grids near neighborhood borders.
- Next steps:
  - Developer B to run aggregator and start defining scoring inputs.


Copilot and future automated scripts will parse PHASE_LOG.md to determine handoff state and continue work.

16. Handoff Requirements (end of each phase)

Every phase must produce:

Completed code module (well-documented)

Unit tests covering key behaviors

Example dataset / sample run showing outputs

Clear PHASE_LOG entry (see above)

Handoff summary (short): Completed, Next, Constraints.

17. Security & Privacy

Do not persist any private user data in cleartext in public repositories.

For scraped social media, store only public content and metadata. Respect TOS; where scraping is risky, use simulated or manual data.

Use environment variables for API keys; do not commit secrets.

18. Risks & Mitigations

Data fragility: Social platforms change endpoints. Mitigation: Design adapters as replaceable modules and allow simulated fallback data.

Rate limits & access: Google Places quotas. Mitigation: Use cached runs and synthetic datasets for demos; apply for small quota increases early.

Explainability: Judges need reasons; Mitigation: store and surface top posts + competitor list as supporting evidence for each recommendation.

Instructor expectations (Java): Course looks for interface/design quality. Mitigation: code should use clear interfaces, DI, and a small Java artifact showing 1:1 interface mapping (optional).

19. Roadmap & Phase Checklist (atomic)

Phase 0 (Day 0–1): Manual validation and dataset assembly (sample runs).

Phase 1 (Day 1–4): Data adapters, normalizer, raw store. Deliver raw JSON + canonical DB + PHASE_LOG entry.

Phase 2 (Day 4–8): Aggregator & scoring engine. Deliver scoring service, test harness, and PHASE_LOG update.

Phase 3 (Day 8–12): Frontend MVP in Flutter. Deliver map + top-3 UI, and PHASE_LOG update.

Phase 4 (Day 12–15): API, deployment, pilot validation, feedback ingestion, final integration tests and demo prep.

Phase 5 (Post-demo): Refinements, expanded categories, multi-city scaling (future).

Each phase is independently testable and has acceptance criteria listed in the implementation plan.

20. What to Demo (presentation day)

Live app: pick a neighborhood + category → show heatmap + top-3 suggestions.

Click into a recommended grid: show business list, top supporting social posts, and GOS + confidence score.

Show PHASE_LOG demonstrating disciplined, traceable development.

Show validation evidence: short results from manual checks or pilot interviews.

21. Assumptions & Constraints (explicit)

MVP uses publicly available data or simulated datasets where necessary.

Scraping will be implemented cautiously; legal and rate-limit constraints may force use of synthetic data for some sources.

Core evaluation by judges will focus on prediction quality and design quality (architecture, modularity, documentation) — not on city scale.

22. Acceptance Criteria (MVP success)

Live deployed MVP demonstrating:

Map + heatmap for selected neighborhoods

Top-3 recommendations for at least two categories

Each recommendation has GOS, confidence, and 1–3 evidence items

Precision: At least 60–70% of top recommendations pass basic human sensibility checks in pilot validation

PHASE_LOG updated and shows structured progress and rationale

23. Appendix: Example Synthetic Data Row (for testing)
{
  "grid_id": "DHA-Phase2-Cell-12",
  "neighborhood": "DHA Phase 2",
  "category": "Gym",
  "business_count": 2,
  "instagram_volume": 48,
  "reddit_mentions": 7,
  "gos": 0.82,
  "confidence": 0.78,
  "top_posts": [
    {"source":"reddit","text":"We need a proper gym in Phase 2, all we have is tiny PT places","link":"..."},
    {"source":"instagram","text":"#Phase2gym #workout", "post_id":"..."}
  ],
  "last_updated":"2025-11-05T12:00:00Z"
}

24. How Copilot / automated agents should use this file

Use STARTUP_IDEA.md as the single authoritative reference for product intent and constraints.

Read PHASE_LOG.md to determine current repo state and next actions.

When generating code or plans, aim for modular adapters and small, testable units.

Always include handoff notes and PHASE_LOG updates after completing synthetic tasks or generating files.

25. Contact / Steering Notes (for team)

Finalize the list of 5 neighborhoods before Phase 1 begins.

Agree on the exact subcategories for Food and Fitness (3 and 2 respectively).

Reserve budget/time for pilot user outreach (5–10 quick interviews).

Prioritize explainability and reproducibility for the demo.

End of STARTUP_IDEA.md