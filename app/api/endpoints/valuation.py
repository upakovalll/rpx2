"""
Valuation API endpoints for loan pricing output.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Any, Optional
from app.database.session import get_db
from sqlalchemy import text
from datetime import date
from app.schemas.loan import PricingEngineOutput, PricingEngineLoanDetail, PortfolioAnalysis
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from app.utils.pricing_transformer import PricingTransformer
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/pricing-output")
def get_pricing_output(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    property_type: Optional[str] = Query(None, description="Filter by property type"),
    loan_status: Optional[str] = Query(None, description="Filter by loan status"),
    db: Session = Depends(get_db)
):
    """Return ALL fields from mv_pricing_engine_output_complete materialized view (Excel-exact calculations)."""
    
    # Build query returning ALL fields from materialized view
    query = """
        SELECT * FROM mv_pricing_engine_output_complete_v4_layered
        WHERE 1=1
    """
    
    params = {}
    if property_type:
        query += " AND property_type = :property_type"
        params["property_type"] = property_type
    
    if loan_status:
        query += " AND loan_status = :loan_status" 
        params["loan_status"] = loan_status
    
    query += f" ORDER BY current_balance DESC LIMIT {limit} OFFSET {skip}"
    
    rows = db.execute(text(query), params).mappings().all()
    return JSONResponse(content=jsonable_encoder([dict(row) for row in rows]))

@router.get("/loan-rpx-adjustments", operation_id="loan_rpx_adjustments") 
def get_loan_rpx_adjustments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get loan RPX adjustments from materialized view (much faster)."""
    rows = db.execute(text(f"""
        SELECT * FROM mv_loan_rpx_adjustments 
        ORDER BY loan_id
        LIMIT {limit} OFFSET {skip}
    """)).mappings().all()
    return JSONResponse(content=jsonable_encoder([dict(row) for row in rows]))





@router.get("/loan-summary", operation_id="loan_summary")
def get_loan_summary(db: Session = Depends(get_db)):
    """Get loan summary from v_loan_summary view."""
    rows = db.execute(text("SELECT * FROM v_loan_summary")).mappings().all()
    return JSONResponse(content=jsonable_encoder([dict(row) for row in rows]))

@router.get("/loan-benchmark", operation_id="loan_benchmark")
def get_loan_benchmark(db: Session = Depends(get_db)):
    """Get loan benchmark data from available benchmark views."""
    
    # Try v_loan_benchmark_with_xirr first
    try:
        rows = db.execute(text("SELECT * FROM v_loan_benchmark_with_xirr")).mappings().all()
        if rows:
            return JSONResponse(content=jsonable_encoder([dict(row) for row in rows]))
    except:
        pass
    
    # Extract comprehensive benchmark and pricing data from materialized view
    rows = db.execute(text("""
        SELECT 
            loan_id,
            loan_name,
            current_balance,
            benchmark_type,
            benchmark_yield,
            component_yield_pct as market_yield,
            component_yield_decimal as market_yield_decimal,
            rpx_total_spread_bps as total_spread_bps,
            rpx_base_spread_bps as base_spread_bps,
            coupon,
            fair_value_clean,
            fair_value_dirty,
            price_clean_pct,
            price_dirty_pct,
            wal_years,
            modified_duration_years,
            convexity,
            npv_methodology as calculation_method,
            valuation_date,
            settlement_date,
            last_updated
        FROM mv_pricing_engine_output_complete_v4_layered
        ORDER BY current_balance DESC
    """)).mappings().all()
    
    return JSONResponse(content=jsonable_encoder([dict(row) for row in rows]))

@router.get("/loan-wal", operation_id="loan_wal")
def get_loan_wal(db: Session = Depends(get_db)):
    """Get loan weighted average life from materialized view."""
    
    # Extract comprehensive WAL and duration analytics from materialized view
    rows = db.execute(text("""
        SELECT 
            loan_id,
            loan_name,
            current_balance,
            original_balance,
            wal_years,
            macaulay_duration_years,
            modified_duration_years,
            convexity,
            effective_maturity_date,
            original_maturity_date,
            origination_date,
            periodicity,
            amortization_type,
            interest_type,
            total_periods,
            final_period,
            first_amort_period,
            io_end_date,
            fair_value_clean,
            price_clean_pct,
            component_yield_decimal as yield_to_maturity,
            npv_methodology as calculation_method,
            last_updated
        FROM mv_pricing_engine_output_complete_v4_layered
        WHERE wal_years IS NOT NULL
        ORDER BY wal_years DESC
    """)).mappings().all()
    
    return JSONResponse(content=jsonable_encoder([dict(row) for row in rows]))

