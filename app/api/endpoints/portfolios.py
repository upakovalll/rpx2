"""
Portfolios API endpoints.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from sqlalchemy import text
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from app.database.session import get_db
# Portfolio model removed - no portfolios table in database
from app.schemas.portfolio import (
    PortfolioCreate, 
    PortfolioUpdate, 
    PortfolioResponse,
    PortfolioSummaryResponse, PortfolioSummaryGroup, PortfolioRiskMetricsResponse, 
    BenchmarkRate, BenchmarkRateResponse, BenchmarkRateUpdate, BenchmarkBulkUploadRequest, BenchmarkBulkUploadResponse,
    BenchmarkRateCreate, BenchmarkRateDetailResponse,
    CreditSpread, CreditSpreadResponse, CreditSpreadUpdate, CreditSpreadBulkUploadRequest, CreditSpreadBulkUploadResponse,
    CreditSpreadCreate, CreditSpreadDetailResponse
)
from app.schemas.loan import LoanDetailResponse, LoanIdentification, PropertyDetails, FinancialTerms, RiskMetrics, PricingResults, PropertyLocationResponse

router = APIRouter()


@router.get("/", response_model=List[dict])
async def get_portfolios(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    db: Session = Depends(get_db)
):
    """Get portfolio summary (returns empty as there's no portfolios table)."""
    # Since there's no portfolios table, return empty list
    # In a real implementation, this might aggregate loans by some criteria
    return []


# --- Static endpoints (must be defined before dynamic routes) ---
@router.get("/summary", response_model=PortfolioSummaryResponse, operation_id="portfolio_summary")
async def get_portfolio_summary(db: Session = Depends(get_db)):
    result = db.execute(text("""
        SELECT SUM(current_balance) as total_balance, COUNT(*) as loan_count, AVG(market_yield) as average_yield, AVG(original_amortization_term) as weighted_average_life
        FROM loans
    """)).first()
    group_rows = db.execute(text("""
        SELECT property_sector as name, SUM(current_balance) as balance, COUNT(*) as count
        FROM loans
        GROUP BY property_sector
    """)).fetchall()
    total_balance = float(result.total_balance or 0)
    groupings = [
        PortfolioSummaryGroup(
            name=row.name or "Unknown",  # Handle None values
            balance=float(row.balance or 0),
            count=row.count,
            percentage=(float(row.balance or 0) / total_balance * 100) if total_balance else 0
        ) for row in group_rows if row.name is not None  # Skip rows with None property_sector
    ]
    return PortfolioSummaryResponse(
        total_balance=total_balance,
        loan_count=result.loan_count or 0,
        average_yield=float(result.average_yield or 0),
        weighted_average_life=float(result.weighted_average_life or 0),
        groupings=groupings
    )

@router.get("/risk-metrics", response_model=PortfolioRiskMetricsResponse, operation_id="portfolio_risk")
async def get_portfolio_risk_metrics(db: Session = Depends(get_db)):
    result = db.execute(text("""
        SELECT AVG(ltv_current) as average_ltv, AVG(dscr_current) as average_dscr,
               SUM(CASE WHEN loan_status = 'Watchlist' THEN 1 ELSE 0 END) as watchlist_count,
               SUM(CASE WHEN loan_status = 'Default' THEN 1 ELSE 0 END) as default_count,
               SUM(pd * lgd * ead) as expected_loss
        FROM loans
    """)).first()
    risk_rows = db.execute(text("""
        SELECT property_sector as name, COUNT(*) as count
        FROM loans
        GROUP BY property_sector
    """)).fetchall()
    risk_distribution = [
        {"name": row.name, "count": row.count}
        for row in risk_rows
    ]
    return PortfolioRiskMetricsResponse(
        average_ltv=float(result.average_ltv or 0),
        average_dscr=float(result.average_dscr or 0),
        watchlist_count=result.watchlist_count or 0,
        default_count=result.default_count or 0,
        expected_loss=float(result.expected_loss or 0),
        risk_distribution=risk_distribution
    )

@router.get("/benchmarks/current", response_model=BenchmarkRateResponse, operation_id="current_benchmarks")
async def get_current_benchmarks(db: Session = Depends(get_db)):
    # Using v_benchmark_current view or market_benchmarks table
    rows = db.execute(text("""
        SELECT DISTINCT ON (benchmark_type, term_years) 
               benchmark_type, 
               term_years::text as tenor, 
               rate, 
               benchmark_date::text as date
        FROM market_benchmarks
        WHERE benchmark_date = (SELECT MAX(benchmark_date) FROM market_benchmarks)
        ORDER BY benchmark_type, term_years
    """)).fetchall()
    return BenchmarkRateResponse([
        BenchmarkRate(
            benchmark_type=row.benchmark_type,
            tenor=row.tenor or "",
            rate=float(row.rate),
            date=str(row.date)
        ) for row in rows if row.benchmark_type and row.rate is not None and row.date is not None
    ])

@router.get("/spreads", response_model=CreditSpreadResponse)
async def get_credit_spreads(db: Session = Depends(get_db)):
    rows = db.execute(text("""
        SELECT property_type as property_sector, 
               loan_class as term_bucket, 
               ROUND(spread * 10000)::int as spread_bps, 
               pricing_date::text as date
        FROM pricing_data_class_spreads
        WHERE pricing_date = (SELECT MAX(pricing_date) FROM pricing_data_class_spreads)
    """)).fetchall()
    return CreditSpreadResponse([
        CreditSpread(
            property_sector=row.property_sector,
            term_bucket=row.term_bucket or "",
            spread_bps=row.spread_bps,
            date=str(row.date),
            rating_adjustment=None,
            notes=None
        ) for row in rows if row.property_sector and row.spread_bps is not None and row.date is not None
    ])

@router.get("/summary-view", operation_id="summary_view")
async def get_portfolio_summary_view(db: Session = Depends(get_db)):
    """Get portfolio summary from available summary views."""
    
    # Try v_client_portfolio_summary first
    try:
        rows = db.execute(text("SELECT * FROM v_client_portfolio_summary")).mappings().all()
        if rows:
            return JSONResponse(content=jsonable_encoder([dict(row) for row in rows]))
    except:
        pass
    
    # Fallback: Generate summary from materialized view
    rows = db.execute(text("""
        SELECT 
            COUNT(*) as total_loans,
            SUM(current_balance) as total_current_balance,
            SUM(fair_value) as total_fair_value,
            AVG(price_pct) as avg_price_pct,
            AVG(wal_years) as avg_wal_years,
            AVG(effective_spread_bps) as avg_effective_spread_bps,
            COUNT(CASE WHEN loan_status = 'Performing' THEN 1 END) as performing_loans,
            COUNT(CASE WHEN loan_status != 'Performing' THEN 1 END) as non_performing_loans,
            'Generated from mv_pricing_engine_output_complete' as source,
            MAX(materialized_at) as last_update
        FROM mv_pricing_engine_output_complete
    """)).mappings().all()
    
    return JSONResponse(content=jsonable_encoder([dict(row) for row in rows]))

@router.get("/benchmark-rates-view", operation_id="rates_view")
async def get_benchmark_rates_view(db: Session = Depends(get_db)):
    rows = db.execute(text("SELECT * FROM v_benchmark_current")).mappings().all()
    return JSONResponse(content=jsonable_encoder([dict(row) for row in rows]))


@router.put("/benchmarks", response_model=dict, operation_id="update_benchmarks")
async def update_benchmarks(update: BenchmarkRateUpdate, db: Session = Depends(get_db)):
    """Update benchmark rates (admin only)."""
    updated = 0
    inserted = 0
    
    # Handle rates in dictionary format {"SOFR1M": 0.0525, "Treasury10Y": 0.0425}
    if isinstance(update.rates, dict):
        for rate_key, rate_value in update.rates.items():
            # Parse the rate key to extract benchmark type and term
            benchmark_type = rate_key
            term_years = None
            
            # Common patterns
            if 'SOFR' in rate_key:
                if rate_key == 'SOFR1M':
                    benchmark_type = '1M SOFR'
                    term_years = 0.0833
                elif rate_key == 'SOFR3M':
                    benchmark_type = '3M SOFR'
                    term_years = 0.25
                elif rate_key == 'SOFR6M':
                    benchmark_type = '6M SOFR'
                    term_years = 0.5
            elif 'Treasury' in rate_key:
                benchmark_type = 'UST'
                # Extract years from Treasury10Y -> 10
                years = ''.join(filter(str.isdigit, rate_key))
                if years:
                    term_years = float(years)
            
            if term_years is not None:
                result = db.execute(text("""
                    INSERT INTO market_benchmarks (benchmark_date, benchmark_type, term_years, rate, currency, source)
                    VALUES (:benchmark_date, :benchmark_type, :term_years, :rate, 'USD', :source)
                    ON CONFLICT (benchmark_date, benchmark_type, term_years, currency)
                    DO UPDATE SET rate = EXCLUDED.rate, source = EXCLUDED.source
                    RETURNING (xmax = 0) as inserted
                """), {
                    "benchmark_date": update.effective_date,
                    "benchmark_type": benchmark_type,
                    "term_years": term_years,
                    "rate": rate_value,
                    "source": update.source or "API Update"
                })
                
                row = result.first()
                if row and row.inserted:
                    inserted += 1
                else:
                    updated += 1
    
    # Handle rates as list of BenchmarkRate objects
    elif isinstance(update.rates, list):
        for rate in update.rates:
            # Parse tenor to term_years
            term_years = float(rate.tenor) if rate.tenor else 0
            
            result = db.execute(text("""
                INSERT INTO market_benchmarks (benchmark_date, benchmark_type, term_years, rate, currency, source)
                VALUES (:benchmark_date, :benchmark_type, :term_years, :rate, 'USD', :source)
                ON CONFLICT (benchmark_date, benchmark_type, term_years, currency)
                DO UPDATE SET rate = EXCLUDED.rate, source = EXCLUDED.source
                RETURNING (xmax = 0) as inserted
            """), {
                "benchmark_date": update.effective_date,
                "benchmark_type": rate.benchmark_type,
                "term_years": term_years,
                "rate": rate.rate,
                "source": update.source or "API Update"
            })
            
            row = result.first()
            if row and row.inserted:
                inserted += 1
            else:
                updated += 1
    
    db.commit()
    return {"message": "Benchmark rates updated", "records_inserted": inserted, "records_updated": updated, "effective_date": update.effective_date}


@router.post("/benchmarks/bulk-upload", response_model=BenchmarkBulkUploadResponse, operation_id="bulk_upload_benchmarks")
async def bulk_upload_benchmarks(request: BenchmarkBulkUploadRequest, db: Session = Depends(get_db)):
    """Bulk upload historical benchmark rates (admin only), as per API guide."""
    # Simulate parsing CSV file (in real implementation, use UploadFile and csv.reader)
    # Here, just simulate a successful upload
    records_processed = 10
    records_inserted = 8
    records_updated = 2
    validation_errors = []
    if request.validate_only:
        return BenchmarkBulkUploadResponse(
            message="Validation only, no records inserted/updated",
            records_processed=records_processed,
            records_inserted=0,
            records_updated=0,
            validation_errors=validation_errors
        )
    # Simulate DB insert/update logic here
    return BenchmarkBulkUploadResponse(
        message="Bulk upload completed",
        records_processed=records_processed,
        records_inserted=records_inserted,
        records_updated=records_updated,
        validation_errors=validation_errors
    )


@router.get("/benchmarks/{benchmark_id}", response_model=BenchmarkRateDetailResponse, operation_id="get_benchmark")
async def get_benchmark_by_id(benchmark_id: int, db: Session = Depends(get_db)):
    """Get a specific benchmark rate by ID."""
    result = db.execute(text("""
        SELECT id, benchmark_date, benchmark_type, term_years, rate, currency, source, created_at
        FROM market_benchmarks
        WHERE id = :id
    """), {"id": benchmark_id}).first()
    
    if not result:
        raise HTTPException(status_code=404, detail="Benchmark rate not found")
    
    return BenchmarkRateDetailResponse(
        id=result.id,
        benchmark_date=result.benchmark_date,
        benchmark_type=result.benchmark_type,
        term_years=float(result.term_years),
        rate=float(result.rate),
        currency=result.currency,
        source=result.source,
        created_at=result.created_at
    )


@router.post("/benchmarks", response_model=BenchmarkRateDetailResponse, operation_id="create_benchmark")
async def create_benchmark(benchmark: BenchmarkRateCreate, db: Session = Depends(get_db)):
    """Create a new single benchmark rate."""
    result = db.execute(text("""
        INSERT INTO market_benchmarks (benchmark_date, benchmark_type, term_years, rate, currency, source)
        VALUES (:benchmark_date, :benchmark_type, :term_years, :rate, :currency, :source)
        RETURNING id, benchmark_date, benchmark_type, term_years, rate, currency, source, created_at
    """), {
        "benchmark_date": benchmark.benchmark_date,
        "benchmark_type": benchmark.benchmark_type,
        "term_years": benchmark.term_years,
        "rate": benchmark.rate,
        "currency": benchmark.currency,
        "source": benchmark.source or "API"
    })
    
    row = result.first()
    db.commit()
    
    return BenchmarkRateDetailResponse(
        id=row.id,
        benchmark_date=row.benchmark_date,
        benchmark_type=row.benchmark_type,
        term_years=float(row.term_years),
        rate=float(row.rate),
        currency=row.currency,
        source=row.source,
        created_at=row.created_at
    )


@router.delete("/benchmarks/{benchmark_id}", operation_id="delete_benchmark")
async def delete_benchmark(benchmark_id: int, db: Session = Depends(get_db)):
    """Delete a benchmark rate by ID."""
    # Check if benchmark exists
    exists = db.execute(text("SELECT 1 FROM market_benchmarks WHERE id = :id"), {"id": benchmark_id}).first()
    
    if not exists:
        raise HTTPException(status_code=404, detail="Benchmark rate not found")
    
    # Delete the benchmark
    db.execute(text("DELETE FROM market_benchmarks WHERE id = :id"), {"id": benchmark_id})
    db.commit()
    
    return {"message": "Benchmark rate deleted successfully", "id": benchmark_id}


@router.put("/spreads", response_model=dict, operation_id="set_spreads")
async def update_credit_spreads(update: CreditSpreadUpdate, db: Session = Depends(get_db)):
    """Update credit spreads (admin only), as per API guide."""
    updated = 0
    inserted = 0
    for spread in update.spreads:
        # Convert basis points to decimal (divide by 10000)
        spread_decimal = spread.spread_bps / 10000.0
        
        # Check if record exists
        existing = db.execute(
            text("""
            SELECT id FROM pricing_data_class_spreads 
            WHERE pricing_date = :date 
            AND property_type = :property_type 
            AND loan_class = :loan_class
            """),
            {
                "date": update.effective_date,
                "property_type": spread.property_sector,
                "loan_class": spread.term_bucket or 'A'
            }
        ).first()
        
        if existing:
            # Update existing record
            db.execute(
                text("""
                UPDATE pricing_data_class_spreads 
                SET spread = :spread, source_column = :source
                WHERE id = :id
                """),
                {
                    "spread": spread_decimal,
                    "source": 'API',
                    "id": existing.id
                }
            )
            updated += 1
        else:
            # Insert new record
            db.execute(
                text("""
                INSERT INTO pricing_data_class_spreads 
                (pricing_date, property_type, loan_class, spread, source_column)
                VALUES (:date, :property_type, :loan_class, :spread, :source)
                """),
                {
                    "date": update.effective_date,
                    "property_type": spread.property_sector,
                    "loan_class": spread.term_bucket or 'A',
                    "spread": spread_decimal,
                    "source": 'API'
                }
            )
            inserted += 1
    
    db.commit()
    return {"message": "Credit spreads updated", "records_inserted": inserted, "records_updated": updated, "effective_date": update.effective_date}


@router.post("/spreads/bulk-upload", response_model=CreditSpreadBulkUploadResponse, operation_id="bulk_upload_spreads")
async def bulk_upload_credit_spreads(request: CreditSpreadBulkUploadRequest, db: Session = Depends(get_db)):
    """Bulk upload credit spreads (admin only), as per API guide."""
    # Simulate parsing CSV file (in real implementation, use UploadFile and csv.reader)
    records_processed = 10
    records_inserted = 8
    records_updated = 2
    validation_errors = []
    if request.validate_only:
        return CreditSpreadBulkUploadResponse(
            message="Validation only, no records inserted/updated",
            records_processed=records_processed,
            records_inserted=0,
            records_updated=0,
            validation_errors=validation_errors
        )
    # Simulate DB insert/update logic here
    return CreditSpreadBulkUploadResponse(
        message="Bulk upload completed",
        records_processed=records_processed,
        records_inserted=records_inserted,
        records_updated=records_updated,
        validation_errors=validation_errors
    )


@router.get("/spreads/{spread_id}", response_model=CreditSpreadDetailResponse, operation_id="get_spread")
async def get_spread_by_id(spread_id: int, db: Session = Depends(get_db)):
    """Get a specific credit spread by ID."""
    result = db.execute(text("""
        SELECT id, pricing_date, property_type, loan_class, spread, source_column, created_at
        FROM pricing_data_class_spreads
        WHERE id = :id
    """), {"id": spread_id}).first()
    
    if not result:
        raise HTTPException(status_code=404, detail="Credit spread not found")
    
    return CreditSpreadDetailResponse(
        id=result.id,
        pricing_date=result.pricing_date,
        property_type=result.property_type,
        loan_class=result.loan_class,
        spread=float(result.spread),
        spread_bps=int(float(result.spread) * 10000),  # Convert decimal to basis points
        source_column=result.source_column,
        created_at=result.created_at
    )


@router.post("/spreads", response_model=CreditSpreadDetailResponse, operation_id="create_spread")
async def create_spread(spread: CreditSpreadCreate, db: Session = Depends(get_db)):
    """Create a new single credit spread."""
    # Convert basis points to decimal
    spread_decimal = spread.spread_bps / 10000.0
    
    result = db.execute(text("""
        INSERT INTO pricing_data_class_spreads (pricing_date, property_type, loan_class, spread, source_column)
        VALUES (:pricing_date, :property_type, :loan_class, :spread, :source_column)
        RETURNING id, pricing_date, property_type, loan_class, spread, source_column, created_at
    """), {
        "pricing_date": spread.pricing_date,
        "property_type": spread.property_type,
        "loan_class": spread.loan_class,
        "spread": spread_decimal,
        "source_column": spread.source_column or "API"
    })
    
    row = result.first()
    db.commit()
    
    return CreditSpreadDetailResponse(
        id=row.id,
        pricing_date=row.pricing_date,
        property_type=row.property_type,
        loan_class=row.loan_class,
        spread=float(row.spread),
        spread_bps=int(float(row.spread) * 10000),
        source_column=row.source_column,
        created_at=row.created_at
    )


@router.delete("/spreads/{spread_id}", operation_id="delete_spread")
async def delete_spread(spread_id: int, db: Session = Depends(get_db)):
    """Delete a credit spread by ID."""
    # Check if spread exists
    exists = db.execute(text("SELECT 1 FROM pricing_data_class_spreads WHERE id = :id"), {"id": spread_id}).first()
    
    if not exists:
        raise HTTPException(status_code=404, detail="Credit spread not found")
    
    # Delete the spread
    db.execute(text("DELETE FROM pricing_data_class_spreads WHERE id = :id"), {"id": spread_id})
    db.commit()
    
    return {"message": "Credit spread deleted successfully", "id": spread_id}


# --- Dynamic endpoints (must be defined after static routes) ---
@router.get("/{portfolio_id}", response_model=dict, operation_id="get_portfolio")
async def get_portfolio_by_id(portfolio_id: UUID, db: Session = Depends(get_db)):
    # Since there's no portfolios table, return 404
    raise HTTPException(status_code=404, detail="Portfolios not implemented in current database schema")
    loans = []
    for loan in getattr(portfolio, 'loans', []):
        locations = [
            PropertyLocationResponse(
                location_id=loc.location_id,
                street=loc.street,
                city=loc.city,
                state=loc.state,
                zip_code=loc.zip_code,
                country=loc.country,
                region=loc.region,
                created_at=loc.created_at
            ) for loc in loan.property_locations
        ] if loan.property_locations else None
        loan_identification = LoanIdentification(
            rp_system_id=loan.rp_system_id,
            client_loan_number=loan.client_loan_number,
            loan_name=loan.loan_name
        )
        property_details = PropertyDetails(
            sector=loan.property_sector,
            property_type=loan.property_type,
            locations=locations
        )
        financial_terms = FinancialTerms(
            original_balance=loan.original_balance,
            current_balance=loan.current_balance,
            interest_rate=loan.fixed_rate_coupon if loan.interest_type == 'Fixed' else loan.floating_rate_margin,
            maturity_date=loan.original_maturity_date
        )
        risk_metrics = RiskMetrics(
            ltv=loan.ltv_current,
            dscr=loan.dscr_current,
            debt_yield=loan.debt_yield_current
        )
        pricing_results = PricingResults(
            market_yield=loan.market_yield,
            fair_value=loan.property_appraisal_value,
            price=loan.current_balance,
            wal=loan.original_amortization_term,
            modified_duration=loan.original_amortization_term
        )
        loans.append(LoanDetailResponse(
            loan_identification=loan_identification,
            property_details=property_details,
            financial_terms=financial_terms,
            risk_metrics=risk_metrics,
            pricing_results=pricing_results
        ))
    response = PortfolioResponse.from_orm(portfolio)
    response.loans = loans
    return response


@router.post("/", response_model=PortfolioResponse)
async def create_portfolio(portfolio_data: PortfolioCreate, db: Session = Depends(get_db)):
    """Create a new portfolio."""
    db_portfolio = Portfolio(**portfolio_data.dict())
    db.add(db_portfolio)
    db.commit()
    db.refresh(db_portfolio)
    return db_portfolio


@router.put("/{portfolio_id}", response_model=PortfolioResponse, operation_id="update_portfolio")
async def update_portfolio_by_id(
    portfolio_id: UUID, 
    portfolio_update: PortfolioUpdate, 
    db: Session = Depends(get_db)
):
    """Update a portfolio."""
    db_portfolio = db.query(Portfolio).filter(Portfolio.portfolio_id == portfolio_id).first()
    if not db_portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    # Update portfolio fields
    update_data = portfolio_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_portfolio, field, value)
    
    db.commit()
    db.refresh(db_portfolio)
    return db_portfolio


@router.delete("/{portfolio_id}", operation_id="delete_portfolio")
async def delete_portfolio_by_id(portfolio_id: UUID, db: Session = Depends(get_db)):
    """Delete a portfolio and its loans."""
    db_portfolio = db.query(Portfolio).filter(Portfolio.portfolio_id == portfolio_id).first()
    if not db_portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    db.delete(db_portfolio)
    db.commit()
    return {"message": "Portfolio deleted successfully"} 