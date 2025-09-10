"""
Comprehensive pricing output schemas for RPX Backend 2026.

This module defines the expected output format for all pricing endpoints
based on RPX pricing engine specifications and current API capabilities.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Dict, List, Optional, Union
from pydantic import BaseModel, Field, ConfigDict


# ============================================================================
# BASE MODELS - Core building blocks for pricing outputs
# ============================================================================

class SpreadAdjustments(BaseModel):
    """Detailed spread adjustments applied during pricing calculations."""
    
    # Base spread from matrix
    matrix_spread_bps: Optional[float] = Field(None, description="Base spread from pricing matrix")
    
    # Individual adjustments
    ltv_factor_adjustment_bps: Optional[float] = Field(0.0, description="LTV factor adjustment")
    sasb_premium_bps: Optional[float] = Field(0, description="SASB premium for certain property types")
    lifecycle_adjustment_bps: Optional[float] = Field(0, description="Property lifecycle adjustment")
    dscr_adjustment_bps: Optional[float] = Field(0, description="DSCR adjustment")
    ltv_performance_adjustment_bps: Optional[float] = Field(0, description="LTV performance adjustment")
    loan_status_adjustment_bps: Optional[float] = Field(0.0, description="Adjustment for loan status (e.g., default)")
    senior_tiering_adjustment_bps: Optional[float] = Field(0, description="Senior loan tiering adjustment")
    mezzanine_adjustment_bps: Optional[float] = Field(0, description="Mezzanine loan adjustment")
    
    # Total and final spreads
    total_rpx_adjustment_bps: Optional[float] = Field(0.0, description="Total RPX adjustments")
    adjusted_spread_bps: Optional[float] = Field(None, description="Matrix spread + adjustments")
    effective_spread_bps: Optional[float] = Field(None, description="Final effective spread")

    model_config = ConfigDict(
        json_encoders={
            Decimal: lambda v: float(v) if v else None,
            date: lambda v: v.isoformat() if v else None,
            datetime: lambda v: v.isoformat() if v else None
        }
    )


class RiskMetrics(BaseModel):
    """Risk metrics including PD, LGD, and expected loss calculations."""
    
    # Probability of Default
    pd: Optional[float] = Field(None, description="Probability of default (0-1)")
    pd_percentage: Optional[float] = Field(None, description="PD as percentage (0-100)")
    
    # Loss Given Default
    lgd: Optional[float] = Field(None, description="Loss given default (0-1)")
    lgd_percentage: Optional[float] = Field(None, description="LGD as percentage (0-100)")
    
    # Exposure at Default
    ead: Optional[float] = Field(None, description="Exposure at default (0-1)")
    ead_amount: Optional[Decimal] = Field(None, description="EAD in currency amount")
    
    # Expected Loss
    expected_loss: Optional[float] = Field(None, description="Expected loss (PD × LGD × EAD)")
    expected_loss_amount: Optional[Decimal] = Field(None, description="Expected loss in currency")
    
    # Default information
    default_date: Optional[date] = Field(None, description="Default date if applicable")
    days_to_default: Optional[int] = Field(None, description="Days until/since default")
    lag_to_recovery: Optional[int] = Field(None, description="Expected months to recovery")
    
    # Loss scenario
    loss_scenario: Optional[str] = Field(None, description="Loss scenario type")
    loss_scenario_formatted: Optional[str] = Field(None, description="Formatted loss scenario")
    default_scenario: Optional[str] = Field(None, description="Default scenario description")

    model_config = ConfigDict(
        json_encoders={
            Decimal: lambda v: float(v) if v else None,
            date: lambda v: v.isoformat() if v else None,
            datetime: lambda v: v.isoformat() if v else None
        }
    )


class PricingMetrics(BaseModel):
    """Core pricing metrics including yields, spreads, and valuation."""
    
    # Benchmark information
    benchmark_type: Optional[str] = Field(None, description="Benchmark type (UST, SOFR, etc.)")
    benchmark_yield: Optional[float] = Field(None, description="Benchmark yield as decimal")
    benchmark_yield_percentage: Optional[float] = Field(None, description="Benchmark yield as percentage")
    
    # Credit spread
    credit_spread: Optional[float] = Field(None, description="Credit spread in percentage")
    credit_spread_decimal: Optional[float] = Field(None, description="Credit spread as decimal")
    credit_spread_bps: Optional[float] = Field(None, description="Credit spread in basis points")
    
    # Market yield
    market_yield: Optional[float] = Field(None, description="Market yield as percentage")
    market_yield_decimal: Optional[float] = Field(None, description="Market yield as decimal")
    
    # Valuation
    price: Optional[float] = Field(None, description="Price as percentage of par (0-100)")
    fair_value: Optional[Decimal] = Field(None, description="Fair value in currency")
    
    # Duration metrics
    wal_years: Optional[float] = Field(None, description="Weighted average life in years")
    modified_duration_years: Optional[float] = Field(None, description="Modified duration in years")
    convexity: Optional[float] = Field(None, description="Convexity measure")

    model_config = ConfigDict(
        json_encoders={
            Decimal: lambda v: float(v) if v else None,
            date: lambda v: v.isoformat() if v else None,
            datetime: lambda v: v.isoformat() if v else None
        }
    )


# ============================================================================
# LOAN-LEVEL SCHEMAS - Individual loan pricing outputs
# ============================================================================

class LoanPricingOutput(BaseModel):
    """Complete pricing output for an individual loan."""
    
    # Identifiers
    loan_id: Optional[int] = Field(None, description="Internal loan ID")
    rp_system_id: int = Field(..., description="Primary key - system ID")
    client_loan_number: Optional[str] = Field(None, description="Client's loan number")
    loan_name: Optional[str] = Field(None, description="Loan name/description")
    
    # Property information
    property_sector: Optional[str] = Field(None, description="Property sector (Office, Retail, etc.)")
    property_type: Optional[str] = Field(None, description="Specific property type")
    property_lifecycle_financing: Optional[str] = Field(None, description="Financing lifecycle stage")
    property_location: Optional[str] = Field(None, description="Property location")
    
    # Loan characteristics
    sponsor_borrower: Optional[str] = Field(None, description="Sponsor/borrower name")
    original_balance: Optional[Decimal] = Field(None, description="Original loan balance")
    current_balance: Optional[Decimal] = Field(None, description="Current outstanding balance")
    currency: Optional[str] = Field("USD", description="Currency code")
    client_percentage: Optional[float] = Field(1.0, description="Client's ownership percentage")
    pik_balance: Optional[Decimal] = Field(0.0, description="PIK balance if applicable")
    
    # Capital structure
    position_in_capital_stack: Optional[str] = Field(None, description="Position in capital stack")
    amortization_type: Optional[str] = Field(None, description="Amortization type")
    periodicity: Optional[str] = Field(None, description="Payment periodicity")
    interest_day_count: Optional[str] = Field(None, description="Interest day count convention")
    
    # Loan status
    loan_status: Optional[str] = Field(None, description="Current loan status")
    commentary: Optional[str] = Field(None, description="Additional commentary")
    in_forbearance: Optional[str] = Field("N", description="Forbearance flag")
    forbearance_start_date: Optional[date] = Field(None, description="Forbearance start date")
    forbearance_type: Optional[str] = Field(None, description="Type of forbearance")
    
    # Interest rate information
    interest_type: Optional[str] = Field(None, description="Fixed or Floating")
    fixed_rate_coupon: Optional[float] = Field(None, description="Fixed rate coupon")
    floating_rate_index: Optional[str] = Field(None, description="Floating rate index")
    floating_rate_margin: Optional[float] = Field(None, description="Floating rate margin")
    contract_rate: Optional[float] = Field(None, description="Current contract rate")
    coupon_description: Optional[str] = Field(None, description="Formatted coupon description")
    
    # Key dates
    origination_date: Optional[date] = Field(None, description="Loan origination date")
    first_payment_date: Optional[date] = Field(None, description="First payment date")
    original_maturity_date: Optional[date] = Field(None, description="Original maturity date")
    effective_maturity_date: Optional[datetime] = Field(None, description="Effective maturity date")
    prepayment_lockout_end_date: Optional[date] = Field(None, description="Prepayment lockout end")
    io_end_date: Optional[date] = Field(None, description="Interest-only period end")
    
    # Extension options
    first_extension_date: Optional[date] = Field(None, description="First extension date")
    first_extension_fee: Optional[float] = Field(None, description="First extension fee")
    second_extension_date: Optional[date] = Field(None, description="Second extension date")
    second_extension_fee: Optional[float] = Field(None, description="Second extension fee")
    third_extension_date: Optional[date] = Field(None, description="Third extension date")
    third_extension_fee: Optional[float] = Field(None, description="Third extension fee")
    exit_fee: Optional[float] = Field(None, description="Exit fee")
    
    # Underwriting metrics
    ltv_current: Optional[float] = Field(None, description="Current LTV ratio")
    dscr_current: Optional[float] = Field(None, description="Current DSCR")
    debt_yield_current: Optional[float] = Field(None, description="Current debt yield")
    noi: Optional[Decimal] = Field(None, description="Net operating income")
    property_appraisal_value: Optional[Decimal] = Field(None, description="Property appraisal value")
    property_appraisal_value_date: Optional[date] = Field(None, description="Appraisal date")
    
    # Pricing scenario
    pricing_scenario: Optional[str] = Field("RPX Pricing", description="Pricing scenario used")
    maturity_assumption: Optional[str] = Field("Maturity", description="Maturity assumption")
    valuation_date: Optional[date] = Field(None, description="Valuation date")
    interest_accrual_type: Optional[str] = Field(None, description="Interest accrual type")
    
    # Time metrics
    remaining_months: Optional[int] = Field(None, description="Months to maturity")
    remaining_years: Optional[float] = Field(None, description="Years to maturity")
    term_bucket: Optional[str] = Field(None, description="Term bucket classification")
    
    # Pricing components
    pricing_metrics: Optional[PricingMetrics] = Field(None, description="Core pricing metrics")
    spread_adjustments: Optional[SpreadAdjustments] = Field(None, description="Spread adjustments")
    risk_metrics: Optional[RiskMetrics] = Field(None, description="Risk metrics")

    model_config = ConfigDict(
        json_encoders={
            Decimal: lambda v: float(v) if v else None,
            date: lambda v: v.isoformat() if v else None,
            datetime: lambda v: v.isoformat() if v else None
        }
    )


class SimplifiedLoanPricing(BaseModel):
    """Simplified pricing output matching current API structure."""
    
    # Core identifiers
    loan_id: Optional[int]
    loan_name: Optional[str]
    property_sector: Optional[str]
    
    # Pricing metrics
    price: Optional[float]
    fair_value: Optional[Decimal]
    current_balance: Optional[Decimal]
    market_yield: Optional[float]
    benchmark_yield: Optional[float]
    wal_years: Optional[float]
    
    # Spread adjustments (nested)
    spread_adjustments: Optional[Dict[str, Optional[float]]]

    model_config = ConfigDict(
        json_encoders={
            Decimal: lambda v: float(v) if v else None,
            date: lambda v: v.isoformat() if v else None,
            datetime: lambda v: v.isoformat() if v else None
        }
    )


# ============================================================================
# PORTFOLIO-LEVEL SCHEMAS - Aggregated pricing outputs
# ============================================================================

class PortfolioSummaryMetrics(BaseModel):
    """Portfolio-level summary metrics."""
    
    # Portfolio size
    total_loans: int = Field(..., description="Total number of loans")
    total_balance: Decimal = Field(..., description="Total current balance")
    total_fair_value: Decimal = Field(..., description="Total fair value")
    
    # Weighted averages
    weighted_avg_price: float = Field(..., description="Weighted average price")
    weighted_avg_yield: float = Field(..., description="Weighted average yield")
    weighted_avg_spread: float = Field(..., description="Weighted average spread")
    weighted_avg_wal: float = Field(..., description="Weighted average life")
    weighted_avg_ltv: float = Field(..., description="Weighted average LTV")
    weighted_avg_dscr: float = Field(..., description="Weighted average DSCR")
    
    # Risk metrics
    total_expected_loss: Decimal = Field(..., description="Total expected loss")
    expected_loss_rate: float = Field(..., description="Expected loss rate")
    loans_in_default: int = Field(0, description="Number of loans in default")
    balance_in_default: Decimal = Field(Decimal("0"), description="Balance of defaulted loans")
    
    # Sector breakdown
    sector_breakdown: Dict[str, Dict[str, Union[int, Decimal, float]]] = Field(
        ..., 
        description="Breakdown by property sector"
    )
    
    # Status breakdown
    status_breakdown: Dict[str, Dict[str, Union[int, Decimal, float]]] = Field(
        ..., 
        description="Breakdown by loan status"
    )

    model_config = ConfigDict(
        json_encoders={
            Decimal: lambda v: float(v) if v else None,
            date: lambda v: v.isoformat() if v else None,
            datetime: lambda v: v.isoformat() if v else None
        }
    )


class PricingSummaryOutput(BaseModel):
    """Complete pricing summary output."""
    
    metadata: Dict[str, Union[str, int, date]] = Field(
        ..., 
        description="Metadata about the pricing run"
    )
    summary_metrics: PortfolioSummaryMetrics = Field(
        ..., 
        description="Portfolio-level summary"
    )
    loans: List[LoanPricingOutput] = Field(
        ..., 
        description="Individual loan pricing details"
    )

    model_config = ConfigDict(
        json_encoders={
            Decimal: lambda v: float(v) if v else None,
            date: lambda v: v.isoformat() if v else None,
            datetime: lambda v: v.isoformat() if v else None
        }
    )


# ============================================================================
# RESPONSE SCHEMAS - API response wrappers
# ============================================================================

class PricingOutputResponse(BaseModel):
    """Response schema for pricing-output endpoint."""
    
    metadata: Dict[str, Union[str, int, date]]
    pricing_results: List[SimplifiedLoanPricing]

    model_config = ConfigDict(
        json_encoders={
            Decimal: lambda v: float(v) if v else None,
            date: lambda v: v.isoformat() if v else None,
            datetime: lambda v: v.isoformat() if v else None
        }
    )


class LoanPricingResponse(BaseModel):
    """Response schema for loan-pricing endpoint (list of detailed pricing)."""
    
    loans: List[LoanPricingOutput]
    total_count: int
    
    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            Decimal: lambda v: float(v) if v else None,
            date: lambda v: v.isoformat() if v else None,
            datetime: lambda v: v.isoformat() if v else None
        }
    )


# ============================================================================
# COMPARISON WITH CURRENT SYSTEM
# ============================================================================

"""
CURRENT vs EXPECTED OUTPUT COMPARISON:

