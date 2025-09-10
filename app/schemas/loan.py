"""
Pydantic schemas for Loan API.
"""

from pydantic import BaseModel, Field, RootModel, ConfigDict
from datetime import datetime, date
from typing import Optional, List, Union
from uuid import UUID
from decimal import Decimal
from app.schemas.property_location import PropertyLocationCreate


class LoanBase(BaseModel):
    """Base schema for Loan. rp_system_id is the business identifier, required for all operations."""
    rp_system_id: int
    pricing_scenario: str
    maturity_assumption: Optional[str] = None
    credit_spread: Decimal
    market_yield: Optional[Decimal] = None
    loss_scenario: Optional[str] = None
    pd: Optional[Decimal] = None
    ead: Optional[Decimal] = None
    lgd: Optional[Decimal] = None
    lag_to_recovery: Optional[int] = None
    default_date: Optional[str] = None
    cdr: Optional[Decimal] = None
    client_loan_number: str
    loan_name: str
    property_sector: str
    property_type: str
    property_lifecycle_financing: str
    sponsor_borrower: str
    original_balance: Decimal
    current_balance: Decimal
    currency: str
    client_percentage: Decimal
    pik_balance: Optional[Decimal] = None
    position_in_capital_stack: str
    amortization_type: str
    periodicity: str
    interest_day_count: str
    io_end_date: Optional[str] = None
    original_amortization_term: Optional[int] = None
    contractual_pi_payment_amount: Optional[Decimal] = None
    accrual_type: str
    pik_coupon: Optional[Decimal] = None
    commitment_type: str
    unfunded_commitment_fee: Optional[Decimal] = None
    interest_type: str
    fixed_rate_coupon: Optional[Decimal] = None
    floating_rate_index: Optional[str] = None
    floating_rate_margin: Optional[Decimal] = None
    index_cap: Optional[Decimal] = None
    index_floor: Optional[Decimal] = None
    ltv_current: Optional[Decimal] = None
    dscr_current: Optional[Decimal] = None
    debt_yield_current: Optional[Decimal] = None
    noi: Optional[Decimal] = None
    origination_date: Optional[Union[date, str]] = None
    first_payment_date: Optional[Union[date, str]] = None
    original_maturity_date: Optional[Union[date, str]] = None
    prepayment_lockout_end_date: Optional[str] = None
    open_call_period_date: Optional[str] = None
    first_extension_date: Optional[str] = None
    first_extension_fee: Optional[Decimal] = None
    second_extension_date: Optional[str] = None
    second_extension_fee: Optional[Decimal] = None
    third_extension_date: Optional[str] = None
    third_extension_fee: Optional[Decimal] = None
    exit_fee: Optional[Decimal] = None
    loan_status: str  # Note: column name is loan_status, not status
    commentary: str
    internal_credit_rating: Optional[str] = None
    watchlist_monitoring: Optional[str] = None
    step_up_date: Optional[str] = None
    step_up_incremental_rate: Optional[Decimal] = None
    prepayment_penalty_type: Optional[str] = None
    prepayment_penalty_description: Optional[str] = None
    in_forbearance: Optional[str] = None
    forbearance_start_date: Optional[str] = None
    forbearance_original_term: Optional[int] = None
    forbearance_type: Optional[str] = None
    forbearance_payback_start_date: Optional[str] = None
    forbearance_payback_term: Optional[int] = None
    pi_scheduled_amortization: Optional[str] = None
    custom_payment_dates_schedule: Optional[str] = None
    default_interest_schedule: Optional[str] = None
    preferred_equity_equity_kicker_schedule: Optional[str] = None
    step_up_coupons: Optional[str] = None
    step_up_margin_interest_rate_floor: Optional[str] = None
    proforma_assumptions: Optional[str] = None
    custom_interest_type_timing: Optional[str] = None
    x1: Optional[str] = None
    x2: Optional[str] = None
    x3: Optional[str] = None
    property_locations: Optional[List[PropertyLocationCreate]] = None


class LoanCreate(LoanBase):
    """Schema for creating a Loan."""
    rp_system_id: int


