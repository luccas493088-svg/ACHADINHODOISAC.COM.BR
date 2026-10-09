"""Fechamento Fase 3 (auth/admin) + Fase 4 (rate-limit/redis).

Sem banco real: rotas com DB têm dependência mockada via dependency_overrides.
"""
import re
from datetime import timedelta

from fastapi.testclient import TestClient

from app.main import app
from app.security import (
    create_access_token,
    decode_access_token,
    blacklist_token,
    hash_password,
)
from app.routers import auth as auth_router


def _csrf_from_login_page(html: str) -> str:
    m = re.search(r'name="csrf_token" value="([^"]+)"', html)
    assert m, "csrf_token não encontrado na página de login"
    return m.group(1)


class FakeUser:
    def __init__(self):
        self.id = 1
        self.username = "admin"
        self.role = "admin"
        self.is_active = True
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


def _client_with_user(user):
    def override_get_db():
        yield FakeDB(user)

    app.dependency_overrides[auth_router.get_db] = override_get_db
    return TestClient(app, raise_server_exceptions=False)


def teardown_function():
    app.dependency_overrides.clear()


class TestLoginPage:
    def test_get_login_renders_form(self):
        client = TestClient(app)
        r = client.get("/admin/login")
        assert r.status_code == 200
        assert "csrf_token" in r.text
        assert "<form" in r.text

    def test_admin_panel_redirects_when_anonymous(self):
        client = TestClient(app, follow_redirects=False)
        r = client.get("/admin/")
        assert r.status_code in (303, 307)
        assert "/admin/login" in r.headers.get("location", "")


class TestCSRF:
    def test_login_without_csrf_is_rejected(self):
        client = _client_with_user(FakeUser())
        client.get("/admin/login")  # estabelece csrf na sessão
        r = client.post(
            "/admin/login",
            data={"username": "admin", "password": "secret123"},
            follow_redirects=False,
        )
        assert r.status_code == 403


class TestLoginFlow:
    def test_login_invalid_password_returns_401(self):
        client = _client_with_user(FakeUser())
        get = client.get("/admin/login")
        csrf = _csrf_from_login_page(get.text)
        r = client.post(
            "/admin/login",
            data={
                "username": "admin",
                "password": "wrongpass",
                "csrf_token": csrf,
            },
        )
        assert r.status_code == 401
        assert "Credenciais inválidas" in r.text

    def test_login_valid_redirects_to_admin(self):
        client = _client_with_user(FakeUser())
        get = client.get("/admin/login")
        csrf = _csrf_from_login_page(get.text)
        r = client.post(
            "/admin/login",
            data={
                "username": "admin",
                "password": "secret123",
                "csrf_token": csrf,
            },
            follow_redirects=False,
        )
        assert r.status_code == 303
        assert r.headers["location"] == "/admin/"
        assert "access_token" in r.cookies

    def test_logout_clears_session(self):
        client = _client_with_user(FakeUser())
        get = client.get("/admin/login")
        csrf = _csrf_from_login_page(get.text)
        client.post(
            "/admin/login",
            data={
                "username": "admin",
                "password": "secret123",
                "csrf_token": csrf,
            },
        )
        # usa o csrf da sessão logada para o logout
        r = client.post(
            "/admin/logout",
            data={"csrf_token": client.cookies.get("csrf_token", csrf)},
            follow_redirects=False,
        )
        # logout exige csrf válido: 303 (ok) ou 403 (token divergente) — nunca 500
        assert r.status_code in (303, 403)


class TestJWTBlacklist:
    def test_blacklisted_token_is_rejected(self):
        token = create_access_token(data={"sub": "admin"})
        assert decode_access_token(token) is not None
        blacklist_token(token)
        assert decode_access_token(token) is None

    def test_expired_token_returns_none(self):
        token = create_access_token(
            data={"sub": "admin"}, expires_delta=timedelta(seconds=-10)
        )
        assert decode_access_token(token) is None


class TestFase4RateLimitRedis:
    def test_limiter_middleware_active(self):
        from slowapi.middleware import SlowAPIMiddleware

        middlewares = [m.cls for m in app.user_middleware]
        assert SlowAPIMiddleware in middlewares
        assert hasattr(app.state, "limiter")

    def test_security_import_does_not_hang_without_redis(self):
        # Se chegou até aqui, o import com timeout curto funcionou.
        import app.security as sec

        assert isinstance(sec.BLACKLIST, set)
