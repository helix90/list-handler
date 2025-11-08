from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class Settings(BaseSettings):
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=False
    )
    
    database_url: str = "sqlite:///./data/list_handler.db"
    secret_key: str = "your-secret-key-change-this-in-production"  # Change this in production!
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30


settings = Settings()

