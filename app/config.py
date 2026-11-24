from pydantic import ConfigDict, Field, field_validator
from pydantic_settings import BaseSettings, NoDecode
from typing import Annotated

# The placeholder earlier versions used when SECRET_KEY was not set. Anyone
# who knows it can sign tokens for any user, so it is refused.
INSECURE_SECRET_KEYS = {
    "your-secret-key-change-this-in-production",
    "your-secret-key-here",
    "changeme",
    "secret",
}

MIN_SECRET_KEY_LENGTH = 32


class Settings(BaseSettings):
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=False
    )

    database_url: str = "sqlite:///./data/list_handler.db"
    # Signs the access tokens. Required: generate one with
    #   python -c "import secrets; print(secrets.token_urlsafe(48))"
    secret_key: str = Field(default="", validate_default=True)
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    # Anyone who can reach the API may register an account when this is on.
    # Off by default: create accounts with `python -m app.manage create-user`.
    allow_registration: bool = False
    # Browser origins allowed to call the API, comma-separated. Empty (the
    # default) sends no CORS headers; the bot and other servers need none.
    cors_origins: Annotated[list[str], NoDecode] = []

    @field_validator("secret_key")
    @classmethod
    def secret_key_must_be_strong(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError(
                "SECRET_KEY is not set. It signs the access tokens; generate one with: "
                "python -c \"import secrets; print(secrets.token_urlsafe(48))\""
            )
        if value.lower() in INSECURE_SECRET_KEYS:
            raise ValueError(
                "SECRET_KEY is a published placeholder; anyone could sign tokens with it. "
                "Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(48))\""
            )
        if len(value) < MIN_SECRET_KEY_LENGTH:
            raise ValueError(
                f"SECRET_KEY must be at least {MIN_SECRET_KEY_LENGTH} characters. "
                "Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(48))\""
            )
        return value

    @field_validator("algorithm")
    @classmethod
    def algorithm_must_be_hmac(cls, value: str) -> str:
        if value not in {"HS256", "HS384", "HS512"}:
            raise ValueError("ALGORITHM must be HS256, HS384 or HS512")
        return value

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_origins(cls, value):
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


settings = Settings()
