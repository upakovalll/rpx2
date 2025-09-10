"""
Application settings configuration using Pydantic.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings."""
    
    # Database - separate variables for flexible deployment
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "rpx_engine_dev"
    DB_USER: str = "rpx_dev_db_user"
    DB_PASSWORD: str = "rpx_password"
    
    # Application
    APP_NAME: str = "RPX Main Backend"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Security
    SECRET_KEY: str = "your-secret-key-here"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get application settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings 