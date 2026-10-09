"""Testes Fase 8 — importadores dry-run, job import e vitrine via banco."""
import socket

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
import app.models  # noqa: F401 — registra todos os modelos
from app.importers import STORES, get_connector
from app.jobs.import_products import run_import
from app.main import app
from app.models.store_product import StoreProduct
from app.routers import auth as auth_router
from app.routers import jobs as jobs_router
from app.routers import vitrine_api as vitrine_router
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
    for _mod in (auth_router, jobs_router, vitrine_router):
        app.dependency_overrides[_mod.get_db] = _override_get_db
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    app.dependency_overrides.clear()
    for _mod in (auth_router, jobs_router, vitrine_router):
        app.dependency_overrides[_mod.get_db] = _override_get_db


class TestConectores:
    def test_quatro_lojas_registradas(self):
        assert set(STORES) == {
            "TikTok Shop",
            "Monetizze",
            "Mercado Livre",
            "AliExpress",
        }

    def test_loja_desconhecida_erro_claro(self):
        with pytest.raises(ValueError, match="Loja desconhecida"):
            get_connector("Meta")

    def test_fetch_ficticio_sem_io(self, monkeypatch):
        def _bomba(*args, **kwargs):
            raise AssertionError("tentou I/O de rede!")

        monkeypatch.setattr(socket, "socket", _bomba)
        for nome in STORES:
            itens = get_connector(nome).fetch()
            assert len(itens) == 2
            for item in itens:
                assert {"nome", "preco", "link_afiliado", "data_cadastro"} <= set(
                    item
                )
                assert "example.com" in item["link_afiliado"]

    def test_credenciais_vem_do_env(self, monkeypatch):
        for nome in STORES:
            for key in get_connector(nome).credentials_env:
                monkeypatch.delenv(key, raising=False)
        assert all(
            get_connector(n).is_configured() is False for n in STORES
        )
        assert get_connector("Monetizze").credentials() == {}


class TestImportJob:
    def test_import_salva_tudo(self):
        db = TestingSessionLocal()
        rel = run_import(db)
        db.close()
        assert rel["total_fetched"] == 8
        assert rel["total_saved"] == 8
        assert rel["total_duplicates"] == 0
        assert rel["live"] is False

    def test_segunda_rodada_so_duplicados(self):
        db = TestingSessionLocal()
        run_import(db)
        rel = run_import(db)
        db.close()
        assert rel["total_saved"] == 0
        assert rel["total_duplicates"] == 8
        db = TestingSessionLocal()
        assert db.query(StoreProduct).count() == 8
        db.close()

    def test_filtro_por_loja(self):
        db = TestingSessionLocal()
        rel = run_import(db, stores=["Monetizze"])
        db.close()
        assert rel["total_saved"] == 2
        assert set(rel["stores"]) == {"Monetizze"}


class TestVitrineAPI:
    def test_catalogo_comeca_vazio(self):
        client = TestClient(app, raise_server_exceptions=False)
        r = client.get("/api/vitrine/produtos")
        assert r.status_code == 200
        assert r.json() == []
        assert client.get("/api/vitrine/destaque").json() == []

    def test_lista_filtra_e_ordena(self):
        db = TestingSessionLocal()
        run_import(db)
        db.close()
        client = TestClient(app, raise_server_exceptions=False)

        r = client.get("/api/vitrine/produtos")
        assert len(r.json()) == 8

        r = client.get("/api/vitrine/produtos", params={"loja": "Monetizze"})
        assert {p["loja"] for p in r.json()} == {"Monetizze"}

        baratos = client.get(
            "/api/vitrine/produtos", params={"ordem": "baratos"}
        ).json()
        precos = [float(p["preco"]) for p in baratos]
        assert precos == sorted(precos)

        caros = client.get(
            "/api/vitrine/produtos", params={"ordem": "caros"}
        ).json()
        precos = [float(p["preco"]) for p in caros]
        assert precos == sorted(precos, reverse=True)

        chegada = client.get("/api/vitrine/produtos").json()
        datas = [p["data_cadastro"] for p in chegada]
        assert datas == sorted(datas)

    def test_loja_invalida_422(self):
        client = TestClient(app, raise_server_exceptions=False)
        assert (
            client.get("/api/vitrine/produtos", params={"loja": "Meta"}).status_code
            == 422
        )

    def test_destaque_mais_baratos(self):
        db = TestingSessionLocal()
        run_import(db)
        db.close()
        client = TestClient(app, raise_server_exceptions=False)
        r = client.get("/api/vitrine/destaque")
        assert r.status_code == 200
        itens = r.json()
        assert len(itens) == 3
        precos = [float(p["preco"]) for p in itens]
        assert precos == sorted(precos)


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


class TestImportAPI:
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
            data={
                "username": "admin",
                "password": "secret123",
                "csrf_token": csrf,
            },
        )
        return client

    def test_sem_sessao_403(self):
        client = TestClient(app, raise_server_exceptions=False)
        assert client.post("/api/jobs/import").status_code == 403

    def test_admin_importa(self):
        client = self._logado()
        r = client.post("/api/jobs/import")
        assert r.status_code == 200, r.text
        assert r.json()["total_saved"] == 8
        r2 = client.post("/api/jobs/import")
        assert r2.json()["total_duplicates"] == 8


class TestFrontendVazio:
    def test_mensagem_em_breve(self):
        from pathlib import Path

        js = (
            Path(__file__).resolve().parent.parent
            / "vitrine"
            / "app.js"
        ).read_text(encoding="utf-8")
        assert "Em breve novas ofertas" in js
        assert "/api/vitrine/produtos" in js
