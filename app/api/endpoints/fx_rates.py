"""
FX Rates API endpoints for managing foreign exchange rates.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from datetime import date
from decimal import Decimal
from pydantic import BaseModel, Field

from app.database.session import get_db

router = APIRouter()


class FXRateBase(BaseModel):
    """Base schema for FX rates."""
    from_currency: str = Field(..., max_length=3, description="Source currency code")
    to_currency: str = Field(..., max_length=3, description="Target currency code")
    rate_date: date = Field(..., description="Date of the exchange rate")
    exchange_rate: Decimal = Field(..., gt=0, description="Exchange rate")
    rate_source: Optional[str] = Field(None, description="Source of the rate")


class FXRateCreate(FXRateBase):
    """Schema for creating FX rates."""
    pass


class FXRateUpdate(BaseModel):
    """Schema for updating FX rates."""
    exchange_rate: Decimal = Field(..., gt=0, description="Updated exchange rate")
    rate_source: Optional[str] = Field(None, description="Updated rate source")


class FXRateResponse(FXRateBase):
    """Schema for FX rate responses."""
    rate_id: int
    created_at: Optional[str] = None


@router.get("/", operation_id="list_fx_rates")
async def get_fx_rates(
    from_currency: Optional[str] = Query(None, description="Filter by source currency"),
    to_currency: Optional[str] = Query(None, description="Filter by target currency"),
    rate_date: Optional[date] = Query(None, description="Filter by rate date"),
    start_date: Optional[date] = Query(None, description="Filter by start date (inclusive)"),
    end_date: Optional[date] = Query(None, description="Filter by end date (inclusive)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get FX rates with optional filters."""
    
    query = "SELECT * FROM fx_rates WHERE 1=1"
    params = {}
    
    if from_currency:
        query += " AND from_currency = :from_currency"
        params["from_currency"] = from_currency
    
    if to_currency:
        query += " AND to_currency = :to_currency"
        params["to_currency"] = to_currency
    
    if rate_date:
        query += " AND rate_date = :rate_date"
        params["rate_date"] = rate_date
    elif start_date and end_date:
        query += " AND rate_date BETWEEN :start_date AND :end_date"
        params["start_date"] = start_date
        params["end_date"] = end_date
    elif start_date:
        query += " AND rate_date >= :start_date"
        params["start_date"] = start_date
    elif end_date:
        query += " AND rate_date <= :end_date"
        params["end_date"] = end_date
    
    query += " ORDER BY rate_date DESC, from_currency, to_currency"
    query += f" LIMIT {limit} OFFSET {skip}"
    
    result = db.execute(text(query), params).mappings().all()
    return JSONResponse(content=jsonable_encoder([dict(row) for row in result]))


@router.get("/latest", operation_id="get_latest_fx_rates")
async def get_latest_fx_rates(
    from_currency: Optional[str] = Query(None, description="Filter by source currency"),
    to_currency: Optional[str] = Query(None, description="Filter by target currency"),
    db: Session = Depends(get_db)
):
    """Get the latest FX rates for each currency pair."""
    
    query = text("""
        WITH latest_rates AS (
            SELECT 
                from_currency,
                to_currency,
                MAX(rate_date) as max_date
            FROM fx_rates
            WHERE 1=1
                AND (:from_currency IS NULL OR from_currency = :from_currency)
                AND (:to_currency IS NULL OR to_currency = :to_currency)
            GROUP BY from_currency, to_currency
        )
        SELECT 
            fr.rate_id,
            fr.from_currency,
            fr.to_currency,
            fr.rate_date,
            fr.exchange_rate,
            fr.rate_source,
            fr.created_at
        FROM fx_rates fr
        INNER JOIN latest_rates lr
            ON fr.from_currency = lr.from_currency
            AND fr.to_currency = lr.to_currency
            AND fr.rate_date = lr.max_date
        ORDER BY fr.from_currency, fr.to_currency
    """)
    
    result = db.execute(query, {
        "from_currency": from_currency,
        "to_currency": to_currency
    }).mappings().all()
    
    return JSONResponse(content=jsonable_encoder([dict(row) for row in result]))


