from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./list_handler.db"
    secret_key: str = "your-secret-key-change-this-in-production"  # Change this in production!
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False
    }


settings = Settings()