1. PRICING-OUTPUT ENDPOINT (/api/v1/valuation/pricing-output)
   Current Structure:
   - Returns simplified pricing with nested spread_adjustments
   - Fields: loan_id, loan_name, price, fair_value, market_yield, etc.
   - Missing: Detailed loan info, risk metrics, dates, underwriting metrics
   
   Expected Structure:
   - Should return full LoanPricingOutput with all fields
   - Include risk metrics (PD, LGD, EAD, expected loss)
   - Include all dates and loan characteristics
   - Include underwriting metrics (LTV, DSCR, debt yield)

2. LOAN-PRICING ENDPOINT (/api/v1/valuation/loan-pricing)
   Current Structure:
   - Returns most fields but in flat structure
   - All spread adjustments at same level as other fields
   - Risk metrics partially included
   
   Expected Structure:
   - Group related fields into nested objects:
     - pricing_metrics: yields, spreads, valuation
     - spread_adjustments: all adjustment fields
     - risk_metrics: PD, LGD, EAD, loss info
   - Consistent field naming and types

3. LOAN-RISK-METRICS ENDPOINT (/api/v1/valuation/loan-risk-metrics)
   Current Structure:
   - Limited risk fields (pd, lgd, ead, expected_loss)
   - Uses rp_system_id correctly
   - Missing many risk-related fields
   
   Expected Structure:
   - Complete RiskMetrics object
   - Include percentage versions of metrics
   - Include amount versions (not just ratios)
   - Include recovery and default timing info

4. PRICING-SUMMARY ENDPOINT (/api/v1/valuation/pricing-summary)
   Current Structure:
   - Not yet implemented
   
   Expected Structure:
   - Portfolio-level aggregations
   - Weighted average metrics
   - Breakdowns by sector and status
   - Total risk metrics

KEY DIFFERENCES TO ADDRESS:

1. Field Organization:
   - Current: Flat structure with all fields at same level
   - Expected: Nested objects grouping related fields

2. Field Naming:
   - Current: Inconsistent (e.g., market_yield vs market_yield_decimal)
   - Expected: Clear naming conventions with units

3. Missing Fields:
   - Many loan characteristics not returned
   - Risk metrics incomplete
   - Portfolio summaries not implemented

4. Data Types:
   - Need consistent use of Decimal for monetary values
   - Proper date/datetime handling
   - Clear percentage vs decimal conventions

IMPLEMENTATION RECOMMENDATIONS:

1. Create view transformations to map current data to expected structure
2. Add computed fields for missing metrics
3. Implement portfolio aggregation logic
4. Ensure consistent JSON serialization
5. Document all field mappings and calculations
"""