from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional
from uuid import UUID
import logging

from app.database.session import get_db
from app.schemas.management import (
    TenantCreate, 
    TenantUpdate, 
    TenantResponse, 
    TenantList,
    TenantOverview,
    TenantResourceUsage
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", operation_id="list_tenants")
async def list_tenants(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    is_active: Optional[bool] = None,
    plan: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all tenants with pagination and filtering"""
    try:
        # Build query
        query = """
            SELECT * FROM tenants 
            WHERE 1=1
        """
        params = {}
        
        if is_active is not None:
            query += " AND is_active = :is_active"
            params['is_active'] = is_active
            
        if plan:
            query += " AND plan = :plan"
            params['plan'] = plan
            
        # Get total count
        count_query = f"SELECT COUNT(*) FROM ({query}) as cnt"
        total = db.execute(text(count_query), params).scalar()
        
        # Add pagination
        query += " ORDER BY created_at DESC LIMIT :limit OFFSET :offset"
        params['limit'] = size
        params['offset'] = (page - 1) * size
        
        # Execute query
        result = db.execute(text(query), params)
        tenants = [dict(row._mapping) for row in result]
        
        return JSONResponse(content=jsonable_encoder({
            "tenants": tenants,
            "total": total,
            "page": page,
            "size": size
        }))
        
    except Exception as e:
        logger.error(f"Error listing tenants: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/overview", operation_id="get_tenants_overview")
async def get_tenants_overview(
    tenant_id: Optional[UUID] = None,
    db: Session = Depends(get_db)
):
    """Get tenant overview with API and user statistics"""
    try:
        query = "SELECT * FROM tenant_api_overview"
        params = {}
        
        if tenant_id:
            query += " WHERE tenant_id = :tenant_id"
            params['tenant_id'] = str(tenant_id)
            
        result = db.execute(text(query), params)
        overviews = [dict(row._mapping) for row in result]
        
        return JSONResponse(content=jsonable_encoder(overviews))
        
    except Exception as e:
        logger.error(f"Error getting tenant overview: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/resource-usage", operation_id="get_resource_usage")
async def get_resource_usage(
    tenant_id: Optional[UUID] = None,
    at_limit: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """Get resource usage statistics for tenants"""
    try:
        query = "SELECT * FROM tenant_resource_usage WHERE 1=1"
        params = {}
        
        if tenant_id:
            query += " AND tenant_id = :tenant_id"
            params['tenant_id'] = str(tenant_id)
            
        if at_limit:
            query += " AND (at_user_limit = true OR at_project_limit = true)"
            
        result = db.execute(text(query), params)
        usage_data = [dict(row._mapping) for row in result]
        
        return JSONResponse(content=jsonable_encoder(usage_data))
        
    except Exception as e:
        logger.error(f"Error getting resource usage: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{tenant_id}", operation_id="get_tenant")
async def get_tenant(tenant_id: UUID, db: Session = Depends(get_db)):
    """Get a specific tenant by ID"""
    try:
        query = "SELECT * FROM tenants WHERE id = :tenant_id"
        result = db.execute(text(query), {"tenant_id": str(tenant_id)})
        tenant = result.mappings().first()
        
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
            
        return JSONResponse(content=jsonable_encoder(dict(tenant)))
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tenant: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", operation_id="create_tenant", response_model=TenantResponse)
async def create_tenant(tenant: TenantCreate, db: Session = Depends(get_db)):
    """Create a new tenant"""
    try:
        # Check if slug already exists
        check_query = "SELECT id FROM tenants WHERE slug = :slug"
        existing = db.execute(text(check_query), {"slug": tenant.slug}).first()
        if existing:
            raise HTTPException(status_code=400, detail="Slug already exists")
            
        # Insert new tenant
        insert_query = """
            INSERT INTO tenants (
                name, slug, subdomain, custom_domain, plan, settings, limits
            ) VALUES (
                :name, :slug, :subdomain, :custom_domain, :plan, :settings, :limits
            ) RETURNING *
        """
        
        params = tenant.model_dump()
        import json
        params['settings'] = json.dumps(params.get('settings', {}))
        params['limits'] = json.dumps(params.get('limits', {
            "max_users": 10,
            "max_projects": 5, 
            "max_storage_gb": 10
        }))
        
        result = db.execute(text(insert_query), params)
        db.commit()
        
        new_tenant = dict(result.mappings().first())
        return JSONResponse(content=jsonable_encoder(new_tenant))
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating tenant: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{tenant_id}", operation_id="update_tenant")
async def update_tenant(
    tenant_id: UUID, 
    tenant_update: TenantUpdate,
    db: Session = Depends(get_db)
):
    """Update a tenant"""
    try:
        # Check if tenant exists
        check_query = "SELECT id FROM tenants WHERE id = :tenant_id"
        existing = db.execute(text(check_query), {"tenant_id": str(tenant_id)}).first()
        if not existing:
            raise HTTPException(status_code=404, detail="Tenant not found")
            
        # Build update query
        update_fields = []
        params = {"tenant_id": str(tenant_id)}
        
        for field, value in tenant_update.model_dump(exclude_unset=True).items():
            if value is not None:
                update_fields.append(f"{field} = :{field}")
                if field in ['settings', 'limits']:
                    import json
                    params[field] = json.dumps(value)
                else:
                    params[field] = value
                    
        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")
            
        update_query = f"""
            UPDATE tenants 
            SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP
            WHERE id = :tenant_id
            RETURNING *
        """
        
        result = db.execute(text(update_query), params)
        db.commit()
        
        updated_tenant = dict(result.mappings().first())
        return JSONResponse(content=jsonable_encoder(updated_tenant))
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating tenant: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{tenant_id}", operation_id="delete_tenant")
async def delete_tenant(tenant_id: UUID, db: Session = Depends(get_db)):
    """Delete a tenant (soft delete by setting is_active=false)"""
    try:
        # Check if tenant exists
        check_query = "SELECT id FROM tenants WHERE id = :tenant_id"
        existing = db.execute(text(check_query), {"tenant_id": str(tenant_id)}).first()
        if not existing:
            raise HTTPException(status_code=404, detail="Tenant not found")
            
        # Soft delete
        update_query = """
            UPDATE tenants 
            SET is_active = false, updated_at = CURRENT_TIMESTAMP
            WHERE id = :tenant_id
            RETURNING id
        """
        
        result = db.execute(text(update_query), {"tenant_id": str(tenant_id)})
        db.commit()
        
        return {"message": "Tenant deactivated successfully", "id": str(tenant_id)}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting tenant: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))