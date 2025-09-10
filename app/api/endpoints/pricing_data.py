"""
Pricing Data API endpoints for managing fixed and floating rate pricing data.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from decimal import Decimal
from pydantic import BaseModel, Field

from app.database.session import get_db

router = APIRouter()


class PricingDataFixedBase(BaseModel):
    """Base schema for fixed pricing data."""
    property_type: str = Field(..., description="Property type (e.g., Office, Retail)")
    ltv_bucket: str = Field(..., description="LTV bucket (e.g., 60-65, 65-70)")
    rating_bucket: str = Field(..., description="Rating bucket (e.g., A, B, C)")
    spread_bps: Decimal = Field(..., description="Spread in basis points", ge=0)


class PricingDataFloatingBase(BaseModel):
    """Base schema for floating pricing data."""
    property_type: str = Field(..., description="Property type")
    ltv_bucket: str = Field(..., description="LTV bucket")
    rating_bucket: str = Field(..., description="Rating bucket")
    margin_bps: Decimal = Field(..., description="Margin in basis points", ge=0)


class PricingDataFixedCreate(PricingDataFixedBase):
    """Schema for creating fixed pricing data."""
    pass


class PricingDataFloatingCreate(PricingDataFloatingBase):
    """Schema for creating floating pricing data."""
    pass


class PricingDataFixedResponse(PricingDataFixedBase):
    """Schema for fixed pricing data responses."""
    id: int
    created_at: Optional[str] = None


class PricingDataFloatingResponse(PricingDataFloatingBase):
    """Schema for floating pricing data responses."""
    id: int
    created_at: Optional[str] = None


# Fixed pricing data endpoints
@router.get("/fixed", operation_id="list_fixed_pricing_data")
async def get_fixed_pricing_data(
    property_type: Optional[str] = Query(None, description="Filter by property type"),
    ltv_bucket: Optional[str] = Query(None, description="Filter by LTV bucket"),
    rating_bucket: Optional[str] = Query(None, description="Filter by rating bucket"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get fixed rate pricing data with optional filters."""
    
    query = "SELECT * FROM pricing_data_fixed WHERE 1=1"
    params = {}
    
    if property_type:
        query += " AND property_type = :property_type"
        params["property_type"] = property_type
    
    if ltv_bucket:
        query += " AND ltv_bucket = :ltv_bucket"
        params["ltv_bucket"] = ltv_bucket
    
    if rating_bucket:
        query += " AND rating_bucket = :rating_bucket"
        params["rating_bucket"] = rating_bucket
    
    query += " ORDER BY property_type, ltv_bucket, rating_bucket"
    query += f" LIMIT {limit} OFFSET {skip}"
    
    result = db.execute(text(query), params).mappings().all()
    return JSONResponse(content=jsonable_encoder([dict(row) for row in result]))


@router.post("/fixed/bulk", operation_id="bulk_create_fixed_pricing_data")
async def bulk_create_fixed_pricing_data(
    pricing_data: List[PricingDataFixedCreate],
    db: Session = Depends(get_db)
):
    """Bulk create or update fixed pricing data."""
    
    try:
        for data in pricing_data:
            # First check if record exists
            check_query = text("""
                SELECT id FROM pricing_data_fixed 
                WHERE property_type = :property_type 
                AND ltv_bucket = :ltv_bucket 
                AND rating_bucket = :rating_bucket
            """)
            
            existing = db.execute(check_query, {
                "property_type": data.property_type,
                "ltv_bucket": data.ltv_bucket,
                "rating_bucket": data.rating_bucket
            }).first()
            
            if existing:
                # Update existing record
                update_query = text("""
                    UPDATE pricing_data_fixed 
                    SET spread_bps = :spread_bps, created_at = CURRENT_TIMESTAMP
                    WHERE id = :id
                """)
                db.execute(update_query, {
                    "id": existing.id,
                    "spread_bps": data.spread_bps
                })
            else:
                # Insert new record
                insert_query = text("""
                    INSERT INTO pricing_data_fixed 
                    (property_type, ltv_bucket, rating_bucket, spread_bps)
                    VALUES (:property_type, :ltv_bucket, :rating_bucket, :spread_bps)
                """)
                db.execute(insert_query, {
                    "property_type": data.property_type,
                    "ltv_bucket": data.ltv_bucket,
                    "rating_bucket": data.rating_bucket,
                    "spread_bps": data.spread_bps
                })
        
        db.commit()
        return {"message": f"Successfully processed {len(pricing_data)} fixed pricing records"}
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