@router.get("/loans-in-forbearance", operation_id="loans_forbearance")
def get_loans_in_forbearance(db: Session = Depends(get_db)):
    """Get loans in forbearance from v_loans_in_forbearance view."""
    rows = db.execute(text("SELECT * FROM v_loans_in_forbearance")).mappings().all()
    return JSONResponse(content=jsonable_encoder([dict(row) for row in rows]))

@router.get("/loan-accrued", operation_id="loan_accrued")
def get_loan_accrued(db: Session = Depends(get_db)):
    """Get comprehensive accrued interest and valuation data from materialized view."""
    rows = db.execute(text("""
        SELECT 
            loan_id,
            loan_name,
            current_balance,
            accrued_interest,
            fair_value_clean,
            fair_value_dirty,
            price_clean_pct,
            price_dirty_pct,
            price_accrued_pct,
            gross_proceeds,
            net_proceeds,
            npv_value,
            coupon,
            periodicity,
            valuation_date,
            settlement_date,
            last_updated
        FROM mv_pricing_engine_output_complete_v4_layered
        WHERE accrued_interest IS NOT NULL
        ORDER BY accrued_interest DESC
    """)).mappings().all()
    
    return JSONResponse(content=jsonable_encoder([dict(row) for row in rows]))

@router.get("/portfolio-summary", operation_id="valuation_portfolio_summary")
def get_portfolio_summary(db: Session = Depends(get_db)):
    """Get comprehensive portfolio summary from materialized view (Excel-exact calculations)."""
    
    rows = db.execute(text("""
        SELECT 
            COUNT(*) as total_loans,
            SUM(current_balance) as total_current_balance,
            SUM(original_balance) as total_original_balance,
            SUM(fair_value_clean) as total_fair_value,
            SUM(fair_value_dirty) as total_market_value,
            SUM(accrued_interest) as total_accrued_interest,
            SUM(gross_proceeds) as total_investment_value,
            AVG(price_clean_decimal) as avg_price,
            AVG(price_clean_pct) as avg_price_pct,
            AVG(wal_years) as avg_wal_years,
            AVG(modified_duration_years) as avg_modified_duration,
            AVG(rpx_total_spread_bps) as avg_effective_spread_bps,
            AVG(rpx_base_spread_bps) as avg_rpx_adjustment_bps,
            AVG(ltv_current) as avg_ltv_current,
            AVG(dscr_current) as avg_dscr_current,
            MIN(valuation_date) as earliest_valuation_date,
            MAX(valuation_date) as latest_valuation_date,
            COUNT(DISTINCT property_type) as property_types_count,
            COUNT(CASE WHEN loan_status = 'Performing' THEN 1 END) as performing_loans,
            COUNT(CASE WHEN loan_status != 'Performing' THEN 1 END) as non_performing_loans,
            MAX(last_updated) as last_update
        FROM mv_pricing_engine_output_complete_v4_layered
    """)).mappings().all()
    
    return JSONResponse(content=jsonable_encoder([dict(row) for row in rows]))

@router.get("/portfolio-breakdown", operation_id="portfolio_breakdown")
def get_portfolio_breakdown(
    group_by: str = Query("property_type", description="Group by: property_type, loan_status, interest_type"),
    db: Session = Depends(get_db)
):
    """Get portfolio breakdown grouped by specified field from materialized view."""
    
    # Validate group_by parameter
    allowed_fields = ["property_type", "loan_status", "interest_type", "sector"]
    if group_by not in allowed_fields:
        raise HTTPException(status_code=400, detail=f"group_by must be one of: {allowed_fields}")
    
    rows = db.execute(text(f"""
        SELECT 
            {group_by} as category,
            COUNT(*) as loan_count,
            SUM(current_balance) as total_current_balance,
            SUM(fair_value_clean) as total_fair_value,
            SUM(fair_value_dirty) as total_market_value,
            AVG(price_clean_pct) as avg_price_pct,
            AVG(wal_years) as avg_wal_years,
            AVG(rpx_total_spread_bps) as avg_effective_spread_bps,
            AVG(rpx_base_spread_bps) as avg_rpx_adjustment_bps,
            AVG(ltv_current) as avg_ltv_current,
            AVG(dscr_current) as avg_dscr_current,
            MIN(current_balance) as min_balance,
            MAX(current_balance) as max_balance,
            MAX(last_updated) as last_update
        FROM mv_pricing_engine_output_complete_v4_layered
        WHERE {group_by} IS NOT NULL
        GROUP BY {group_by}
        ORDER BY total_current_balance DESC
    """)).mappings().all()
    
    return JSONResponse(content=jsonable_encoder([dict(row) for row in rows]))

