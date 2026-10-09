import logging
import secrets
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.config import Settings
from app.database import SessionLocal
from app.models.user import User
from app.schemas.category import CategoryCreate, CategoryUpdate
from app.schemas.product import ProductCreate, ProductUpdate
from app.schemas.campaign import CampaignCreate, CampaignUpdate
from app.security import (
    create_access_token,
    verify_password,
    blacklist_token,
)
from app.services.category_service import (
    get_categories,
    get_category,
    create_category,
    update_category,
    soft_delete_category,
)
from app.services.product_service import (
    get_products,
    get_product,
    create_product,
    update_product,
    soft_delete_product,
)
from app.services.campaign_service import (
    get_campaigns,
    get_campaign,
    create_campaign,
    update_campaign,
    soft_delete_campaign,
)
from app.services.metrics_service import get_metrics_summary

logger = logging.getLogger("isac_achadinhos")
settings = Settings()

router = APIRouter(prefix="/admin", tags=["admin"])

templates = Jinja2Templates(directory="app/templates")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def require_admin(request: Request) -> dict:
    """Dependência mínima de autorização: exige sessão com role admin/superuser."""
    user = request.session.get("user")
    if not user:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            detail="Não autenticado",
            headers={"Location": "/admin/login"},
        )
    if user.get("role") not in ("admin", "superuser"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito ao administrador",
        )
    return user


def _csrf_token(request: Request) -> str:
    """Garante um token CSRF na sessão e o retorna."""
    token = request.session.get("csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        request.session["csrf_token"] = token
    return token


async def _check_csrf(request: Request):
    """Valida o token CSRF em requisições POST de formulários."""
    form = await request.form()
    expected = request.session.get("csrf_token")
    got = form.get("csrf_token")
    if not expected or not got or got != expected:
        raise HTTPException(status_code=403, detail="CSRF token inválido")


# Rotas de autenticação
@router.get("/login", response_class=HTMLResponse, include_in_schema=False)
async def login_page(request: Request):
    """Página de login ( Problema 1: antes redirecionava para si mesma )."""
    user = request.session.get("user")
    if user:
        return RedirectResponse(url="/admin/", status_code=303)
    return templates.TemplateResponse(
        request,
        "login.html",
        {"error": None, "csrf_token": _csrf_token(request)},
    )


@router.post("/login", include_in_schema=False)
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    """Autentica o usuário e cria a sessão."""
    # Rate limiting de 5/minuto é aplicado pelo SlowAPIMiddleware
    # (configurado em app/main.py com app.state.limit e app.add_exception_handler)
    # Acesso ao limitador via request.app.state.limiter
    await _check_csrf(request)
    user = db.query(User).filter(User.username == username).first()

    if not user or not user.is_active:
        # Não revelar se o usuário ou senha estão errados
        return templates.TemplateResponse(
            request,
            "login.html",
            {
                "error": "Credenciais inválidas",
                "csrf_token": _csrf_token(request),
            },
            status_code=401,
        )

    # Verifica senha
    if not verify_password(password, user.password_hash):
        return templates.TemplateResponse(
            request,
            "login.html",
            {
                "error": "Credenciais inválidas",
                "csrf_token": _csrf_token(request),
            },
            status_code=401,
        )

    # Cria token JWT
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role, "user_id": user.id},
        expires_delta=access_token_expires,
    )

    # Cria sessão no cookie
    request.session["user"] = {
        "id": user.id,
        "username": user.username,
        "role": user.role,
    }

    # Define cookie HttpOnly e SameSite
    response = RedirectResponse(url="/admin/", status_code=303)
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        samesite="lax",
        secure=settings.environment == "production",
        max_age=30 * 60,
    )

    return response


@router.post("/logout", include_in_schema=False)
async def logout(request: Request):
    """Fazer logout e invalidar sessão (Problema 5: session.clear)."""
    await _check_csrf(request)
    # Adiciona token à blacklist antes de limpar
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        blacklist_token(token)
    cookie_token = request.cookies.get("access_token", "")
    if cookie_token.startswith("Bearer "):
        blacklist_token(cookie_token[7:])

    # Limpa a sessão por completo
    request.session.clear()

    # Remove cookie
    response = RedirectResponse(url="/admin/login", status_code=303)
    response.delete_cookie(key="access_token")

    return response




