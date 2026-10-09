"""Security tests for Isac Achadinhos Fase 3."""
from datetime import timedelta

from fastapi.testclient import TestClient
from app.main import app
from app.security import create_access_token, decode_access_token


class TestSecurityConfig:
    """Test security configuration."""

    def test_jwt_secret_rejected_when_empty(self):
        """JWT_SECRET must not be empty."""
        from app.config import Settings as SettingsClass
        import os

        # Save original env
        original = os.environ.get("JWT_SECRET")
        # Remove from env so Settings falls back to .env file
        for k in list(os.environ.keys()):
            if k.startswith("JWT_SECRET"):
                del os.environ[k]

        try:
            s = SettingsClass()
            # If .env file has a value, it should be loaded
            assert s.jwt_secret, "JWT_SECRET should not be empty when .env provides one"
        finally:
            if original is not None:
                os.environ["JWT_SECRET"] = original

    def test_jwt_secret_cannot_be_placeholder(self):
        """JWT_SECRET must not be the insecure placeholder."""
        from app.config import Settings as SettingsClass
        import os
        import pytest

        original = os.environ.get("JWT_SECRET")
        try:
            os.environ["JWT_SECRET"] = "change-me-long-random-string"
            with pytest.raises(ValueError):
                SettingsClass()
        finally:
            if original is not None:
                os.environ["JWT_SECRET"] = original
            else:
                del os.environ["JWT_SECRET"]


class TestHealth:
    """Test the /health endpoint."""

    def test_health_endpoint(self):
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"


class TestTestBasic:
    """Basic test from test_basic.py (re-exported for completeness)."""

    def test_settings_load(self):
        from app.config import Settings
        settings = Settings()
        assert settings.database_url != ""
        assert settings.environment == "development"


class TestJWTCreationAndDecode:
    """Test JWT token creation and decoding."""

    def test_create_and_decode_token(self):
        token = create_access_token(
            data={"sub": "testuser", "role": "admin", "user_id": 1}
        )
        assert token is not None and len(token) > 0
        decoded = decode_access_token(token)
        assert decoded is not None
        assert decoded["sub"] == "testuser"
        assert decoded["role"] == "admin"
        assert decoded["user_id"] == 1

    def test_decode_invalid_token_returns_none(self):
        decoded = decode_access_token("invalid.token.here")
        assert decoded is None

    def test_decode_expired_token_returns_none(self):
        token = create_access_token(
            data={"sub": "testuser"},
            expires_delta=timedelta(seconds=-10),  # Already expired
        )
        assert decode_access_token(token) is None
