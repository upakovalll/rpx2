from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime


class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    tenant_id: UUID
    is_admin: Optional[bool] = False
    is_super_admin: Optional[bool] = False


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    is_admin: Optional[bool] = None
    is_super_admin: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None


class UserResponse(UserBase):
    id: UUID
    tenant_id: UUID
    is_active: bool
    is_verified: bool
    is_admin: bool
    is_super_admin: bool
    last_login: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class UserDetail(UserResponse):
    tenant_name: str
    tenant_subdomain: Optional[str]
    organizations_count: int
    assigned_tasks_count: int
    completed_tasks_count: int
    organizations: Optional[str]
    roles: Optional[str]
    
    model_config = ConfigDict(from_attributes=True)


class UserSummary(BaseModel):
    tenant_id: UUID
    tenant_name: str
    tenant_plan: Optional[str]
    total_users: int
    active_users: int
    admin_users: int
    verified_users: int
    active_last_30_days: int
    active_last_7_days: int
    new_users_last_30_days: int
    user_limit: Optional[int]
    user_limit_percentage: Optional[float]
    
    model_config = ConfigDict(from_attributes=True)


class UserList(BaseModel):
    users: List[UserResponse]
    total: int
    page: int
    size: int


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)