"""
Excel export endpoints for loans and pricing data.
"""

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional
from datetime import date
import logging

from app.database.session import get_db
from app.utils.excel_exporter import ExcelExporter

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/loans/excel", operation_id="export_loans_excel")
async def export_loans_excel(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: Optional[int] = Query(None, ge=1, description="Number of records to return"),
    include_properties: bool = Query(True, description="Include property locations"),
    db: Session = Depends(get_db)
):
    """
    Export loans data to Excel format.
    
    Returns an Excel file with:
    - Sheet 1: Loans data with complete pricing from materialized view
    - Sheet 2: Property locations (if include_properties=True)
    """
    try:
        # Query loans from materialized view for complete pricing data
        loans_query = "SELECT * FROM mv_pricing_engine_output_complete_v4_layered"
        if limit:
            loans_query += f" ORDER BY loan_id OFFSET {skip} LIMIT {limit}"
        else:
            loans_query += f" ORDER BY loan_id OFFSET {skip}"
            
        loans_rows = db.execute(text(loans_query)).mappings().all()
        loans_data = [dict(row) for row in loans_rows]
        
        # Query properties if requested
        properties_data = None
        if include_properties:
            # Get loan_ids from materialized view data
            loan_ids = [loan['loan_id'] for loan in loans_data]
            if loan_ids:
                # Query properties for these loans
                props_query = text("""
                    SELECT * FROM loan_properties 
                    WHERE rp_system_id = ANY(:loan_ids)
                    ORDER BY rp_system_id, property_number
                """)
                props_rows = db.execute(props_query, {"loan_ids": loan_ids}).mappings().all()
                properties_data = [dict(row) for row in props_rows]
        
        # Create Excel file
        excel_file = ExcelExporter.create_loans_excel(loans_data, properties_data)
        
        # Return as streaming response
        filename = f"loans_export_{date.today().strftime('%Y%m%d')}.xlsx"
        return StreamingResponse(
            excel_file,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error(f"Error exporting loans to Excel: {str(e)}")
        raise


@router.get("/pricing-results/excel", operation_id="export_pricing_excel")
async def export_pricing_results_excel(
    include_risk_metrics: bool = Query(True, description="Include risk metrics"),
    include_market_data: bool = Query(True, description="Include benchmarks and spreads"),
    db: Session = Depends(get_db)
):
    """
    Export pricing results to Excel format.
    
    Returns an Excel file with:
    - Sheet 1: Complete pricing results from v_pricing_engine_output_complete with property locations
    - Sheet 2: Risk metrics (if include_risk_metrics=True)
    - Sheet 3: Market data - benchmarks and spreads (if include_market_data=True)
    """
    try:
        # Get comprehensive pricing data from materialized view (much faster)
        pricing_query = text("SELECT * FROM mv_pricing_engine_output_complete_v4_layered ORDER BY loan_id")
        pricing_rows = db.execute(pricing_query).mappings().all()
        pricing_data = [dict(row) for row in pricing_rows]
        
        # Get optional data (using materialized view for risk metrics too)
        risk_metrics = None
        if include_risk_metrics:
            # Use the materialized view for risk metrics instead
            risk_query = text("""
                SELECT 
                    loan_id,
                    loan_name,
                    current_balance,
                    sector as property_sector,
                    property_type,
                    loan_status,
                    borrower,
                    ltv_current,
                    dscr_current,
                    rpx_total_spread_bps as total_rpx_adjustment_bps,
                    rpx_base_spread_bps as effective_spread_bps
                FROM mv_pricing_engine_output_complete_v4_layered
                WHERE ltv_current IS NOT NULL OR dscr_current IS NOT NULL
                ORDER BY current_balance DESC
            """)
            risk_rows = db.execute(risk_query).mappings().all()
            risk_metrics = [dict(row) for row in risk_rows]
        
        benchmarks = None
        spreads = None
        if include_market_data:
            # Get current benchmarks
            bench_rows = db.execute(text("SELECT * FROM v_benchmark_current")).mappings().all()
            benchmarks = [dict(row) for row in bench_rows]
            
            # Get current spreads
            spread_rows = db.execute(text("SELECT * FROM v_current_pricing_spreads")).mappings().all()
            spreads = [dict(row) for row in spread_rows]
        
        # Create Excel file
        excel_file = ExcelExporter.create_pricing_results_excel(
            pricing_data=pricing_data,
            summary_data=None,  # No longer using v_pricing_summary
            risk_metrics=risk_metrics,
            benchmarks=benchmarks,
            spreads=spreads
        )
        
        # Return as streaming response
        filename = f"pricing_results_{date.today().strftime('%Y%m%d')}.xlsx"
        return StreamingResponse(
            excel_file,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error(f"Error exporting pricing results to Excel: {str(e)}")
        raise


@router.get("/complete-report/excel", operation_id="export_complete_excel")
async def export_complete_report_excel(
    db: Session = Depends(get_db)
):
    """
    Export complete analysis report to Excel format.
    
    Returns a comprehensive Excel file with:
    - Report Info: Metadata about the report
    - Source Loans: All loans from the loans table  
    - Source Properties: All property locations
    - Pricing Results: Complete pricing data from v_loan_pricing
    - Portfolio Summary: Aggregated portfolio metrics
    - Risk Analysis: Risk metrics for all loans
    - Market Data: Current benchmarks and credit spreads
    
    This provides a complete snapshot of both source data and calculated results.
    """
    try:
        logger.info("Starting complete report export")
        
        # Get all source data
        loans_rows = db.execute(text("SELECT * FROM loans")).mappings().all()
        loans_data = [dict(row) for row in loans_rows]
        logger.info(f"Retrieved {len(loans_data)} loans")
        
        props_rows = db.execute(text("SELECT * FROM loan_properties ORDER BY rp_system_id, property_number")).mappings().all()
        properties_data = [dict(row) for row in props_rows]
        logger.info(f"Retrieved {len(properties_data)} properties")
        
        # Get pricing data from materialized view (much faster)
        pricing_query = text("""
            SELECT * FROM mv_pricing_engine_output_complete_v4_layered
            ORDER BY loan_id
        """)
        pricing_rows = db.execute(pricing_query).mappings().all()
        pricing_data = [dict(row) for row in pricing_rows]
        logger.info(f"Retrieved {len(pricing_data)} pricing records")
        
        # Create summary data from pricing data (since v_pricing_summary doesn't exist)
        summary_data = []
        if pricing_data:
            total_loans = len(pricing_data)
            total_balance = sum(float(row.get('current_balance', 0) or 0) for row in pricing_data)
            total_fair_value = sum(float(row.get('fair_value_clean', 0) or 0) for row in pricing_data)
            
            summary_data = [{
                'total_loans': total_loans,
                'total_balance': total_balance,
                'total_fair_value': total_fair_value,
                'avg_price': (total_fair_value / total_balance * 100) if total_balance > 0 else 0
            }]
        logger.info(f"Created summary data with {len(summary_data)} records")
        
        # Get risk metrics from materialized view
        risk_metrics = []
        try:
            risk_query = text("""
                SELECT 
                    loan_id,
                    loan_name,
                    current_balance,
                    sector as property_sector,
                    property_type,
                    loan_status,
                    borrower,
                    ltv_current,
                    dscr_current,
                    rpx_total_spread_bps as total_rpx_adjustment_bps,
                    rpx_base_spread_bps as effective_spread_bps,
                    fair_value_clean as fair_value,
                    fair_value_dirty as market_value
                FROM mv_pricing_engine_output_complete_v4_layered
                WHERE ltv_current IS NOT NULL OR dscr_current IS NOT NULL
                ORDER BY current_balance DESC
            """)
            risk_rows = db.execute(risk_query).mappings().all()
            risk_metrics = [dict(row) for row in risk_rows]
            logger.info(f"Retrieved {len(risk_metrics)} risk metric records from materialized view")
        except Exception as e:
            logger.warning(f"Could not retrieve risk metrics from materialized view: {e}")
        
        # Get market data (handle gracefully if views don't exist)  
        benchmarks = []
        spreads = []
        try:
            bench_rows = db.execute(text("SELECT * FROM v_benchmark_current")).mappings().all()
            benchmarks = [dict(row) for row in bench_rows]
            logger.info(f"Retrieved {len(benchmarks)} benchmark rates")
        except Exception as e:
            logger.warning(f"Could not retrieve benchmarks: {e}")
            
        try:
            spread_rows = db.execute(text("SELECT * FROM v_current_pricing_spreads")).mappings().all()
            spreads = [dict(row) for row in spread_rows]
            logger.info(f"Retrieved {len(spreads)} credit spreads")
        except Exception as e:
            logger.warning(f"Could not retrieve spreads: {e}")
        
        # Create comprehensive Excel file using the pricing results format
        # This ensures the exact column format you need
        excel_file = ExcelExporter.create_pricing_results_excel(
            pricing_data=pricing_data,
            summary_data=None,  # Don't include summary sheet
            risk_metrics=None,  # Don't include risk metrics sheet
            benchmarks=None,    # Don't include benchmarks sheet
            spreads=None        # Don't include spreads sheet
        )
        
        # Return as streaming response
        filename = f"rpx_complete_report_{date.today().strftime('%Y%m%d')}.xlsx"
        return StreamingResponse(
            excel_file,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error(f"Error exporting complete report to Excel: {str(e)}")
        raise


@router.get("/portfolio-analysis/excel", operation_id="export_portfolio_analysis_excel")
async def export_portfolio_analysis_excel(
    include_individual_loans: bool = Query(True, description="Include individual loan details"),
    include_portfolio_breakdown: bool = Query(True, description="Include portfolio breakdown by categories"),
    db: Session = Depends(get_db)
):
    """
    Export comprehensive portfolio analysis to Excel format using materialized view.
    
    Returns an Excel file with:
    - Portfolio Summary: High-level portfolio metrics
    - Individual Loans: Complete loan details with pricing (if enabled)
    - Property Type Breakdown: Analysis by property type
    - Loan Status Breakdown: Analysis by loan status
    - Risk Analysis: LTV/DSCR analysis
    - Duration & Spread Analysis: Duration and spread metrics
    """
    try:
        logger.info("Starting portfolio analysis export")
        
        # Get portfolio summary from materialized view
        portfolio_summary = db.execute(text("""
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
                COUNT(CASE WHEN loan_status = 'Performing' THEN 1 END) as performing_loans,
                COUNT(CASE WHEN loan_status != 'Performing' THEN 1 END) as non_performing_loans,
                MAX(last_updated) as last_update
            FROM mv_pricing_engine_output_complete_v4_layered
        """)).mappings().all()
        
        # Get individual loans data if requested
        individual_loans = []
        if include_individual_loans:
            loan_rows = db.execute(text("""
                SELECT * FROM mv_pricing_engine_output_complete_v4_layered 
                ORDER BY current_balance DESC
            """)).mappings().all()
            individual_loans = [dict(row) for row in loan_rows]
        
        # Get breakdown data if requested
        breakdowns = {}
        if include_portfolio_breakdown:
            # Property type breakdown
            prop_breakdown = db.execute(text("""
                SELECT 
                    COALESCE(property_type, 'Unknown') as category,
                    COUNT(*) as loan_count,
                    SUM(current_balance) as total_current_balance,
                    SUM(fair_value_clean) as total_fair_value,
                    AVG(price_clean_pct) as avg_price_pct,
                    AVG(wal_years) as avg_wal_years,
                    AVG(rpx_total_spread_bps) as avg_effective_spread_bps,
                    AVG(rpx_base_spread_bps) as avg_rpx_adjustment_bps,
                    AVG(ltv_current) as avg_ltv_current,
                    AVG(dscr_current) as avg_dscr_current
                FROM mv_pricing_engine_output_complete_v4_layered
                GROUP BY property_type
                ORDER BY total_current_balance DESC
            """)).mappings().all()
            breakdowns['property_type'] = [dict(row) for row in prop_breakdown]
            
            # Loan status breakdown
            status_breakdown = db.execute(text("""
                SELECT 
                    loan_status as category,
                    COUNT(*) as loan_count,
                    SUM(current_balance) as total_current_balance,
                    SUM(fair_value_clean) as total_fair_value,
                    AVG(price_clean_pct) as avg_price_pct,
                    AVG(wal_years) as avg_wal_years,
                    AVG(rpx_total_spread_bps) as avg_effective_spread_bps,
                    AVG(rpx_base_spread_bps) as avg_rpx_adjustment_bps,
                    AVG(ltv_current) as avg_ltv_current,
                    AVG(dscr_current) as avg_dscr_current
                FROM mv_pricing_engine_output_complete_v4_layered
                GROUP BY loan_status
                ORDER BY total_current_balance DESC
            """)).mappings().all()
            breakdowns['loan_status'] = [dict(row) for row in status_breakdown]
        
        # Create Excel file using existing exporter
        excel_file = ExcelExporter.create_portfolio_analysis_excel(
            portfolio_summary=[dict(row) for row in portfolio_summary],
            individual_loans=individual_loans,
            breakdowns=breakdowns
        )
        
        # Return as streaming response
        filename = f"portfolio_analysis_{date.today().strftime('%Y%m%d')}.xlsx"
        return StreamingResponse(
            excel_file,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error(f"Error exporting portfolio analysis to Excel: {str(e)}")
        raise

# Removed redundant pricing-engine-output/excel endpoint
# Use /pricing-results/excel for main pricing export or /complete-report/excel for comprehensive export