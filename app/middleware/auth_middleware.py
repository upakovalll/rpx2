"""
Authentication middleware for FastAPI.
"""

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import logging
from typing import Callable

from app.core.auth_config import auth_config
from app.core.auth import decode_token, api_key_header

logger = logging.getLogger(__name__)


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle authentication globally.
    Only active when AUTHENTICATION_ENABLED is True.
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.public_paths = set(auth_config.PUBLIC_ENDPOINTS)
        # Add MCP endpoints to public paths
        self.public_paths.add("/mcp")
        self.public_paths.add("/mcp/tools")
    
    async def dispatch(self, request: Request, call_next: Callable):
        """Process the request and check authentication if enabled."""
        
        # If authentication is disabled, pass through
        if not auth_config.AUTHENTICATION_ENABLED:
            response = await call_next(request)
            return response
        
        # Check if path is public
        path = request.url.path
        if self._is_public_path(path):
            response = await call_next(request)
            return response
        
        # Check for authentication
        try:
            # Check API key first
            if auth_config.API_KEY_ENABLED:
                api_key = request.headers.get(auth_config.API_KEY_HEADER)
                if api_key and self._validate_api_key(api_key):
                    response = await call_next(request)
                    return response
            
            # Check JWT token
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
                payload = decode_token(token)
                # Add user info to request state
                request.state.user = payload
                response = await call_next(request)
                return response
            
            # No valid authentication found
            return JSONResponse(
                status_code=401,
                content={"detail": "Not authenticated"},
                headers={"WWW-Authenticate": "Bearer"}
            )
            
        except HTTPException as e:
            return JSONResponse(
                status_code=e.status_code,
                content={"detail": e.detail}
            )
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal authentication error"}
            )
    
    def _is_public_path(self, path: str) -> bool:
        """Check if the path is public (no auth required)."""
        # Exact match
        if path in self.public_paths:
            return True
        
        # Prefix match for API docs
        if path.startswith("/docs") or path.startswith("/redoc"):
            return True
        
        # Check if it's an auth endpoint
        if path.startswith("/api/v1/auth/"):
            return True
        
        return False
    
    def _validate_api_key(self, api_key: str) -> bool:
        """Validate API key (implement your logic here)."""
        import os
        master_key = os.getenv("MASTER_API_KEY", "")
        return api_key == master_key and master_key != ""


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Optional rate limiting middleware.
    Can be enabled separately from authentication.
    """
    
    def __init__(self, app: ASGIApp, calls: int = 100, period: int = 60):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.cache = {}  # In production, use Redis
    
    async def dispatch(self, request: Request, call_next: Callable):
        """Apply rate limiting if configured."""
        # Simple implementation - in production use Redis
        client_ip = request.client.host
        
        # For now, just pass through
        # Implement actual rate limiting logic here
        response = await call_next(request)
        return response