"""
Database field to Excel column name mappings.
This module defines how database fields map to Excel column headers.
"""

# Database field to Excel column name mapping
COLUMN_MAPPING = {
    # Core identifiers
    'loan_id': 'Loan ID',
    'loan_name': 'Loan Name',
    'client_loan_number': 'Client Loan Number',
    'pricing_scenario': 'Pricing Scenario',
    
    # Property details
    'property_type': 'Property Type',
    'sector': 'Sector',
    'property_lifecycle_financing': 'Property Lifecycle Financing',
    'property_location': 'Property Location',
    
    # Loan amounts
    'original_balance': 'Original Balance',
    'current_balance': 'Current Balance - Includes Accrued Interest & PIK Interest',
    'pik_balance': 'PIK Balance',
    'currency': 'Currency',
    
    # Loan structure
    'periodicity': 'Periodicity',
    'loan_status': 'Loan Status',
    'coupon': 'Coupon',
    'interest_type': 'Interest Type',
    'amortization_type': 'Amortization Type',
    'position_in_capital_stack': 'Position in Capital Stack',
    'interest_day_count': 'Interest Day Count',
    
    # Risk fields - Using *_final versions with proper defaults and conversions
    'loss_scenario_final': 'Loss Scenario',
    'pd_final': 'PD',
    'ead_final': 'EAD',
    'lgd_final': 'LGD',
    'lag_to_recovery_final': 'Lag to Recovery',
    'default_date_final': 'Default Date',
    'cdr_final': 'CDR',
    'default_scenario_code': 'Default Scenario',
    
    # Dates
    'io_end_date': 'IO End Date',
    'original_maturity_date': 'Original Maturity Date',
    'effective_maturity_date': 'Maturity',
    'origination_date': 'Loan Origination Date',
    'first_extension_date': 'Extension 1st',
    'second_extension_date': 'Extension 2nd',
    'third_extension_date': 'Extension 3rd',
    'valuation_date': 'Valuation Date',
    'settlement_date': 'Settlement Date',
    
    # Pricing values
    'fair_value_clean': 'Fair Value',
    'fair_value_dirty': 'Fair Value + Accrued Interest',
    'accrued_interest': 'Accrued Interest',  # Column 33 - dollar amount
    'price_clean_decimal': 'Price Clean',
    'price_dirty_decimal': 'Price Dirty',
    'price_clean_pct': 'Price',
    'price_dirty_pct': 'Price including Accrued',
    # Note: Column 36 also called 'Accrued Interest' but is percentage
    # Handled separately in column_transformations.py
    
    # NPV and proceeds
    'npv_value': 'NPV',
    'gross_proceeds': 'Gross Proceeds',
    'net_proceeds': 'Net Proceeds',
    
    # Yields and spreads  
    'market_yield_cbe': 'Market Yield (or Discount Rate)',
    'component_yield_pct': 'Component Yield %',
    'component_yield_decimal': 'Conponent Yield',  # Intentional typo
    'benchmark_yield': 'Benchmark Yield | Index Rate',
    'benchmark_type': 'Becnhmark',  # Intentional typo
    'rpx_total_spread_bps': 'Total Spread (bps)',
    'display_credit_spread': 'Credit Spread',  # Using display_credit_spread for Excel
    'dmor_spread_bps': 'DMor Spread (bps)',
    'effective_credit_spread': 'Effective Spread',
    
    # Risk metrics
    'wal_years': 'WAL (yrs)',
    'macaulay_duration_years': 'Macaulay Duration',
    'modified_duration_years': 'Modified Duration (yrs)',
    'convexity': 'Convexity',
    
    # Credit metrics
    'ltv_current': 'LTV',
    'dscr_current': 'DSCR',
    'client_percentage': 'Client % of Total Loan Facility',
    
    # Other details
    'borrower': 'Sponsor/Borrower',
    'commentary': 'Propoerty & Loan Commentary',  # Intentional typo
    'coupon_description': 'Coupon Description',
    'prepayment_penalty_type': 'Prepayment Type',
    'internal_credit_rating': 'Credit Rating',
    'calculated_maturity_assumption': 'Maturity Assumption'
}