class LoanUpdate(BaseModel):
    """Schema for updating a Loan."""
    rp_system_id: Optional[int] = None
    portfolio_id: Optional[UUID] = None
    system_id: Optional[int] = None
    pricing_scenario: Optional[str] = None
    maturity_assumption: Optional[str] = None
    credit_spread: Optional[Decimal] = None
    market_yield: Optional[Decimal] = None
    loss_scenario: Optional[str] = None
    pd: Optional[Decimal] = None
    ead: Optional[Decimal] = None
    lgd: Optional[Decimal] = None
    lag_to_recovery: Optional[int] = None
    default_date: Optional[str] = None
    cdr: Optional[Decimal] = None
    client_loan_number: Optional[str] = None
    loan_name: Optional[str] = None
    property_sector: Optional[str] = None
    property_type: Optional[str] = None
    property_lifecycle_financing: Optional[str] = None
    sponsor_borrower: Optional[str] = None
    original_balance: Optional[Decimal] = None
    current_balance: Optional[Decimal] = None
    currency: Optional[str] = None
    client_percentage: Optional[Decimal] = None
    pik_balance: Optional[Decimal] = None
    position_in_capital_stack: Optional[str] = None
    amortization_type: Optional[str] = None
    periodicity: Optional[str] = None
    interest_day_count: Optional[str] = None
    io_end_date: Optional[str] = None
    original_amortization_term: Optional[int] = None
    contractual_pi_payment_amount: Optional[Decimal] = None
    accrual_type: Optional[str] = None
    pik_coupon: Optional[Decimal] = None
    commitment_type: Optional[str] = None
    unfunded_commitment_fee: Optional[Decimal] = None
    interest_type: Optional[str] = None
    fixed_rate_coupon: Optional[Decimal] = None
    floating_rate_index: Optional[str] = None
    floating_rate_margin: Optional[Decimal] = None
    index_cap: Optional[Decimal] = None
    index_floor: Optional[Decimal] = None
    ltv_current: Optional[Decimal] = None
    dscr_current: Optional[Decimal] = None
    debt_yield_current: Optional[Decimal] = None
    noi: Optional[Decimal] = None
    origination_date: Optional[str] = None
    first_payment_date: Optional[str] = None
    original_maturity_date: Optional[str] = None
    prepayment_lockout_end_date: Optional[str] = None
    open_call_period_date: Optional[str] = None
    first_extension_date: Optional[str] = None
    first_extension_fee: Optional[Decimal] = None
    second_extension_date: Optional[str] = None
    second_extension_fee: Optional[Decimal] = None
    third_extension_date: Optional[str] = None
    third_extension_fee: Optional[Decimal] = None
    exit_fee: Optional[Decimal] = None
    loan_status: Optional[str] = None
    commentary: Optional[str] = None
    internal_credit_rating: Optional[str] = None
    watchlist_monitoring: Optional[str] = None
    step_up_date: Optional[str] = None
    step_up_incremental_rate: Optional[Decimal] = None
    prepayment_penalty_type: Optional[str] = None
    prepayment_penalty_description: Optional[str] = None
    in_forbearance: Optional[str] = None
    forbearance_start_date: Optional[str] = None
    forbearance_original_term: Optional[int] = None
    forbearance_type: Optional[str] = None
    forbearance_payback_start_date: Optional[str] = None
    forbearance_payback_term: Optional[int] = None
    pi_scheduled_amortization: Optional[str] = None
    custom_payment_dates_schedule: Optional[str] = None
    default_interest_schedule: Optional[str] = None
    preferred_equity_equity_kicker_schedule: Optional[str] = None
    step_up_coupons: Optional[str] = None
    step_up_margin_interest_rate_floor: Optional[str] = None
    proforma_assumptions: Optional[str] = None
    custom_interest_type_timing: Optional[str] = None
    x1: Optional[str] = None
    x2: Optional[str] = None
    x3: Optional[str] = None


class LoanResponse(LoanBase):
    """Schema for Loan responses."""
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            datetime: lambda v: v.isoformat() if v else None,
            date: lambda v: v.isoformat() if v else None,
            Decimal: lambda v: str(v) if v else None
        }
    ) 


class LoanIdentification(BaseModel):
    rp_system_id: int
    client_loan_number: str
    loan_name: str

class PropertyLocationResponse(BaseModel):
    location_id: str  # String to handle both UUID and integer IDs
    street: str
    city: str
    state: str
    zip_code: Optional[str] = None
    country: str
    region: str
    created_at: Optional[datetime] = None
    
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat() if v else None,
            date: lambda v: v.isoformat() if v else None
        }
    )

class PropertyDetails(BaseModel):
    sector: str
    property_type: str
    locations: Optional[List[PropertyLocationResponse]] = None

class FinancialTerms(BaseModel):
    original_balance: Decimal
    current_balance: Decimal
    interest_rate: Optional[Decimal] = None
    maturity_date: str

class RiskMetrics(BaseModel):
    ltv: Optional[Decimal] = None
    dscr: Optional[Decimal] = None
    debt_yield: Optional[Decimal] = None

class PricingResults(BaseModel):
    market_yield: Optional[Decimal] = None
    fair_value: Optional[Decimal] = None
    price: Optional[Decimal] = None
    wal: Optional[Decimal] = None
    modified_duration: Optional[Decimal] = None

class LoanDetailResponse(BaseModel):
    loan_identification: LoanIdentification
    property_details: PropertyDetails
    financial_terms: FinancialTerms
    risk_metrics: RiskMetrics
    pricing_results: PricingResults 

class PricingEngineLoanDetail(BaseModel):
    loan_id: str
    pricing_scenario: Optional[str] = None
    maturity_assumption: Optional[str] = None
    credit_spread: Optional[Decimal] = None
    market_yield: Optional[Decimal] = None
    loss_scenario: Optional[str] = None
    risk_metrics: Optional[dict] = None
    loan_identification: Optional[dict] = None
    property_details: Optional[dict] = None
    borrower: Optional[dict] = None
    loan_amounts: Optional[dict] = None
    loan_structure: Optional[dict] = None
    valuation_results: Optional[dict] = None
    # Add more fields as needed

class PortfolioAnalysis(RootModel[dict]):
    pass

class PricingEngineOutput(BaseModel):
    metadata: dict
    pricing_results: List[PricingEngineLoanDetail]
    portfolio_analysis: Optional[PortfolioAnalysis] = None 