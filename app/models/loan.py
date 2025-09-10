"""
Loan database model - Updated to match actual database schema.
"""

from sqlalchemy import Column, String, Integer, BigInteger, Numeric, Text, DateTime, Date, CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database.session import Base


class Loan(Base):
    """Loan model matching the actual database schema."""
    
    __tablename__ = "loans"
    
    # Primary key
    rp_system_id = Column(BigInteger, primary_key=True)
    
    # Loan identification and scenario fields
    pricing_scenario = Column(String(100))
    maturity_assumption = Column(String(100))
    client_loan_number = Column(String(100))
    loan_name = Column(String(255))
    
    # Property information
    property_sector = Column(String(50))
    property_type = Column(String(100))
    property_lifecycle_financing = Column(String(50))
    sponsor_borrower = Column(String(255))
    
    # Financial amounts
    original_balance = Column(Numeric(18, 2))
    current_balance = Column(Numeric(18, 2))
    currency = Column(String(3), default='USD')
    client_percentage = Column(Numeric(5, 2), default=100)
    pik_balance = Column(Numeric(18, 2))
    
    # Loan structure
    position_in_capital_stack = Column(String(100))
    amortization_type = Column(String(50))
    periodicity = Column(String(20))
    interest_day_count = Column(String(20))
    io_end_date = Column(Date)
    original_amortization_term = Column(Integer)
    contractual_pi_payment_amount = Column(Numeric(18, 2))
    
    # Interest and fees
    accrual_type = Column(String(50))
    pik_coupon = Column(Numeric(10, 6))
    commitment_type = Column(String(50))
    unfunded_commitment_fee = Column(Numeric(10, 6))
    interest_type = Column(String(20))
    fixed_rate_coupon = Column(Numeric(10, 6))
    floating_rate_index = Column(String(50))
    floating_rate_margin = Column(Numeric(10, 6))
    index_cap = Column(Numeric(10, 6))
    index_floor = Column(Numeric(10, 6))
    
    # Risk metrics
    ltv_current = Column(Numeric(10, 2))
    dscr_current = Column(Numeric(10, 2))
    debt_yield_current = Column(Numeric(10, 4))
    noi = Column(Numeric(18, 2))
    
    # Important dates
    origination_date = Column(Date)
    first_payment_date = Column(Date)
    original_maturity_date = Column(Date)
    prepayment_lockout_end_date = Column(Date)
    open_call_period_date = Column(Date)
    
    # Extension dates and fees
    first_extension_date = Column(Date)
    first_extension_fee = Column(Numeric(10, 6))
    second_extension_date = Column(Date)
    second_extension_fee = Column(Numeric(10, 6))
    third_extension_date = Column(Date)
    third_extension_fee = Column(Numeric(10, 6))
    exit_fee = Column(Numeric(10, 6))
    
    # Status and monitoring
    loan_status = Column(String(50))  # Note: column name is loan_status, not status
    commentary = Column(Text)
    internal_credit_rating = Column(String(10))
    watchlist_monitoring = Column(String(10))
    
    # Step-up and prepayment
    step_up_date = Column(Date)
    step_up_incremental_rate = Column(Numeric(10, 6))
    prepayment_penalty_type = Column(String(50))
    prepayment_penalty_description = Column(Text)
    
    # Forbearance
    in_forbearance = Column(String(10))
    forbearance_start_date = Column(Date)
    forbearance_original_term = Column(Integer)
    forbearance_type = Column(String(50))
    forbearance_payback_start_date = Column(Date)
    forbearance_payback_term = Column(Integer)
    
    # Pricing and risk parameters
    credit_spread = Column(Numeric(10, 6))
    market_yield = Column(Numeric(10, 6))
    loss_scenario = Column(String(50))
    pd = Column(Numeric(5, 2))
    ead = Column(Numeric(5, 2))
    lgd = Column(Numeric(5, 2))
    lag_to_recovery = Column(Integer)
    default_date = Column(Date)
    cdr = Column(Numeric(10, 6))
    
    # JSON fields for schedules
    pi_scheduled_amortization = Column(JSONB)
    custom_payment_dates_schedule = Column(JSONB)
    default_interest_schedule = Column(JSONB)
    preferred_equity_equity_kicker_schedule = Column(JSONB)
    step_up_coupons = Column(JSONB)
    step_up_margin_interest_rate_floor = Column(JSONB)
    proforma_assumptions = Column(JSONB)
    custom_interest_type_timing = Column(JSONB)
    
    # Additional fields
    x1 = Column(Text)
    x2 = Column(Text)
    x3 = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    loan_properties = relationship("LoanProperty", back_populates="loan", cascade="all, delete-orphan")
    
    # Table constraints matching the database
    __table_args__ = (
        CheckConstraint("ltv_current >= 0 AND ltv_current <= 200", name="chk_ltv"),
        CheckConstraint("dscr_current >= 0", name="chk_dscr"),
        CheckConstraint("pd >= 0 AND pd <= 100", name="chk_pd"),
        CheckConstraint("ead >= 0 AND ead <= 100", name="chk_ead"),
        CheckConstraint("lgd >= 0 AND lgd <= 100", name="chk_lgd"),
    )
    
    def __repr__(self):
        return f"<Loan(rp_system_id='{self.rp_system_id}', loan_name='{self.loan_name}')>"