"""Basic tests for Isac Achadinhos Fase 1."""
from fastapi.testclient import TestClient
from app.main import app


class TestHealth:
    """Test the /health endpoint."""

    def test_health_endpoint(self):
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"


class TestConfig:
    """Test the configuration loading."""

    def test_settings_load(self):
        from app.config import Settings
        settings = Settings()
        assert settings.database_url != ""
        assert settings.environment == "development"
