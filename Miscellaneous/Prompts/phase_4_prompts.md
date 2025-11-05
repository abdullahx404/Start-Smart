# Phase 4: API, Deployment & End-to-End Testing

**PREREQUISITES**: Phases 1, 2, and 3 must be complete. Backend has scoring logic, frontend has UI ready.

**READ THIS FIRST**: This file contains sequential prompts to implement Phase 4. Feed these to GitHub Copilot **one by one**, in order.

---

## Prompt 1: Read All Previous Handoffs and Plan API

```
I am implementing Phase 4 of the StartSmart MVP project (API & Deployment).

Please read PHASE_LOG.md to understand:
- Phase 1: What data adapters and database models exist
- Phase 2: What scoring services are available
- Phase 3: What API responses the frontend expects

Then create a plan for the REST API:
1. List all 5 endpoints from contracts/api_spec.yaml
2. Map each endpoint to backend services:
   - GET /neighborhoods -> query grid_cells table
   - GET /grids -> query grid_metrics table
   - GET /recommendations -> call scoring_service.get_top_recommendations()
   - GET /grid/{grid_id} -> query grid_metrics + format detail response
   - POST /feedback -> insert into user_feedback table

Document dependencies and any missing pieces.
```

---

## Prompt 2: Create FastAPI Application Structure

```
Set up the FastAPI application.

Please create `backend/api/main.py`:

1. Initialize FastAPI app:
   - Title: "StartSmart Location Intelligence API"
   - Version: "1.0.0"
   - Description: from STARTUP_IDEA.md

2. Add CORS middleware:
   - Allow origins: ["http://localhost:*", "https://startsmart-mvp.web.app"]
   - Allow methods: ["GET", "POST"]
   - Allow headers: ["*"]

3. Add request logging middleware:
   - Log each request: method, path, duration, status code

4. Add health check endpoint:
   - GET /health -> return {"status": "ok", "timestamp": <now>}

5. Include routers (will create next):
   - neighborhoods router
   - grids router
   - recommendations router
   - feedback router

6. Add global exception handler:
   - Catch all exceptions
   - Return structured error response
   - Log error with stack trace

Dependencies: fastapi, uvicorn, python-multipart
```

---

## Prompt 3: Create Neighborhoods Router

```
Create the neighborhoods endpoint.

Please create `backend/api/routers/neighborhoods.py`:

1. Endpoint: GET /api/v1/neighborhoods

2. Logic:
   - Query grid_cells table for distinct neighborhoods
   - For each neighborhood, count grids
   - Return list of neighborhood objects

3. Response format (from contracts/api_spec.yaml):
   ```json
   [
     {
       "id": "DHA-Phase2",
       "name": "DHA Phase 2",
       "grid_count": 12
     }
   ]
   ```

4. Use Pydantic response model (from contracts/models.py)

5. Include OpenAPI documentation:
   - Summary: "List all available neighborhoods"
   - Response description
   - Example response

Use database connection from src.database.connection.
Import models from src.database.models.
```

---

## Prompt 4: Create Grids Router

```
Create the grids endpoint.

Please create `backend/api/routers/grids.py`:

1. Endpoint: GET /api/v1/grids

2. Query parameters:
   - neighborhood: str (required)
   - category: str (required, enum: Gym, Cafe)

3. Logic:
   - Join grid_cells and grid_metrics tables
   - WHERE neighborhood = ? AND category = ?
   - Return grid list with GOS, confidence, coordinates

4. Response format:
   ```json
   [
     {
       "grid_id": "DHA-Phase2-Cell-07",
       "lat_center": 24.8275,
       "lon_center": 67.0595,
       "gos": 0.82,
       "confidence": 0.78
     }
   ]
   ```

5. Error handling:
   - Invalid neighborhood -> 404 "Neighborhood not found"
   - Invalid category -> 422 "Invalid category"
   - No grids found -> return empty array (not error)

6. Add caching headers:
   - Cache-Control: max-age=3600 (1 hour)

Use Pydantic models for request validation and response serialization.
```

---

## Prompt 5: Create Recommendations Router

