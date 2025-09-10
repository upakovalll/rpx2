"""
Launch Configuration API endpoints for managing valuation and settlement dates.
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import date
from typing import Optional
from pydantic import BaseModel, Field

from app.database.session import get_db

router = APIRouter()


class LaunchConfigBase(BaseModel):
    """Base schema for launch configuration."""
    valuation_date: date = Field(..., description="Valuation date for pricing calculations")
    settlement_date: date = Field(..., description="Settlement date for transactions")


class LaunchConfigUpdate(BaseModel):
    """Schema for updating launch configuration."""
    valuation_date: Optional[date] = Field(None, description="New valuation date")
    settlement_date: Optional[date] = Field(None, description="New settlement date")


class LaunchConfigResponse(LaunchConfigBase):
    """Schema for launch config responses."""
    name: str = Field(..., description="Configuration name")
    updated_at: Optional[str] = None


@router.get("/current", operation_id="get_current_launch_config")
async def get_current_launch_config(db: Session = Depends(get_db)):
    """Get the current launch configuration (valuation and settlement dates)."""
    
    result = db.execute(text("""
        SELECT name, valuation_date, settlement_date, updated_at
        FROM launch_config
        WHERE name = 'DEFAULT'
    """)).mappings().first()
    
    if not result:
        # Create default configuration if it doesn't exist
        db.execute(text("""
            INSERT INTO launch_config (name, valuation_date, settlement_date)
            VALUES ('DEFAULT', CURRENT_DATE, CURRENT_DATE)
        """))
        db.commit()
        
        result = db.execute(text("""
            SELECT name, valuation_date, settlement_date, updated_at
            FROM launch_config
            WHERE name = 'DEFAULT'
        """)).mappings().first()
    
    return JSONResponse(content=jsonable_encoder(dict(result)))


@router.get("/valuation-date", operation_id="get_current_valuation_date")
async def get_current_valuation_date(db: Session = Depends(get_db)):
    """Get just the current valuation date."""
    
    result = db.execute(text("""
        SELECT valuation_date
        FROM launch_config
        WHERE name = 'DEFAULT'
    """)).mappings().first()
    
    if not result:
        raise HTTPException(status_code=404, detail="No launch configuration found")
    
    return JSONResponse(content={
        "valuation_date": result.valuation_date.isoformat(),
        "message": "Current valuation date for pricing calculations"
    })


@router.get("/settlement-date", operation_id="get_current_settlement_date")
async def get_current_settlement_date(db: Session = Depends(get_db)):
    """Get just the current settlement date."""
    
    result = db.execute(text("""
        SELECT settlement_date
        FROM launch_config
        WHERE name = 'DEFAULT'
    """)).mappings().first()
    
    if not result:
        raise HTTPException(status_code=404, detail="No launch configuration found")
    
    return JSONResponse(content={
        "settlement_date": result.settlement_date.isoformat(),
        "message": "Current settlement date for transactions"
    })


@router.put("/valuation-date", operation_id="update_valuation_date")
async def update_valuation_date(
    valuation_date: date,
    db: Session = Depends(get_db)
):
    """Update the valuation date."""
    
    result = db.execute(text("""
        UPDATE launch_config 
        SET valuation_date = :valuation_date,
            updated_at = CURRENT_TIMESTAMP
        WHERE name = 'DEFAULT'
        RETURNING name, valuation_date, settlement_date, updated_at
    """), {"valuation_date": valuation_date}).mappings().first()
    
    if not result:
        # Create default if it doesn't exist
        result = db.execute(text("""
            INSERT INTO launch_config (name, valuation_date, settlement_date)
            VALUES ('DEFAULT', :valuation_date, CURRENT_DATE)
            RETURNING name, valuation_date, settlement_date, updated_at
        """), {"valuation_date": valuation_date}).mappings().first()
    
    db.commit()
    
    return JSONResponse(content={
        "config": jsonable_encoder(dict(result)),
        "message": f"Valuation date updated to {valuation_date}"
    })


@router.put("/settlement-date", operation_id="update_settlement_date")
async def update_settlement_date(
    settlement_date: date,
    db: Session = Depends(get_db)
):
    """Update the settlement date."""
    
    result = db.execute(text("""
        UPDATE launch_config 
        SET settlement_date = :settlement_date,
            updated_at = CURRENT_TIMESTAMP
        WHERE name = 'DEFAULT'
        RETURNING name, valuation_date, settlement_date, updated_at
    """), {"settlement_date": settlement_date}).mappings().first()
    
    if not result:
        # Create default if it doesn't exist
        result = db.execute(text("""
            INSERT INTO launch_config (name, valuation_date, settlement_date)
            VALUES ('DEFAULT', CURRENT_DATE, :settlement_date)
            RETURNING name, valuation_date, settlement_date, updated_at
        """), {"settlement_date": settlement_date}).mappings().first()
    
    db.commit()
    
    return JSONResponse(content={
        "config": jsonable_encoder(dict(result)),
        "message": f"Settlement date updated to {settlement_date}"
    })


@router.put("/", operation_id="update_launch_config")
async def update_launch_config(
    config_update: LaunchConfigUpdate,
    db: Session = Depends(get_db)
):
    """Update both valuation and settlement dates."""
    
    # Build dynamic update query based on what fields are provided
    update_fields = []
    params = {}
    
    if config_update.valuation_date is not None:
        update_fields.append("valuation_date = :valuation_date")
        params["valuation_date"] = config_update.valuation_date
    
    if config_update.settlement_date is not None:
        update_fields.append("settlement_date = :settlement_date")
        params["settlement_date"] = config_update.settlement_date
    
    if not update_fields:
        raise HTTPException(status_code=400, detail="At least one date field must be provided")
    
    update_fields.append("updated_at = CURRENT_TIMESTAMP")
    
    query = f"""
        UPDATE launch_config 
        SET {', '.join(update_fields)}
        WHERE name = 'DEFAULT'
        RETURNING name, valuation_date, settlement_date, updated_at
    """
    
    result = db.execute(text(query), params).mappings().first()
    
    if not result:
        # Create default if it doesn't exist
        valuation_date = config_update.valuation_date or date.today()
        settlement_date = config_update.settlement_date or date.today()
        
        result = db.execute(text("""
            INSERT INTO launch_config (name, valuation_date, settlement_date)
            VALUES ('DEFAULT', :valuation_date, :settlement_date)
            RETURNING name, valuation_date, settlement_date, updated_at
        """), {
            "valuation_date": valuation_date,
            "settlement_date": settlement_date
        }).mappings().first()
    
    db.commit()
    
    return JSONResponse(content={
        "config": jsonable_encoder(dict(result)),
        "message": "Launch configuration updated successfully"
    })


@router.get("/", operation_id="list_launch_configs")
async def list_launch_configs(db: Session = Depends(get_db)):
    """List all launch configurations."""
    
    results = db.execute(text("""
        SELECT name, valuation_date, settlement_date, updated_at
        FROM launch_config
        ORDER BY name
    """)).mappings().all()
    
    return JSONResponse(content=jsonable_encoder([dict(row) for row in results]))


# Utility function to get the current valuation date for use in other modules
async def get_valuation_date_from_config(db: Session) -> date:
    """Get the current valuation date from launch_config. Used internally by other endpoints."""
    
    result = db.execute(text("""
        SELECT valuation_date
        FROM launch_config
        WHERE name = 'DEFAULT'
    """)).mappings().first()
    
    if not result:
        # Fallback to current date if no config exists
        return date.today()
    
    return result.valuation_date


# Utility function to get the current settlement date for use in other modules
async def get_settlement_date_from_config(db: Session) -> date:
    """Get the current settlement date from launch_config. Used internally by other endpoints."""
    
    result = db.execute(text("""
        SELECT settlement_date
        FROM launch_config
        WHERE name = 'DEFAULT'
    """)).mappings().first()
    
    if not result:
        # Fallback to current date if no config exists
        return date.today()
    
    return result.settlement_date