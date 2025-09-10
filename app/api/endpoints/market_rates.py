"""
Market Rates API endpoints for managing benchmark rates.
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


class MarketRateBase(BaseModel):
    """Base schema for market rates."""
    benchmark_date: date = Field(..., description="Date of the benchmark rate")
    benchmark_type: str = Field(..., description="Type of benchmark (e.g., UST, SOFR, EURIBOR)")
    currency: str = Field("USD", description="Currency code")
    term_years: Decimal = Field(..., description="Term in years", ge=0)
    rate: Decimal = Field(..., description="Rate value", ge=0)
    source: Optional[str] = Field(None, description="Data source")


class MarketRateCreate(MarketRateBase):
    """Schema for creating market rates."""
    pass


class MarketRateUpdate(BaseModel):
    """Schema for updating market rates."""
    rate: Decimal = Field(..., description="Updated rate value", ge=0)
    source: Optional[str] = Field(None, description="Updated data source")


class MarketRateResponse(MarketRateBase):
    """Schema for market rate responses."""
    id: int
    created_at: Optional[str] = None


@router.get("/", operation_id="list_market_rates")
async def get_market_rates(
    benchmark_date: Optional[date] = Query(None, description="Filter by benchmark date"),
    benchmark_type: Optional[str] = Query(None, description="Filter by benchmark type"),
    currency: Optional[str] = Query("USD", description="Filter by currency"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get market rates with optional filters."""
    
    query = "SELECT * FROM market_benchmarks WHERE 1=1"
    params = {}
    
    if benchmark_date:
        query += " AND benchmark_date = :benchmark_date"
        params["benchmark_date"] = benchmark_date
    
    if benchmark_type:
        query += " AND benchmark_type = :benchmark_type"
        params["benchmark_type"] = benchmark_type
    
    if currency:
        query += " AND currency = :currency"
        params["currency"] = currency
    
    query += " ORDER BY benchmark_date DESC, benchmark_type, term_years"
    query += f" LIMIT {limit} OFFSET {skip}"
    
    result = db.execute(text(query), params).mappings().all()
    return JSONResponse(content=jsonable_encoder([dict(row) for row in result]))


@router.post("/bulk", operation_id="bulk_create_market_rates")
async def bulk_create_market_rates(
    rates: List[MarketRateCreate],
    db: Session = Depends(get_db)
):
    """Bulk create or update market rates."""
    
    try:
        # Use INSERT ... ON CONFLICT to handle updates
        for rate in rates:
            query = text("""
                INSERT INTO market_benchmarks 
                (benchmark_date, benchmark_type, term_years, rate, currency, source)
                VALUES (:benchmark_date, :benchmark_type, :term_years, :rate, :currency, :source)
                ON CONFLICT (benchmark_date, benchmark_type, term_years, currency)
                DO UPDATE SET 
                    rate = EXCLUDED.rate,
                    source = EXCLUDED.source,
                    created_at = CURRENT_TIMESTAMP
            """)
            
            db.execute(query, {
                "benchmark_date": rate.benchmark_date,
                "benchmark_type": rate.benchmark_type,
                "term_years": rate.term_years,
                "rate": rate.rate,
                "currency": rate.currency,
                "source": rate.source
            })
        
        db.commit()
        return {"message": f"Successfully processed {len(rates)} market rates"}
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{rate_id}", operation_id="update_market_rate")
async def update_market_rate(
    rate_id: int,
    rate_update: MarketRateUpdate,
    db: Session = Depends(get_db)
):
    """Update a specific market rate."""
    
    # Check if rate exists
    existing = db.execute(
        text("SELECT * FROM market_benchmarks WHERE id = :id"),
        {"id": rate_id}
    ).first()
    
    if not existing:
        raise HTTPException(status_code=404, detail="Market rate not found")
    
    # Update rate
    query = text("""
        UPDATE market_benchmarks 
        SET rate = :rate, source = :source
        WHERE id = :id
    """)
    
    db.execute(query, {
        "id": rate_id,
        "rate": rate_update.rate,
        "source": rate_update.source
    })
    db.commit()
    
    # Return updated rate
    updated = db.execute(
        text("SELECT * FROM market_benchmarks WHERE id = :id"),
        {"id": rate_id}
    ).mappings().first()
    
    return JSONResponse(content=jsonable_encoder(dict(updated)))


@router.get("/interpolate", operation_id="interpolate_market_rate")
async def interpolate_market_rate(
    benchmark_date: date = Query(..., description="Date for interpolation"),
    term_years: Decimal = Query(..., description="Term in years to interpolate"),
    benchmark_type: str = Query(..., description="Type of benchmark"),
    currency: str = Query("USD", description="Currency code"),
    db: Session = Depends(get_db)
):
    """Get interpolated market rate for a specific term."""
    
    # Get the closest rates above and below the requested term
    query = text("""
        WITH closest_rates AS (
            SELECT 
                term_years,
                rate,
                ABS(term_years - :term_years) as distance
            FROM market_benchmarks
            WHERE benchmark_date = :benchmark_date
                AND benchmark_type = :benchmark_type
                AND currency = :currency
            ORDER BY distance
            LIMIT 2
        )
        SELECT * FROM closest_rates
    """)
    
    rates = db.execute(query, {
        "benchmark_date": benchmark_date,
        "term_years": term_years,
        "benchmark_type": benchmark_type,
        "currency": currency
    }).mappings().all()
    
    if not rates:
        raise HTTPException(
            status_code=404, 
            detail=f"No rates found for {benchmark_type} on {benchmark_date}"
        )
    
    if len(rates) == 1:
        # Only one rate found, return it
        return {
            "interpolated_rate": float(rates[0]["rate"]),
            "term_years": float(term_years),
            "method": "exact_match"
        }
    
    # Linear interpolation between two closest rates
    r1, r2 = rates[0], rates[1]
    t1, t2 = float(r1["term_years"]), float(r2["term_years"])
    rate1, rate2 = float(r1["rate"]), float(r2["rate"])
    
    if t1 == t2:
        interpolated_rate = rate1
    else:
        # Linear interpolation formula
        interpolated_rate = rate1 + (rate2 - rate1) * (float(term_years) - t1) / (t2 - t1)
    
    return {
        "interpolated_rate": interpolated_rate,
        "term_years": float(term_years),
        "method": "linear_interpolation",
        "based_on": [
            {"term_years": t1, "rate": rate1},
            {"term_years": t2, "rate": rate2}
        ]
    }


@router.delete("/{rate_id}", operation_id="delete_market_rate")
async def delete_market_rate(
    rate_id: int,
    db: Session = Depends(get_db)
):
    """Delete a specific market rate."""
    
    # Check if rate exists
    existing = db.execute(
        text("SELECT * FROM market_benchmarks WHERE id = :id"),
        {"id": rate_id}
    ).first()
    
    if not existing:
        raise HTTPException(status_code=404, detail="Market rate not found")
    
    # Delete rate
    db.execute(text("DELETE FROM market_benchmarks WHERE id = :id"), {"id": rate_id})
    db.commit()
    
    return {"message": "Market rate deleted successfully"}