```
Create the recommendations endpoint.

Please create `backend/api/routers/recommendations.py`:

1. Endpoint: GET /api/v1/recommendations

2. Query parameters:
   - neighborhood: str (required)
   - category: str (required)
   - limit: int (optional, default 3, max 10)

3. Logic:
   - Call scoring_service.get_top_recommendations(neighborhood, category, limit)
   - If no recommendations, check if neighborhood exists (helpful error)
   - Format response

4. Response format:
   ```json
   {
     "neighborhood": "DHA Phase 2",
     "category": "Gym",
     "recommendations": [
       {
         "grid_id": "DHA-Phase2-Cell-07",
         "gos": 0.82,
         "confidence": 0.78,
         "rationale": "High demand (48 posts), low competition (2 gyms)",
         "lat_center": 24.8275,
         "lon_center": 67.0595
       }
     ]
   }
   ```

5. Add logging:
   - Log each recommendation request
   - Log top grid_id returned

Import get_top_recommendations from src.services.scoring_service.
```

---

## Prompt 6: Create Grid Detail Router

```
Create the grid detail endpoint.

Please create `backend/api/routers/grid_detail.py`:

1. Endpoint: GET /api/v1/grid/{grid_id}

2. Path parameter:
   - grid_id: str

3. Query parameter:
   - category: str (required)

4. Logic:
   - Query grid_metrics WHERE grid_id = ? AND category = ?
   - Parse top_posts_json and competitors_json
   - Build detailed response

5. Response format:
   ```json
   {
     "grid_id": "DHA-Phase2-Cell-07",
     "gos": 0.82,
     "confidence": 0.78,
     "metrics": {
       "business_count": 2,
       "instagram_volume": 48,
       "reddit_mentions": 15
     },
     "top_posts": [
       {
         "source": "simulated",
         "text": "Looking for a good gym in Phase 2...",
         "timestamp": "2025-10-28T14:30:00Z",
         "link": "https://simulated.example/abc123"
       }
     ],
     "competitors": [
       {
         "name": "FitZone Gym",
         "distance_km": 0.3,
         "rating": 4.5
       }
     ]
   }
   ```

6. Error handling:
   - grid_id not found -> 404 "Grid not found"

Use scoring_service helper functions if available (get_top_posts, get_competitors).
```

---

## Prompt 7: Create Feedback Router

```
Create the feedback submission endpoint.

Please create `backend/api/routers/feedback.py`:

1. Endpoint: POST /api/v1/feedback

2. Request body:
   ```json
   {
     "grid_id": "DHA-Phase2-Cell-07",
     "category": "Gym",
     "rating": 1,
     "comment": "Great recommendation!",
     "user_email": "user@example.com"
   }
   ```

3. Validation:
   - grid_id: required, must exist in grid_cells
   - category: required
   - rating: required, must be -1 or 1
   - comment: optional, max 500 chars
   - user_email: optional

4. Logic:
   - Insert into user_feedback table
   - Return 201 Created

5. Response:
   ```json
   {
     "message": "Feedback received",
     "id": 123
   }
   ```

6. Error handling:
   - Invalid grid_id -> 404 "Grid not found"
   - Validation error -> 422 with details

7. Add logging:
   - Log all feedback submissions
   - Track rating distribution (for future analysis)

This endpoint is optional for MVP but good to have for pilot testing.
```

---

## Prompt 8: Wire Up All Routers to Main App

```
Connect all routers to the main FastAPI app.

Update `backend/api/main.py`:

1. Import all routers:
   - from api.routers import neighborhoods, grids, recommendations, grid_detail, feedback

2. Include routers with prefix "/api/v1":
   ```python
   app.include_router(neighborhoods.router, prefix="/api/v1", tags=["neighborhoods"])
   app.include_router(grids.router, prefix="/api/v1", tags=["grids"])
   app.include_router(recommendations.router, prefix="/api/v1", tags=["recommendations"])
   app.include_router(grid_detail.router, prefix="/api/v1", tags=["grid"])
   app.include_router(feedback.router, prefix="/api/v1", tags=["feedback"])
   ```

3. Add startup event:
   - Log "API starting..."
   - Verify database connection
   - Log "API ready"

4. Add shutdown event:
   - Log "API shutting down..."
   - Close database connections

Test locally:
```powershell
cd backend
uvicorn api.main:app --reload --port 8000
```

Open browser: http://localhost:8000/docs (Swagger UI)
Verify all 6 endpoints listed.
```

