"""Testes Fase 5 — campanhas, rastreamento de cliques e métricas.

Usa SQLite em memória: nenhum Postgres/Redis necessário.
"""
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
import app.models  # noqa: F401 — registra todos os modelos antes de criar tabelas
from app.main import app
from app.models.campaign import Campaign
from app.models.click_event import ClickEvent
from app.models.product import Product
from app.routers import auth as auth_router
from app.routers import campaigns as campaigns_router
from app.routers import metrics as metrics_router
from app.routers import offers as offers_router

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


for _mod in (auth_router, campaigns_router, metrics_router, offers_router):
    app.dependency_overrides[_mod.get_db] = _override_get_db


@pytest.fixture(autouse=True)
def _db():
    for _mod in (auth_router, campaigns_router, metrics_router, offers_router):
        app.dependency_overrides[_mod.get_db] = _override_get_db
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    app.dependency_overrides.clear()
    for _mod in (auth_router, campaigns_router, metrics_router, offers_router):
        app.dependency_overrides[_mod.get_db] = _override_get_db


def _seed_product(affiliate_url="https://afiliado.exemplo/oferta-1"):
    db = TestingSessionLocal()
    camp = Campaign(name="Black Friday", slug="black-friday", is_active=True)
    db.add(camp)
    db.flush()
    prod = Product(
        name="Fone Top",
        slug="fone-top",
        price=Decimal("199.90"),
        affiliate_url=affiliate_url,
        campaign_id=camp.id,
        is_active=True,
    )
    db.add(prod)
    db.commit()
    ids = (camp.id, prod.id)
    db.close()
    return ids


class TestCampaignAPI:
    def test_crud_cycle(self):
        client = TestClient(app, raise_server_exceptions=False)
        r = client.post(
            "/api/campaigns/",
            json={"name": "Natal", "slug": "natal"},
        )
        assert r.status_code == 201
        cid = r.json()["id"]

        r = client.get("/api/campaigns/")
        assert r.status_code == 200
        assert any(c["slug"] == "natal" for c in r.json())

        r = client.get(f"/api/campaigns/{cid}")
        assert r.status_code == 200
        assert r.json()["name"] == "Natal"

        r = client.put(
            f"/api/campaigns/{cid}", json={"name": "Natal 2026"}
        )
        assert r.status_code == 200
        assert r.json()["name"] == "Natal 2026"

        r = client.delete(f"/api/campaigns/{cid}")
        assert r.status_code == 200

        db = TestingSessionLocal()
        camp = db.query(Campaign).filter(Campaign.id == cid).first()
        assert camp is not None and camp.is_active is False
        db.close()

    def test_invalid_slug_rejected(self):
        client = TestClient(app, raise_server_exceptions=False)
        r = client.post(
            "/api/campaigns/",
            json={"name": "X", "slug": "Slug Inválido!"},
        )
        assert r.status_code == 422

    def test_inconsistent_period_rejected(self):
        client = TestClient(app, raise_server_exceptions=False)
        r = client.post(
            "/api/campaigns/",
            json={
                "name": "Y",
                "slug": "y-camp",
                "starts_at": "2026-12-31T00:00:00Z",
                "ends_at": "2026-01-01T00:00:00Z",
            },
        )
        assert r.status_code == 422

    def test_get_missing_returns_404(self):
        client = TestClient(app, raise_server_exceptions=False)
        assert client.get("/api/campaigns/9999").status_code == 404


class TestOfferRedirect:
    def test_redirect_logs_click(self):
        camp_id, prod_id = _seed_product()
        client = TestClient(app, raise_server_exceptions=False)
        r = client.get("/r/fone-top", follow_redirects=False)
        assert r.status_code == 302
        assert r.headers["location"] == "https://afiliado.exemplo/oferta-1"

        db = TestingSessionLocal()
        events = db.query(ClickEvent).all()
        assert len(events) == 1
        assert events[0].product_id == prod_id
        assert events[0].campaign_id == camp_id
        # privacidade: hash, nunca IP cru
        assert events[0].ip_hash is not None
        assert len(events[0].ip_hash) == 64
        assert "127.0.0.1" not in (events[0].ip_hash or "")
        db.close()

    def test_redirect_without_affiliate_goes_home(self):
        _seed_product(affiliate_url=None)
        # affiliate_url None viola NOT NULL? modelo permite NULL -> ok
        client = TestClient(app, raise_server_exceptions=False)
        r = client.get("/r/fone-top", follow_redirects=False)
        assert r.status_code == 302
        assert r.headers["location"] == "/"

    def test_redirect_unknown_slug_404(self):
        client = TestClient(app, raise_server_exceptions=False)
        assert client.get("/r/nao-existe").status_code == 404


class TestMetrics:
    def test_summary_aggregates(self):
        _seed_product()
        client = TestClient(app, raise_server_exceptions=False)
        client.get("/r/fone-top")
        client.get("/r/fone-top")

        r = client.get("/api/metrics/summary")
        assert r.status_code == 200
        data = r.json()
        assert data["total_clicks"] == 2
        assert data["active_products"] == 1
        assert data["active_campaigns"] == 1
        assert data["top_products"][0]["product_slug"] == "fone-top"
        assert data["top_products"][0]["clicks"] == 2
        assert data["by_campaign"][0]["campaign_slug"] == "black-friday"
        assert data["by_campaign"][0]["clicks"] == 2
        assert len(data["by_day"]) >= 1
        assert data["by_day"][-1]["clicks"] == 2

    def test_summary_empty(self):
        client = TestClient(app, raise_server_exceptions=False)
        r = client.get("/api/metrics/summary")
        assert r.status_code == 200
        assert r.json()["total_clicks"] == 0

    def test_metrics_admin_requires_login(self):
        client = TestClient(app, follow_redirects=False)
        r = client.get("/admin/metrics")
        assert r.status_code in (303, 307)
        assert "/admin/login" in r.headers.get("location", "")
