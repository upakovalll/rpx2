"""
Pydantic schemas for PropertyLocation/LoanProperty API.
"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class PropertyLocationBase(BaseModel):
    """Base schema for PropertyLocation/LoanProperty."""
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = 'United States'
    region: Optional[str] = None


class PropertyLocationCreate(PropertyLocationBase):
    """Schema for creating a PropertyLocation/LoanProperty."""
    pass


class PropertyLocationUpdate(BaseModel):
    """Schema for updating a PropertyLocation/LoanProperty."""
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None
    region: Optional[str] = None


class PropertyLocationResponse(PropertyLocationBase):
    """Schema for PropertyLocation/LoanProperty responses."""
    id: str  # Changed from int to str to handle UUIDs  
    rp_system_id: str  # Changed to str to handle bigint values
    property_number: int
    created_at: datetime
    
    class Config:
        from_attributes = True