---

## Prompt 9: Create API Tests

```
Create comprehensive API tests.

Please create `backend/tests/api/test_api.py`:

1. Use pytest and TestClient from FastAPI

2. Test each endpoint:
   - test_health_check: GET /health -> 200 OK
   - test_get_neighborhoods: GET /neighborhoods -> returns list
   - test_get_grids: GET /grids?neighborhood=DHA-Phase2&category=Gym -> returns grids
   - test_get_grids_invalid_neighborhood: 404
   - test_get_recommendations: GET /recommendations -> top 3
   - test_get_recommendations_with_limit: limit parameter works
   - test_get_grid_detail: GET /grid/{grid_id} -> detailed response
   - test_get_grid_detail_not_found: 404
   - test_post_feedback: POST /feedback -> 201
   - test_post_feedback_invalid_rating: 422

3. Use test database with seeded data

4. Test CORS headers present

5. Test error responses have correct format

6. Coverage target: ≥85%

Run tests:
```powershell
pytest backend/tests/api/ -v --cov=backend/api --cov-report=term
```
```

---

## Prompt 10: Create Deployment Configuration (Docker)

```
Create Docker configuration for backend deployment.

Please create `backend/Dockerfile`:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Create `backend/.dockerignore`:
```
__pycache__
*.pyc
.env
.pytest_cache
venv/
tests/
data/raw/
*.sqlite
```

Create `docker-compose.yml` (for local testing):
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:14
    environment:
      POSTGRES_DB: startsmart_dev
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  api:
    build:
      context: ./backend
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://postgres:postgres@postgres:5432/startsmart_dev
      GOOGLE_PLACES_API_KEY: ${GOOGLE_PLACES_API_KEY}
    depends_on:
      - postgres

volumes:
  postgres_data:
```

Test:
```powershell
docker-compose up --build
# Test API: http://localhost:8000/docs
```
```

---

## Prompt 11: Set Up Deployment on Render

```
Create deployment configuration for Render.

Please create `render.yaml`:

```yaml
services:
  - type: web
    name: startsmart-api
    env: python
    region: oregon
    plan: free
    buildCommand: "cd backend && pip install -r requirements.txt"
    startCommand: "cd backend && uvicorn api.main:app --host 0.0.0.0 --port $PORT"
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: startsmart-db
          property: connectionString
      - key: GOOGLE_PLACES_API_KEY
        sync: false
      - key: PYTHON_VERSION
        value: "3.10"

databases:
  - name: startsmart-db
    plan: free
    databaseName: startsmart_prod
    user: startsmart
```

Manual steps (document in README):
1. Create Render account
2. Connect GitHub repo
3. Create Web Service from render.yaml
4. Add environment variable: GOOGLE_PLACES_API_KEY
5. Deploy

After deployment:
- Note the URL: https://startsmart-api.onrender.com
- Test /health endpoint
- Update frontend AppConstants.baseUrl with production URL
```

---

## Prompt 12: Deploy Frontend to Firebase Hosting

```
Deploy Flutter web app to Firebase Hosting.

Steps:

1. Initialize Firebase in frontend directory:
```powershell
cd frontend
firebase login
firebase init hosting
# Select: public directory = build/web
# Configure as single-page app: Yes
# Set up automatic builds: No
```

2. Build Flutter web:
```powershell
flutter build web --release
```

3. Update build/web/index.html to set backend API URL:
   - Add environment variable or config.js with API_BASE_URL

4. Deploy:
```powershell
firebase deploy --only hosting
```

5. Note hosting URL: https://startsmart-mvp.web.app

6. Update CORS in backend to allow this origin

7. Test full flow:
   - Open web app
   - Select category
   - Verify map loads
   - Verify recommendations from REAL API (not mock)

Document deployment URL in PHASE_LOG.md.
```

---

## Prompt 13: Switch Frontend from Mock to Real API

```
Update Flutter app to use real API instead of mock data.

Update `lib/providers/data_provider.dart`:

1. Import ApiService instead of MockDataService

