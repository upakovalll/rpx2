"""
Authentication utilities and JWT token handling.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from sqlalchemy.orm import Session
import re

from app.core.auth_config import auth_config
from app.database.session import get_db


# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme (optional - only used when auth is enabled)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

# API Key scheme
api_key_header = APIKeyHeader(name=auth_config.API_KEY_HEADER, auto_error=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)


def validate_password(password: str) -> tuple[bool, str]:
    """
    Validate password against configured requirements.
    Returns (is_valid, error_message)
    """
    if len(password) < auth_config.PASSWORD_MIN_LENGTH:
        return False, f"Password must be at least {auth_config.PASSWORD_MIN_LENGTH} characters long"
    
    if auth_config.PASSWORD_REQUIRE_UPPERCASE and not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    
    if auth_config.PASSWORD_REQUIRE_LOWERCASE and not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    
    if auth_config.PASSWORD_REQUIRE_NUMBERS and not re.search(r"\d", password):
        return False, "Password must contain at least one number"
    
    if auth_config.PASSWORD_REQUIRE_SPECIAL and not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character"
    
    return True, ""


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=auth_config.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, auth_config.SECRET_KEY, algorithm=auth_config.ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """Create a JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=auth_config.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, auth_config.SECRET_KEY, algorithm=auth_config.ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Dict[str, Any]:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, auth_config.SECRET_KEY, algorithms=[auth_config.ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme),
    api_key: Optional[str] = Depends(api_key_header),
    db: Session = Depends(get_db)
) -> Optional[Dict[str, Any]]:
    """
    Get current user if authenticated, otherwise return None.
    This is the main function that checks if auth is enabled.
    """
    # If authentication is disabled, return a default user
    if not auth_config.AUTHENTICATION_ENABLED:
        return {"id": "default", "username": "anonymous", "role": "admin"}
    
    # Check API key first if enabled
    if auth_config.API_KEY_ENABLED and api_key:
        # Here you would validate the API key against your database
        # For now, we'll use a simple check
        if api_key == os.getenv("MASTER_API_KEY", ""):
            return {"id": "api_user", "username": "api_user", "role": "admin"}
    
    # Check JWT token
    if token:
        try:
            payload = decode_token(token)
            if payload.get("type") != "access":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type"
                )
            # Here you would fetch the user from database
            # For now, return the payload data
            return {
                "id": payload.get("sub"),
                "username": payload.get("username"),
                "role": payload.get("role", "user")
            }
        except HTTPException:
            pass
    
    return None


async def get_current_user(
    user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)
) -> Dict[str, Any]:
    """
    Get current user or raise 401 if not authenticated.
    Use this for endpoints that require authentication.
    """
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_current_active_user(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get current active user."""
    if current_user.get("disabled"):
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def require_role(required_role: str):
    """
    Dependency to require a specific role.
    Usage: Depends(require_role("admin"))
    """
    async def role_checker(current_user: Dict[str, Any] = Depends(get_current_active_user)):
        if not auth_config.RBAC_ENABLED:
            return current_user
        
        user_role = current_user.get("role", "user")
        # Simple role hierarchy: admin > manager > user
        role_hierarchy = {"admin": 3, "manager": 2, "user": 1}
        
        if role_hierarchy.get(user_role, 0) < role_hierarchy.get(required_role, 999):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    
    return role_checker


# Optional: Create a dependency that can be used to optionally check auth
def auth_required(required: bool = True):
    """
    Flexible auth dependency.
    Usage: 
    - Depends(auth_required(True)) - requires auth
    - Depends(auth_required(False)) - auth optional
    """
    if required:
        return Depends(get_current_user)
    else:
        return Depends(get_current_user_optional)


import os