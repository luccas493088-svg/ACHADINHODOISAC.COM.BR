"""Testes Fase 6 — job de sincronia + scheduler (offline, sem I/O)."""
import socket

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
import app.models  # noqa: F401 — registra todos os modelos
from app.jobs import scheduler
from app.jobs.sync import infer_network, run_sync_report
from app.main import app
from app.models.product import Product
from app.routers import auth as auth_router
from app.routers import jobs as jobs_router
from app.security import hash_password

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


@pytest.fixture(autouse=True)
def _db():
    for _mod in (auth_router, jobs_router):
        app.dependency_overrides[_mod.get_db] = _override_get_db
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    app.dependency_overrides.clear()
    for _mod in (auth_router, jobs_router):
        app.dependency_overrides[_mod.get_db] = _override_get_db


class TestInferNetwork:
    def test_hosts_conhecidos(self):
        assert infer_network("https://www.amazon.com.br/dp/B0X") == "amazon"
        assert (
            infer_network("https://www.mercadolivre.com.br/itm/MLB1")
            == "mercadolivre"
        )
        assert (
            infer_network("https://app.monetizze.com.br/r/A_1") == "monetizze"
        )
        assert infer_network("https://www.tiktok.com/shop/x") == "tiktok"

    def test_sem_link_e_invalido(self):
        assert infer_network(None) == "sem-link"
        assert infer_network("") == "sem-link"
        assert infer_network("nao-url") == "invalido"

    def test_outro_host(self):
        assert infer_network("https://www.example.com/oferta") == "outro"


def _seed():
    db = TestingSessionLocal()
    db.add_all(
        [
            Product(
                name="A",
                slug="a",
                price=10,
                affiliate_url="https://www.amazon.com.br/dp/B0A",
                is_active=True,
            ),
            Product(name="B", slug="b", price=20, is_active=True),
            Product(
                name="C",
                slug="c",
                price=30,
                affiliate_url="lixo-sem-host",
                is_active=True,
            ),
            Product(
                name="D",
                slug="d",
                price=40,
                affiliate_url="https://x.com/o",
                is_active=False,
            ),
        ]
    )
    db.commit()
    db.close()


class TestSyncReport:
    def test_relatorio_sem_io(self, monkeypatch):
        def _bomba(*args, **kwargs):
            raise AssertionError("tentou I/O de rede!")

        monkeypatch.setattr(socket, "socket", _bomba)
        _seed()
        db = TestingSessionLocal()
        report = run_sync_report(db)
        db.close()
        assert report["checked"] == 3  # D inativo fica fora
        assert report["with_links"] == 1
        assert report["without_links"] == 1
        assert report["invalid_links"] == 1
        assert report["by_network"]["amazon"] == 1
        assert report["live"] is False
        assert len(report["missing"]) == 1
        assert len(report["invalid"]) == 1

    def test_filtro_por_rede(self):
        _seed()
        db = TestingSessionLocal()
        report = run_sync_report(db, network="amazon")
        db.close()
        assert report["checked"] == 1
        assert report["with_links"] == 1


class FakeUser:
    id = 1
    username = "admin"
    role = "admin"
    is_active = True
    password_hash = None

    def __init__(self):
        self.password_hash = hash_password("secret123")


class FakeQuery:
    def __init__(self, user):
        self._user = user

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self._user


class FakeDB:
    def __init__(self, user):
        self._user = user

    def query(self, *args, **kwargs):
        return FakeQuery(self._user)


class TestJobsAPI:
    def _logado(self):
        def _ov():
            yield FakeDB(FakeUser())

        app.dependency_overrides[auth_router.get_db] = _ov
        client = TestClient(app, raise_server_exceptions=False)
        import re

        get = client.get("/admin/login")
        csrf = re.search(r'name="csrf_token" value="([^"]+)"', get.text).group(1)
        client.post(
            "/admin/login",
            data={"username": "admin", "password": "secret123",
                  "csrf_token": csrf},
        )
        return client

    def test_sem_sessao_403(self):
        client = TestClient(app, raise_server_exceptions=False)
        r = client.post("/api/jobs/sync")
        assert r.status_code == 403

    def test_admin_dispara_relatorio(self):
        _seed()
        client = self._logado()
        r = client.post("/api/jobs/sync")
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["checked"] >= 3
        assert data["live"] is False


class TestScheduler:
    def test_desligado_por_padrao(self, monkeypatch):
        monkeypatch.delenv("ENABLE_SCHEDULER", raising=False)
        assert scheduler.enabled() is False
        with pytest.raises(RuntimeError, match="desligado"):
            scheduler.start_scheduler()

    def test_sem_lib_erro_claro(self, monkeypatch):
        monkeypatch.setenv("ENABLE_SCHEDULER", "1")
        with pytest.raises(RuntimeError, match="APScheduler"):
            scheduler.start_scheduler()

    def test_intervalo_padrao_e_invalido(self, monkeypatch):
        monkeypatch.delenv("SYNC_INTERVAL_MINUTES", raising=False)
        assert scheduler.interval_minutes() == 60
        monkeypatch.setenv("SYNC_INTERVAL_MINUTES", "lixo")
        assert scheduler.interval_minutes() == 60