@router.get("/config/dates", operation_id="get_valuation_config_dates")
def get_valuation_config_dates(db: Session = Depends(get_db)):
    """Get the current valuation and settlement dates being used by the pricing engine."""
    
    # Get dates from the database functions (which use launch_config)
    result = db.execute(text("""
        SELECT 
            get_valuation_date() as current_valuation_date,
            get_settlement_date() as current_settlement_date
    """)).mappings().first()
    
    # Also get the source configuration from launch_config
    config_result = db.execute(text("""
        SELECT name, valuation_date, settlement_date, updated_at
        FROM launch_config
        WHERE name = 'DEFAULT'
    """)).mappings().first()
    
    return JSONResponse(content={
        'active_dates': {
            'valuation_date': result.current_valuation_date.isoformat(),
            'settlement_date': result.current_settlement_date.isoformat()
        },
        'source_config': jsonable_encoder(dict(config_result)) if config_result else None,
        'message': 'These dates are used for all pricing calculations and materialized view refreshes'
    })

@router.post("/refresh-materialized-views", operation_id="refresh_materialized_views")
def refresh_materialized_views(db: Session = Depends(get_db)):
    """Refresh all existing materialized views using current launch_config dates."""
    try:
        # Get current dates being used
        dates_result = db.execute(text("""
            SELECT 
                get_valuation_date() as valuation_date,
                get_settlement_date() as settlement_date
        """)).mappings().first()
        
        logger.info(f"Refreshing materialized views with valuation_date={dates_result.valuation_date}, settlement_date={dates_result.settlement_date}")
        
        # Get list of existing materialized views
        result = db.execute(text("""
            SELECT matviewname FROM pg_matviews 
            WHERE schemaname = 'public'
            ORDER BY matviewname
        """)).mappings().all()
        
        refreshed_views = []
        for row in result:
            view_name = row['matviewname']
            try:
                db.execute(text(f"REFRESH MATERIALIZED VIEW {view_name}"))
                refreshed_views.append({'view': view_name, 'status': 'success'})
                logger.info(f"Successfully refreshed {view_name}")
            except Exception as e:
                refreshed_views.append({'view': view_name, 'status': 'failed', 'error': str(e)})
                logger.error(f"Failed to refresh {view_name}: {e}")
        
        db.commit()
        
        return JSONResponse(content={
            'message': f'Refreshed {len([v for v in refreshed_views if v["status"] == "success"])} of {len(refreshed_views)} materialized views',
            'refresh_config': {
                'valuation_date': dates_result.valuation_date.isoformat(),
                'settlement_date': dates_result.settlement_date.isoformat()
            },
            'results': refreshed_views
        })
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to refresh materialized views: {str(e)}")