2. Create apiService instance:
   ```dart
   final apiService = ApiService(baseUrl: AppConstants.baseUrl);
   ```

3. Replace all provider implementations:
   ```dart
   final gridsProvider = FutureProvider.family<List<Grid>, Map<String, String>>((ref, params) async {
     return apiService.fetchGrids(params['neighborhood']!, params['category']!);
   });
   // ... same for other providers
   ```

4. Test with local backend first:
   - Set baseUrl = 'http://localhost:8000/api/v1'
   - Run: flutter run -d chrome
   - Verify real data loads

5. Then test with production backend:
   - Set baseUrl = 'https://startsmart-api.onrender.com/api/v1'
   - Rebuild and deploy

6. Add error handling for API failures:
   - Network timeout -> show retry
   - 404 -> show helpful message

Document the switch in PHASE_LOG.md (before/after screenshots).
```

---

## Prompt 14: Create End-to-End Integration Test

```
Create full stack integration test.

Please create `backend/tests/test_e2e.py`:

1. Test full data pipeline:
   - Start with empty grid_metrics table
   - Run scoring for Gym category
   - Verify grid_metrics populated
   - Make API call to /recommendations
   - Verify response matches database
   - Make API call to /grid/{grid_id}
   - Verify detail data correct

2. Test feedback loop:
   - Submit feedback via API
   - Verify stored in database
   - Query feedback table
   - Verify data matches submission

3. Use test database (not production)

4. This test verifies entire system works end-to-end

Run:
```powershell
pytest backend/tests/test_e2e.py -v
```

Also create a manual E2E test checklist:
- [ ] User can select category
- [ ] Map displays with heatmap
- [ ] Recommendations appear
- [ ] Clicking recommendation shows detail
- [ ] Detail screen shows real data (businesses, posts)
- [ ] Feedback submission works (optional)

Document results in PHASE_LOG.md.
```

---

## Prompt 15: Create Load Testing Script

```
Create a simple load test to verify API performance.

Please create `backend/tests/load_test.py`:

Use locust library:

```python
from locust import HttpUser, task, between

class StartSmartUser(HttpUser):
    wait_time = between(1, 3)
    
    @task(3)
    def get_recommendations(self):
        self.client.get("/api/v1/recommendations?neighborhood=DHA-Phase2&category=Gym&limit=3")
    
    @task(2)
    def get_grids(self):
        self.client.get("/api/v1/grids?neighborhood=DHA-Phase2&category=Gym")
    
    @task(1)
    def get_grid_detail(self):
        self.client.get("/api/v1/grid/DHA-Phase2-Cell-07?category=Gym")
```

Run load test:
```powershell
locust -f backend/tests/load_test.py --host http://localhost:8000
# Open browser: http://localhost:8089
# Run with 10 users, spawn rate 1/sec, duration 60sec
```

Acceptance criteria:
- p95 response time < 500ms
- 0% error rate
- Handles 10 concurrent users smoothly

Document results (response times, throughput) in PHASE_LOG.md.
```

---

## Prompt 16: Create Deployment Runbook

```
Create operational documentation.

Please create `docs/DEPLOYMENT.md`:

Document:

1. **Local Development Setup**:
   - Prerequisites
   - Environment variables
   - Database setup
   - Running backend
   - Running frontend

2. **Deployment Process**:
   - Backend deployment steps (Render)
   - Frontend deployment steps (Firebase)
   - Database migrations (how to run)
   - Environment variables (where to set)

3. **Monitoring**:
   - Health check URL
   - Log locations (Render logs)
   - How to check database status

4. **Rollback Procedure**:
   - How to revert to previous version
   - Database rollback (if needed)

5. **Common Issues**:
   - CORS errors -> check allowed origins
   - Database connection failed -> check DATABASE_URL
   - API timeout -> check Render status

6. **Maintenance**:
   - How to update scoring formula (redeploy)
   - How to add new neighborhoods (database + config)
   - How to add new categories

Make it comprehensive enough that a new developer can deploy without help.
```

---

## Prompt 17: Final Validation and Documentation

```
Perform final validation and update all documentation.

1. Create validation checklist and run through it:

