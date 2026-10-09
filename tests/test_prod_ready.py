"""Testes Fase 7 — readiness, guards de publicação e backup."""
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
import app.models  # noqa: F401 — registra todos os modelos
from app.main import app
from app.routers import health as health_router

ROOT = Path(__file__).resolve().parent.parent

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
def _overrides():
    app.dependency_overrides[health_router.get_db] = _override_get_db
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    app.dependency_overrides.clear()
    app.dependency_overrides[health_router.get_db] = _override_get_db


class TestReady:
    def test_ready_200_com_banco(self):
        client = TestClient(app, raise_server_exceptions=False)
        r = client.get("/ready")
        assert r.status_code == 200
        assert r.json()["status"] == "ready"

    def test_ready_503_sem_banco(self):
        class _BrokenDB:
            def execute(self, *args, **kwargs):
                raise Exception("banco fora")

            def close(self):
                pass

        def _quebrado():
            yield _BrokenDB()

        app.dependency_overrides[health_router.get_db] = _quebrado
        try:
            client = TestClient(app, raise_server_exceptions=False)
            r = client.get("/ready")
            assert r.status_code == 503
            assert r.json()["status"] == "not_ready"
        finally:
            app.dependency_overrides[health_router.get_db] = _override_get_db


class TestPublishGuards:
    def test_dockerignore_bloqueia_segredos(self):
        texto = (ROOT / ".dockerignore").read_text(encoding="utf-8")
        for padrao in (".env", ".venv/", "venv/", ".git/"):
            assert padrao in texto, f"faltando no .dockerignore: {padrao}"

    def test_requirements_cobre_imports(self):
        reqs = (ROOT / "requirements.txt").read_text(encoding="utf-8")
        for dep in ("jinja2", "redis", "psycopg", "slowapi", "argon2-cffi"):
            assert dep in reqs, f"faltando no requirements.txt: {dep}"

    def test_healthcheck_no_docker(self):
        dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
        compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
        assert "HEALTHCHECK" in dockerfile
        assert "healthcheck" in compose

    def test_backup_script_existe_e_protege_env(self):
        script = ROOT / "scripts" / "backup_db.sh"
        assert script.exists()
        texto = script.read_text(encoding="utf-8")
        assert "DATABASE_URL" in texto
        assert "set -euo pipefail" in texto
