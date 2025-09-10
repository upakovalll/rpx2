"""
RPX Adjustments API endpoints for managing all RPX adjustment tables.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional, Dict, Any
from decimal import Decimal
from pydantic import BaseModel, Field

from app.database.session import get_db

router = APIRouter()


# LTV Factor Adjustment Schemas
class LTVFactorAdjustmentBase(BaseModel):
    """Base schema for LTV factor adjustments."""
    property_sector: str = Field(..., description="Property sector")
    ltv_lt_50_pct: Optional[Decimal] = Field(None, description="Adjustment for LTV < 50%")
    ltv_50_59_pct: Optional[Decimal] = Field(None, description="Adjustment for LTV 50-59%")
    ltv_60_65_pct: Optional[Decimal] = Field(None, description="Adjustment for LTV 60-65%")
    ltv_66_70_pct: Optional[Decimal] = Field(None, description="Adjustment for LTV 66-70%")


class LTVFactorAdjustmentCreate(LTVFactorAdjustmentBase):
    pass


# DSCR Adjustment Schemas
class DSCRAdjustmentBase(BaseModel):
    """Base schema for DSCR adjustments."""
    min_value: Decimal = Field(..., description="Minimum DSCR value")
    max_value: Decimal = Field(..., description="Maximum DSCR value")
    adjustment_value: Decimal = Field(0, description="Adjustment value")
    dscr_threshold: Optional[str] = Field(None, description="DSCR threshold description")
    sort_order: Optional[int] = Field(None, description="Sort order")


class DSCRAdjustmentCreate(DSCRAdjustmentBase):
    pass


# SASB Premium Schemas
class SASBPremiumBase(BaseModel):
    """Base schema for SASB loan size premiums."""
    loan_size_threshold: Decimal = Field(default=125000000, description="Loan size threshold")
    premium_rate: Decimal = Field(..., description="Premium rate")


class SASBPremiumCreate(SASBPremiumBase):
    pass


# Loan Status Adjustment Schemas
class LoanStatusAdjustmentBase(BaseModel):
    """Base schema for loan status adjustments."""
    loan_status: str = Field(..., description="Loan status")
    adjustment_bps: Decimal = Field(..., description="Adjustment in basis points")
    description: Optional[str] = Field(None, description="Description")


class LoanStatusAdjustmentCreate(LoanStatusAdjustmentBase):
    pass


# Generic Response Schema
class RPXAdjustmentResponse(BaseModel):
    """Generic response for RPX adjustments."""
    id: int
    data: Dict[str, Any]
    created_at: Optional[str] = None


# LTV Factor Adjustments
@router.get("/ltv-factor", operation_id="list_ltv_factor_adjustments")
async def get_ltv_factor_adjustments(
    property_sector: Optional[str] = Query(None, description="Filter by property sector"),
    db: Session = Depends(get_db)
):
    """Get LTV factor adjustments."""
    
    query = "SELECT * FROM rpx_ltv_factor_adjustment WHERE 1=1"
    params = {}
    
    if property_sector:
        query += " AND property_sector = :property_sector"
        params["property_sector"] = property_sector
    
    query += " ORDER BY property_sector"
    
    result = db.execute(text(query), params).mappings().all()
    return JSONResponse(content=jsonable_encoder([dict(row) for row in result]))


@router.post("/ltv-factor/bulk", operation_id="bulk_create_ltv_factor_adjustments")
async def bulk_create_ltv_factor_adjustments(
    adjustments: List[LTVFactorAdjustmentCreate],
    db: Session = Depends(get_db)
):
    """Bulk create or update LTV factor adjustments."""
    
    try:
        for adj in adjustments:
            # Check if exists
            existing = db.execute(text("""
                SELECT id FROM rpx_ltv_factor_adjustment 
                WHERE property_sector = :property_sector
            """), {"property_sector": adj.property_sector}).first()
            
            if existing:
                # Update
                db.execute(text("""
                    UPDATE rpx_ltv_factor_adjustment 
                    SET ltv_lt_50_pct = :ltv_lt_50_pct,
                        ltv_50_59_pct = :ltv_50_59_pct,
                        ltv_60_65_pct = :ltv_60_65_pct,
                        ltv_66_70_pct = :ltv_66_70_pct
                    WHERE id = :id
                """), {
                    "id": existing.id,
                    "ltv_lt_50_pct": adj.ltv_lt_50_pct,
                    "ltv_50_59_pct": adj.ltv_50_59_pct,
                    "ltv_60_65_pct": adj.ltv_60_65_pct,
                    "ltv_66_70_pct": adj.ltv_66_70_pct
                })
            else:
                # Insert
                db.execute(text("""
                    INSERT INTO rpx_ltv_factor_adjustment 
                    (property_sector, ltv_lt_50_pct, ltv_50_59_pct, ltv_60_65_pct, ltv_66_70_pct)
                    VALUES (:property_sector, :ltv_lt_50_pct, :ltv_50_59_pct, :ltv_60_65_pct, :ltv_66_70_pct)
                """), {
                    "property_sector": adj.property_sector,
                    "ltv_lt_50_pct": adj.ltv_lt_50_pct,
                    "ltv_50_59_pct": adj.ltv_50_59_pct,
                    "ltv_60_65_pct": adj.ltv_60_65_pct,
                    "ltv_66_70_pct": adj.ltv_66_70_pct
                })
        
        db.commit()
        return {"message": f"Successfully processed {len(adjustments)} LTV factor adjustments"}
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


# DSCR Adjustments
@router.get("/dscr", operation_id="list_dscr_adjustments")
async def get_dscr_adjustments(db: Session = Depends(get_db)):
    """Get DSCR adjustments."""
    
    result = db.execute(text("""
        SELECT * FROM rpx_dscr_adjustment 
        ORDER BY sort_order, min_value
    """)).mappings().all()
    
    return JSONResponse(content=jsonable_encoder([dict(row) for row in result]))


@router.post("/dscr/bulk", operation_id="bulk_create_dscr_adjustments")
async def bulk_create_dscr_adjustments(
    adjustments: List[DSCRAdjustmentCreate],
    db: Session = Depends(get_db)
):
    """Bulk create DSCR adjustments."""
    
    try:
        # Clear existing adjustments
        db.execute(text("DELETE FROM rpx_dscr_adjustment"))
        
        # Insert new adjustments
        for i, adj in enumerate(adjustments):
            db.execute(text("""
                INSERT INTO rpx_dscr_adjustment 
                (min_value, max_value, adjustment_value, dscr_threshold, sort_order)
                VALUES (:min_value, :max_value, :adjustment_value, :dscr_threshold, :sort_order)
            """), {
                "min_value": adj.min_value,
                "max_value": adj.max_value,
                "adjustment_value": adj.adjustment_value,
                "dscr_threshold": adj.dscr_threshold,
                "sort_order": adj.sort_order or i
            })
        
        db.commit()
        return {"message": f"Successfully created {len(adjustments)} DSCR adjustments"}
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


# SASB Premium (Property Type Premium)
@router.get("/sasb-premium", operation_id="list_sasb_premiums")
async def get_sasb_premiums(
    db: Session = Depends(get_db)
):
    """Get SASB loan size premiums."""
    
    query = "SELECT * FROM rpx_sasb_premium ORDER BY loan_size_threshold"
    
    result = db.execute(text(query)).mappings().all()
    return JSONResponse(content=jsonable_encoder([dict(row) for row in result]))


@router.post("/sasb-premium/bulk", operation_id="bulk_create_sasb_premiums")
async def bulk_create_sasb_premiums(
    premiums: List[SASBPremiumCreate],
    db: Session = Depends(get_db)
):
    """Bulk create or update SASB loan size premiums."""
    
    try:
        # Clear existing data first
        db.execute(text("DELETE FROM rpx_sasb_premium"))
        
        for premium in premiums:
            # Insert new record
            db.execute(text("""
                INSERT INTO rpx_sasb_premium 
                (loan_size_threshold, premium_rate)
                VALUES (:loan_size_threshold, :premium_rate)
            """), {
                "loan_size_threshold": premium.loan_size_threshold,
                "premium_rate": premium.premium_rate
            })
        
        db.commit()
        return {"message": f"Successfully processed {len(premiums)} SASB premiums"}
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


# Loan Status Adjustments
@router.get("/loan-status", operation_id="list_loan_status_adjustments")
async def get_loan_status_adjustments(
    loan_status: Optional[str] = Query(None, description="Filter by loan status"),
    db: Session = Depends(get_db)
):
    """Get loan status adjustments."""
    
    query = "SELECT * FROM rpx_loan_status_adjustment WHERE 1=1"
    params = {}
    
    if loan_status:
        query += " AND loan_status = :loan_status"
        params["loan_status"] = loan_status
    
    query += " ORDER BY loan_status"
    
    result = db.execute(text(query), params).mappings().all()
    return JSONResponse(content=jsonable_encoder([dict(row) for row in result]))


@router.post("/loan-status/bulk", operation_id="bulk_create_loan_status_adjustments")
async def bulk_create_loan_status_adjustments(
    adjustments: List[LoanStatusAdjustmentCreate],
    db: Session = Depends(get_db)
):
    """Bulk create or update loan status adjustments."""
    
    try:
        for adj in adjustments:
            # Check if exists
            existing = db.execute(text("""
                SELECT id FROM rpx_loan_status_adjustment 
                WHERE loan_status = :loan_status
            """), {"loan_status": adj.loan_status}).first()
            
            if existing:
                # Update
                db.execute(text("""
                    UPDATE rpx_loan_status_adjustment 
                    SET adjustment_bps = :adjustment_bps,
                        description = :description
                    WHERE id = :id
                """), {
                    "id": existing.id,
                    "adjustment_bps": adj.adjustment_bps,
                    "description": adj.description
                })
            else:
                # Insert
                db.execute(text("""
                    INSERT INTO rpx_loan_status_adjustment 
                    (loan_status, adjustment_bps, description)
                    VALUES (:loan_status, :adjustment_bps, :description)
                """), {
                    "loan_status": adj.loan_status,
                    "adjustment_bps": adj.adjustment_bps,
                    "description": adj.description
                })
        
        db.commit()
        return {"message": f"Successfully processed {len(adjustments)} loan status adjustments"}
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


# Generic endpoints for other RPX tables
@router.get("/{table_name}", operation_id="list_rpx_adjustments")
async def get_rpx_adjustments(
    table_name: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get adjustments from any RPX table."""
    
    # Validate table name
    allowed_tables = [
        "rpx_lifecycle_adjustment",
        "rpx_senior_loan_tiering",
        "rpx_mezzanine_factors",
        "rpx_mezzanine_ltv_tiering",
        "rpx_ltv_adjustment",
        "rpx_ltv_performance_adjustment",
        "rpx_tenor_adjustment",
        "rpx_amount_adjustment",
        "rpx_external_adjustment",
        "rpx_property_adjustment",
        "rpx_recovery_adjustment"
    ]
    
    if table_name not in allowed_tables:
        raise HTTPException(status_code=404, detail=f"Table {table_name} not found")
    
    # Check if table exists
    check_query = text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = :table_name
        )
    """)
    
    if not db.execute(check_query, {"table_name": table_name}).scalar():
        raise HTTPException(status_code=404, detail=f"Table {table_name} not found")
    
    # Get data
    query = f"SELECT * FROM {table_name} ORDER BY id LIMIT {limit} OFFSET {skip}"
    result = db.execute(text(query)).mappings().all()
    
    return JSONResponse(content=jsonable_encoder([dict(row) for row in result]))


@router.post("/{table_name}/bulk", operation_id="bulk_update_rpx_adjustments")
async def bulk_update_rpx_adjustments(
    table_name: str,
    adjustments: List[Dict[str, Any]],
    db: Session = Depends(get_db)
):
    """Bulk update adjustments in any RPX table."""
    
    # Validate table name
    allowed_tables = [
        "rpx_lifecycle_adjustment",
        "rpx_senior_loan_tiering",
        "rpx_mezzanine_factors",
        "rpx_mezzanine_ltv_tiering",
        "rpx_ltv_adjustment",
        "rpx_ltv_performance_adjustment",
        "rpx_tenor_adjustment",
        "rpx_amount_adjustment",
        "rpx_external_adjustment",
        "rpx_property_adjustment",
        "rpx_recovery_adjustment"
    ]
    
    if table_name not in allowed_tables:
        raise HTTPException(status_code=404, detail=f"Table {table_name} not found")
    
    try:
        # Clear existing data
        db.execute(text(f"DELETE FROM {table_name}"))
        
        # Insert new data
        for adj in adjustments:
            # Build dynamic insert query
            columns = list(adj.keys())
            values_placeholder = ", ".join([f":{col}" for col in columns])
            columns_str = ", ".join(columns)
            
            query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({values_placeholder})"
            db.execute(text(query), adj)
        
        db.commit()
        return {"message": f"Successfully updated {len(adjustments)} records in {table_name}"}
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))