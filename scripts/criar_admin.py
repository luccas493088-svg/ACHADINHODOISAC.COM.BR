"""Cria o primeiro usuário admin (Fase 8, chave de ouro).

Uso:
    .venv/bin/python scripts/criar_admin.py --username admin --email voce@exemplo.com

A senha é pedida no terminal (nunca como argumento, nunca em arquivo).
Banco: `--db-url` ou `DATABASE_URL` do ambiente/`.env`.
"""
import argparse
import getpass
import os
import sys

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

from sqlalchemy import create_engine, or_
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
import app.models  # noqa: F401 — registra modelos
from app.models.user import User
from app.security import hash_password


def criar_admin(db, username: str, email: str, password: str, role: str = "admin"):
    """Cria admin ativo; erro claro se username/e-mail já existirem."""
    if len(password) < 6:
        raise ValueError("Senha deve ter ao menos 6 caracteres")
    exists = (
        db.query(User)
        .filter(or_(User.username == username, User.email == email))
        .first()
    )
    if exists:
        raise ValueError("username ou e-mail já cadastrado")
    user = User(
        username=username,
        email=email,
        password_hash=hash_password(password),
        role=role,
        is_active=True,
        is_superuser=(role == "superuser"),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Cria o primeiro admin")
    parser.add_argument("--username", required=True)
    parser.add_argument("--email", required=True)
    parser.add_argument("--role", default="admin")
    parser.add_argument("--db-url", default=os.getenv("DATABASE_URL", ""))
    args = parser.parse_args(argv)

    if not args.db_url:
        print("ERRO: informe --db-url ou defina DATABASE_URL", file=sys.stderr)
        return 2
    password = getpass.getpass("Senha (mín. 6 caracteres): ")
    confirmar = getpass.getpass("Confirme a senha: ")
    if password != confirmar:
        print("ERRO: senhas diferentes", file=sys.stderr)
        return 2

    engine = create_engine(args.db_url)
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    try:
        user = criar_admin(session, args.username, args.email, password, args.role)
    except ValueError as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 1
    finally:
        session.close()
    print(f"Admin '{user.username}' criado (id={user.id}). Entre em /admin/login")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