@router.post("/refresh-with-dates", operation_id="refresh_with_custom_dates")
def refresh_with_custom_dates(
    valuation_date: Optional[date] = Query(None, description="Custom valuation date for this refresh"),
    settlement_date: Optional[date] = Query(None, description="Custom settlement date for this refresh"),
    update_config: bool = Query(False, description="Whether to update the launch_config with these dates"),
    db: Session = Depends(get_db)
):
    """Refresh materialized views with custom dates (optionally updating launch_config)."""
    try:
        original_config = None
        
        # If custom dates provided, set transaction-level context
        if valuation_date or settlement_date:
            if update_config:
                # Update launch_config permanently
                update_fields = []
                params = {}
                
                if valuation_date:
                    update_fields.append("valuation_date = :valuation_date")
                    params["valuation_date"] = valuation_date
                
                if settlement_date:
                    update_fields.append("settlement_date = :settlement_date") 
                    params["settlement_date"] = settlement_date
                
                if update_fields:
                    update_fields.append("updated_at = CURRENT_TIMESTAMP")
                    query = f"""
                        UPDATE launch_config 
                        SET {', '.join(update_fields)}
                        WHERE name = 'DEFAULT'
                        RETURNING name, valuation_date, settlement_date, updated_at
                    """
                    
                    result = db.execute(text(query), params).mappings().first()
                    logger.info(f"Updated launch_config: {dict(result)}")
            else:
                # Use transaction-level context (temporary)
                if valuation_date:
                    db.execute(text(f"SET LOCAL rpx.valuation_date = '{valuation_date}'"))
                
                if settlement_date:
                    db.execute(text(f"SET LOCAL rpx.settlement_date = '{settlement_date}'"))
        
        # Get effective dates
        dates_result = db.execute(text("""
            SELECT 
                get_valuation_date() as valuation_date,
                get_settlement_date() as settlement_date
        """)).mappings().first()
        
        logger.info(f"Refreshing with effective dates: valuation={dates_result.valuation_date}, settlement={dates_result.settlement_date}")
        
        # Refresh materialized views
        result = db.execute(text("""
            SELECT matviewname FROM pg_matviews 
            WHERE schemaname = 'public'
            ORDER BY matviewname
        """)).mappings().all()
        
        refreshed_views = []
        for row in result:
            view_name = row['matviewname']
            try:
                db.execute(text(f"REFRESH MATERIALIZED VIEW {view_name}"))
                refreshed_views.append({'view': view_name, 'status': 'success'})
                logger.info(f"Successfully refreshed {view_name}")
            except Exception as e:
                refreshed_views.append({'view': view_name, 'status': 'failed', 'error': str(e)})
                logger.error(f"Failed to refresh {view_name}: {e}")
        
        db.commit()
        
        return JSONResponse(content={
            'message': f'Refreshed {len([v for v in refreshed_views if v["status"] == "success"])} of {len(refreshed_views)} materialized views',
            'refresh_config': {
                'valuation_date': dates_result.valuation_date.isoformat(),
                'settlement_date': dates_result.settlement_date.isoformat(),
                'config_updated': update_config
            },
            'results': refreshed_views
        })
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to refresh materialized views: {str(e)}")

@router.get("/pricing-summary", operation_id="pricing_summary")
def get_pricing_summary(db: Session = Depends(get_db)):
    """Get portfolio summary from available summary views."""
    
    # Try v_client_portfolio_summary first, fall back to materialized view calculation
    try:
        rows = db.execute(text("SELECT * FROM v_client_portfolio_summary")).mappings().all()
        if rows:
            return JSONResponse(content=jsonable_encoder([dict(row) for row in rows]))
    except:
        pass
    
    # Fallback: Calculate summary from materialized view
    rows = db.execute(text("""
        SELECT 
            COUNT(*) as total_loans,
            SUM(current_balance) as total_current_balance,
            SUM(fair_value_clean) as total_fair_value,
            AVG(price_clean_pct) as avg_price_pct,
            AVG(wal_years) as avg_wal_years,
            AVG(rpx_total_spread_bps) as avg_effective_spread_bps,
            COUNT(CASE WHEN loan_status = 'Performing' THEN 1 END) as performing_loans,
            COUNT(CASE WHEN loan_status != 'Performing' THEN 1 END) as non_performing_loans,
            MAX(last_updated) as last_update
        FROM mv_pricing_engine_output_complete_v4_layered
    """)).mappings().all()
    
    return JSONResponse(content=jsonable_encoder([dict(row) for row in rows]))

@router.get("/risk-metrics", operation_id="risk_metrics")
def get_risk_metrics(db: Session = Depends(get_db)):
    """Get comprehensive risk metrics for all loans from materialized view."""
    rows = db.execute(text("""
        SELECT 
            loan_id,
            loan_name,
            loan_status,
            property_type,
            sector,
            current_balance,
            original_balance,
            ltv_current,
            dscr_current,
            internal_credit_rating,
            fair_value_clean,
            price_clean_pct,
            rpx_total_spread_bps,
            rpx_base_spread_bps,
            component_yield_decimal as market_yield,
            wal_years,
            modified_duration_years,
            effective_maturity_date,
            valuation_date,
            last_updated
        FROM mv_pricing_engine_output_complete_v4_layered
        WHERE ltv_current IS NOT NULL OR dscr_current IS NOT NULL
        ORDER BY current_balance DESC
    """)).mappings().all()
    
    return JSONResponse(content=jsonable_encoder([dict(row) for row in rows]))