# Rotas do painel administrativo
@router.get("/", include_in_schema=False)
async def admin_panel(request: Request):
    """Painel administrativo - requer autenticação + role admin."""
    try:
        user = require_admin(request)
    except HTTPException as exc:
        if exc.status_code == 303:
            return RedirectResponse(url="/admin/login", status_code=303)
        raise

    db = SessionLocal()
    try:
        categories = get_categories(db=db, skip=0, limit=100)
        products = get_products(db=db, skip=0, limit=20)
        campaigns = get_campaigns(db=db, skip=0, limit=100)
    finally:
        db.close()

    username = user["username"] if user else "Convidado"

    return templates.TemplateResponse(
        request,
        "admin_panel.html",
        {
            "username": username,
            "categories": categories,
            "products": products,
            "campaigns": campaigns,
            "csrf_token": _csrf_token(request),
        },
    )


def _require_admin_redirect(request: Request):
    """Helper para rotas HTML: redireciona em vez de lançar 403/303."""
    user = request.session.get("user")
    if not user:
        return None
    if user.get("role") not in ("admin", "superuser"):
        return None
    return user


# Rotas de Categoria (CRUD administrado)
@router.get("/categories/new", response_class=HTMLResponse, include_in_schema=False)
async def new_category_page(request: Request):
    """Página para nova categoria (Problema 8: renderiza formulário)."""
    user = _require_admin_redirect(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    return templates.TemplateResponse(
        request,
        "category_form.html",
        {"category": None, "action": "/admin/categories/new",
         "csrf_token": _csrf_token(request)},
    )


@router.post("/categories/new", include_in_schema=False)
async def create_category_admin(
    request: Request,
    name: str = Form(...), slug: str = Form(...), description: str = Form(""),
    db: Session = Depends(get_db),
):
    """Criar nova categoria."""
    await _check_csrf(request)
    user = _require_admin_redirect(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)

    try:
        payload = CategoryCreate(name=name, slug=slug, description=description or None)
        create_category(db=db, category_in=payload)
    except Exception:
        logger.exception("Erro ao criar categoria")
        return templates.TemplateResponse(
            request,
            "category_form.html",
            {"category": None, "action": "/admin/categories/new",
             "error": "Dados inválidos. Verifique nome e slug."},
            status_code=400,
        )

    return RedirectResponse(url="/admin/", status_code=303)


@router.get(
    "/categories/{category_id}/edit",
    response_class=HTMLResponse,
    include_in_schema=False,
)
async def edit_category_page(category_id: int, request: Request):
    """Página para editar categoria."""
    user = _require_admin_redirect(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    db = SessionLocal()
    try:
        category = get_category(db, category_id)
    finally:
        db.close()
    if not category:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")
    return templates.TemplateResponse(
        request,
        "category_form.html",
        {"category": category,
         "action": f"/admin/categories/{category_id}/edit",
         "csrf_token": _csrf_token(request)},
    )


@router.post("/categories/{category_id}/edit", include_in_schema=False)
async def update_category_admin(
    category_id: int,
    request: Request,
    name: str = Form(...), slug: str = Form(...), description: str = Form(""),
    db: Session = Depends(get_db),
):
    """Atualizar categoria."""
    await _check_csrf(request)
    user = _require_admin_redirect(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)

    try:
        payload = CategoryUpdate(name=name, slug=slug, description=description or None)
        updated = update_category(db=db, category_id=category_id, category_in=payload)
        if not updated:
            raise HTTPException(status_code=404, detail="Categoria não encontrada")
    except HTTPException:
        raise
    except Exception:
        logger.exception("Erro ao atualizar categoria %s", category_id)
        raise HTTPException(status_code=400, detail="Dados inválidos") from None

    return RedirectResponse(url="/admin/", status_code=303)


@router.post("/categories/{category_id}", include_in_schema=False)
async def delete_category_admin(
    category_id: int, request: Request,
    db: Session = Depends(get_db),
):
    """Soft delete de categoria (POST: forms HTML não têm DELETE)."""
    await _check_csrf(request)
    user = _require_admin_redirect(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)

    try:
        deleted = soft_delete_category(db=db, category_id=category_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Categoria não encontrada")
    except HTTPException:
        raise
    except Exception:
        logger.exception("Erro ao excluir categoria %s", category_id)
        raise HTTPException(
            status_code=400, detail="Não foi possível excluir"
        ) from None

    return RedirectResponse(url="/admin/", status_code=303)


# Rotas de Produto (CRUD administrado)
@router.get("/products/new", response_class=HTMLResponse, include_in_schema=False)
async def new_product_page(request: Request):
    """Página para novo produto."""
    user = _require_admin_redirect(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    db = SessionLocal()
    try:
        categories = get_categories(db=db, skip=0, limit=100)
    finally:
        db.close()
    return templates.TemplateResponse(
        request,
        "product_form.html",
        {"product": None, "categories": categories,
         "action": "/admin/products/new", "csrf_token": _csrf_token(request)},
    )


@router.post("/products/new", include_in_schema=False)
async def create_product_admin(
    request: Request,
    name: str = Form(...), slug: str = Form(...), price: float = Form(...),
    description: str = Form(""), category_id: int = Form(...),
    db: Session = Depends(get_db),
):
    """Criar novo produto."""
    await _check_csrf(request)
    user = _require_admin_redirect(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)

    try:
        payload = ProductCreate(
            name=name, slug=slug, price=price,
            description=description or None, category_id=category_id,
        )
        create_product(db=db, product_in=payload)
    except Exception:
        logger.exception("Erro ao criar produto")
        raise HTTPException(status_code=400, detail="Dados inválidos") from None

    return RedirectResponse(url="/admin/", status_code=303)


@router.get(
    "/products/{product_id}/edit",
    response_class=HTMLResponse,
    include_in_schema=False,
)
async def edit_product_page(product_id: int, request: Request):
    """Página para editar produto."""
    user = _require_admin_redirect(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    db = SessionLocal()
    try:
        product = get_product(db, product_id)
        categories = get_categories(db=db, skip=0, limit=100)
    finally:
        db.close()
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    return templates.TemplateResponse(
        request,
        "product_form.html",
        {"product": product, "categories": categories,
         "action": f"/admin/products/{product_id}/edit",
         "csrf_token": _csrf_token(request)},
    )


@router.post("/products/{product_id}/edit", include_in_schema=False)
async def update_product_admin(
    product_id: int,
    request: Request,
    name: str = Form(...), slug: str = Form(...), price: float = Form(...),
    description: str = Form(""), category_id: int = Form(...),
    db: Session = Depends(get_db),
):
    """Atualizar produto."""
    await _check_csrf(request)
    user = _require_admin_redirect(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)

    try:
        payload = ProductUpdate(
            name=name, slug=slug, price=price,
            description=description or None, category_id=category_id,
        )
        updated = update_product(db=db, product_id=product_id, product_in=payload)
        if not updated:
            raise HTTPException(status_code=404, detail="Produto não encontrado")
    except HTTPException:
        raise
    except Exception:
        logger.exception("Erro ao atualizar produto %s", product_id)
        raise HTTPException(status_code=400, detail="Dados inválidos") from None

    return RedirectResponse(url="/admin/", status_code=303)


@router.post("/products/{product_id}", include_in_schema=False)
async def delete_product_admin(
    product_id: int, request: Request,
    db: Session = Depends(get_db),
):
    """Excluir produto (soft delete). Mantido POST pelo mesmo motivo das categorias."""
    await _check_csrf(request)
    user = _require_admin_redirect(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)

    try:
        deleted = soft_delete_product(db=db, product_id=product_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Produto não encontrado")
    except HTTPException:
        raise
    except Exception:
        logger.exception("Erro ao excluir produto %s", product_id)
        raise HTTPException(
            status_code=400, detail="Não foi possível excluir"
        ) from None

    return RedirectResponse(url="/admin/", status_code=303)


# Rotas de Campanha (CRUD administrado — Fase 5)
@router.get("/campaigns/new", response_class=HTMLResponse, include_in_schema=False)
async def new_campaign_page(request: Request):
    """Página para nova campanha."""
    user = _require_admin_redirect(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    return templates.TemplateResponse(
        request,
        "campaign_form.html",
        {
            "campaign": None,
            "action": "/admin/campaigns/new",
            "csrf_token": _csrf_token(request),
        },
    )


@router.post("/campaigns/new", include_in_schema=False)
async def create_campaign_admin(
    request: Request,
    name: str = Form(...),
    slug: str = Form(...),
    description: str = Form(""),
    is_active: bool = Form(True),
    db: Session = Depends(get_db),
):
    """Criar nova campanha."""
    await _check_csrf(request)
    user = _require_admin_redirect(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)

    try:
        payload = CampaignCreate(
            name=name,
            slug=slug,
            description=description or None,
            is_active=is_active,
        )
        create_campaign(db=db, campaign_in=payload)
    except Exception:
        logger.exception("Erro ao criar campanha")
        return templates.TemplateResponse(
            request,
            "campaign_form.html",
            {
                "campaign": None,
                "action": "/admin/campaigns/new",
                "error": "Dados inválidos. Verifique nome e slug.",
            },
            status_code=400,
        )

    return RedirectResponse(url="/admin/", status_code=303)


@router.get(
    "/campaigns/{campaign_id}/edit",
    response_class=HTMLResponse,
    include_in_schema=False,
)
async def edit_campaign_page(campaign_id: int, request: Request):
    """Página para editar campanha."""
    user = _require_admin_redirect(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    db = SessionLocal()
    try:
        campaign = get_campaign(db, campaign_id)
    finally:
        db.close()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campanha não encontrada")
    return templates.TemplateResponse(
        request,
        "campaign_form.html",
        {
            "campaign": campaign,
            "action": f"/admin/campaigns/{campaign_id}/edit",
            "csrf_token": _csrf_token(request),
        },
    )


@router.post("/campaigns/{campaign_id}/edit", include_in_schema=False)
async def update_campaign_admin(
    campaign_id: int,
    request: Request,
    name: str = Form(...),
    slug: str = Form(...),
    description: str = Form(""),
    is_active: bool = Form(True),
    db: Session = Depends(get_db),
):
    """Atualizar campanha."""
    await _check_csrf(request)
    user = _require_admin_redirect(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)

    try:
        payload = CampaignUpdate(
            name=name,
            slug=slug,
            description=description or None,
            is_active=is_active,
        )
        updated = update_campaign(
            db=db, campaign_id=campaign_id, campaign_in=payload
        )
        if not updated:
            raise HTTPException(status_code=404, detail="Campanha não encontrada")
    except HTTPException:
        raise
    except Exception:
        logger.exception("Erro ao atualizar campanha %s", campaign_id)
        raise HTTPException(
            status_code=400, detail="Dados inválidos"
        ) from None

    return RedirectResponse(url="/admin/", status_code=303)


@router.post("/campaigns/{campaign_id}", include_in_schema=False)
async def delete_campaign_admin(
    campaign_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    """Soft delete de campanha (POST: forms HTML não têm DELETE)."""
    await _check_csrf(request)
    user = _require_admin_redirect(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)

    try:
        deleted = soft_delete_campaign(db=db, campaign_id=campaign_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Campanha não encontrada")
    except HTTPException:
        raise
    except Exception:
        logger.exception("Erro ao excluir campanha %s", campaign_id)
        raise HTTPException(
            status_code=400, detail="Não foi possível excluir"
        ) from None

    return RedirectResponse(url="/admin/", status_code=303)


# Painel de métricas (Fase 5)
@router.get("/metrics", response_class=HTMLResponse, include_in_schema=False)
async def metrics_page(request: Request):
    """Dashboard de resultados: desempenho das ofertas e campanhas."""
    user = _require_admin_redirect(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
    db = SessionLocal()
    try:
        summary = get_metrics_summary(db, days=30, top_n=10)
    finally:
        db.close()
    return templates.TemplateResponse(
        request,
        "metrics.html",
        {"summary": summary, "csrf_token": _csrf_token(request)},
    )

