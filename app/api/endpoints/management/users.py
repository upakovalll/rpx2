from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional
from uuid import UUID
import logging
import hashlib
import secrets

from app.database.session import get_db
from app.schemas.management import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserList,
    UserDetail,
    UserSummary,
    PasswordChange
)

logger = logging.getLogger(__name__)
router = APIRouter()


def hash_password(password: str) -> str:
    """Simple password hashing for demo purposes"""
    salt = secrets.token_hex(16)
    pwd_hash = hashlib.sha256(f"{password}{salt}".encode()).hexdigest()
    return f"{salt}${pwd_hash}"


def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against hash"""
    try:
        salt, pwd_hash = password_hash.split('$')
        return hashlib.sha256(f"{password}{salt}".encode()).hexdigest() == pwd_hash
    except:
        return False


@router.get("/", operation_id="list_users")
async def list_users(
    tenant_id: Optional[UUID] = None,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    is_active: Optional[bool] = None,
    is_admin: Optional[bool] = None,
    is_verified: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """List users with pagination and filtering"""
    try:
        query = """
            SELECT id, tenant_id, email, username, first_name, last_name,
                   is_active, is_verified, is_admin, is_super_admin,
                   last_login, metadata, created_at, updated_at
            FROM users 
            WHERE 1=1
        """
        params = {}
        
        if tenant_id:
            query += " AND tenant_id = :tenant_id"
            params['tenant_id'] = str(tenant_id)
            
        if is_active is not None:
            query += " AND is_active = :is_active"
            params['is_active'] = is_active
            
        if is_admin is not None:
            query += " AND is_admin = :is_admin"
            params['is_admin'] = is_admin
            
        if is_verified is not None:
            query += " AND is_verified = :is_verified"
            params['is_verified'] = is_verified
            
        # Get total count
        count_query = f"SELECT COUNT(*) FROM ({query}) as cnt"
        total = db.execute(text(count_query), params).scalar()
        
        # Add pagination
        query += " ORDER BY created_at DESC LIMIT :limit OFFSET :offset"
        params['limit'] = size
        params['offset'] = (page - 1) * size
        
        # Execute query
        result = db.execute(text(query), params)
        users = [dict(row._mapping) for row in result]
        
        return JSONResponse(content=jsonable_encoder({
            "users": users,
            "total": total,
            "page": page,
            "size": size
        }))
        
    except Exception as e:
        logger.error(f"Error listing users: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary", operation_id="get_user_summary")
async def get_user_summary(
    tenant_id: Optional[UUID] = None,
    db: Session = Depends(get_db)
):
    """Get user statistics summary by tenant"""
    try:
        query = "SELECT * FROM tenant_user_summary"
        params = {}
        
        if tenant_id:
            query += " WHERE tenant_id = :tenant_id"
            params['tenant_id'] = str(tenant_id)
            
        result = db.execute(text(query), params)
        summaries = [dict(row._mapping) for row in result]
        
        return JSONResponse(content=jsonable_encoder(summaries))
        
    except Exception as e:
        logger.error(f"Error getting user summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/details", operation_id="get_user_details")
async def get_user_details(
    tenant_id: Optional[UUID] = None,
    user_id: Optional[UUID] = None,
    db: Session = Depends(get_db)
):
    """Get detailed user information including organizations and tasks"""
    try:
        query = "SELECT * FROM tenant_user_details WHERE 1=1"
        params = {}
        
        if tenant_id:
            query += " AND tenant_id = :tenant_id"
            params['tenant_id'] = str(tenant_id)
            
        if user_id:
            query += " AND user_id = :user_id"
            params['user_id'] = str(user_id)
            
        query += " ORDER BY user_created_at DESC"
        
        result = db.execute(text(query), params)
        details = [dict(row._mapping) for row in result]
        
        return JSONResponse(content=jsonable_encoder(details))
        
    except Exception as e:
        logger.error(f"Error getting user details: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{user_id}", operation_id="get_user")
async def get_user(user_id: UUID, db: Session = Depends(get_db)):
    """Get a specific user by ID"""
    try:
        query = """
            SELECT id, tenant_id, email, username, first_name, last_name,
                   is_active, is_verified, is_admin, is_super_admin,
                   last_login, metadata, created_at, updated_at
            FROM users WHERE id = :user_id
        """
        result = db.execute(text(query), {"user_id": str(user_id)})
        user = result.mappings().first()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
            
        return JSONResponse(content=jsonable_encoder(dict(user)))
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", operation_id="create_user")
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Create a new user"""
    try:
        # Check if tenant exists
        tenant_check = "SELECT id FROM tenants WHERE id = :tenant_id"
        tenant_exists = db.execute(text(tenant_check), {"tenant_id": str(user.tenant_id)}).first()
        if not tenant_exists:
            raise HTTPException(status_code=404, detail="Tenant not found")
            
        # Check if email already exists for tenant
        email_check = "SELECT id FROM users WHERE tenant_id = :tenant_id AND email = :email"
        existing_email = db.execute(text(email_check), {
            "tenant_id": str(user.tenant_id),
            "email": user.email
        }).first()
        if existing_email:
            raise HTTPException(status_code=400, detail="Email already exists for this tenant")
            
        # Hash password
        password_hash = hash_password(user.password)
        
        # Insert new user
        insert_query = """
            INSERT INTO users (
                tenant_id, email, username, first_name, last_name,
                password_hash, is_admin, is_super_admin, metadata
            ) VALUES (
                :tenant_id, :email, :username, :first_name, :last_name,
                :password_hash, :is_admin, :is_super_admin, :metadata
            ) RETURNING id, tenant_id, email, username, first_name, last_name,
                       is_active, is_verified, is_admin, is_super_admin,
                       last_login, metadata, created_at, updated_at
        """
        
        params = user.model_dump(exclude={'password'})
        params['tenant_id'] = str(params['tenant_id'])
        params['password_hash'] = password_hash
        import json
        params['metadata'] = json.dumps(params.get('metadata', {}))
        
        result = db.execute(text(insert_query), params)
        db.commit()
        
        new_user = dict(result.mappings().first())
        return JSONResponse(content=jsonable_encoder(new_user))
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating user: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{user_id}", operation_id="update_user")
async def update_user(
    user_id: UUID,
    user_update: UserUpdate,
    db: Session = Depends(get_db)
):
    """Update a user"""
    try:
        # Check if user exists
        check_query = "SELECT id FROM users WHERE id = :user_id"
        existing = db.execute(text(check_query), {"user_id": str(user_id)}).first()
        if not existing:
            raise HTTPException(status_code=404, detail="User not found")
            
        # Build update query
        update_fields = []
        params = {"user_id": str(user_id)}
        
        for field, value in user_update.model_dump(exclude_unset=True).items():
            if value is not None:
                update_fields.append(f"{field} = :{field}")
                if field == 'metadata':
                    import json
                    params[field] = json.dumps(value)
                else:
                    params[field] = value
                    
        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")
            
        update_query = f"""
            UPDATE users 
            SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP
            WHERE id = :user_id
            RETURNING id, tenant_id, email, username, first_name, last_name,
                      is_active, is_verified, is_admin, is_super_admin,
                      last_login, metadata, created_at, updated_at
        """
        
        result = db.execute(text(update_query), params)
        db.commit()
        
        updated_user = dict(result.mappings().first())
        return JSONResponse(content=jsonable_encoder(updated_user))
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating user: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{user_id}/activate", operation_id="activate_user")
async def activate_user(user_id: UUID, db: Session = Depends(get_db)):
    """Activate a user"""
    try:
        update_query = """
            UPDATE users 
            SET is_active = true, updated_at = CURRENT_TIMESTAMP
            WHERE id = :user_id
            RETURNING id
        """
        
        result = db.execute(text(update_query), {"user_id": str(user_id)})
        if not result.rowcount:
            raise HTTPException(status_code=404, detail="User not found")
            
        db.commit()
        return {"message": "User activated successfully", "id": str(user_id)}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error activating user: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{user_id}/deactivate", operation_id="deactivate_user")
