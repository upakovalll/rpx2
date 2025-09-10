"""
Authentication configuration and settings.
"""

from pydantic import BaseModel
from typing import Optional, List
import os
from dotenv import load_dotenv

load_dotenv()


class AuthConfig(BaseModel):
    """Authentication configuration settings."""
    
    # Master switch for authentication
    AUTHENTICATION_ENABLED: bool = os.getenv("AUTHENTICATION_ENABLED", "false").lower() == "true"
    
    # JWT Settings
    SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-here-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    
    # API Key Settings (alternative to JWT)
    API_KEY_ENABLED: bool = os.getenv("API_KEY_ENABLED", "false").lower() == "true"
    API_KEY_HEADER: str = "X-API-Key"
    
    # OAuth2 Settings (for future use)
    OAUTH2_ENABLED: bool = os.getenv("OAUTH2_ENABLED", "false").lower() == "true"
    
    # Public endpoints (no auth required even when auth is enabled)
    PUBLIC_ENDPOINTS: List[str] = [
        "/",
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/v1/auth/login",
        "/api/v1/auth/register",
        "/api/v1/auth/refresh",
    ]
    
    # Role-based access control
    RBAC_ENABLED: bool = os.getenv("RBAC_ENABLED", "false").lower() == "true"
    
    # Password requirements
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_NUMBERS: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = True
    
    # Session settings
    SESSION_TIMEOUT_MINUTES: int = int(os.getenv("SESSION_TIMEOUT_MINUTES", "60"))
    CONCURRENT_SESSIONS_ALLOWED: bool = os.getenv("CONCURRENT_SESSIONS_ALLOWED", "true").lower() == "true"
    
    # Security headers
    ENABLE_CORS: bool = os.getenv("ENABLE_CORS", "true").lower() == "true"
    CORS_ORIGINS: List[str] = os.getenv("CORS_ORIGINS", "*").split(",")
    
    class Config:
        env_file = ".env"


# Global auth config instance
auth_config = AuthConfig()