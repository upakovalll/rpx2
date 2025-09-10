from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime


class TenantBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=255)
    subdomain: Optional[str] = Field(None, max_length=100)
    custom_domain: Optional[str] = Field(None, max_length=255)
    plan: Optional[str] = Field("free", pattern="^(free|starter|professional|enterprise)$")
    settings: Optional[Dict[str, Any]] = Field(default_factory=dict)
    limits: Optional[Dict[str, Any]] = Field(
        default_factory=lambda: {
            "max_users": 10,
            "max_projects": 5,
            "max_storage_gb": 10
        }
    )
    

class TenantCreate(TenantBase):
    pass


class TenantUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    subdomain: Optional[str] = Field(None, max_length=100)
    custom_domain: Optional[str] = Field(None, max_length=255)
    plan: Optional[str] = Field(None, pattern="^(free|starter|professional|enterprise)$")
    is_active: Optional[bool] = None
    settings: Optional[Dict[str, Any]] = None
    limits: Optional[Dict[str, Any]] = None


class TenantResponse(TenantBase):
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class TenantOverview(BaseModel):
    tenant_id: UUID
    tenant_name: str
    tenant_plan: Optional[str]
    total_configurations: int
    unique_providers: int
    active_configurations: int
    total_api_keys: int
    active_api_keys: int
    total_webhooks: int
    active_webhooks: int
    
    model_config = ConfigDict(from_attributes=True)


class TenantResourceUsage(BaseModel):
    tenant_id: UUID
    tenant_name: str
    plan: Optional[str]
    is_active: bool
    users_count: int
    max_users: Optional[int]
    projects_count: int
    max_projects: Optional[int]
    max_storage_gb: Optional[int]
    at_user_limit: bool
    at_project_limit: bool
    tenant_created_at: datetime
    last_user_activity: Optional[datetime]
    
    model_config = ConfigDict(from_attributes=True)


class TenantList(BaseModel):
    tenants: List[TenantResponse]
    total: int
    page: int
    size: int