@router.post("/bulk", operation_id="bulk_create_fx_rates")
async def bulk_create_fx_rates(
    rates: List[FXRateCreate],
    db: Session = Depends(get_db)
):
    """Bulk create or update FX rates."""
    
    try:
        created_count = 0
        updated_count = 0
        
        for rate in rates:
            # Check if rate exists
            check_query = text("""
                SELECT rate_id FROM fx_rates 
                WHERE from_currency = :from_currency 
                AND to_currency = :to_currency 
                AND rate_date = :rate_date
            """)
            
            existing = db.execute(check_query, {
                "from_currency": rate.from_currency,
                "to_currency": rate.to_currency,
                "rate_date": rate.rate_date
            }).first()
            
            if existing:
                # Update existing rate
                update_query = text("""
                    UPDATE fx_rates 
                    SET exchange_rate = :exchange_rate,
                        rate_source = :rate_source
                    WHERE rate_id = :rate_id
                """)
                db.execute(update_query, {
                    "rate_id": existing.rate_id,
                    "exchange_rate": rate.exchange_rate,
                    "rate_source": rate.rate_source
                })
                updated_count += 1
            else:
                # Get next rate_id
                max_id_result = db.execute(text("SELECT COALESCE(MAX(rate_id), 0) + 1 as next_id FROM fx_rates")).first()
                next_id = max_id_result.next_id
                
                # Insert new rate
                insert_query = text("""
                    INSERT INTO fx_rates 
                    (rate_id, from_currency, to_currency, rate_date, exchange_rate, rate_source)
                    VALUES (:rate_id, :from_currency, :to_currency, :rate_date, :exchange_rate, :rate_source)
                """)
                db.execute(insert_query, {
                    "rate_id": next_id,
                    "from_currency": rate.from_currency,
                    "to_currency": rate.to_currency,
                    "rate_date": rate.rate_date,
                    "exchange_rate": rate.exchange_rate,
                    "rate_source": rate.rate_source
                })
                created_count += 1
        
        db.commit()
        return {
            "message": f"Successfully processed {len(rates)} FX rates",
            "created": created_count,
            "updated": updated_count
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/convert", operation_id="convert_currency")
async def convert_currency(
    amount: Decimal = Query(..., description="Amount to convert"),
    from_currency: str = Query(..., description="Source currency"),
    to_currency: str = Query(..., description="Target currency"),
    rate_date: Optional[date] = Query(None, description="Date for conversion rate (uses latest if not specified)"),
    db: Session = Depends(get_db)
):
    """Convert an amount from one currency to another."""
    
    if from_currency == to_currency:
        return {
            "amount": float(amount),
            "from_currency": from_currency,
            "to_currency": to_currency,
            "converted_amount": float(amount),
            "exchange_rate": 1.0,
            "rate_date": rate_date or date.today()
        }
    
    # Get the exchange rate
    if rate_date:
        query = text("""
            SELECT exchange_rate, rate_date 
            FROM fx_rates 
            WHERE from_currency = :from_currency 
            AND to_currency = :to_currency 
            AND rate_date = :rate_date
            ORDER BY rate_date DESC
            LIMIT 1
        """)
        params = {
            "from_currency": from_currency,
            "to_currency": to_currency,
            "rate_date": rate_date
        }
    else:
        # Get latest rate
        query = text("""
            SELECT exchange_rate, rate_date 
            FROM fx_rates 
            WHERE from_currency = :from_currency 
            AND to_currency = :to_currency 
            ORDER BY rate_date DESC
            LIMIT 1
        """)
        params = {
            "from_currency": from_currency,
            "to_currency": to_currency
        }
    
    result = db.execute(query, params).first()
    
    if not result:
        # Try reverse rate
        if rate_date:
            reverse_query = text("""
                SELECT exchange_rate, rate_date 
                FROM fx_rates 
                WHERE from_currency = :to_currency 
                AND to_currency = :from_currency 
                AND rate_date = :rate_date
                ORDER BY rate_date DESC
                LIMIT 1
            """)
            params["rate_date"] = rate_date
        else:
            reverse_query = text("""
                SELECT exchange_rate, rate_date 
                FROM fx_rates 
                WHERE from_currency = :to_currency 
                AND to_currency = :from_currency 
                ORDER BY rate_date DESC
                LIMIT 1
            """)
        
        reverse_result = db.execute(reverse_query, {
            "from_currency": from_currency,
            "to_currency": to_currency
        }).first()
        
        if reverse_result:
            exchange_rate = 1 / reverse_result.exchange_rate
            rate_date_used = reverse_result.rate_date
        else:
            raise HTTPException(
                status_code=404, 
                detail=f"No exchange rate found for {from_currency} to {to_currency}"
            )
    else:
        exchange_rate = result.exchange_rate
        rate_date_used = result.rate_date
    
    converted_amount = amount * exchange_rate
    
    return {
        "amount": float(amount),
        "from_currency": from_currency,
        "to_currency": to_currency,
        "converted_amount": float(converted_amount),
        "exchange_rate": float(exchange_rate),
        "rate_date": rate_date_used
    }


@router.delete("/{rate_id}", operation_id="delete_fx_rate")
async def delete_fx_rate(
    rate_id: int,
    db: Session = Depends(get_db)
):
    """Delete a specific FX rate."""
    
    # Check if rate exists
    existing = db.execute(
        text("SELECT rate_id FROM fx_rates WHERE rate_id = :rate_id"),
        {"rate_id": rate_id}
    ).first()
    
    if not existing:
        raise HTTPException(status_code=404, detail="FX rate not found")
    
    # Delete rate
    db.execute(text("DELETE FROM fx_rates WHERE rate_id = :rate_id"), {"rate_id": rate_id})
    db.commit()
    
    return {"message": "FX rate deleted successfully"}