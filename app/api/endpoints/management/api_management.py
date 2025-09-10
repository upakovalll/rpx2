from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional, List
from uuid import UUID, uuid4
import logging
import secrets
import string

from app.database.session import get_db
from app.schemas.management import (
    APIProviderResponse,
    APIConfigurationCreate,
    APIConfigurationUpdate,
    APIConfigurationResponse,
    APIKeyCreate,
    APIKeyResponse,
    APIKeyWithValue,
    APIKeyStatus,
    APIUsageStatistics,
    APICallPerformance,
    APIRateLimitStatus,
    APISecurityAudit
)

logger = logging.getLogger(__name__)
router = APIRouter()


def generate_api_key() -> tuple[str, str]:
    """Generate a new API key and its hint"""
    key = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
    hint = f"****{key[-4:]}"
    return key, hint


@router.get("/providers", operation_id="list_providers")
async def list_api_providers(
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """List all available API providers"""
    try:
        query = "SELECT * FROM api_providers WHERE 1=1"
        params = {}
        
        if is_active is not None:
            query += " AND is_active = :is_active"
            params['is_active'] = is_active
            
        query += " ORDER BY display_name"
        
        result = db.execute(text(query), params)
        providers = [dict(row._mapping) for row in result]
        
        return JSONResponse(content=jsonable_encoder(providers))
        
    except Exception as e:
        logger.error(f"Error listing API providers: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/configurations", operation_id="list_configs")
async def list_api_configurations(
    tenant_id: Optional[UUID] = None,
    provider_id: Optional[UUID] = None,
    environment: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """List API configurations with filtering"""
    try:
        query = """
            SELECT ac.*, ap.name as provider_name, ap.display_name as provider_display_name
            FROM api_configurations ac
            JOIN api_providers ap ON ac.provider_id = ap.id
            WHERE 1=1
        """
        params = {}
        
        if tenant_id:
            query += " AND ac.tenant_id = :tenant_id"
            params['tenant_id'] = str(tenant_id)
            
        if provider_id:
            query += " AND ac.provider_id = :provider_id"
            params['provider_id'] = str(provider_id)
            
        if environment:
            query += " AND ac.environment = :environment"
            params['environment'] = environment
            
        if is_active is not None:
            query += " AND ac.is_active = :is_active"
            params['is_active'] = is_active
            
        query += " ORDER BY ac.created_at DESC"
        
        result = db.execute(text(query), params)
        configurations = [dict(row._mapping) for row in result]
        
        return JSONResponse(content=jsonable_encoder(configurations))
        
    except Exception as e:
        logger.error(f"Error listing configurations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/configurations/{config_id}", operation_id="get_config")
async def get_api_configuration(config_id: UUID, db: Session = Depends(get_db)):
    """Get a specific API configuration"""
    try:
        query = """
            SELECT ac.*, ap.name as provider_name, ap.display_name as provider_display_name
            FROM api_configurations ac
            JOIN api_providers ap ON ac.provider_id = ap.id
            WHERE ac.id = :config_id
        """
        result = db.execute(text(query), {"config_id": str(config_id)})
        config = result.mappings().first()
        
        if not config:
            raise HTTPException(status_code=404, detail="Configuration not found")
            
        return JSONResponse(content=jsonable_encoder(dict(config)))
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting configuration: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/configurations", operation_id="create_config")
async def create_api_configuration(
    config: APIConfigurationCreate,
    db: Session = Depends(get_db)
):
    """Create a new API configuration"""
    try:
        # Check if tenant and provider exist
        tenant_check = "SELECT id FROM tenants WHERE id = :tenant_id"
        if not db.execute(text(tenant_check), {"tenant_id": str(config.tenant_id)}).first():
            raise HTTPException(status_code=404, detail="Tenant not found")
            
        provider_check = "SELECT id FROM api_providers WHERE id = :provider_id"
        if not db.execute(text(provider_check), {"provider_id": str(config.provider_id)}).first():
            raise HTTPException(status_code=404, detail="Provider not found")
            
        # Check for duplicate configuration
        dup_check = """
            SELECT id FROM api_configurations 
            WHERE tenant_id = :tenant_id AND provider_id = :provider_id AND environment = :environment
        """
        if db.execute(text(dup_check), {
            "tenant_id": str(config.tenant_id),
            "provider_id": str(config.provider_id),
            "environment": config.environment
        }).first():
            raise HTTPException(status_code=400, detail="Configuration already exists for this combination")
            
        # Insert new configuration
        insert_query = """
            INSERT INTO api_configurations (
                tenant_id, provider_id, name, environment, settings
            ) VALUES (
                :tenant_id, :provider_id, :name, :environment, :settings
            ) RETURNING *
        """
        
        params = config.model_dump()
        params['tenant_id'] = str(params['tenant_id'])
        params['provider_id'] = str(params['provider_id'])
        import json
        params['settings'] = json.dumps(params.get('settings', {}))
        
        result = db.execute(text(insert_query), params)
        db.commit()
        
        new_config = dict(result.mappings().first())
        return JSONResponse(content=jsonable_encoder(new_config))
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating configuration: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/configurations/{config_id}", operation_id="update_config")
async def update_api_configuration(
    config_id: UUID,
    config_update: APIConfigurationUpdate,
    db: Session = Depends(get_db)
):
    """Update an API configuration"""
    try:
        # Check if configuration exists
        check_query = "SELECT id FROM api_configurations WHERE id = :config_id"
        if not db.execute(text(check_query), {"config_id": str(config_id)}).first():
            raise HTTPException(status_code=404, detail="Configuration not found")
            
        # Build update query
        update_fields = []
        params = {"config_id": str(config_id)}
        
        for field, value in config_update.model_dump(exclude_unset=True).items():
            if value is not None:
                update_fields.append(f"{field} = :{field}")
                if field == 'settings':
                    import json
                    params[field] = json.dumps(value)
                else:
                    params[field] = value
                    
        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")
            
        update_query = f"""
            UPDATE api_configurations 
            SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP
            WHERE id = :config_id
            RETURNING *
        """
        
        result = db.execute(text(update_query), params)
        db.commit()
        
        updated_config = dict(result.mappings().first())
        return JSONResponse(content=jsonable_encoder(updated_config))
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating configuration: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/configurations/{config_id}", operation_id="delete_config")
async def delete_api_configuration(config_id: UUID, db: Session = Depends(get_db)):
    """Delete an API configuration (soft delete)"""
    try:
        update_query = """
            UPDATE api_configurations 
            SET is_active = false, updated_at = CURRENT_TIMESTAMP
            WHERE id = :config_id
            RETURNING id
        """
        
        result = db.execute(text(update_query), {"config_id": str(config_id)})
        if not result.rowcount:
            raise HTTPException(status_code=404, detail="Configuration not found")
            
        db.commit()
        return {"message": "Configuration deactivated successfully", "id": str(config_id)}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting configuration: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# API Key Management
@router.get("/keys", operation_id="list_api_keys")
async def list_api_keys(
    configuration_id: Optional[UUID] = None,
    tenant_id: Optional[UUID] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """List API keys with filtering"""
    try:
        query = """
            SELECT * FROM api_key_status WHERE 1=1
        """
        params = {}
        
        if configuration_id:
            query += " AND configuration_id = :configuration_id"
            params['configuration_id'] = str(configuration_id)
            
        if tenant_id:
            query += " AND tenant_id = :tenant_id"
            params['tenant_id'] = str(tenant_id)
            
        if is_active is not None:
            query += " AND is_active = :is_active"
            params['is_active'] = is_active
            
        query += " ORDER BY created_at DESC"
        
        result = db.execute(text(query), params)
        keys = [dict(row._mapping) for row in result]
        
        return JSONResponse(content=jsonable_encoder(keys))
        
    except Exception as e:
        logger.error(f"Error listing API keys: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/keys", operation_id="create_api_key")
async def create_api_key(
    key_data: APIKeyCreate,
    created_by: Optional[UUID] = None,
    db: Session = Depends(get_db)
):
    """Create a new API key"""
    try:
        # Check if configuration exists
        config_check = "SELECT id FROM api_configurations WHERE id = :config_id"
        if not db.execute(text(config_check), {"config_id": str(key_data.configuration_id)}).first():
            raise HTTPException(status_code=404, detail="Configuration not found")
            
        # Generate API key
        api_key, key_hint = generate_api_key()
        
        # Insert new key (store hash in production)
        insert_query = """
            INSERT INTO api_keys (
                configuration_id, key_name, encrypted_value, key_hint, expires_at, created_by
            ) VALUES (
                :configuration_id, :key_name, :encrypted_value, :key_hint, :expires_at, :created_by
            ) RETURNING id, configuration_id, key_name, key_hint, is_active, 
                       expires_at, last_used_at, created_by, created_at, updated_at
        """
        
        params = key_data.model_dump()
        params['configuration_id'] = str(params['configuration_id'])
        params['encrypted_value'] = api_key  # In production, encrypt this properly
        params['key_hint'] = key_hint
        params['created_by'] = str(created_by) if created_by else None
        
        result = db.execute(text(insert_query), params)
        db.commit()
        
        new_key = dict(result.mappings().first())
        new_key['api_key'] = api_key  # Return full key only on creation
        
        return JSONResponse(content=jsonable_encoder(new_key))
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating API key: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/keys/{key_id}/revoke", operation_id="revoke_api_key")
async def revoke_api_key(key_id: UUID, db: Session = Depends(get_db)):
    """Revoke an API key"""
    try:
        update_query = """
            UPDATE api_keys 
            SET is_active = false, updated_at = CURRENT_TIMESTAMP
            WHERE id = :key_id
            RETURNING id
        """
        
        result = db.execute(text(update_query), {"key_id": str(key_id)})
        if not result.rowcount:
            raise HTTPException(status_code=404, detail="API key not found")
            
        db.commit()
        return {"message": "API key revoked successfully", "id": str(key_id)}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error revoking API key: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/keys/{key_id}/rotate", operation_id="rotate_api_key")
async def rotate_api_key(key_id: UUID, db: Session = Depends(get_db)):
    """Rotate an API key (revoke old, create new)"""
    try:
        # Get existing key info
        query = """
            SELECT configuration_id, key_name, expires_at, created_by
            FROM api_keys WHERE id = :key_id AND is_active = true
        """
        result = db.execute(text(query), {"key_id": str(key_id)})
        old_key = result.mappings().first()
        
        if not old_key:
            raise HTTPException(status_code=404, detail="Active API key not found")
            
        # Revoke old key
        revoke_query = """
            UPDATE api_keys 
            SET is_active = false, updated_at = CURRENT_TIMESTAMP
            WHERE id = :key_id
        """
        db.execute(text(revoke_query), {"key_id": str(key_id)})
        
        # Create new key
        api_key, key_hint = generate_api_key()
        
        create_query = """
            INSERT INTO api_keys (
                configuration_id, key_name, encrypted_value, key_hint, expires_at, created_by
            ) VALUES (
                :configuration_id, :key_name, :encrypted_value, :key_hint, :expires_at, :created_by
            ) RETURNING id, configuration_id, key_name, key_hint, is_active, 
                       expires_at, last_used_at, created_by, created_at, updated_at
        """
        
        params = dict(old_key)
        params['key_name'] = f"{params['key_name']} (rotated)"
        params['encrypted_value'] = api_key
        params['key_hint'] = key_hint
        params['configuration_id'] = str(params['configuration_id'])
        params['created_by'] = str(params['created_by']) if params.get('created_by') else None
        
        result = db.execute(text(create_query), params)
        db.commit()
        
        new_key = dict(result.mappings().first())
        new_key['api_key'] = api_key
        new_key['old_key_id'] = str(key_id)
        
        return JSONResponse(content=jsonable_encoder(new_key))
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error rotating API key: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))