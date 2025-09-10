"""
Authentication endpoints for user login, registration, and token management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import Optional

from app.database.session import get_db
from app.core.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
    validate_password,
    get_current_user
)
from app.core.auth_config import auth_config
from app.schemas.auth import (
    Token,
    TokenRefresh,
    UserCreate,
    UserResponse,
    UserLogin,
    PasswordChange,
    APIKeyCreate,
    APIKeyResponse
)

router = APIRouter()


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    OAuth2 compatible token login endpoint.
    Returns access and refresh tokens.
    """
    # In a real implementation, you would:
    # 1. Query the user from database
    # 2. Verify the password
    # 3. Generate tokens
    
    # For demo purposes, using hardcoded check
    if form_data.username == "admin" and form_data.password == "admin123":
        user_data = {
            "sub": "1",
            "username": "admin",
            "role": "admin"
        }
    elif form_data.username == "user" and form_data.password == "user123":
        user_data = {
            "sub": "2",
            "username": "user",
            "role": "user"
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create tokens
    access_token = create_access_token(data=user_data)
    refresh_token = create_refresh_token(data=user_data)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/register", response_model=UserResponse)
async def register(
    user: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new user.
    Only available when authentication is enabled.
    """
    if not auth_config.AUTHENTICATION_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Registration is disabled when authentication is disabled"
        )
    
    # Validate password
    is_valid, error_msg = validate_password(user.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    # In a real implementation:
    # 1. Check if user exists
    # 2. Hash the password
    # 3. Save to database
    
    # For demo purposes, return success
    hashed_password = get_password_hash(user.password)
    
    return UserResponse(
        id="3",
        username=user.username,
        email=user.email,
        role="user",
        is_active=True
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    token_data: TokenRefresh,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token.
    """
    try:
        payload = decode_token(token_data.refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        # Create new access token
        user_data = {
            "sub": payload.get("sub"),
            "username": payload.get("username"),
            "role": payload.get("role")
        }
        access_token = create_access_token(data=user_data)
        
        # Optionally create new refresh token
        refresh_token = create_refresh_token(data=user_data)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: dict = Depends(get_current_user)
):
    """
    Get current user information.
    Requires authentication.
    """
    return UserResponse(
        id=current_user.get("id", ""),
        username=current_user.get("username", ""),
        email=current_user.get("email", "user@example.com"),
        role=current_user.get("role", "user"),
        is_active=True
    )


@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Change user password.
    Requires authentication.
    """
    # Validate new password
    is_valid, error_msg = validate_password(password_data.new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    # In a real implementation:
    # 1. Verify old password
    # 2. Hash new password
    # 3. Update in database
    
    return {"message": "Password changed successfully"}


@router.post("/logout")
async def logout(
    current_user: dict = Depends(get_current_user)
):
    """
    Logout user (client should discard tokens).
    In a real implementation, you might blacklist the token.
    """
    # In production, you might want to:
    # 1. Add token to blacklist
    # 2. Clear server-side session
    # 3. Log the logout event
    
    return {"message": "Successfully logged out"}


@router.post("/api-keys", response_model=APIKeyResponse)
async def create_api_key(
    key_data: APIKeyCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new API key for the current user.
    Requires authentication and API keys must be enabled.
    """
    if not auth_config.API_KEY_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="API key authentication is disabled"
        )
    
    # In a real implementation:
    # 1. Generate secure random key
    # 2. Hash it
    # 3. Save to database with user association
    
    import secrets
    api_key = secrets.token_urlsafe(32)
    
    return APIKeyResponse(
        id="key_1",
        name=key_data.name,
        key=api_key,  # Only shown once
        created_at="2024-01-15T10:00:00Z",
        expires_at=key_data.expires_at
    )


@router.get("/status")
async def auth_status():
    """
    Get authentication system status.
    Public endpoint to check auth configuration.
    """
    return {
        "authentication_enabled": auth_config.AUTHENTICATION_ENABLED,
        "api_key_enabled": auth_config.API_KEY_ENABLED,
        "oauth2_enabled": auth_config.OAUTH2_ENABLED,
        "rbac_enabled": auth_config.RBAC_ENABLED,
        "registration_open": auth_config.AUTHENTICATION_ENABLED,
        "password_requirements": {
            "min_length": auth_config.PASSWORD_MIN_LENGTH,
            "require_uppercase": auth_config.PASSWORD_REQUIRE_UPPERCASE,
            "require_lowercase": auth_config.PASSWORD_REQUIRE_LOWERCASE,
            "require_numbers": auth_config.PASSWORD_REQUIRE_NUMBERS,
            "require_special": auth_config.PASSWORD_REQUIRE_SPECIAL
        }
    }