@router.get("/pricing-components", operation_id="pricing_components")
def get_pricing_components(db: Session = Depends(get_db)):
    """Get detailed pricing components breakdown for all loans."""
    rows = db.execute(text("""
        SELECT 
            loan_id,
            loan_name,
            current_balance,
            coupon,
            benchmark_type,
            benchmark_yield,
            component_yield_decimal as total_yield,
            component_yield_pct as total_yield_pct,
            rpx_total_spread_bps,
            rpx_base_spread_bps,
            fair_value_clean,
            fair_value_dirty,
            accrued_interest,
            price_clean_decimal,
            price_dirty_decimal,
            price_clean_pct,
            price_dirty_pct,
            price_accrued_pct,
            npv_value,
            gross_proceeds,
            net_proceeds,
            npv_methodology,
            last_updated
        FROM mv_pricing_engine_output_complete_v4_layered
        ORDER BY loan_id
    """)).mappings().all()
    
    return JSONResponse(content=jsonable_encoder([dict(row) for row in rows]))

@router.get("/loan-cashflows", operation_id="loan_cashflows")
def get_loan_cashflows(db: Session = Depends(get_db)):
    """Get cashflow analytics for all loans."""
    rows = db.execute(text("""
        SELECT 
            loan_id,
            loan_name,
            current_balance,
            total_cashflows,
            total_periods,
            final_period,
            first_amort_period,
            periodicity,
            amortization_type,
            io_end_date,
            effective_maturity_date,
            wal_years,
            macaulay_duration_years,
            modified_duration_years,
            convexity,
            npv_value,
            component_yield_decimal as irr,
            last_updated
        FROM mv_pricing_engine_output_complete_v4_layered
        WHERE total_cashflows IS NOT NULL
        ORDER BY loan_id
    """)).mappings().all()
    
    return JSONResponse(content=jsonable_encoder([dict(row) for row in rows]))

@router.get("/loan-cashflows-detailed/{loan_id}", operation_id="loan_cashflows_detailed")
def get_loan_cashflows_detailed(
    loan_id: int,
    max_periods: int = Query(625, ge=1, le=1000, description="Maximum number of periods to generate"),
    db: Session = Depends(get_db)
):
    """
    Get detailed cashflow schedule for a specific loan using the same calculation functions
    as the materialized view.
    
    Returns the complete payment schedule with period-by-period breakdown:
    - Payment dates
    - Beginning and ending balances
    - Interest and principal payments
    - Time factors for NPV calculations
    """
    
    # First, get loan details from the loans table
    loan = db.execute(text("""
        SELECT 
            rp_system_id,
            current_balance,
            fixed_rate_coupon as coupon_rate,
            first_payment_date,
            calculate_effective_maturity_date(rp_system_id) as maturity_date,
            periodicity,
            amortization_type,
            io_end_date,
            original_balance,
            original_amort_term_months,
            contractual_pi_payment_amount as scheduled_payment
        FROM loans
        WHERE rp_system_id = :loan_id
    """), {"loan_id": str(loan_id)}).mappings().first()
    
    if not loan:
        return JSONResponse(
            status_code=404,
            content={"error": f"Loan with ID {loan_id} not found"}
        )
    
    # Call the cashflow generation function - same one used by materialized view
    cashflows = db.execute(text("""
        SELECT 
            period_number,
            payment_date,
            month_beginning_date_for_valuation,
            beginning_balance,
            interest_payment,
            principal_payment,
            total_payment,
            ending_balance,
            time_factor,
            is_payment_period
        FROM generate_cashflow_excel_unified(
            p_current_balance := :current_balance,
            p_coupon_rate := :coupon_rate,
            p_payment_amount := :payment_amount,
            p_first_payment_date := :first_payment_date,
            p_maturity_date := :maturity_date,
            p_periodicity := :periodicity,
            p_amortization_type := :amortization_type,
            p_io_end_date := :io_end_date,
            p_original_balance := :original_balance,
            p_original_amort_term_months := :original_amort_term_months,
            p_max_periods := :max_periods,
            p_include_prepayment_period := false,
            p_loan_id := :loan_id,
            p_calculation_mode := 'pricing'
        )
        ORDER BY period_number
    """), {
        "current_balance": loan["current_balance"],
        "coupon_rate": loan["coupon_rate"],
        "payment_amount": loan["scheduled_payment"] or 0,
        "first_payment_date": loan["first_payment_date"],
        "maturity_date": loan["maturity_date"],
        "periodicity": loan["periodicity"],
        "amortization_type": loan["amortization_type"],
        "io_end_date": loan["io_end_date"],
        "original_balance": loan["original_balance"],
        "original_amort_term_months": loan["original_amort_term_months"],
        "max_periods": max_periods,
        "loan_id": loan_id
    }).mappings().all()
    
    # Calculate summary statistics
    total_interest = sum(float(row.get("interest_payment", 0)) for row in cashflows)
    total_principal = sum(float(row.get("principal_payment", 0)) for row in cashflows)
    total_payments = sum(float(row.get("total_payment", 0)) for row in cashflows)
    num_periods = len([row for row in cashflows if row.get("is_payment_period")])
    
    return JSONResponse(content=jsonable_encoder({
        "loan_id": loan_id,
        "loan_summary": {
            "current_balance": float(loan["current_balance"]),
            "coupon_rate": float(loan["coupon_rate"]) if loan["coupon_rate"] else 0,
            "maturity_date": str(loan["maturity_date"]),
            "periodicity": loan["periodicity"],
            "amortization_type": loan["amortization_type"],
            "total_periods": num_periods,
            "total_interest": total_interest,
            "total_principal": total_principal,
            "total_payments": total_payments
        },
        "cashflows": [dict(row) for row in cashflows]
    }))

