from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from fastapi.responses import JSONResponse
from jinja2 import Environment, FileSystemLoader, select_autoescape
import uuid
import logging

from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.limiter import limiter


from app.config import Settings
from app.routers.auth import router as auth_router
from app.routers.accounts import router as accounts_router
from app.routers.products import router as products_router
from app.routers.categories import router as categories_router
from app.routers.campaigns import router as campaigns_router
from app.routers.metrics import router as metrics_router
from app.routers.offers import router as offers_router
from app.routers.webhooks import router as webhooks_router
from app.routers.jobs import router as jobs_router
from app.routers.health import router as health_router
from app.routers.vitrine_api import router as vitrine_api_router

settings = Settings()

app = FastAPI(title="Isac Achadinhos")
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

# --- Security Headers Middleware ---
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

# --- CORS Middleware ---
allowed_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# --- Rate Limiting ---
# Global rate limits applied via Limiter defaults:
# - 200 requests per day
# - 50 requests per minute
# Route-specific limits can be added with @limiter.limit() decorators

# --- Session Middleware ---
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.jwt_secret,
    same_site="lax",
    https_only=settings.environment == "production",
)

# --- Request ID Middleware ---
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("isac_achadinhos")


@app.exception_handler(Exception)
async def global_error_handler(request: Request, exc: Exception):
    logger.error(
        "Unhandled error: %s %s - %s",
        request.method,
        request.url.path,
        exc,
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Erro interno do servidor"},
    )

@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Muitas requisições. Tente novamente mais tarde."},
    )


# --- Health Check ---
@app.get("/health", include_in_schema=False)
async def health():
    return {"status": "ok", "service": "isac_achadinhos_api"}


# --- Jinja2 Setup ---
env = Environment(
    loader=FileSystemLoader("app/templates"),
    autoescape=select_autoescape(["html", "jsp"]),
)


@app.get("/", include_in_schema=False)
async def home(request: Request):
    template = env.get_template("home.html")
    return Response(
        content=template.render(request=request),
        media_type="text/html",
    )


# --- API Routers ---
app.include_router(auth_router)
app.include_router(accounts_router)
app.include_router(products_router)
app.include_router(categories_router)
app.include_router(campaigns_router)
app.include_router(metrics_router)
app.include_router(offers_router)
app.include_router(webhooks_router)
app.include_router(jobs_router)
app.include_router(health_router)
app.include_router(vitrine_api_router)

# --- Vitrine estática (links de afiliados via JSON, dry-run) ---
app.mount("/vitrine", StaticFiles(directory="vitrine", html=True), name="vitrine")
