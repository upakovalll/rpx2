"""
Example of how to protect endpoints with authentication.
This file demonstrates different authentication patterns.
"""

from fastapi import APIRouter, Depends
from typing import Optional, Dict, Any

from app.core.auth import (
    get_current_user,
    get_current_user_optional,
    get_current_active_user,
    require_role,
    auth_required
)

router = APIRouter()


# Example 1: Public endpoint (no auth required)
@router.get("/public")
async def public_endpoint():
    """This endpoint is always accessible."""
    return {"message": "This is a public endpoint"}


# Example 2: Protected endpoint (requires authentication)
@router.get("/protected")
async def protected_endpoint(current_user: Dict[str, Any] = Depends(get_current_user)):
    """This endpoint requires authentication."""
    return {
        "message": "This is a protected endpoint",
        "user": current_user.get("username"),
        "role": current_user.get("role")
    }


# Example 3: Optional authentication (works with or without auth)
@router.get("/optional")
async def optional_auth_endpoint(
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)
):
    """This endpoint works with or without authentication."""
    if current_user:
        return {
            "message": f"Hello {current_user.get('username')}!",
            "authenticated": True
        }
    else:
        return {
            "message": "Hello anonymous user!",
            "authenticated": False
        }


# Example 4: Role-based access control
@router.get("/admin-only")
async def admin_only_endpoint(
    current_user: Dict[str, Any] = Depends(require_role("admin"))
):
    """This endpoint requires admin role."""
    return {
        "message": "Admin access granted",
        "user": current_user.get("username")
    }


# Example 5: Manager or higher role
@router.get("/manager-area")
async def manager_area_endpoint(
    current_user: Dict[str, Any] = Depends(require_role("manager"))
):
    """This endpoint requires manager role or higher."""
    return {
        "message": "Manager access granted",
        "user": current_user.get("username"),
        "role": current_user.get("role")
    }


# Example 6: Using flexible auth dependency
@router.get("/flexible/{require_auth}")
async def flexible_auth_endpoint(
    require_auth: bool,
    current_user: Optional[Dict[str, Any]] = Depends(auth_required(False))
):
    """
    This endpoint can be configured to require auth or not.
    In a real app, this would be based on configuration, not URL parameter.
    """
    if require_auth and not current_user:
        return {"error": "Authentication required for this operation"}
    
    return {
        "message": "Flexible endpoint accessed",
        "auth_required": require_auth,
        "authenticated": current_user is not None,
        "user": current_user.get("username") if current_user else None
    }


# Example 7: Protecting existing endpoints
# You can modify existing endpoints like this:
from app.database.session import get_db
from sqlalchemy.orm import Session

@router.post("/protected-create")
async def create_protected_resource(
    data: dict,
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Example of protecting a create operation.
    Only authenticated and active users can create resources.
    """
    # Your create logic here
    return {
        "message": "Resource created",
        "created_by": current_user.get("username"),
        "data": data
    }