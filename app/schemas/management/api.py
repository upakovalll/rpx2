from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime


class APIProviderBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    display_name: str = Field(..., min_length=1, max_length=255)
    auth_type: str = Field(..., pattern="^(api_key|oauth2|basic|jwt)$")
    base_url: str
    rate_limits: Optional[Dict[str, Any]] = Field(default_factory=dict)
    settings: Optional[Dict[str, Any]] = Field(default_factory=dict)


class APIProviderResponse(APIProviderBase):
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class APIConfigurationBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    environment: Optional[str] = Field("production", pattern="^(development|staging|production)$")
    settings: Optional[Dict[str, Any]] = Field(default_factory=dict)


class APIConfigurationCreate(APIConfigurationBase):
    tenant_id: UUID
    provider_id: UUID


class APIConfigurationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    environment: Optional[str] = Field(None, pattern="^(development|staging|production)$")
    is_active: Optional[bool] = None
    settings: Optional[Dict[str, Any]] = None


class APIConfigurationResponse(APIConfigurationBase):
    id: UUID
    tenant_id: UUID
    provider_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class APIKeyBase(BaseModel):
    key_name: str = Field(..., min_length=1, max_length=255)
    key_hint: Optional[str] = Field(None, max_length=20)
    expires_at: Optional[datetime] = None


class APIKeyCreate(APIKeyBase):
    configuration_id: UUID


class APIKeyResponse(APIKeyBase):
    id: UUID
    configuration_id: UUID
    is_active: bool
    last_used_at: Optional[datetime]
    created_by: Optional[UUID]
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class APIKeyWithValue(APIKeyResponse):
    api_key: str


class APIKeyStatus(BaseModel):
    tenant_id: UUID
    tenant_name: str
    provider_name: str
    configuration_name: str
    environment: Optional[str]
    key_id: UUID
    key_name: str
    key_hint: Optional[str]
    is_active: bool
    expires_at: Optional[datetime]
    expiry_status: str
    last_used_at: Optional[datetime]
    usage_status: str
    created_by_email: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class APIUsageStatistics(BaseModel):
    tenant_id: UUID
    tenant_name: str
    provider_name: str
    provider_display_name: str
    configuration_name: str
    environment: Optional[str]
    total_calls: int
    successful_calls: int
    failed_calls: int
    avg_duration_ms: Optional[float]
    max_duration_ms: Optional[float]
    min_duration_ms: Optional[float]
    unique_users: int
    days_with_activity: int
    last_call_at: Optional[datetime]
    
    model_config = ConfigDict(from_attributes=True)


class APICallPerformance(BaseModel):
    tenant_id: UUID
    tenant_name: str
    provider_name: str
    endpoint: str
    method: str
    call_count: int
    avg_duration_ms: Optional[float]
    median_duration_ms: Optional[float]
    p95_duration_ms: Optional[float]
    max_duration_ms: Optional[float]
    success_count: int
    client_error_count: int
    server_error_count: int
    success_rate: Optional[float]
    
    model_config = ConfigDict(from_attributes=True)


class APIRateLimitStatus(BaseModel):
    tenant_id: UUID
    tenant_name: str
    provider_name: str
    provider_display_name: str
    configuration_name: str
    calls_last_minute: int
    rate_limit_per_minute: Optional[int]
    minute_usage_percentage: Optional[float]
    calls_last_hour: int
    rate_limit_per_hour: Optional[int]
    hour_usage_percentage: Optional[float]
    rate_limit_status: str
    
    model_config = ConfigDict(from_attributes=True)


class APISecurityAudit(BaseModel):
    tenant_id: UUID
    tenant_name: str
    provider_name: str
    configuration_name: str
    environment: Optional[str]
    auth_type: str
    total_keys: int
    expired_keys: int
    expiring_soon_keys: int
    unused_keys: int
    oldest_key_created: Optional[datetime]
    last_key_updated: Optional[datetime]
    users_making_calls: int
    auth_failures_last_30d: int
    
    model_config = ConfigDict(from_attributes=True)