**Functional Testing**:
- [ ] All API endpoints return 200/201 (except expected errors)
- [ ] Frontend loads real data from API
- [ ] Heatmap displays correctly
- [ ] Top-3 recommendations make sense (manual review)
- [ ] Grid detail shows actual businesses and posts
- [ ] Cross-origin requests work (web app to API)

**Performance Testing**:
- [ ] API p95 < 500ms (load test results)
- [ ] Frontend loads < 3s on 4G
- [ ] No memory leaks (run for 10 mins, check memory)

**Deployment Testing**:
- [ ] Production API accessible
- [ ] Production frontend accessible
- [ ] Health check endpoint returns OK
- [ ] Database connected

2. Take final screenshots:
   - Full user journey (5-6 screenshots)
   - API docs (Swagger UI)
   - Load test results

3. Create demo script (docs/DEMO_SCRIPT.md):
   - 5-minute presentation flow
   - Key points to highlight
   - Backup plan (if API fails, use local/mock)

4. Update README.md with:
   - Project description
   - Live demo URLs
   - Screenshots
   - Tech stack
   - Setup instructions
   - Team members

Save everything in docs/ directory.
```

---

## Prompt 18: Update PHASE_LOG.md with Phase 4 Handoff

```
Phase 4 is complete. Update PHASE_LOG.md with the final handoff entry.

Append to PHASE_LOG.md following the format from IMPLEMENTATION_PLAN.md Phase 4 section.

Fill in:
- Your name as owner
- Completion date
- All files created
- Deployment URLs (API + Frontend)
- Test results (unit, integration, load, E2E)
- Performance metrics
- Known issues
- Operational notes (monitoring, logs)

Include:
- Final database row counts
- API endpoint list with example URLs
- Frontend URL
- Demo credentials (if any)
- Maintenance instructions

Document:
- What went well
- What was challenging
- Recommendations for future phases

This is the final handoff to showcase to instructors/judges.
```

---

## Phase 4 Completion Checklist

**Before Final Demo**, verify:

- [ ] Backend API deployed and accessible
- [ ] Frontend web app deployed and accessible
- [ ] Database populated with real + synthetic data
- [ ] All API tests passing
- [ ] Load test meets performance criteria
- [ ] End-to-end manual test completed
- [ ] CORS configured correctly
- [ ] Environment variables set in production
- [ ] Health check endpoint working
- [ ] Swagger docs accessible (/docs)
- [ ] README.md comprehensive
- [ ] DEPLOYMENT.md complete
- [ ] DEMO_SCRIPT.md ready
- [ ] Screenshots captured
- [ ] PHASE_LOG.md fully updated
- [ ] No critical bugs or crashes

**Final Demo Preparation**:
1. Test demo flow 3 times (to catch any random failures)
2. Prepare backup (screen recording or local version)
3. Test on different networks (in case firewall issues)
4. Have URLs ready in browser tabs
5. Practice 5-minute pitch

**Deliverables Checklist**:
- [ ] Live web app URL
- [ ] Live API URL
- [ ] GitHub repo (clean, organized)
- [ ] PHASE_LOG.md (comprehensive)
- [ ] Demo video (5 mins)
- [ ] Presentation slides (optional but recommended)

**CONGRATULATIONS!** 🎉 
If all checks pass, your MVP is ready for investors, judges, and the next phase of your startup journey!

---

## Post-MVP: Phase 5 Preview

After successful demo, consider:

1. **Real-time Social Data Integration**:
   - Replace SimulatedSocialAdapter with real Instagram/Reddit adapters
   - Requires legal review and API access

2. **ML-Based Scoring**:
   - Train model on pilot feedback
   - Replace formula with XGBoost/neural net

3. **Multi-City Expansion**:
   - Add Lahore, Islamabad
   - Abstract city-specific config

4. **B2B Features**:
   - White-label for real estate consultants
   - PDF report generation
   - Client dashboard

5. **Mobile Apps**:
   - Native Android/iOS builds
   - Push notifications for new opportunities

6. **Advanced Analytics**:
   - Temporal trends (opportunity over time)
   - Competitive analysis dashboard
   - ROI prediction

Document Phase 5 ideas but focus on MVP perfection first!