async def deactivate_user(user_id: UUID, db: Session = Depends(get_db)):
    """Deactivate a user"""
    try:
        update_query = """
            UPDATE users 
            SET is_active = false, updated_at = CURRENT_TIMESTAMP
            WHERE id = :user_id
            RETURNING id
        """
        
        result = db.execute(text(update_query), {"user_id": str(user_id)})
        if not result.rowcount:
            raise HTTPException(status_code=404, detail="User not found")
            
        db.commit()
        return {"message": "User deactivated successfully", "id": str(user_id)}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deactivating user: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{user_id}/change-password", operation_id="change_password")
async def change_password(
    user_id: UUID,
    password_change: PasswordChange,
    db: Session = Depends(get_db)
):
    """Change user password"""
    try:
        # Get current password hash
        query = "SELECT password_hash FROM users WHERE id = :user_id"
        result = db.execute(text(query), {"user_id": str(user_id)})
        user = result.first()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
            
        # Verify current password
        if not verify_password(password_change.current_password, user.password_hash):
            raise HTTPException(status_code=400, detail="Current password is incorrect")
            
        # Hash new password
        new_password_hash = hash_password(password_change.new_password)
        
        # Update password
        update_query = """
            UPDATE users 
            SET password_hash = :password_hash, updated_at = CURRENT_TIMESTAMP
            WHERE id = :user_id
        """
        
        db.execute(text(update_query), {
            "user_id": str(user_id),
            "password_hash": new_password_hash
        })
        db.commit()
        
        return {"message": "Password changed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error changing password: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))