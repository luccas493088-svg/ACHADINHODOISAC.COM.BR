"""Rotas públicas de conta: cadastro e login de clientes."""
import logging
import secrets
from datetime import timedelta

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import Settings
from app.database import SessionLocal
from app.models.user import User
from app.schemas.user import UserCreate
from app.security import (
    blacklist_token,
    create_access_token,
    hash_password,
    verify_password,
)

logger = logging.getLogger("isac_achadinhos")
settings = Settings()

router = APIRouter(tags=["conta"])
templates = Jinja2Templates(directory="app/templates")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _csrf_token(request: Request) -> str:
    token = request.session.get("csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        request.session["csrf_token"] = token
    return token


async def _check_csrf(request: Request):
    form = await request.form()
    expected = request.session.get("csrf_token")
    got = form.get("csrf_token")
    if not expected or not got or got != expected:
        raise HTTPException(status_code=403, detail="CSRF token inválido")


def _usuario_logado(request: Request):
    return request.session.get("user")


def _login_response(request: Request, user: User) -> RedirectResponse:
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role, "user_id": user.id},
        expires_delta=timedelta(minutes=30),
    )
    request.session["user"] = {
        "id": user.id,
        "username": user.username,
        "role": user.role,
    }
    response = RedirectResponse(url="/conta", status_code=303)
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        samesite="lax",
        secure=settings.environment == "production",
        max_age=30 * 60,
    )
    return response


@router.get("/cadastro", include_in_schema=False)
async def cadastro_page(request: Request):
    if _usuario_logado(request):
        return RedirectResponse(url="/conta", status_code=303)
    return templates.TemplateResponse(
        request,
        "cadastro.html",
        {"error": None, "csrf_token": _csrf_token(request)},
    )


@router.post("/cadastro", include_in_schema=False)
async def cadastro(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirm: str = Form(...),
    db: Session = Depends(get_db),
):
    await _check_csrf(request)
    if _usuario_logado(request):
        return RedirectResponse(url="/conta", status_code=303)

    if password != confirm:
        return templates.TemplateResponse(
            request,
            "cadastro.html",
            {
                "error": "Senhas diferentes. Tente novamente.",
                "csrf_token": _csrf_token(request),
            },
            status_code=400,
        )

    try:
        payload = UserCreate(
            username=username.strip(),
            email=email.strip().lower(),
            password=password,
        )
    except ValidationError:
        return templates.TemplateResponse(
            request,
            "cadastro.html",
            {
                "error": "Dados inválidos: nome (3+ caracteres), "
                "e-mail válido e senha (6+ caracteres).",
                "csrf_token": _csrf_token(request),
            },
            status_code=400,
        )

    exists = (
        db.query(User)
        .filter(or_(User.username == payload.username, User.email == payload.email))
        .first()
    )
    if exists:
        return templates.TemplateResponse(
            request,
            "cadastro.html",
            {
                "error": "Nome de usuário ou e-mail já cadastrado.",
                "csrf_token": _csrf_token(request),
            },
            status_code=400,
        )

    user = User(
        username=payload.username,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role="customer",
        is_active=True,
        is_superuser=False,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return templates.TemplateResponse(
            request,
            "cadastro.html",
            {
                "error": "Nome de usuário ou e-mail já cadastrado.",
                "csrf_token": _csrf_token(request),
            },
            status_code=400,
        )
    db.refresh(user)
    logger.info("Novo cliente cadastrado: %s (id=%s)", user.username, user.id)
    return _login_response(request, user)


@router.get("/login", include_in_schema=False)
async def login_page(request: Request):
    if _usuario_logado(request):
        return RedirectResponse(url="/conta", status_code=303)
    return templates.TemplateResponse(
        request,
        "login_cliente.html",
        {"error": None, "csrf_token": _csrf_token(request)},
    )


@router.post("/login", include_in_schema=False)
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    await _check_csrf(request)
    user = (
        db.query(User)
        .filter(or_(User.username == username, User.email == username))
        .first()
    )
    if not user or not user.is_active or not verify_password(password, user.password_hash):
        return templates.TemplateResponse(
            request,
            "login_cliente.html",
            {"error": "Credenciais inválidas", "csrf_token": _csrf_token(request)},
            status_code=401,
        )
    return _login_response(request, user)


@router.post("/sair", include_in_schema=False)
async def logout(request: Request):
    await _check_csrf(request)
    cookie_token = request.cookies.get("access_token", "")
    if cookie_token.startswith("Bearer "):
        blacklist_token(cookie_token[7:])
    request.session.clear()
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie(key="access_token")
    return response


@router.get("/conta", include_in_schema=False)
async def conta_page(request: Request, db: Session = Depends(get_db)):
    user = _usuario_logado(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    perfil = db.query(User).filter(User.id == user["id"]).first()
    return templates.TemplateResponse(
        request,
        "conta.html",
        {
            "user": user,
            "email": perfil.email if perfil else "",
            "csrf_token": _csrf_token(request),
        },
    )