@router.get("/benchmark-current", operation_id="benchmark_current")
def get_benchmark_current(db: Session = Depends(get_db)):
    """Get current benchmark rates from v_benchmark_current view."""
    rows = db.execute(text("SELECT * FROM v_benchmark_current")).mappings().all()
    return JSONResponse(content=jsonable_encoder([dict(row) for row in rows]))

@router.get("/current-pricing-spreads", operation_id="current_pricing_spreads")
def get_current_pricing_spreads(db: Session = Depends(get_db)):
    """Get current pricing spreads from v_current_pricing_spreads view."""
    rows = db.execute(text("SELECT * FROM v_current_pricing_spreads")).mappings().all()
    return JSONResponse(content=jsonable_encoder([dict(row) for row in rows]))

@router.get("/valuation-reports", operation_id="valuation_reports")
def get_valuation_reports(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    property_type: Optional[str] = Query(None, description="Filter by property type"),
    loan_status: Optional[str] = Query(None, description="Filter by loan status"),
    db: Session = Depends(get_db)
):
    """Frontend-expected valuation reports endpoint - returns ALL fields from mv_pricing_engine_output_complete sorted by loan ID.
    
    Key fields for frontend:
    - loan_name: Loan identifier
    - current_balance: Original loan amount
    - fair_value: Current valuation in dollars
    - price_pct: Main price field (percentage, e.g., 96.5% means trading at 96.5% of par)
    """
    
    # Build query returning ALL fields from materialized view, sorted by ID ASC
    query = """
        SELECT * FROM mv_pricing_engine_output_complete_v4_layered
        WHERE 1=1
    """
    
    params = {}
    if property_type:
        query += " AND property_type = :property_type"
        params["property_type"] = property_type
    
    if loan_status:
        query += " AND loan_status = :loan_status" 
        params["loan_status"] = loan_status
    
    query += f" ORDER BY loan_id ASC LIMIT {limit} OFFSET {skip}"
    
    rows = db.execute(text(query), params).mappings().all()
    return JSONResponse(content=jsonable_encoder([dict(row) for row in rows]))

