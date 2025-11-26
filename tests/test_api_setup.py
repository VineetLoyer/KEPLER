"""Unit tests for API setup

Tests CORS configuration and health endpoint.
Validates: Requirements 10.1
"""
import pytest
from fastapi.testclient import TestClient
from src.api.app import create_app
from src.api.config import APISettings


@pytest.fixture
def test_settings():
    """Create test API settings"""
    return APISettings(
        host="127.0.0.1",
        port=8000,
        cors_origins=["http://localhost:3000", "http://localhost:5173"],
        environment="test",
        log_level="DEBUG",
    )


@pytest.fixture
def client(test_settings):
    """Create test client"""
    app = create_app(test_settings)
    return TestClient(app)


class TestCORSConfiguration:
    """Test CORS middleware configuration"""
    
    def test_cors_allows_configured_origins(self, client):
        """Test that CORS allows requests from configured origins"""
        response = client.get(
            "/api/health",
            headers={"Origin": "http://localhost:3000"}
        )
        
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers
    
    def test_cors_allows_credentials(self, client):
        """Test that CORS allows credentials"""
        response = client.options(
            "/api/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            }
        )
        
        assert "access-control-allow-credentials" in response.headers
        assert response.headers["access-control-allow-credentials"] == "true"
    
    def test_cors_allows_all_methods(self, client):
        """Test that CORS allows all HTTP methods"""
        response = client.options(
            "/api/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
            }
        )
        
        assert "access-control-allow-methods" in response.headers
        # FastAPI CORS middleware returns "*" for allow_methods=["*"]
        allowed_methods = response.headers.get("access-control-allow-methods", "")
        assert "*" in allowed_methods or "POST" in allowed_methods
    
    def test_cors_allows_all_headers(self, client):
        """Test that CORS allows all headers"""
        response = client.options(
            "/api/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "content-type,authorization",
            }
        )
        
        assert "access-control-allow-headers" in response.headers


class TestHealthEndpoint:
    """Test health check endpoint"""
    
    def test_health_endpoint_returns_200(self, client):
        """Test that health endpoint returns 200 status"""
        response = client.get("/api/health")
        assert response.status_code == 200
    
    def test_health_endpoint_returns_correct_structure(self, client):
        """Test that health endpoint returns correct JSON structure"""
        response = client.get("/api/health")
        data = response.json()
        
        assert "status" in data
        assert "version" in data
    
    def test_health_endpoint_returns_healthy_status(self, client):
        """Test that health endpoint returns 'healthy' status"""
        response = client.get("/api/health")
        data = response.json()
        
        assert data["status"] == "healthy"
    
    def test_health_endpoint_returns_version(self, client):
        """Test that health endpoint returns version string"""
        response = client.get("/api/health")
        data = response.json()
        
        assert isinstance(data["version"], str)
        assert len(data["version"]) > 0
    
    def test_health_endpoint_content_type(self, client):
        """Test that health endpoint returns JSON content type"""
        response = client.get("/api/health")
        
        assert "application/json" in response.headers["content-type"]


class TestAPIConfiguration:
    """Test API configuration"""
    
    def test_api_settings_from_defaults(self):
        """Test that API settings can be created with defaults"""
        settings = APISettings()
        
        assert settings.host == "0.0.0.0"
        assert settings.port == 8000
        assert settings.cors_origins == ["*"]
        assert settings.environment == "development"
        assert settings.log_level == "INFO"
    
    def test_api_settings_custom_values(self):
        """Test that API settings can be created with custom values"""
        settings = APISettings(
            host="127.0.0.1",
            port=9000,
            cors_origins=["http://example.com"],
            environment="production",
            log_level="ERROR",
        )
        
        assert settings.host == "127.0.0.1"
        assert settings.port == 9000
        assert settings.cors_origins == ["http://example.com"]
        assert settings.environment == "production"
        assert settings.log_level == "ERROR"
    
    def test_app_creation_with_settings(self, test_settings):
        """Test that app can be created with custom settings"""
        app = create_app(test_settings)
        
        assert app is not None
        assert app.title == "KEPLER API"
        assert app.version == "1.0.0"
    
    def test_app_stores_settings_in_state(self, test_settings):
        """Test that app stores settings in state"""
        app = create_app(test_settings)
        
        assert hasattr(app.state, "settings")
        assert app.state.settings == test_settings


class TestAPIDocumentation:
    """Test API documentation endpoints"""
    
    def test_openapi_schema_available(self, client):
        """Test that OpenAPI schema is available"""
        response = client.get("/api/openapi.json")
        assert response.status_code == 200
    
    def test_docs_endpoint_available(self, client):
        """Test that Swagger UI docs are available"""
        response = client.get("/api/docs")
        assert response.status_code == 200
    
    def test_redoc_endpoint_available(self, client):
        """Test that ReDoc documentation is available"""
        response = client.get("/api/redoc")
        assert response.status_code == 200
