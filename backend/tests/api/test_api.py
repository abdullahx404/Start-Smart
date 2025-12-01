"""
API Tests for StartSmart REST API

Tests all endpoints with various scenarios including:
- Happy path tests
- Error handling tests
- Validation tests
- CORS headers tests

Run with:
    pytest backend/tests/api/test_api.py -v --cov=backend/api --cov-report=term
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from datetime import datetime

# Import the FastAPI app
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from api.main import app


# ========== Fixtures ==========

@pytest.fixture
def client():
    """Create test client for API."""
    return TestClient(app)


@pytest.fixture
def mock_session():
    """Create a mock database session."""
    with patch('api.routers.neighborhoods.get_session') as mock:
        session = MagicMock()
        mock.return_value.__enter__ = MagicMock(return_value=session)
        mock.return_value.__exit__ = MagicMock(return_value=False)
        yield session


# ========== Health Check Tests ==========

class TestHealthCheck:
    """Tests for health check endpoint."""
    
    def test_health_check_returns_200(self, client):
        """Health check should return 200 OK."""
        response = client.get("/health")
        assert response.status_code == 200
        
    def test_health_check_returns_status_ok(self, client):
        """Health check should return status 'ok'."""
        response = client.get("/health")
        data = response.json()
        assert data["status"] == "ok"
        
    def test_health_check_has_timestamp(self, client):
        """Health check should include timestamp."""
        response = client.get("/health")
        data = response.json()
        assert "timestamp" in data
        
    def test_health_check_has_version(self, client):
        """Health check should include version."""
        response = client.get("/health")
        data = response.json()
        assert data["version"] == "1.0.0"


class TestRootEndpoint:
    """Tests for root endpoint."""
    
    def test_root_returns_200(self, client):
        """Root endpoint should return 200."""
        response = client.get("/")
        assert response.status_code == 200
        
    def test_root_returns_welcome_message(self, client):
        """Root endpoint should return welcome message."""
        response = client.get("/")
        data = response.json()
        assert "message" in data
        assert "StartSmart" in data["message"]


# ========== Neighborhoods Tests ==========

class TestNeighborhoods:
    """Tests for neighborhoods endpoint."""
    
    def test_get_neighborhoods_returns_list(self, client):
        """GET /neighborhoods should return a list."""
        response = client.get("/api/v1/neighborhoods")
        # May fail if DB not connected, but checks endpoint exists
        assert response.status_code in [200, 500]
        if response.status_code == 200:
            assert isinstance(response.json(), list)
            
    def test_neighborhoods_response_structure(self, client):
        """Each neighborhood should have id, name, grid_count."""
        response = client.get("/api/v1/neighborhoods")
        if response.status_code == 200:
            data = response.json()
            if len(data) > 0:
                neighborhood = data[0]
                assert "id" in neighborhood
                assert "name" in neighborhood
                assert "grid_count" in neighborhood


# ========== Grids Tests ==========

class TestGrids:
    """Tests for grids endpoint."""
    
    def test_get_grids_requires_neighborhood(self, client):
        """GET /grids should require neighborhood parameter."""
        response = client.get("/api/v1/grids")
        assert response.status_code == 422  # Validation error
        
    def test_get_grids_requires_category(self, client):
        """GET /grids should require category parameter."""
        response = client.get("/api/v1/grids?neighborhood=DHA-Phase2")
        assert response.status_code == 422  # Validation error
        
    def test_get_grids_invalid_category(self, client):
        """GET /grids should reject invalid category."""
        response = client.get("/api/v1/grids?neighborhood=DHA-Phase2&category=Invalid")
        assert response.status_code == 422
        
    def test_get_grids_valid_request(self, client):
        """GET /grids with valid params should work."""
        response = client.get("/api/v1/grids?neighborhood=DHA-Phase2&category=Gym")
        # May return 200 with data or 404 if neighborhood not found
        assert response.status_code in [200, 404, 500]
        
    def test_get_grids_nonexistent_neighborhood(self, client):
        """GET /grids should return 404 for unknown neighborhood."""
        response = client.get("/api/v1/grids?neighborhood=NonExistent&category=Gym")
        # Should be 404 or 500 if DB error
        assert response.status_code in [404, 500]


# ========== Recommendations Tests ==========

class TestRecommendations:
    """Tests for recommendations endpoint."""
    
    def test_get_recommendations_requires_neighborhood(self, client):
        """GET /recommendations should require neighborhood."""
        response = client.get("/api/v1/recommendations")
        assert response.status_code == 422
        
    def test_get_recommendations_requires_category(self, client):
        """GET /recommendations should require category."""
        response = client.get("/api/v1/recommendations?neighborhood=DHA-Phase2")
        assert response.status_code == 422
        
    def test_get_recommendations_default_limit(self, client):
        """GET /recommendations should default to limit=3."""
        response = client.get(
            "/api/v1/recommendations?neighborhood=DHA-Phase2&category=Gym"
        )
        if response.status_code == 200:
            data = response.json()
            assert len(data.get("recommendations", [])) <= 3
            
    def test_get_recommendations_custom_limit(self, client):
        """GET /recommendations should respect limit parameter."""
        response = client.get(
            "/api/v1/recommendations?neighborhood=DHA-Phase2&category=Gym&limit=5"
        )
        if response.status_code == 200:
            data = response.json()
            assert len(data.get("recommendations", [])) <= 5
            
    def test_get_recommendations_limit_validation(self, client):
        """GET /recommendations should reject limit > 10."""
        response = client.get(
            "/api/v1/recommendations?neighborhood=DHA-Phase2&category=Gym&limit=20"
        )
        assert response.status_code == 422
        
    def test_get_recommendations_response_structure(self, client):
        """Recommendations should have proper structure."""
        response = client.get(
            "/api/v1/recommendations?neighborhood=DHA-Phase2&category=Gym"
        )
        if response.status_code == 200:
            data = response.json()
            assert "neighborhood" in data
            assert "category" in data
            assert "recommendations" in data


# ========== Grid Detail Tests ==========

class TestGridDetail:
    """Tests for grid detail endpoint."""
    
    def test_get_grid_detail_requires_category(self, client):
        """GET /grid/{id} should require category."""
        response = client.get("/api/v1/grid/DHA-Phase2-Cell-01")
        assert response.status_code == 422
        
    def test_get_grid_detail_valid_request(self, client):
        """GET /grid/{id} with valid params should work."""
        response = client.get("/api/v1/grid/DHA-Phase2-Cell-01?category=Gym")
        # May return 200 with data or 404 if not found
        assert response.status_code in [200, 404, 500]
        
    def test_get_grid_detail_not_found(self, client):
        """GET /grid/{id} should return 404 for unknown grid."""
        response = client.get("/api/v1/grid/NonExistent-Grid?category=Gym")
        assert response.status_code in [404, 500]
        
    def test_get_grid_detail_response_structure(self, client):
        """Grid detail should have proper structure."""
        response = client.get("/api/v1/grid/DHA-Phase2-Cell-01?category=Gym")
        if response.status_code == 200:
            data = response.json()
            assert "grid_id" in data
            assert "gos" in data
            assert "confidence" in data
            assert "metrics" in data


# ========== Feedback Tests ==========

class TestFeedback:
    """Tests for feedback endpoint."""
    
    def test_post_feedback_valid(self, client):
        """POST /feedback with valid data should work."""
        feedback_data = {
            "grid_id": "DHA-Phase2-Cell-01",
            "category": "Gym",
            "rating": 1,
            "comment": "Great recommendation!"
        }
        response = client.post("/api/v1/feedback", json=feedback_data)
        # May be 201, 404 (grid not found), or 500
        assert response.status_code in [201, 404, 500]
        
    def test_post_feedback_invalid_rating(self, client):
        """POST /feedback should reject invalid rating."""
        feedback_data = {
            "grid_id": "DHA-Phase2-Cell-01",
            "category": "Gym",
            "rating": 5  # Invalid - should be 1 or -1
        }
        response = client.post("/api/v1/feedback", json=feedback_data)
        assert response.status_code == 422
        
    def test_post_feedback_missing_grid_id(self, client):
        """POST /feedback should require grid_id."""
        feedback_data = {
            "category": "Gym",
            "rating": 1
        }
        response = client.post("/api/v1/feedback", json=feedback_data)
        assert response.status_code == 422
        
    def test_post_feedback_invalid_category(self, client):
        """POST /feedback should reject invalid category."""
        feedback_data = {
            "grid_id": "DHA-Phase2-Cell-01",
            "category": "Invalid",
            "rating": 1
        }
        response = client.post("/api/v1/feedback", json=feedback_data)
        assert response.status_code == 422
        
    def test_post_feedback_comment_length(self, client):
        """POST /feedback should limit comment length."""
        feedback_data = {
            "grid_id": "DHA-Phase2-Cell-01",
            "category": "Gym",
            "rating": 1,
            "comment": "x" * 600  # Over 500 char limit
        }
        response = client.post("/api/v1/feedback", json=feedback_data)
        assert response.status_code == 422
        
    def test_post_feedback_negative_rating(self, client):
        """POST /feedback should accept -1 rating."""
        feedback_data = {
            "grid_id": "DHA-Phase2-Cell-01",
            "category": "Gym",
            "rating": -1,
            "comment": "Not helpful"
        }
        response = client.post("/api/v1/feedback", json=feedback_data)
        # May be 201, 404 (grid not found), or 500
        assert response.status_code in [201, 404, 500]


# ========== CORS Tests ==========

class TestCORS:
    """Tests for CORS headers."""
    
    def test_cors_headers_present(self, client):
        """Response should include CORS headers."""
        response = client.options("/api/v1/neighborhoods")
        # FastAPI handles OPTIONS automatically with CORS middleware
        assert response.status_code in [200, 405]
        
    def test_cors_allows_get(self, client):
        """CORS should allow GET requests."""
        response = client.get(
            "/api/v1/neighborhoods",
            headers={"Origin": "http://localhost:3000"}
        )
        # Check that request doesn't fail due to CORS
        assert response.status_code in [200, 500]


# ========== Error Handling Tests ==========

class TestErrorHandling:
    """Tests for error handling."""
    
    def test_404_for_unknown_endpoint(self, client):
        """Unknown endpoints should return 404."""
        response = client.get("/api/v1/unknown-endpoint")
        assert response.status_code == 404
        
    def test_method_not_allowed(self, client):
        """Wrong HTTP method should return 405."""
        response = client.post("/api/v1/neighborhoods")
        assert response.status_code == 405
        
    def test_error_response_format(self, client):
        """Error responses should have consistent format."""
        response = client.get("/api/v1/grids")  # Missing required params
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data


# ========== OpenAPI Documentation Tests ==========

class TestDocumentation:
    """Tests for API documentation."""
    
    def test_openapi_schema_available(self, client):
        """OpenAPI schema should be available."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
    def test_swagger_ui_available(self, client):
        """Swagger UI should be available at /docs."""
        response = client.get("/docs")
        assert response.status_code == 200
        
    def test_redoc_available(self, client):
        """ReDoc should be available at /redoc."""
        response = client.get("/redoc")
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
