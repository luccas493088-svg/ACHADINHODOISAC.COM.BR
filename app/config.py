from pydantic_settings import BaseSettings, SettingsConfigDict

_PLACEHOLDER_SECRET = "change-me-long-random-string"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    database_url: str = "postgresql://user:password@localhost:5432/isac_achadinhos"
    jwt_secret: str
    redis_url: str = "redis://localhost:6379/0"
    environment: str = "development"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.jwt_secret or self.jwt_secret == _PLACEHOLDER_SECRET:
            raise ValueError(
                "JWT_SECRET inválido: defina uma chave forte no .env "
                "(ex: openssl rand -hex 32)"
            )