@router.post("/the-refresh", operation_id="the_refresh_materialized_views")
async def refresh_materialized_views(db: Session = Depends(get_db)):
    """
    Refresh all materialized views in the correct dependency order.
    
    This endpoint triggers a refresh of all materialized views used for pricing calculations.
    Views are refreshed in the correct order to maintain dependencies:
    1. Level 1 views (base calculations): mv_loan_pricing, mv_loan_valuation, mv_loan_accrued, mv_loan_spread
    2. Level 2 views (aggregations): mv_pricing_engine_output_complete
    
    Returns the refresh status and timing for each view.
    """
    import time
    from datetime import datetime
    refresh_results = []
    
    try:
        # Level 1 views - can be refreshed in any order
        level1_views = [
            'mv_loan_pricing',
            'mv_loan_valuation',
            'mv_loan_accrued',
            'mv_loan_spread'
        ]
        
        # Refresh Level 1 views
        logger.info("Starting Level 1 materialized view refresh...")
        for view_name in level1_views:
            start_time = time.time()
            try:
                db.execute(text(f"REFRESH MATERIALIZED VIEW {view_name}"))
                db.commit()
                duration = time.time() - start_time
                
                refresh_results.append({
                    "view": view_name,
                    "status": "success",
                    "duration_seconds": round(duration, 2),
                    "level": 1
                })
                logger.info(f"✅ Refreshed {view_name} in {duration:.2f}s")
                
            except Exception as e:
                duration = time.time() - start_time
                refresh_results.append({
                    "view": view_name,
                    "status": "failed",
                    "error": str(e),
                    "duration_seconds": round(duration, 2),
                    "level": 1
                })
                logger.error(f"❌ Failed to refresh {view_name}: {e}")
        
        # Level 2 views - depends on Level 1
        level2_views = ['mv_pricing_engine_output_complete_v4_layered']
        
        logger.info("Starting Level 2 materialized view refresh...")
        for view_name in level2_views:
            start_time = time.time()
            try:
                db.execute(text(f"REFRESH MATERIALIZED VIEW {view_name}"))
                db.commit()
                duration = time.time() - start_time
                
                refresh_results.append({
                    "view": view_name,
                    "status": "success",
                    "duration_seconds": round(duration, 2),
                    "level": 2
                })
                logger.info(f"✅ Refreshed {view_name} in {duration:.2f}s")
                
            except Exception as e:
                duration = time.time() - start_time
                refresh_results.append({
                    "view": view_name,
                    "status": "failed",
                    "error": str(e),
                    "duration_seconds": round(duration, 2),
                    "level": 2
                })
                logger.error(f"❌ Failed to refresh {view_name}: {e}")
        
        # Calculate summary
        total_duration = sum(r["duration_seconds"] for r in refresh_results)
        successful_count = sum(1 for r in refresh_results if r["status"] == "success")
        failed_count = sum(1 for r in refresh_results if r["status"] == "failed")
        
        return JSONResponse(content={
            "message": f"Materialized view refresh completed. {successful_count} succeeded, {failed_count} failed.",
            "total_duration_seconds": round(total_duration, 2),
            "timestamp": str(datetime.now()),
            "results": refresh_results,
            "summary": {
                "total_views": len(refresh_results),
                "successful": successful_count,
                "failed": failed_count,
                "performance_note": "Materialized views provide ~1200x performance improvement over regular views"
            }
        })
        
    except Exception as e:
        logger.error(f"Error during materialized view refresh: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "error": "Failed to refresh materialized views",
                "detail": str(e),
                "results": refresh_results
            }
        )


        


# CRUD endpoints for loan_pricing table
# TODO: Implement LoanPricingCreate, LoanPricingUpdate, LoanPricingResponse schemas
# Temporarily commented out until schemas are implemented

# @router.get("/pricing-data/{rp_system_id}/{valuation_date}", response_model=LoanPricingResponse, operation_id="get_pricing_data")
# async def get_pricing_data(
#     rp_system_id: str,
#     valuation_date: date,
#     db: Session = Depends(get_db)
# ):
#     """Get pricing data for a specific loan and valuation date."""
#     result = db.execute(text("""
#         SELECT * FROM loan_pricing
#         WHERE rp_system_id = :rp_system_id AND valuation_date = :valuation_date
#     """), {
#         "rp_system_id": rp_system_id,
#         "valuation_date": valuation_date
#     }).first()
#     
#     if not result:
#         raise HTTPException(status_code=404, detail="Pricing data not found")
#     
#     # Convert to dict and handle the 'yield' field
#     data = dict(result._mapping)
#     if 'yield' in data:
#         data['yield_field'] = data.pop('yield')
#     
#     return LoanPricingResponse(**data)


