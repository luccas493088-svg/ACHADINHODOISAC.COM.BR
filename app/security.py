from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from argon2 import PasswordHasher as Argon2PasswordHasher
from argon2.exceptions import (
    InvalidHashError,
    VerificationError,
)

from app.config import Settings

# Configuração centralizada
settings = Settings()

# Senhas protegidas com Argon2
hasher = Argon2PasswordHasher()

# JWT
SECRET_KEY = settings.jwt_secret
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Blacklist de tokens
# Fase 4: Redis é 100% lazy — nenhum I/O no import. Sem Redis, fallback em
# memória. Com Redis, primeira chamada tenta conectar 1x com timeout curto.
_redis_client = None
_redis_available = False
_redis_tried = False

# Armazenamento em memória (fallback ou produção standalone)
BLACKLIST: set[str] = set()


def _lazy_redis():
    """Conecta ao Redis uma única vez, com timeout curto. Nunca levanta."""
    global _redis_client, _redis_available, _redis_tried
    if _redis_tried:
        return _redis_client if _redis_available else None
    _redis_tried = True
    try:
        import redis
        from urllib.parse import urlparse

        _parsed = urlparse(settings.redis_url)
        client = redis.Redis(
            host=_parsed.hostname or "localhost",
            port=_parsed.port or 6379,
            db=int((_parsed.path or "/0").lstrip("/") or 0),
            decode_responses=True,
            socket_connect_timeout=1,
            socket_timeout=1,
        )
        if client.ping():
            _redis_client = client
            _redis_available = True
            return client
    except Exception:
        pass
    _redis_available = False
    return None


def _is_redis_available() -> bool:
    """Verifica se o Redis está disponível (lazy, 1 tentativa)."""
    if _redis_available and _redis_client is not None:
        return True
    return _lazy_redis() is not None


def _redis_blacklist_set(token: str) -> None:
    """Adiciona token à blacklist via Redis (quando disponível)."""
    if _is_redis_available():
        try:
            _redis_client.set(token, "1", ex=1800)  # 30 min TTL
            return
        except Exception:
            pass
    # Fallback para memória
    BLACKLIST.add(token)


def _redis_blacklist_get(token: str) -> bool:
    """Verifica se token está na blacklist via Redis (quando disponível)."""
    if _is_redis_available():
        try:
            result = _redis_client.get(token)
            return result is not None
        except Exception:
            pass
    # Fallback para memória
    return token in BLACKLIST


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a signed JWT access token."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    to_encode.update({"iat": now, "exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str):
    """Decode a JWT and reject revoked tokens."""
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )
    except jwt.PyJWTError:
        return None

    if is_token_blacklisted(token):
        return None

    return payload


def hash_password(password: str) -> str:
    """Hash a password using Argon2."""
    return hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify an Argon2 password hash."""
    try:
        return hasher.verify(hashed_password, plain_password)
    except (VerificationError, InvalidHashError, TypeError):
        return False


def is_token_blacklisted(token: str) -> bool:
    """Check whether a token has been revoked."""
    return _redis_blacklist_get(token)


def blacklist_token(token: str) -> None:
    """Revoke a token."""
    _redis_blacklist_set(token)


def verify_password_legacy(
    plain_password: str,
    hashed_password: str,
) -> bool:
    """Maintain compatibility with existing Argon2 password hashes."""
    return verify_password(plain_password, hashed_password)
