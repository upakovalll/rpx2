"""
PropertyLocations API endpoints.
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.database.session import get_db
from app.models.property_location import PropertyLocation
from app.schemas.property_location import (
    PropertyLocationCreate, 
    PropertyLocationUpdate, 
    PropertyLocationResponse
)

router = APIRouter()

@router.get("/", response_model=List[PropertyLocationResponse], operation_id="list_properties")
async def get_property_locations(db: Session = Depends(get_db)):
    """Get all property locations."""
    return db.query(PropertyLocation).all()

@router.get("/{location_id}", response_model=PropertyLocationResponse, operation_id="get_property")
async def get_property_location_by_id(location_id: UUID, db: Session = Depends(get_db)):
    """Get a specific property location by ID."""
    location = db.query(PropertyLocation).filter(PropertyLocation.location_id == location_id).first()
    if not location:
        raise HTTPException(status_code=404, detail="Property location not found")
    return location

@router.post("/", response_model=PropertyLocationResponse, operation_id="create_property")
async def create_property_location(location_data: PropertyLocationCreate, db: Session = Depends(get_db)):
    """Create a new property location."""
    db_location = PropertyLocation(**location_data.dict())
    db.add(db_location)
    db.commit()
    db.refresh(db_location)
    return db_location

@router.put("/{location_id}", response_model=PropertyLocationResponse, operation_id="update_property")
async def update_property_location_by_id(location_id: UUID, location_update: PropertyLocationUpdate, db: Session = Depends(get_db)):
    """Update a property location."""
    db_location = db.query(PropertyLocation).filter(PropertyLocation.location_id == location_id).first()
    if not db_location:
        raise HTTPException(status_code=404, detail="Property location not found")
    update_data = location_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_location, field, value)
    db.commit()
    db.refresh(db_location)
    return db_location

@router.delete("/{location_id}", operation_id="delete_property")
async def delete_property_location_by_id(location_id: UUID, db: Session = Depends(get_db)):
    """Delete a property location."""
    db_location = db.query(PropertyLocation).filter(PropertyLocation.location_id == location_id).first()
    if not db_location:
        raise HTTPException(status_code=404, detail="Property location not found")
    db.delete(db_location)
    db.commit()
    return {"message": "Property location deleted successfully"} 