# @router.post("/pricing-data", response_model=LoanPricingResponse, operation_id="create_pricing_data")
# async def create_pricing_data(pricing: LoanPricingCreate, db: Session = Depends(get_db)):
#     """Create new pricing data for a loan."""
#     # Check if loan exists
#     loan_exists = db.execute(
#         text("SELECT 1 FROM loans WHERE rp_system_id = :rp_system_id"),
#         {"rp_system_id": pricing.rp_system_id}
#     ).first()
#     
#     if not loan_exists:
#         raise HTTPException(status_code=404, detail="Loan not found")
#     
#     # Check if pricing data already exists
#     existing = db.execute(text("""
#         SELECT 1 FROM loan_pricing
#         WHERE rp_system_id = :rp_system_id AND valuation_date = :valuation_date
#     """), {
#         "rp_system_id": pricing.rp_system_id,
#         "valuation_date": pricing.valuation_date
#     }).first()
#     
#     if existing:
#         raise HTTPException(status_code=400, detail="Pricing data already exists for this loan and date")
#     
#     # Prepare values dict, converting yield_field to yield
#     values = pricing.dict()
#     if 'yield_field' in values:
#         values['yield'] = values.pop('yield_field')
#     
#     # Build dynamic INSERT statement
#     columns = [k for k in values.keys() if values[k] is not None]
#     placeholders = [f":{k}" for k in columns]
#     
#     query = f"""
#         INSERT INTO loan_pricing ({', '.join(columns)})
#         VALUES ({', '.join(placeholders)})
#         RETURNING *
#     """
#     
#     result = db.execute(text(query), values)
#     row = result.first()
#     db.commit()
#     
#     # Convert result to dict and handle yield field
#     data = dict(row._mapping)
#     if 'yield' in data:
#         data['yield_field'] = data.pop('yield')
#     
#     return LoanPricingResponse(**data)


# @router.put("/pricing-data/{rp_system_id}/{valuation_date}", response_model=LoanPricingResponse, operation_id="update_pricing_data")
# async def update_pricing_data(
#     rp_system_id: str,
#     valuation_date: date,
#     pricing_update: LoanPricingUpdate,
#     db: Session = Depends(get_db)
# ):
#     """Update existing pricing data."""
#     # Check if pricing data exists
#     existing = db.execute(text("""
#         SELECT 1 FROM loan_pricing
#         WHERE rp_system_id = :rp_system_id AND valuation_date = :valuation_date
#     """), {
#         "rp_system_id": rp_system_id,
#         "valuation_date": valuation_date
#     }).first()
#     
#     if not existing:
#         raise HTTPException(status_code=404, detail="Pricing data not found")
#     
#     # Build dynamic UPDATE statement
#     update_data = pricing_update.dict(exclude_unset=True)
#     if not update_data:
#         raise HTTPException(status_code=400, detail="No fields to update")
#     
#     # Handle yield field
#     if 'yield_field' in update_data:
#         update_data['yield'] = update_data.pop('yield_field')
#     
#     set_clauses = [f"{k} = :{k}" for k in update_data.keys()]
#     update_data['rp_system_id'] = rp_system_id
#     update_data['valuation_date'] = valuation_date
#     
#     query = f"""
#         UPDATE loan_pricing
#         SET {', '.join(set_clauses)}
#         WHERE rp_system_id = :rp_system_id AND valuation_date = :valuation_date
#         RETURNING *
#     """
#     
#     result = db.execute(text(query), update_data)
#     row = result.first()
#     db.commit()
#     
#     # Convert result to dict and handle yield field
#     data = dict(row._mapping)
#     if 'yield' in data:
#         data['yield_field'] = data.pop('yield')
#     
#     return LoanPricingResponse(**data)


# @router.delete("/pricing-data/{rp_system_id}/{valuation_date}", operation_id="delete_pricing_data")
# async def delete_pricing_data(
#     rp_system_id: str,
#     valuation_date: date,
#     db: Session = Depends(get_db)
# ):
#     """Delete pricing data for a specific loan and valuation date."""
#     # Check if pricing data exists
#     existing = db.execute(text("""
#         SELECT 1 FROM loan_pricing
#         WHERE rp_system_id = :rp_system_id AND valuation_date = :valuation_date
#     """), {
#         "rp_system_id": rp_system_id,
#         "valuation_date": valuation_date
#     }).first()
#     
#     if not existing:
#         raise HTTPException(status_code=404, detail="Pricing data not found")
#     
#     # Delete the pricing data
#     db.execute(text("""
#         DELETE FROM loan_pricing
#         WHERE rp_system_id = :rp_system_id AND valuation_date = :valuation_date
#     """), {
#         "rp_system_id": rp_system_id,
#         "valuation_date": valuation_date
#     })
#     db.commit()
#     
#     return {
#         "message": "Pricing data deleted successfully",
#         "rp_system_id": rp_system_id,
#         "valuation_date": str(valuation_date)
#     } 