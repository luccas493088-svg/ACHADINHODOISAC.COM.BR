"""Testes Fase 6 — webhooks HMAC (SQLite em memória, sem I/O externo)."""
import hashlib
import hmac
import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
import app.models  # noqa: F401 — registra todos os modelos
from app.main import app
from app.models.conversion_event import ConversionEvent
from app.models.product import Product
from app.routers import webhooks as webhooks_router

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[webhooks_router.get_db] = _override_get_db


@pytest.fixture(autouse=True)
def _db():
    app.dependency_overrides[webhooks_router.get_db] = _override_get_db
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    app.dependency_overrides.clear()
    app.dependency_overrides[webhooks_router.get_db] = _override_get_db


SECRET = "segredo-de-teste"


def _sign(body: bytes) -> str:
    digest = hmac.new(SECRET.encode(), body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def _post(client, network="amazon", payload=None, raw=None, secret=SECRET):
    body = raw if raw is not None else json.dumps(payload).encode()
    headers = {"X-Signature": _sign(body)} if secret else {}
    if secret and secret != SECRET:
        digest = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        headers = {"X-Signature": f"sha256={digest}"}
    return client.post(
        f"/api/webhooks/{network}", content=body, headers=headers
    )


class TestWebhookFlow:
    def test_created(self, monkeypatch):
        monkeypatch.setenv("AMAZON_WEBHOOK_SECRET", SECRET)
        client = TestClient(app, raise_server_exceptions=False)
        r = _post(client, payload={"external_id": "PED-1", "amount": "99.90"})
        assert r.status_code == 200, r.text
        assert r.json()["status"] == "created"
        assert r.json()["event_id"]

    def test_duplicate_idempotent(self, monkeypatch):
        monkeypatch.setenv("AMAZON_WEBHOOK_SECRET", SECRET)
        client = TestClient(app, raise_server_exceptions=False)
        payload = {"external_id": "PED-2"}
        first = _post(client, payload=payload).json()
        second = _post(client, payload=payload).json()
        assert second["status"] == "duplicate"
        assert second["event_id"] == first["event_id"]
        db = TestingSessionLocal()
        count = db.query(ConversionEvent).count()
        db.close()
        assert count == 1

    def test_resolves_product_and_campaign(self, monkeypatch):
        monkeypatch.setenv("AMAZON_WEBHOOK_SECRET", SECRET)
        db = TestingSessionLocal()
        db.add(Product(name="P", slug="p-web", price=10, is_active=True))
        db.commit()
        db.close()
        client = TestClient(app, raise_server_exceptions=False)
        r = _post(
            client, payload={"external_id": "PED-3", "product_slug": "p-web"}
        )
        assert r.status_code == 200
        db = TestingSessionLocal()
        ev = db.query(ConversionEvent).filter_by(external_id="PED-3").first()
        assert ev is not None and ev.product_id is not None
        db.close()


class TestWebhookSecurity:
    def test_wrong_signature_401(self, monkeypatch):
        monkeypatch.setenv("AMAZON_WEBHOOK_SECRET", SECRET)
        client = TestClient(app, raise_server_exceptions=False)
        r = _post(client, payload={"external_id": "X"}, secret="errado")
        assert r.status_code == 401

    def test_missing_signature_401(self, monkeypatch):
        monkeypatch.setenv("AMAZON_WEBHOOK_SECRET", SECRET)
        client = TestClient(app, raise_server_exceptions=False)
        r = client.post("/api/webhooks/amazon", json={"external_id": "X"})
        assert r.status_code == 401

    def test_no_secret_configured_401(self, monkeypatch):
        monkeypatch.delenv("AMAZON_WEBHOOK_SECRET", raising=False)
        client = TestClient(app, raise_server_exceptions=False)
        r = client.post("/api/webhooks/amazon", json={"external_id": "X"})
        assert r.status_code == 401

    def test_unknown_network_404(self):
        client = TestClient(app, raise_server_exceptions=False)
        r = client.post("/api/webhooks/nope", json={"external_id": "X"})
        assert r.status_code == 404

    def test_invalid_json_422(self, monkeypatch):
        monkeypatch.setenv("AMAZON_WEBHOOK_SECRET", SECRET)
        client = TestClient(app, raise_server_exceptions=False)
        r = _post(client, raw=b"nao-e-json{")
        assert r.status_code == 422

    def test_missing_external_id_422(self, monkeypatch):
        monkeypatch.setenv("AMAZON_WEBHOOK_SECRET", SECRET)
        client = TestClient(app, raise_server_exceptions=False)
        r = _post(client, payload={"amount": "10.00"})
        assert r.status_code == 422