# Floating pricing data endpoints
@router.get("/floating", operation_id="list_floating_pricing_data")
async def get_floating_pricing_data(
    property_type: Optional[str] = Query(None, description="Filter by property type"),
    ltv_bucket: Optional[str] = Query(None, description="Filter by LTV bucket"),
    rating_bucket: Optional[str] = Query(None, description="Filter by rating bucket"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get floating rate pricing data with optional filters."""
    
    query = "SELECT * FROM pricing_data_floating WHERE 1=1"
    params = {}
    
    if property_type:
        query += " AND property_type = :property_type"
        params["property_type"] = property_type
    
    if ltv_bucket:
        query += " AND ltv_bucket = :ltv_bucket"
        params["ltv_bucket"] = ltv_bucket
    
    if rating_bucket:
        query += " AND rating_bucket = :rating_bucket"
        params["rating_bucket"] = rating_bucket
    
    query += " ORDER BY property_type, ltv_bucket, rating_bucket"
    query += f" LIMIT {limit} OFFSET {skip}"
    
    result = db.execute(text(query), params).mappings().all()
    return JSONResponse(content=jsonable_encoder([dict(row) for row in result]))


@router.post("/floating/bulk", operation_id="bulk_create_floating_pricing_data")
async def bulk_create_floating_pricing_data(
    pricing_data: List[PricingDataFloatingCreate],
    db: Session = Depends(get_db)
):
    """Bulk create or update floating pricing data."""
    
    try:
        for data in pricing_data:
            # First check if record exists
            check_query = text("""
                SELECT id FROM pricing_data_floating 
                WHERE property_type = :property_type 
                AND ltv_bucket = :ltv_bucket 
                AND rating_bucket = :rating_bucket
            """)
            
            existing = db.execute(check_query, {
                "property_type": data.property_type,
                "ltv_bucket": data.ltv_bucket,
                "rating_bucket": data.rating_bucket
            }).first()
            
            if existing:
                # Update existing record
                update_query = text("""
                    UPDATE pricing_data_floating 
                    SET margin_bps = :margin_bps, created_at = CURRENT_TIMESTAMP
                    WHERE id = :id
                """)
                db.execute(update_query, {
                    "id": existing.id,
                    "margin_bps": data.margin_bps
                })
            else:
                # Insert new record
                insert_query = text("""
                    INSERT INTO pricing_data_floating 
                    (property_type, ltv_bucket, rating_bucket, margin_bps)
                    VALUES (:property_type, :ltv_bucket, :rating_bucket, :margin_bps)
                """)
                db.execute(insert_query, {
                    "property_type": data.property_type,
                    "ltv_bucket": data.ltv_bucket,
                    "rating_bucket": data.rating_bucket,
                    "margin_bps": data.margin_bps
                })
        
        db.commit()
        return {"message": f"Successfully processed {len(pricing_data)} floating pricing records"}
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


# Class spreads endpoint (from pricing_data_class_spreads table)
@router.get("/class-spreads", operation_id="list_class_spreads")
async def get_class_spreads(
    property_sector: Optional[str] = Query(None, description="Filter by property sector"),
    term_bucket: Optional[str] = Query(None, description="Filter by term bucket"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get class spreads data."""
    
    query = "SELECT * FROM pricing_data_class_spreads WHERE 1=1"
    params = {}
    
    if property_sector:
        query += " AND property_sector = :property_sector"
        params["property_sector"] = property_sector
    
    if term_bucket:
        query += " AND term_bucket = :term_bucket"
        params["term_bucket"] = term_bucket
    
    query += " ORDER BY property_sector, term_bucket"
    query += f" LIMIT {limit} OFFSET {skip}"
    
    result = db.execute(text(query), params).mappings().all()
    return JSONResponse(content=jsonable_encoder([dict(row) for row in result]))