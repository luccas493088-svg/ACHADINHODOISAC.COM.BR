"""Teste do criar_admin (importa a função, sem CLI)."""
import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from app.db.base import Base
import app.models  # noqa: F401 — registra todos os modelos
from app.models.user import User
from criar_admin import criar_admin

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def _db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


class TestCriarAdmin:
    def test_cria_admin_ativo(self):
        db = TestingSessionLocal()
        user = criar_admin(db, "admin", "a@a.co", "secret123")
        assert user.id is not None
        assert user.is_active is True
        assert user.role == "admin"
        assert user.password_hash != "secret123"
        db.close()

    def test_duplicado_erro_claro(self):
        db = TestingSessionLocal()
        criar_admin(db, "admin", "a@a.co", "secret123")
        with pytest.raises(ValueError, match="já cadastrado"):
            criar_admin(db, "admin", "b@b.co", "secret123")
        db.close()

    def test_senha_curta_rejeitada(self):
        db = TestingSessionLocal()
        with pytest.raises(ValueError, match="6 caracteres"):
            criar_admin(db, "x", "x@x.co", "123")
        db.close()

    def test_login_end_to_end(self):
        from app.security import verify_password

        db = TestingSessionLocal()
        user = criar_admin(db, "root", "r@r.co", "secret123")
        achado = db.query(User).filter_by(username="root").first()
        assert verify_password("secret123", achado.password_hash)
        assert user.id == achado.id
        db.close()
